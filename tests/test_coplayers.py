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


if __name__ == "__main__":
    unittest.main()
