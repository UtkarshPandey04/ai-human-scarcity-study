"""Fast, no-training tests for agents/rl_policy.py: observation/action encoding, reward shaping,
and Gymnasium API structural correctness (via SB3's check_env). Deliberately excludes an actual
PPO training run — that's slow (minutes, not milliseconds) and belongs in a manually-run gate
check (`python -m agents.rl_policy train && python -m agents.rl_policy evaluate`), not the fast
suite `python tasks.py validate` runs on every change.
"""

import unittest

import numpy as np

from agents.environment import Observation, OtherPlayerView
from agents.rl_policy import (
    DEATH_PENALTY,
    LEARNER_ACTIONS,
    OBS_DIM,
    ScarcitySingleAgentEnv,
    _reward_for,
    decode_action,
    encode_observation,
)
from common.actions import ActionType


def _make_observation(**overrides) -> Observation:
    defaults = dict(
        player_id="LEARNER",
        round=1,
        total_rounds=10,
        scenario="calm",
        is_drought=False,
        own_resource=5.0,
        own_alive=True,
        received_share_last_round=0.0,
        pool_stock=80.0,
        pool_capacity=100.0,
        others=(
            OtherPlayerView(player_id="OPP1", alive=True, last_action=None, last_action_target=None),
        ),
    )
    defaults.update(overrides)
    return Observation(**defaults)


class TestObservationEncoding(unittest.TestCase):
    def test_shape_and_dtype(self):
        vec = encode_observation(_make_observation())
        self.assertEqual(vec.shape, (OBS_DIM,))
        self.assertEqual(vec.dtype, np.float32)

    def test_is_drought_flag_reflected(self):
        calm_vec = encode_observation(_make_observation(is_drought=False))
        drought_vec = encode_observation(_make_observation(is_drought=True))
        self.assertNotEqual(calm_vec[2], drought_vec[2])

    def test_no_others_does_not_divide_by_zero(self):
        vec = encode_observation(_make_observation(others=()))
        self.assertTrue(np.all(np.isfinite(vec)))

    def test_zero_pool_capacity_does_not_divide_by_zero(self):
        vec = encode_observation(_make_observation(pool_stock=0.0, pool_capacity=0.0))
        self.assertTrue(np.all(np.isfinite(vec)))


class TestActionDecoding(unittest.TestCase):
    def test_every_index_decodes_to_a_valid_action(self):
        for i in range(len(LEARNER_ACTIONS)):
            action = decode_action(i)
            action.validate()  # must not raise

    def test_decoded_actions_exclude_social_actions(self):
        decoded_types = {decode_action(i).type for i in range(len(LEARNER_ACTIONS))}
        self.assertNotIn(ActionType.SHARE, decoded_types)
        self.assertNotIn(ActionType.COMMUNICATE, decoded_types)


class TestRewardShaping(unittest.TestCase):
    def test_positive_delta_when_alive(self):
        self.assertEqual(_reward_for(resource_before=5, resource_after=6, alive=True), 1.0)

    def test_negative_delta_when_alive(self):
        self.assertEqual(_reward_for(resource_before=5, resource_after=3, alive=True), -2.0)

    def test_death_adds_penalty_on_top_of_delta(self):
        reward = _reward_for(resource_before=2, resource_after=-1, alive=False)
        self.assertEqual(reward, (-1 - 2) + DEATH_PENALTY)


class TestEnvStructural(unittest.TestCase):
    """Structural correctness only — no training. See module docstring."""

    def test_check_env_passes(self):
        from stable_baselines3.common.env_checker import check_env

        env = ScarcitySingleAgentEnv(scenario="calm", seed=0)
        check_env(env, warn=True)  # raises on structural violations

    def test_reset_returns_obs_and_info(self):
        env = ScarcitySingleAgentEnv(scenario="calm", seed=0)
        obs, info = env.reset(seed=0)
        self.assertEqual(obs.shape, (OBS_DIM,))
        self.assertIsInstance(info, dict)

    def test_step_returns_five_tuple_with_correct_types(self):
        env = ScarcitySingleAgentEnv(scenario="calm", seed=0)
        env.reset(seed=0)
        obs, reward, terminated, truncated, info = env.step(0)
        self.assertEqual(obs.shape, (OBS_DIM,))
        self.assertIsInstance(reward, float)
        self.assertIsInstance(terminated, bool)
        self.assertIsInstance(truncated, bool)
        self.assertIsInstance(info, dict)

    def test_always_gather_survives_calm_without_training(self):
        """Sanity check on the environment/reward design itself, independent of any learned
        policy: under `calm`, always gathering should comfortably survive the full 10 rounds
        (gather yield 3 > survival cost 2 every round). If this fails, the environment or reward
        shaping is broken, not the RL policy.
        """
        gather_idx = LEARNER_ACTIONS.index(ActionType.GATHER)
        env = ScarcitySingleAgentEnv(scenario="calm", seed=0)
        env.reset(seed=0)
        done = False
        info = {}
        while not done:
            obs, reward, terminated, truncated, info = env.step(gather_idx)
            done = terminated or truncated
        self.assertTrue(info["alive"])

    def test_same_seed_is_reproducible(self):
        gather_idx = LEARNER_ACTIONS.index(ActionType.GATHER)

        def run(seed):
            env = ScarcitySingleAgentEnv(scenario="calm", seed=seed)
            obs, _ = env.reset(seed=seed)
            trace = [obs.tolist()]
            done = False
            while not done:
                obs, reward, terminated, truncated, info = env.step(gather_idx)
                trace.append(obs.tolist())
                done = terminated or truncated
            return trace

        self.assertEqual(run(7), run(7))


if __name__ == "__main__":
    unittest.main()
