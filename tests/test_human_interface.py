"""Tests for human_interface components:
- session_analysis metrics (deception, Gini, action rates, latency)
- logging_utils trial validation
- focal player substitution end-to-end simulation
"""

import os
import shutil
import tempfile
import unittest

from agents.coplayers import get_policy
from agents.environment import ScarcityEnv
from common.actions import Action, ActionType, Message, MessageKind
from common.config import SURVIVAL_COST, START_WATER
from common.schema import validate_trial
from human_interface.logging_utils import log_action, log_round_records, load_trial_log, validate_trial_log
from human_interface.session_analysis import (
    action_rates,
    calculate_deception,
    calculate_gini,
    calculate_latency_stats,
    count_actions,
    resource_change,
)


class TestSessionAnalysis(unittest.TestCase):
    def test_count_and_action_rates(self):
        log = [
            {"action_type": "gather", "resource_before": 5, "resource_after": 6},
            {"action_type": "gather", "resource_before": 6, "resource_after": 7},
            {"action_type": "share", "resource_before": 7, "resource_after": 4},
            {"action_type": "hoard", "resource_before": 4, "resource_after": 3},
        ]
        counts = count_actions(log)
        self.assertEqual(counts["gather"], 2)
        self.assertEqual(counts["share"], 1)
        self.assertEqual(counts["hoard"], 1)
        self.assertEqual(counts["skip"], 0)

        rates = action_rates(log)
        self.assertAlmostEqual(rates["gather"], 50.0)
        self.assertAlmostEqual(rates["share"], 25.0)
        self.assertAlmostEqual(rates["hoard"], 25.0)

    def test_calculate_deception(self):
        log = [
            # Truthful claim: resource_before 5, claimed 5
            {
                "action_type": "communicate",
                "resource_before": 5,
                "meta": {"claim": {"kind": "claim_stock", "value": 5, "target": "all"}},
            },
            # Deceptive claim: resource_before 8, claimed 1
            {
                "action_type": "communicate",
                "resource_before": 8,
                "meta": {"claim": {"kind": "claim_stock", "value": 1, "target": "all"}},
            },
            # Non-claim message: request
            {
                "action_type": "communicate",
                "resource_before": 5,
                "meta": {"claim": {"kind": "request", "value": 1, "target": "A2"}},
            },
        ]
        stats = calculate_deception(log)
        self.assertEqual(stats["total_claims"], 2)
        self.assertEqual(stats["deceptive_claims"], 1)
        self.assertAlmostEqual(stats["deception_rate"], 50.0)

    def test_calculate_gini(self):
        # Perfect equality
        self.assertAlmostEqual(calculate_gini([5.0, 5.0, 5.0, 5.0]), 0.0)
        # Inequality
        gini_unequal = calculate_gini([0.0, 0.0, 0.0, 10.0])
        self.assertGreater(gini_unequal, 0.5)

    def test_latency_stats(self):
        log = [
            {"meta": {"decision_latency_ms": 1000}},
            {"meta": {"decision_latency_ms": 2000}},
            {"meta": {"decision_latency_ms": 3000}},
        ]
        stats = calculate_latency_stats(log)
        self.assertAlmostEqual(stats["mean_ms"], 2000.0)
        self.assertAlmostEqual(stats["median_ms"], 2000.0)
        self.assertEqual(stats["count"], 3)


class TestFocalPlayerIntegration(unittest.TestCase):
    def test_focal_player_substitution_episode(self):
        """Simulate a 10-round episode where focal player is substituted alongside 4 co-players."""
        focal_id = "PTEST"
        coplayer_ids = ["A2", "A3", "A4", "A5"]
        coplayer_types = ["cooperator", "free_rider", "tit_for_tat", "random"]

        env = ScarcityEnv(scenario="drought", seed=42, player_ids=[focal_id] + coplayer_ids)
        coplayers = {
            pid: get_policy(coplayer_types[i], seed=42 + i + 1)
            for i, pid in enumerate(coplayer_ids)
        }

        obs = env.reset()
        all_rows = []
        done = False

        while not done:
            actions = {}
            # Focal human does GATHER on rounds 1-5, HOARD on drought round (6), SHARE on round 7
            r = env.round
            if r <= 5:
                actions[focal_id] = Action(type=ActionType.GATHER)
            elif r == 6:
                actions[focal_id] = Action(type=ActionType.HOARD)
            elif r == 7:
                actions[focal_id] = Action(type=ActionType.SHARE, target="A2", amount=1)
            else:
                actions[focal_id] = Action(type=ActionType.SKIP)

            for pid in coplayer_ids:
                if env.players[pid].alive:
                    actions[pid] = coplayers[pid].act(obs[pid])

            obs, done, rows = env.step(actions)
            for row in rows:
                row["trial_id"] = "drought_human_test_001"
                row["source"] = "human" if row["agent_id"] == focal_id else "ai"
                row["timestamp"] = "2026-10-06T12:00:00+00:00"
                row["meta"] = {
                    "arm": "human",
                    "seed": 42,
                    "severity": 0.7,
                    "decision_latency_ms": 1500,
                }
                all_rows.append(row)

        # Validate that the entire 5-player trial passes schema validation
        validate_trial(all_rows)
        self.assertTrue(len(all_rows) > 0)

    def test_hoard_mechanic_incurs_survival_cost(self):
        """Test that hoarding incurs standard SURVIVAL_COST (2) matching ACTIONS.md."""
        env = ScarcityEnv(scenario="calm", seed=0, player_ids=["A1"])
        env.reset()
        start_res = env.players["A1"].resource
        self.assertEqual(start_res, START_WATER)

        # Hoard
        env.step({"A1": Action(type=ActionType.HOARD)})
        res_after_hoard = env.players["A1"].resource
        self.assertEqual(res_after_hoard, start_res - SURVIVAL_COST)

        # Skip
        env.step({"A1": Action(type=ActionType.SKIP)})
        res_after_skip = env.players["A1"].resource
        self.assertEqual(res_after_skip, res_after_hoard - SURVIVAL_COST)


