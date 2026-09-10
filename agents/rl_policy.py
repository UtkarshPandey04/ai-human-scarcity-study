"""Phase D — the RL reflex policy. Trains one shared PPO network (via Stable-Baselines3) to
handle movement/gathering decisions; see agents/PHASE_PLAN.md Phase D for why plain SB3 can't
just be pointed at a 5-player env, and agents/hybrid_agent.py (Phase F) for where this plugs in
alongside the LLM reasoning layer for social decisions.

Scope, per the plan: "the RL layer learns movement and harvest timing — nothing social." The
learner's action space is therefore restricted to gather / hoard / skip / move — no share, no
communicate. Trained on `calm` only, with no scripted shock, so the gate is a pure test of
"can this policy keep itself alive," not scarcity-response behaviour (that's what the LLM layer
and the full trial campaign are for).

## Architecture: single-slot self-play (a deliberate simplification of "true" IPPO)

The plan's recommended design is parameter-shared IPPO: every player's (obs, action, reward) each
round becomes a training sample for one shared policy, so a single episode yields NUM_PLAYERS
samples. What's implemented here is simpler: only the designated "learner" slot's transitions are
pushed into SB3's rollout buffer. The other `NUM_PLAYERS - 1` seats are driven by the *same live
model* (via `ScarcitySingleAgentEnv.set_self_play_policy`), so it genuinely is self-play against a
shared policy — just without the ~5x sample-efficiency of pushing every seat's experience into the
buffer. That upgrade (wrap as a multi-agent VecEnv, or move to PufferLib's native multi-agent
vectorization — see the pufferlib skill) is a bounded follow-up if training proves too slow, not a
prerequisite for Gate D: calm has no adversarial pressure over the shared pool at 5 players, so a
single well-trained slot should clear "beats random" comfortably. Don't upgrade this speculatively;
upgrade it only if a real training run shows it's needed.

Opponents default to a mix of agents/coplayers.py policies (for a stable, always-available
baseline) until `set_self_play_policy` is called, which is what `train()` does once the model
exists — see the reset()/opponent-selection logic below.
"""

from __future__ import annotations

import argparse
from typing import Callable

import numpy as np
from gymnasium import Env, spaces

from agents.coplayers import get_policy
from agents.environment import Observation, ScarcityEnv
from common.actions import Action, ActionType, Direction
from common.config import NUM_PLAYERS, START_WATER

# --- Observation encoding: Observation -> fixed-length float vector -------------------------

OBS_DIM = 6

# The four non-social actions Phase D's learner is allowed to take. Index order is the discrete
# action encoding SB3 sees; do not reorder without retraining.
LEARNER_ACTIONS = (ActionType.GATHER, ActionType.HOARD, ActionType.SKIP, ActionType.MOVE)


def encode_observation(obs: Observation) -> np.ndarray:
    """Flatten an Observation into the fixed vector the policy network sees. Deliberately
    excludes anything about *other* players beyond a headcount — Phase D is not social."""
    alive_others = sum(1 for o in obs.others if o.alive)
    return np.array(
        [
            obs.own_resource / (START_WATER * 2),  # loose scale; PPO tolerates unnormalized obs
            obs.round / obs.total_rounds,
            float(obs.is_drought),
            obs.pool_stock / obs.pool_capacity if obs.pool_capacity else 0.0,
            obs.received_share_last_round,
            alive_others / max(1, len(obs.others)),
        ],
        dtype=np.float32,
    )


def decode_action(action_idx: int) -> Action:
    action_type = LEARNER_ACTIONS[int(action_idx)]
    if action_type == ActionType.MOVE:
        # Direction is inert (no grid — see environment.py's module docstring / Blocker 3), so
        # any fixed direction is equivalent; NORTH is arbitrary.
        return Action(type=action_type, direction=Direction.NORTH)
    return Action(type=action_type)


# --- Reward shaping ----------------------------------------------------------------------------

DEATH_PENALTY = -5.0


def _reward_for(resource_before: float, resource_after: float, alive: bool) -> float:
    reward = resource_after - resource_before
    if not alive:
        reward += DEATH_PENALTY
    return float(reward)


