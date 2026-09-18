"""Phase F — hybrid arbitration. The architectural claim of the paper: reflex versus deliberation.
Non-social rounds go to the RL policy (Phase D); social ones go to the LLM (Phase E). Every
decision logs `meta.decision_source` ("rl" or "llm"), which is what buys the free figure the plan
calls out — how often does the agent deliberate, and does that rate climb with scarcity.

Also the home of the three ablation arms Phase G's trial campaign will sweep: `rl_only`,
`llm_only`, `hybrid`. Selecting between them is a constructor argument, not a code branch — see
`HybridAgent.arm` and Gate F's requirement that switching arms costs no code change.
"""

from __future__ import annotations

from dataclasses import dataclass

from agents.environment import Observation
from agents.llm_reasoning import decide as llm_decide
from agents.rl_policy import DEFAULT_MODEL_PATH, decode_action, encode_observation
from common.actions import Action
from common.config import SURVIVAL_COST

ARMS = ("rl_only", "llm_only", "hybrid")

# own_resource <= SURVIVAL_COST * this multiplier counts as "under pressure" for routing purposes.
SOCIAL_STOCK_THRESHOLD_MULTIPLIER = 2


def is_social_decision(obs: Observation) -> bool:
    """Whether this round's decision needs the LLM's social reasoning, rather than the RL reflex
    policy alone.

    Adapted from the plan's "another player adjacent, a pending promise, stock below threshold"
    for a no-grid environment (INTEGRATION_ISSUES.md Blocker 3): there is no spatial adjacency
    here — every alive co-player is always "present" every round, so raw adjacency would fire on
    nearly every round and defeat the point of routing at all. Instead this fires when the round
    actually has scarcity-relevant social stakes: the player is under resource pressure, it's a
    drought round, or another player shared with them last round (a live reciprocity opportunity
    worth reasoning about, e.g. whether to reciprocate or exploit it).
    """
    if not any(o.alive for o in obs.others):
        return False
    under_pressure = obs.own_resource <= SURVIVAL_COST * SOCIAL_STOCK_THRESHOLD_MULTIPLIER
    reciprocity_opportunity = obs.received_share_last_round > 0
    return under_pressure or obs.is_drought or reciprocity_opportunity


def load_rl_model(model_path: str = DEFAULT_MODEL_PATH):
    """Loads a trained PPO checkpoint (agents/rl_policy.py train). Import kept local so importing
    this module doesn't require stable-baselines3 to be installed for an llm_only-only use case.
    """
    from stable_baselines3 import PPO

    return PPO.load(model_path)


@dataclass
class HybridAgent:
    """Decides one action for one player, per `arm`:

    - "rl_only": always the trained RL policy. Action space is gather/hoard/skip/move only — no
      share, no communicate — by construction of the RL policy's action space (agents/rl_policy.py).
      This is a real ablation, not a limitation: it answers "what happens if this agent can never
      act socially at all."
    - "llm_only": always the LLM reasoning layer (agents/llm_reasoning.py) — full six-action space.
    - "hybrid": RL for non-social rounds, LLM for social ones, per `is_social_decision` above.
    """

    arm: str
    rl_model: object | None = None  # a loaded stable_baselines3.PPO; required for rl_only/hybrid
    provider: str | None = None  # passed through to agents.llm_reasoning.decide
    model: str | None = None

    def __post_init__(self):
        if self.arm not in ARMS:
            raise ValueError(f"unknown arm {self.arm!r}, must be one of {ARMS}")
        if self.arm in ("rl_only", "hybrid") and self.rl_model is None:
            raise ValueError(f"arm {self.arm!r} requires rl_model — see agents.hybrid_agent.load_rl_model")

    def decide(self, obs: Observation) -> tuple[Action, dict]:
        if self.arm == "llm_only":
            return self._decide_llm(obs)
        if self.arm == "rl_only":
            return self._decide_rl(obs)
        # hybrid
        if is_social_decision(obs):
            return self._decide_llm(obs)
        return self._decide_rl(obs)

    def _decide_rl(self, obs: Observation) -> tuple[Action, dict]:
        vec = encode_observation(obs)
        action_idx = int(self.rl_model.predict(vec, deterministic=True)[0])
        action = decode_action(action_idx)
        return action, {"decision_source": "rl", "llm_parse_failure": False}

    def _decide_llm(self, obs: Observation) -> tuple[Action, dict]:
        action, meta = llm_decide(obs, provider=self.provider, model=self.model)
        meta["decision_source"] = "llm"
        return action, meta
