"""Fast tests for agents/hybrid_trial.py.
No live LLM calls and no disk-checkpoint dependencies — uses a MagicMock for the RL model
and verifies trial execution, coplayer rosters, claim threading, trial id formatting,
and schema validity.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock

from agents.hybrid_trial import build_trial_id, run_trial, write_trial
from common.actions import Action, ActionType
from common.schema import validate_trial


class TestBuildTrialId(unittest.TestCase):
    def test_standard_coplayer_mode_has_no_roster_tag(self):
        tid = build_trial_id("calm", "rl_only", 0.0, 5, 0, coplayer_mode="standard")
        self.assertEqual(tid, "calm_ai_rl_only_sev000_005_000")

    def test_non_standard_coplayer_mode_includes_roster_tag(self):
        tid = build_trial_id("drought", "hybrid", 0.7, 12, 1, coplayer_mode="deceptive")
        self.assertEqual(tid, "drought_ai_hybrid_deceptive_sev070_012_001")

        tid_llm = build_trial_id("repeated_trust", "rl_only", 0.3, 0, 0, coplayer_mode="llm_ecology")
        self.assertEqual(tid_llm, "repeated_trust_ai_rl_only_llm_ecology_sev030_000_000")


class TestHybridTrialExecution(unittest.TestCase):
    def setUp(self):
        self.fake_rl_model = MagicMock()
        # Learner actions: GATHER is index 0 in LEARNER_ACTIONS
        self.fake_rl_model.predict.return_value = (0, None)

    def test_run_trial_standard_passes_schema(self):
        rows, stats = run_trial(
            scenario="calm",
            seed=42,
            arm="rl_only",
            rl_model=self.fake_rl_model,
            coplayer_mode="standard",
        )
        self.assertGreater(len(rows), 0)
        validate_trial(rows)
        self.assertEqual(stats["arm"], "rl_only")
        self.assertEqual(stats["coplayer_mode"], "standard")

        # Check focal row metadata
        focal_rows = [r for r in rows if r["agent_id"] == "A1"]
        self.assertGreater(len(focal_rows), 0)
        for r in focal_rows:
            self.assertEqual(r["source"], "ai")
            self.assertEqual(r["meta"]["arm"], "rl_only")
            self.assertEqual(r["meta"]["coplayer_mode"], "standard")

    def test_run_trial_deceptive_threads_claims(self):
        # Under drought, StrategicDeceiver emits a false CLAIM_STOCK message
        rows, stats = run_trial(
            scenario="drought",
            seed=1,
            arm="rl_only",
            severity=0.7,
            rl_model=self.fake_rl_model,
            coplayer_mode="deceptive",
        )
        validate_trial(rows)
        self.assertEqual(stats["coplayer_mode"], "deceptive")

        # Verify co-player A5 (StrategicDeceiver, last in roster) claims are folded into meta["claim"]
        deceiver_rows = [r for r in rows if r["agent_id"] == "A5"]
        self.assertGreater(len(deceiver_rows), 0)
        claims = [r["meta"].get("claim") for r in deceiver_rows if r["meta"].get("claim")]
        self.assertGreater(len(claims), 0, "StrategicDeceiver should emit at least one claim under drought")
        for claim in claims:
            self.assertEqual(claim["kind"], "claim_stock")
            self.assertIn("value", claim)

    def test_unknown_coplayer_mode_raises(self):
        with self.assertRaises(ValueError):
            run_trial(
                scenario="calm",
                seed=0,
                arm="rl_only",
                rl_model=self.fake_rl_model,
                coplayer_mode="invalid_roster",
            )

    def test_write_trial_persists_valid_jsonl(self):
        rows, _ = run_trial(
            scenario="calm",
            seed=0,
            arm="rl_only",
            rl_model=self.fake_rl_model,
            coplayer_mode="standard",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            from unittest.mock import patch
            with patch("agents.hybrid_trial.LOG_DIR", tmpdir):
                path = write_trial(rows)
                self.assertTrue(os.path.exists(path))
                with open(path, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                self.assertEqual(len(lines), len(rows))


if __name__ == "__main__":
    unittest.main()
