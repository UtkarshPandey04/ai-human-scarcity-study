"""
test_database.py — Regression tests for SQLite database schema and pilot data isolation.

Ensures that:
(a) Synthetic trials with meta.pilot=True persist pilot=1 in trials and trial_features.
(b) Training queries used by train_models.py and classifier.py strictly exclude pilot=1 rows.
(c) sync_all_logs_to_db() correctly parses and propagates meta.pilot and meta.policy from JSONL to DB.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

import pandas as pd

from common.database import (
    get_connection,
    init_db,
    save_trial_to_db,
    sync_all_logs_to_db,
)
from common.schema import validate_trial


def make_trial_rows(
    trial_id: str,
    source: str = "ai",
    arm: str = "scripted",
    pilot: bool = False,
    policy: str | None = None,
    n_rounds: int = 2,
) -> list[dict]:
    """Generate synthetic rows adhering strictly to common.schema.validate_trial."""
    rows = []
    meta = {
        "arm": arm,
        "pilot": pilot,
        "seed": 42,
        "severity": 0.5,
    }
    if policy:
        meta["policy"] = policy

    for r in range(1, n_rounds + 1):
        rows.append(
            {
                "trial_id": trial_id,
                "source": source,
                "agent_id": "A1" if source == "ai" else "P001",
                "round": r,
                "scenario": "drought",
                "action_type": "gather",
                "target_agent": None,
                "message_sent": None,
                "resource_before": 5.0 + (r - 1),
                "resource_after": 6.0 + (r - 1),
                "alive": True,
                "timestamp": f"2026-10-14T00:00:0{r}Z",
                "meta": meta,
            }
        )
    return rows


class DatabasePilotIsolationTest(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test_scarcity.db")
        init_db(self.db_path)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_synthetic_trial_pilot_flag_persistence(self):
        """(a) & (c): Verify meta.pilot is correctly persisted in trials and trial_features."""
        pilot_rows = make_trial_rows(
            trial_id="test_ai_pilot_deception_01",
            source="ai",
            arm="scripted",
            pilot=True,
            policy="mixed_roster_pilot",
        )
        std_rows = make_trial_rows(
            trial_id="test_ai_standard_01",
            source="ai",
            arm="scripted",
            pilot=False,
            policy="cooperator",
        )

        # Validate with common.schema before DB insertion
        validate_trial(pilot_rows)
        validate_trial(std_rows)

        save_trial_to_db(pilot_rows, db_path=self.db_path)
        save_trial_to_db(std_rows, db_path=self.db_path)

        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # Check trials table
            cursor.execute("SELECT trial_id, pilot FROM trials ORDER BY trial_id")
            trials_data = {r["trial_id"]: r["pilot"] for r in cursor.fetchall()}
            self.assertEqual(trials_data.get("test_ai_pilot_deception_01"), 1)
            self.assertEqual(trials_data.get("test_ai_standard_01"), 0)

            # Check trial_features table
            cursor.execute("SELECT trial_id, pilot, policy FROM trial_features ORDER BY trial_id")
            feats_data = {r["trial_id"]: (r["pilot"], r["policy"]) for r in cursor.fetchall()}
            self.assertEqual(
                feats_data.get("test_ai_pilot_deception_01"),
                (1, "mixed_roster_pilot"),
            )
            self.assertEqual(
                feats_data.get("test_ai_standard_01"),
                (0, "cooperator"),
            )

    def test_training_query_excludes_pilot_trials(self):
        """(b): Verify training queries from train_models.py and classifier.py exclude pilot=1."""
        human_rows = make_trial_rows("test_human_01", source="human", arm="human", pilot=False)
        ai_std_rows = make_trial_rows("test_ai_01", source="ai", arm="scripted", pilot=False)
        ai_pilot_rows = make_trial_rows("test_ai_pilot_01", source="ai", arm="scripted", pilot=True)
        steered_rows = make_trial_rows("test_steered_01", source="ai", arm="llm_human_steered", pilot=False)

        for trial in (human_rows, ai_std_rows, ai_pilot_rows, steered_rows):
            validate_trial(trial)
            save_trial_to_db(trial, db_path=self.db_path)

        training_query = """
            SELECT trial_id FROM trial_features
            WHERE source IN ('human', 'ai')
              AND (arm IS NULL OR arm != 'llm_human_steered')
              AND (pilot IS NULL OR pilot = 0)
        """

        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(training_query)
            included = {r["trial_id"] for r in cursor.fetchall()}

        # Pilot trial and steered trial MUST be excluded
        self.assertNotIn("test_ai_pilot_01", included)
        self.assertNotIn("test_steered_01", included)
        # Standard human and standard AI trials MUST be included
        self.assertIn("test_human_01", included)
        self.assertIn("test_ai_01", included)

        # Equivalent DataFrame filter check (as in classifier.py & stats_tests.py)
        with get_connection(self.db_path) as conn:
            df = pd.read_sql_query("SELECT * FROM trial_features", conn)
        filtered_df = df[(df["arm"] != "llm_human_steered") & (df["pilot"] != 1)]
        df_included = set(filtered_df["trial_id"])
        self.assertNotIn("test_ai_pilot_01", df_included)
        self.assertNotIn("test_steered_01", df_included)
        self.assertIn("test_human_01", df_included)
        self.assertIn("test_ai_01", df_included)

        # Researcher Hub empirical summary query check (Task 1)
        summary_query = """
            SELECT source, COUNT(*) as n_trials
            FROM trial_features
            WHERE (pilot IS NULL OR pilot = 0)
            GROUP BY source
        """
        with get_connection(self.db_path) as conn:
            summary_res = dict(conn.execute(summary_query).fetchall())
        self.assertEqual(summary_res.get("ai"), 2)  # test_ai_01 + test_steered_01; test_ai_pilot_01 excluded

        # Researcher Hub game performance query check (Task 2)
        game_query = """
            SELECT COALESCE(a.policy, CASE WHEN a.source = 'human' THEN 'human' ELSE 'unknown_ai' END) as agent_policy,
                   COUNT(*) as total_actions
            FROM actions a
            JOIN trials t ON a.trial_id = t.trial_id
            WHERE (t.pilot IS NULL OR t.pilot = 0)
            GROUP BY agent_policy
        """
        with get_connection(self.db_path) as conn:
            game_res = dict(conn.execute(game_query).fetchall())
        # Verify actions from test_ai_pilot_01 are excluded from game_res
        total_actions_pilot_free = sum(game_res.values())
        with get_connection(self.db_path) as conn:
            total_actions_all = conn.execute("SELECT COUNT(*) FROM actions").fetchone()[0]
        self.assertLess(total_actions_pilot_free, total_actions_all)

    def test_sync_all_logs_to_db_propagates_pilot_flag(self):
        """(c): Verify sync_all_logs_to_db() reads JSONL files and populates pilot/policy."""
        fake_ai_dir = os.path.join(self.tmp_dir, "data", "ai_logs")
        fake_human_dir = os.path.join(self.tmp_dir, "data", "human_logs")
        os.makedirs(fake_ai_dir, exist_ok=True)
        os.makedirs(fake_human_dir, exist_ok=True)

        pilot_trial = make_trial_rows(
            "sync_ai_pilot_01",
            source="ai",
            arm="scripted",
            pilot=True,
            policy="mixed_roster_pilot",
        )
        validate_trial(pilot_trial)

        with open(os.path.join(fake_ai_dir, "sync_ai_pilot_01.jsonl"), "w", encoding="utf-8") as f:
            for r in pilot_trial:
                f.write(json.dumps(r) + "\n")

        with mock.patch("common.database.PROJECT_ROOT", self.tmp_dir):
            synced, total = sync_all_logs_to_db(db_path=self.db_path)
            self.assertEqual(synced, 1)
            self.assertEqual(total, 1)

        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pilot, policy FROM trial_features WHERE trial_id = 'sync_ai_pilot_01'"
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["pilot"], 1)
            self.assertEqual(row["policy"], "mixed_roster_pilot")


if __name__ == "__main__":
    unittest.main()