# --- The Gymnasium environment ------------------------------------------------------------------

OpponentPolicyFn = Callable[[np.ndarray], int]


class ScarcitySingleAgentEnv(Env):
    """Wraps ScarcityEnv from one designated player's ("the learner") point of view. The other
    `NUM_PLAYERS - 1` seats are filled by fixed agents/coplayers.py policies unless
    `set_self_play_policy` has been called, in which case they're driven by that callable instead
    (see module docstring: this is what makes training self-play against a shared policy).
    """

    metadata = {"render_modes": []}

    def __init__(self, scenario: str = "calm", seed: int = 0):
        super().__init__()
        self.scenario = scenario
        self.base_seed = seed
        self.observation_space = spaces.Box(low=-10.0, high=10.0, shape=(OBS_DIM,), dtype=np.float32)
        self.action_space = spaces.Discrete(len(LEARNER_ACTIONS))

        self.learner_id = "LEARNER"
        self._opponent_ids = [f"OPP{i + 1}" for i in range(NUM_PLAYERS - 1)]
        self._self_play_policy_fn: OpponentPolicyFn | None = None
        self._env: ScarcityEnv | None = None
        self._opponent_policies: dict[str, object] = {}
        self._episode_count = 0
        self._current_obs_dict: dict[str, Observation] = {}

    def set_self_play_policy(self, policy_fn: OpponentPolicyFn | None) -> None:
        """Pass a callable(obs_vector) -> discrete_action_idx to drive every opponent seat with
        it (typically the live model being trained). Pass None to fall back to the fixed
        agents/coplayers.py mix.
        """
        self._self_play_policy_fn = policy_fn

    def _make_opponent_policies(self, seed: int) -> dict[str, object]:
        if self._self_play_policy_fn is not None:
            return {}  # handled directly in step(); no per-policy objects needed
        # Fixed, always-available baseline: cycle through the Phase B policy roster so the
        # learner sees some variety even before self-play kicks in.
        names = ["cooperator", "free_rider", "tit_for_tat", "random"]
        return {
            pid: get_policy(names[i % len(names)], seed=seed + i)
            for i, pid in enumerate(self._opponent_ids)
        }

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        episode_seed = seed if seed is not None else self.base_seed + self._episode_count
        self._episode_count += 1

        self._env = ScarcityEnv(
            scenario=self.scenario, seed=episode_seed, player_ids=[self.learner_id, *self._opponent_ids]
        )
        self._opponent_policies = self._make_opponent_policies(episode_seed)
        self._current_obs_dict = self._env.reset()
        return encode_observation(self._current_obs_dict[self.learner_id]), {}

    def step(self, action: int):
        assert self._env is not None, "call reset() before step()"

        obs_dict = self._current_obs_dict  # this round's obs, for opponent decisions
        actions: dict[str, Action] = {self.learner_id: decode_action(action)}
        for pid in self._opponent_ids:
            if not self._env.players[pid].alive:
                continue
            if self._self_play_policy_fn is not None:
                opp_action_idx = self._self_play_policy_fn(encode_observation(obs_dict[pid]))
                actions[pid] = decode_action(opp_action_idx)
            else:
                actions[pid] = self._opponent_policies[pid].act(obs_dict[pid])

        resource_before = self._env.players[self.learner_id].resource
        next_obs_dict, done, _log_rows = self._env.step(actions)
        self._current_obs_dict = next_obs_dict
        learner_state = self._env.players[self.learner_id]

        reward = _reward_for(resource_before, learner_state.resource, learner_state.alive)
        terminated = not learner_state.alive
        truncated = done and learner_state.alive  # ran out of rounds while still alive
        obs = encode_observation(next_obs_dict[self.learner_id])
        info = {"resource": learner_state.resource, "alive": learner_state.alive}
        return obs, reward, terminated, truncated, info


# --- Training / evaluation entry points --------------------------------------------------------

MODEL_DIR = "models"
DEFAULT_MODEL_PATH = f"{MODEL_DIR}/rl_policy_calm.zip"


