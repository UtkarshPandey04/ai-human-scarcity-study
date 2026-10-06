"""Self-tests for agents/qa_logs.py — the Phase H log QA script. Uses real ScarcityEnv trials so the
invariants are checked against what the environment actually logs, plus hand-corrupted copies to
prove each check fires.
"""

import copy
import unittest

from agents.qa_logs import qa_check_trial, summarize_trials
from agents.smoke_random import run_trial


def run_scripted_trial(scenario="drought", seed=0, policy="random"):
    return run_trial(scenario, seed, policy)


class QaCheckTrialTest(unittest.TestCase):
    def test_env_trials_pass(self):
        for policy in ("random", "cooperator", "free_rider", "tit_for_tat"):
            for seed in range(5):
                rows = run_scripted_trial(seed=seed, policy=policy)
                self.assertEqual(qa_check_trial(rows), [], f"{policy} seed {seed}")

    def test_continuity_break_is_caught(self):
        rows = copy.deepcopy(run_scripted_trial(policy="cooperator"))
        later = next(r for r in rows if r["round"] == 2)
        later["resource_before"] += 1
        self.assertTrue(any("resource_before" in e for e in qa_check_trial(rows)))

    def test_duplicate_row_is_caught(self):
        rows = run_scripted_trial(policy="cooperator")
        rows = rows + [copy.deepcopy(rows[0])]
        self.assertTrue(any("more than one row" in e for e in qa_check_trial(rows)))

    def test_share_to_dead_agent_is_caught(self):
        rows = copy.deepcopy(run_scripted_trial(policy="cooperator"))
        # Mark A5 dead at the end of round 1, then have A1 share with it in round 2.
        for r in rows:
            if r["agent_id"] == "A5" and r["round"] == 1:
                r["resource_after"], r["alive"] = 0, False
        rows = [r for r in rows if not (r["agent_id"] == "A5" and r["round"] > 1)]
        a1_r2 = next(r for r in rows if r["agent_id"] == "A1" and r["round"] == 2)
        a1_r2.update(action_type="share", target_agent="A5")
        self.assertTrue(any("shared with dead agent A5" in e for e in qa_check_trial(rows)))


class SummarizeTrialsTest(unittest.TestCase):
    def test_parse_failure_rate_excludes_rate_limited(self):
        base = run_scripted_trial(policy="cooperator")[:4]
        metas = [
            {"arm": "llm_only", "llm_parse_failure": False, "prompt_tokens": 10, "completion_tokens": 2},
            {"arm": "llm_only", "llm_parse_failure": True, "prompt_tokens": 10, "completion_tokens": 2},
            {"arm": "llm_only", "llm_parse_failure": True, "llm_rate_limited": True},
            {"arm": "llm_only", "llm_parse_failure": False, "prompt_tokens": 10, "completion_tokens": 2},
        ]
        for row, meta in zip(base, metas):
            row["meta"] = meta
        s = summarize_trials([base])
        self.assertEqual(s["llm_calls"], 3)
        self.assertEqual(s["llm_rate_limited"], 1)
        self.assertEqual(s["llm_parse_failures"], 1)
        self.assertAlmostEqual(s["llm_parse_failure_rate"], 1 / 3)
        self.assertEqual(s["prompt_tokens"], 30)
        self.assertEqual(s["cells"], {"drought/llm_only": {"trials": 1, "rows": 4}})

    def test_rl_rows_in_hybrid_arm_are_not_llm_calls(self):
        rows = run_scripted_trial(policy="cooperator")[:2]
        rows[0]["meta"] = {"arm": "hybrid", "decision_source": "rl"}
        rows[1]["meta"] = {"arm": "hybrid", "decision_source": "llm", "llm_parse_failure": False}
        self.assertEqual(summarize_trials([rows])["llm_calls"], 1)


if __name__ == "__main__":
    unittest.main()