class TestDatabaseAndModelTraining(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_database_trial_and_judgment_persistence(self):
        from common.database import init_db, save_trial_to_db, save_turing_judgment, get_db_summary
        init_db(self.db_path)

        dummy_rows = [
            {
                "trial_id": "test_trial_001",
                "round": 1,
                "agent_id": "P001",
                "source": "human",
                "action_type": "gather",
                "scenario": "calm",
                "resource_before": 5.0,
                "resource_after": 6.0,
                "alive": True,
                "timestamp": "2026-10-06T12:00:00Z",
                "meta": {"arm": "human", "seed": 0, "decision_latency_ms": 1200},
            }
        ]
        trial_id = save_trial_to_db(dummy_rows, db_path=self.db_path)
        self.assertEqual(trial_id, "test_trial_001")

        save_turing_judgment("P001", "Trajectory A is Human", True, db_path=self.db_path)
        stats = get_db_summary(self.db_path)
        self.assertEqual(stats["total_trials"], 1)
        self.assertEqual(stats["human_trials"], 1)
        self.assertEqual(stats["total_judgments"], 1)
        self.assertEqual(stats["turing_accuracy"], 100.0)

    def test_model_training_pipeline_and_policy(self):
        # Trains on the real study DB, which is untracked (.gitignore) — on a fresh checkout it's
        # missing or empty until `python tasks.py sync_db` has run on real session logs.
        from common.database import DEFAULT_DB_PATH, get_db_summary
        if not os.path.exists(DEFAULT_DB_PATH) or get_db_summary(DEFAULT_DB_PATH).get("human_trials", 0) == 0:
            self.skipTest("no human trials in data/scarcity_study.db yet (run `python tasks.py sync_db`)")

        from analysis.train_models import (
            train_distinguishability_classifier,
            train_human_behavior_policy,
            HumanClonePolicy,
        )
        # Train on actual project database
        res_clf = train_distinguishability_classifier()
        self.assertNotIn("error", res_clf)
        self.assertGreater(res_clf["auc"], 0.7)

        res_pol = train_human_behavior_policy()
        self.assertNotIn("error", res_pol)
        self.assertGreater(res_pol["n_samples"], 10)

        # Test clone policy inference
        policy = HumanClonePolicy()
        env = ScarcityEnv(scenario="drought", seed=0)
        obs = env.reset()
        act = policy.act(obs["A1"])
        self.assertIn(act.type, [ActionType.GATHER, ActionType.SHARE, ActionType.HOARD, ActionType.SKIP, ActionType.COMMUNICATE])


class TestStreamlitAppScreens(unittest.TestCase):
    def test_all_screens_render_without_errors(self):
        """Test all 4 screens (consent, instructions, game, debrief) end-to-end using AppTest."""
        from streamlit.testing.v1 import AppTest

        app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "human_interface", "app.py"))
        at = AppTest.from_file(app_path, default_timeout=15)
        at.run()
        self.assertFalse(at.exception, f"Consent screen error: {at.exception}")
        self.assertEqual(at.session_state.stage, "consent")

        # Agree & continue -> instructions
        at.checkbox[0].check().run()
        at.button[0].click().run()
        self.assertFalse(at.exception, f"Instructions screen error: {at.exception}")
        self.assertEqual(at.session_state.stage, "instructions")

        # Start simulation -> game
        at.button[0].click().run()
        self.assertFalse(at.exception, f"Game screen error: {at.exception}")
        self.assertEqual(at.session_state.stage, "game")

        # Execute game action
        for btn in at.button:
            if "Submit" in btn.label:
                btn.click().run()
                break
        self.assertFalse(at.exception, f"Game step error: {at.exception}")

        # Debrief screen
        at.session_state.stage = "debrief"
        at.run()
        self.assertFalse(at.exception, f"Debrief screen error: {at.exception}")
        self.assertEqual(at.session_state.stage, "debrief")


if __name__ == "__main__":
    unittest.main()

