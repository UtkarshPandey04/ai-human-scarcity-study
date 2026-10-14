"""Smoke tests for agents/coplayers.py: every policy must return a structurally valid Action for
any observation it can actually encounter, for the full trial length, without crashing.
"""

import unittest

from agents.coplayers import POLICIES, get_policy
from agents.environment import ScarcityEnv


class TestAllPoliciesSurviveAFullTrial(unittest.TestCase):
    def test_every_policy_runs_without_error(self):
        for policy_name in POLICIES:
            with self.subTest(policy=policy_name):
                env = ScarcityEnv(scenario="drought", seed=3)
                policies = {
                    pid: get_policy(policy_name, seed=i) for i, pid in enumerate(env.player_ids)
                }
                obs = env.reset()
                done = False
                rounds_played = 0
                while not done:
                    actions = {}
                    for pid, o in obs.items():
                        if not env.players[pid].alive:
                            continue
                        action = policies[pid].act(o)
                        action.validate()  # raises if structurally malformed
                        actions[pid] = action
                    obs, done, _ = env.step(actions)
                    rounds_played += 1
                    self.assertLess(rounds_played, 1000, "trial did not terminate")

    def test_unknown_policy_name_raises(self):
        with self.assertRaises(ValueError):
            get_policy("not_a_real_policy")


class TestSmokeRunnerTrialIds(unittest.TestCase):
    """Regression test: a pilot-log sweep across multiple policies at the same seed must not
    produce colliding filenames — see the comment in agents/smoke_random.py::run_trial. This bug
    silently overwrote 45 of 60 pilot trials on disk before trial_id included the policy name.
    """

    def test_trial_id_differs_across_policies_at_same_seed(self):
        from agents.smoke_random import run_trial

        ids = {
            policy: run_trial("drought", seed=0, policy_name=policy)[0]["trial_id"]
            for policy in POLICIES
        }
        self.assertEqual(len(set(ids.values())), len(POLICIES))


class TestStrategicDeceiver(unittest.TestCase):
    """Verify StrategicDeceiver behavior: gathers when critical, deceives under scarcity,
    and gathers/hoards normally in abundance."""

    def setUp(self):
        from agents.coplayers import StrategicDeceiver
        self.policy = StrategicDeceiver(seed=42)

    def _make_obs(self, own_resource=10.0, is_drought=False, pool_stock=50.0):
        from agents.environment import Observation, OtherPlayerView
        return Observation(
            player_id="A2",
            round=1,
            total_rounds=10,
            scenario="drought" if is_drought else "calm",
            is_drought=is_drought,
            own_resource=own_resource,
            own_alive=True,
            received_share_last_round=0.0,
            pool_stock=pool_stock,
            pool_capacity=100.0,
            others=(OtherPlayerView(player_id="A1", alive=True, last_action=None, last_action_target=None),),
        )

    def test_gathers_when_own_resource_critical(self):
        from common.actions import ActionType
        from common.config import SURVIVAL_COST

        # Critical: own_resource <= SURVIVAL_COST (even during drought)
        obs_critical = self._make_obs(own_resource=SURVIVAL_COST, is_drought=True, pool_stock=5.0)
        action = self.policy.act(obs_critical)
        self.assertEqual(action.type, ActionType.GATHER)

        obs_below = self._make_obs(own_resource=SURVIVAL_COST - 1, is_drought=False, pool_stock=50.0)
        action_below = self.policy.act(obs_below)
        self.assertEqual(action_below.type, ActionType.GATHER)

    def test_emits_deceptive_claim_under_drought(self):
        from common.actions import ActionType, MessageKind

        obs = self._make_obs(own_resource=8.0, is_drought=True, pool_stock=50.0)
        action = self.policy.act(obs)
        self.assertEqual(action.type, ActionType.COMMUNICATE)
        self.assertEqual(action.target, "all")
        self.assertIsNotNone(action.message)
        self.assertEqual(action.message.kind, MessageKind.CLAIM_STOCK)
        self.assertLess(action.message.value, obs.own_resource)

    def test_emits_deceptive_claim_under_low_pool_stock(self):
        from common.actions import ActionType, MessageKind

        obs = self._make_obs(own_resource=6.0, is_drought=False, pool_stock=10.0)
        action = self.policy.act(obs)
        self.assertEqual(action.type, ActionType.COMMUNICATE)
        self.assertEqual(action.target, "all")
        self.assertIsNotNone(action.message)
        self.assertEqual(action.message.kind, MessageKind.CLAIM_STOCK)
        self.assertLess(action.message.value, obs.own_resource)

    def test_gathers_normally_in_abundance(self):
        from common.actions import ActionType

        obs = self._make_obs(own_resource=8.0, is_drought=False, pool_stock=50.0)
        action = self.policy.act(obs)
        self.assertEqual(action.type, ActionType.GATHER)


if __name__ == "__main__":
    unittest.main()