def train(scenario: str = "calm", seed: int = 0, timesteps: int = 100_000, model_path: str = DEFAULT_MODEL_PATH):
    import os

    from stable_baselines3 import PPO

    env = ScarcitySingleAgentEnv(scenario=scenario, seed=seed)
    model = PPO("MlpPolicy", env, seed=seed, n_steps=256, batch_size=64, verbose=0)
    # Self-play: opponents are driven by this same model's current weights (see module docstring
    # for why this isn't snapshot-frozen self-play). Bound after construction so the closure
    # captures `model` itself, not a copy.
    env.set_self_play_policy(lambda obs: int(model.predict(obs, deterministic=False)[0]))

    model.learn(total_timesteps=timesteps, progress_bar=False)

    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save(model_path)
    return model_path


def _mean_survival(action_fn: Callable[[np.ndarray], int], scenario: str, seeds: list[int]) -> dict:
    """Run one episode per seed with the *learner* driven by `action_fn` and opponents driven by
    the fixed agents/coplayers.py mix (not self-play — this is a held-out evaluation, so opponents
    should be the same stable baseline regardless of which policy is being scored).
    """
    survived = 0
    final_resources = []
    for seed in seeds:
        env = ScarcitySingleAgentEnv(scenario=scenario, seed=seed)
        env.set_self_play_policy(None)
        obs, _info = env.reset(seed=seed)
        done = False
        while not done:
            action = action_fn(obs)
            obs, _reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
        survived += int(info["alive"])
        final_resources.append(info["resource"])
    n = len(seeds)
    return {
        "survival_rate": survived / n,
        "mean_final_resource": sum(final_resources) / n,
        "n_seeds": n,
    }


def evaluate_gate_d(model_path: str = DEFAULT_MODEL_PATH, scenario: str = "calm", n_seeds: int = 20) -> bool:
    """Gate D: the trained policy must beat a random baseline on mean survival under `calm`
    across held-out seeds. Held out from training by starting well past any seed `train()` could
    plausibly have used (training reseeds per-episode starting at its own `seed` argument, so a
    large offset here avoids any accidental overlap).
    """
    from stable_baselines3 import PPO

    model = PPO.load(model_path)
    held_out_seeds = range(10_000, 10_000 + n_seeds)

    rl_result = _mean_survival(
        lambda obs: int(model.predict(obs, deterministic=True)[0]), scenario, held_out_seeds
    )
    random_result = _mean_survival(
        lambda obs: int(np.random.randint(len(LEARNER_ACTIONS))), scenario, held_out_seeds
    )

    print(f"RL policy:     survival_rate={rl_result['survival_rate']:.2%}  "
          f"mean_final_resource={rl_result['mean_final_resource']:.2f}  (n={rl_result['n_seeds']})")
    print(f"Random policy: survival_rate={random_result['survival_rate']:.2%}  "
          f"mean_final_resource={random_result['mean_final_resource']:.2f}  (n={random_result['n_seeds']})")

    passed = rl_result["survival_rate"] > random_result["survival_rate"] or (
        rl_result["survival_rate"] == random_result["survival_rate"] == 1.0
        and rl_result["mean_final_resource"] > random_result["mean_final_resource"]
    )
    print(f"Gate D: {'PASS' if passed else 'FAIL'}")
    return passed


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_train = sub.add_parser("train")
    p_train.add_argument("--scenario", default="calm")
    p_train.add_argument("--seed", type=int, default=0)
    p_train.add_argument("--timesteps", type=int, default=100_000)
    p_train.add_argument("--model-path", default=DEFAULT_MODEL_PATH)

    p_eval = sub.add_parser("evaluate")
    p_eval.add_argument("--scenario", default="calm")
    p_eval.add_argument("--n-seeds", type=int, default=20)
    p_eval.add_argument("--model-path", default=DEFAULT_MODEL_PATH)

    args = parser.parse_args()
    if args.command == "train":
        path = train(scenario=args.scenario, seed=args.seed, timesteps=args.timesteps, model_path=args.model_path)
        print(f"Saved model to {path}")
        return 0
    else:
        passed = evaluate_gate_d(model_path=args.model_path, scenario=args.scenario, n_seeds=args.n_seeds)
        return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(_main())
