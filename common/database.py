"""
database.py — Relational Database Layer for the AI-Human Scarcity Study

Manages persistent SQLite storage (data/scarcity_study.db) for:
1. `trials`: Top-level trial metadata (scenario, arm, seed, participant, outcome)
2. `actions`: Individual round action events (action_type, target, messages, resources, latency)
3. `trial_features`: Extracted behavioral metrics per trial
4. `turing_judgments`: Human-judge discrimination responses from the debrief screen

Supports bidirectional sync with canonical JSONL logs.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from typing import Any

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from human_interface.session_analysis import calculate_gini

DEFAULT_DB_PATH = os.path.join(PROJECT_ROOT, "data", "scarcity_study.db")


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Get a SQLite database connection with row factory enabled."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initialize database tables and indexes if they do not exist."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Trials table with demographic fields
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trials (
                trial_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                arm TEXT,
                scenario TEXT NOT NULL,
                seed INTEGER,
                severity REAL,
                participant_id TEXT,
                participant_name TEXT,
                age_group TEXT,
                gender TEXT,
                ai_familiarity TEXT,
                rounds_completed INTEGER,
                survived INTEGER,
                final_resource REAL,
                society_gini REAL,
                alliance_count INTEGER,
                created_at TEXT
            )
            """
        )

        # Migration: add demographic columns if trials table existed prior
        for col in ["participant_name", "age_group", "gender", "ai_familiarity"]:
            try:
                cursor.execute(f"ALTER TABLE trials ADD COLUMN {col} TEXT")
            except sqlite3.OperationalError:
                pass  # column already exists


        # 2. Actions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trial_id TEXT NOT NULL,
                round INTEGER NOT NULL,
                agent_id TEXT NOT NULL,
                source TEXT NOT NULL,
                action_type TEXT NOT NULL,
                target_agent TEXT,
                message_kind TEXT,
                message_value REAL,
                message_surface TEXT,
                resource_before REAL,
                resource_after REAL,
                alive INTEGER NOT NULL,
                decision_latency_ms REAL,
                policy TEXT,
                timestamp TEXT,
                FOREIGN KEY (trial_id) REFERENCES trials(trial_id)
            )
            """
        )

        # 3. Behavioral Features table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trial_features (
                trial_id TEXT PRIMARY KEY,
                source TEXT,
                arm TEXT,
                scenario TEXT,
                seed INTEGER,
                severity REAL,
                rounds_survived INTEGER,
                survived INTEGER,
                final_resource REAL,
                gather_rate REAL,
                share_rate REAL,
                hoard_rate REAL,
                skip_rate REAL,
                communicate_rate REAL,
                total_shared REAL,
                stock_claims_count INTEGER,
                deceptive_claims_count INTEGER,
                deception_rate REAL,
                mean_latency_ms REAL,
                society_survival_rate REAL,
                society_gini REAL,
                alliance_count INTEGER,
                FOREIGN KEY (trial_id) REFERENCES trials(trial_id)
            )
            """
        )

        # 4. Turing Judgments table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS turing_judgments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT,
                guess TEXT NOT NULL,
                correct INTEGER NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )

        # 5. Unified View combining trial metadata, demographics, and behavioral features
        cursor.execute("DROP VIEW IF EXISTS v_combined_dataset")
        cursor.execute(
            """
            CREATE VIEW v_combined_dataset AS
            SELECT 
                t.trial_id,
                t.source,
                t.arm,
                t.scenario,
                t.seed,
                t.severity,
                t.participant_id,
                t.participant_name,
                t.age_group,
                t.gender,
                t.ai_familiarity,
                t.rounds_completed,
                t.survived,
                t.final_resource,
                t.society_gini,
                t.alliance_count,
                f.gather_rate,
                f.share_rate,
                f.hoard_rate,
                f.skip_rate,
                f.communicate_rate,
                f.total_shared,
                f.stock_claims_count,
                f.deceptive_claims_count,
                f.deception_rate,
                f.mean_latency_ms,
                f.society_survival_rate,
                t.created_at
            FROM trials t
            LEFT JOIN trial_features f ON t.trial_id = f.trial_id
            """
        )

        conn.commit()



def save_trial_to_db(rows: list[dict[str, Any]], db_path: str = DEFAULT_DB_PATH) -> str | None:
    """Save or update a trial, all its actions, and derived features in the database."""
    if not rows:
        return None

    init_db(db_path)
    trial_id = rows[0]["trial_id"]
    scenario = rows[0].get("scenario", "drought")
    meta = rows[0].get("meta") or {}

    # Determine focal agent
    human_agents = [r["agent_id"] for r in rows if r.get("source") == "human"]
    focal_id = human_agents[0] if human_agents else "A1"

    source = "human" if human_agents else rows[0].get("source", "ai")
    arm = "human" if human_agents else meta.get("arm", "ai")
    seed = meta.get("seed", 0)
    severity = meta.get("severity", 0.7 if scenario == "drought" else 0.0)

    focal_rows = [r for r in rows if r["agent_id"] == focal_id]
    rounds_completed = len(focal_rows)
    final_alive = 1 if (focal_rows and focal_rows[-1].get("alive", False)) else 0
    final_res = focal_rows[-1].get("resource_after", 0.0) if focal_rows else 0.0

    # Final round resources across players for society Gini
    max_rnd = max(r["round"] for r in rows)
    final_rnd_rows = [r for r in rows if r["round"] == max_rnd]
    final_resources = [r.get("resource_after", 0.0) for r in final_rnd_rows]
    society_gini = calculate_gini(final_resources)

    # Alliance detection
    sharing_pairs: set[tuple[str, str]] = set()
    for r in rows:
        if r.get("action_type") == "share" and r.get("agent_id") and r.get("target_agent"):
            sharing_pairs.add((r["agent_id"], r["target_agent"]))

    alliances = 0
    checked = set()
    for (a, b) in sharing_pairs:
        if (b, a) in sharing_pairs and (b, a) not in checked and a != b:
            alliances += 1
            checked.add((a, b))

    created_at = rows[0].get("timestamp", datetime.now(timezone.utc).isoformat())

    # Extract demographic info if recorded across any row
    demographics = meta.get("demographics") or {}
    if not demographics:
        for r in rows:
            r_meta = r.get("meta") or {}
            if r_meta.get("demographics"):
                demographics = r_meta["demographics"]
                break

    p_name = demographics.get("name")
    p_age = demographics.get("age_group")
    p_gender = demographics.get("gender")
    p_ai_fam = demographics.get("ai_familiarity")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Upsert trials table
        cursor.execute(
            """
            INSERT INTO trials (
                trial_id, source, arm, scenario, seed, severity, participant_id,
                participant_name, age_group, gender, ai_familiarity,
                rounds_completed, survived, final_resource, society_gini, alliance_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(trial_id) DO UPDATE SET
                participant_name=COALESCE(excluded.participant_name, trials.participant_name),
                age_group=COALESCE(excluded.age_group, trials.age_group),
                gender=COALESCE(excluded.gender, trials.gender),
                ai_familiarity=COALESCE(excluded.ai_familiarity, trials.ai_familiarity),
                rounds_completed=excluded.rounds_completed,
                survived=excluded.survived,
                final_resource=excluded.final_resource,
                society_gini=excluded.society_gini,
                alliance_count=excluded.alliance_count
            """,
            (
                trial_id, source, arm, scenario, seed, severity, focal_id,
                p_name, p_age, p_gender, p_ai_fam,
                rounds_completed, final_alive, final_res, society_gini, alliances, created_at
            ),
        )


        # Delete existing actions for this trial to avoid duplicate appends on replay
        cursor.execute("DELETE FROM actions WHERE trial_id = ?", (trial_id,))

        action_tuples = []
        for r in rows:
            r_meta = r.get("meta") or {}
            claim = r_meta.get("claim") or {}
            action_tuples.append(
                (
                    trial_id,
                    r.get("round", 1),
                    r.get("agent_id", "A1"),
                    r.get("source", "ai"),
                    r.get("action_type", "skip"),
                    r.get("target_agent"),
                    claim.get("kind"),
                    claim.get("value"),
                    claim.get("surface") or r.get("message_sent"),
                    r.get("resource_before", 0.0),
                    r.get("resource_after", 0.0),
                    1 if r.get("alive", False) else 0,
                    r_meta.get("decision_latency_ms"),
                    r_meta.get("policy"),
                    r.get("timestamp"),
                )
            )

        cursor.executemany(
            """
            INSERT INTO actions (
                trial_id, round, agent_id, source, action_type, target_agent,
                message_kind, message_value, message_surface, resource_before,
                resource_after, alive, decision_latency_ms, policy, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            action_tuples,
        )

        # Compute and upsert trial_features
        from analysis.feature_extraction import extract_trial_features
        feat = extract_trial_features(rows, focal_id=focal_id)
        if feat:
            cursor.execute(
                """
                INSERT INTO trial_features (
                    trial_id, source, arm, scenario, seed, severity, rounds_survived,
                    survived, final_resource, gather_rate, share_rate, hoard_rate,
                    skip_rate, communicate_rate, total_shared, stock_claims_count,
                    deceptive_claims_count, deception_rate, mean_latency_ms,
                    society_survival_rate, society_gini, alliance_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(trial_id) DO UPDATE SET
                    rounds_survived=excluded.rounds_survived,
                    survived=excluded.survived,
                    final_resource=excluded.final_resource,
                    gather_rate=excluded.gather_rate,
                    share_rate=excluded.share_rate,
                    hoard_rate=excluded.hoard_rate,
                    skip_rate=excluded.skip_rate,
                    communicate_rate=excluded.communicate_rate,
                    total_shared=excluded.total_shared,
                    deception_rate=excluded.deception_rate,
                    society_gini=excluded.society_gini
                """,
                (
                    trial_id, feat["source"], feat["arm"], feat["scenario"], feat["seed"],
                    feat["severity"], feat["rounds_survived"], feat["survived"], feat["final_resource"],
                    feat["gather_rate"], feat["share_rate"], feat["hoard_rate"], feat["skip_rate"],
                    feat["communicate_rate"], feat["total_shared"], feat["stock_claims_count"],
                    feat["deceptive_claims_count"], feat["deception_rate"], feat["mean_latency_ms"],
                    feat["society_survival_rate"], feat["society_gini"], feat["alliance_count"]
                ),
            )

        conn.commit()

    return trial_id


def save_turing_judgment(
    participant_id: str, guess: str, correct: bool, db_path: str = DEFAULT_DB_PATH
) -> None:
    """Save a human behavioral Turing judgment to the database."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO turing_judgments (participant_id, guess, correct, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (participant_id, guess, 1 if correct else 0, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()


def sync_all_logs_to_db(db_path: str = DEFAULT_DB_PATH) -> tuple[int, int]:
    """Scan data/human_logs and data/ai_logs and sync all trials into SQLite."""
    import glob

    init_db(db_path)
    dirs = [
        os.path.join(PROJECT_ROOT, "data", "human_logs"),
        os.path.join(PROJECT_ROOT, "data", "ai_logs"),
    ]
    synced = 0
    total = 0

    for d in dirs:
        if not os.path.exists(d):
            continue
        for fpath in glob.glob(os.path.join(d, "*.jsonl")):
            if "turing_judgments" in fpath or "manifest" in fpath:
                continue
            total += 1
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    rows = [json.loads(line) for line in f if line.strip()]
                save_trial_to_db(rows, db_path=db_path)
                synced += 1
            except Exception as e:
                print(f"Error syncing {fpath}: {e}")

    return synced, total


def get_db_summary(db_path: str = DEFAULT_DB_PATH) -> dict[str, Any]:
    """Get high-level summary statistics of the database."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM trials")
        total_trials = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM trials WHERE source = 'human'")
        human_trials = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM trials WHERE source = 'ai'")
        ai_trials = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM actions")
        total_actions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM turing_judgments")
        total_judgments = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(correct) FROM turing_judgments")
        row = cursor.fetchone()[0]
        turing_acc = (row * 100.0) if row is not None else 0.0

        cursor.execute("SELECT scenario, COUNT(*) FROM trials GROUP BY scenario")
        scenario_counts = dict(cursor.fetchall())

    return {
        "total_trials": total_trials,
        "human_trials": human_trials,
        "ai_trials": ai_trials,
        "total_actions": total_actions,
        "total_judgments": total_judgments,
        "turing_accuracy": turing_acc,
        "scenario_counts": scenario_counts,
    }


def save_turing_judgment(
    participant_id: str,
    guess: str,
    correct: bool,
    db_path: str = DEFAULT_DB_PATH,
) -> None:
    """Save participant judgment from the Behavioral Turing Test."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO turing_judgments (participant_id, guess, correct, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (participant_id, guess, 1 if correct else 0, datetime.now(timezone.utc).isoformat()),
        )


def load_human_action_dataset(db_path: str = DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    """Load state-action observation pairs from human actions for training behavioral models."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT a.trial_id, a.round, a.action_type, a.resource_before,
                   a.resource_after, a.decision_latency_ms, t.scenario, t.severity
            FROM actions a
            JOIN trials t ON a.trial_id = t.trial_id
            WHERE a.source = 'human'
            ORDER BY a.trial_id, a.round
            """
        )
        return [dict(row) for row in cursor.fetchall()]



def export_combined_dataset(
    output_path: str = os.path.join(PROJECT_ROOT, "data", "combined_scarcity_dataset.csv"),
    db_path: str = DEFAULT_DB_PATH,
) -> str:
    """Export the unified dataset view (metadata, demographics, features) to CSV."""
    import csv

    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM v_combined_dataset")
        rows = cursor.fetchall()
        if not rows:
            return output_path

        headers = [desc[0] for desc in cursor.description]
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in rows:
                writer.writerow(list(row))

    return output_path


def export_sft_dataset(
    output_path: str = os.path.join(PROJECT_ROOT, "data", "llm_sft_dataset.jsonl"),
    db_path: str = DEFAULT_DB_PATH,
) -> str:
    """Export human trial actions as a Supervised Fine-Tuning (SFT / LoRA) JSONL dataset.

    Formats each human turn into OpenAI / HuggingFace standard conversational format:
    {"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}
    """
    init_db(db_path)
    system_instruction = (
        "You are a player in a resource-scarcity survival game. Each round you need 2 units of "
        "water to survive. Decide your action (gather, share, hoard, skip, communicate) to survive "
        "while navigating shared commons dilemmas."
    )

    records = []
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        query = """
            SELECT a.trial_id, a.round, a.agent_id, a.action_type, a.target_agent,
                   a.message_kind, a.message_value, a.message_surface,
                   a.resource_before, a.decision_latency_ms,
                   t.scenario, t.severity
            FROM actions a
            JOIN trials t ON a.trial_id = t.trial_id
            WHERE a.source = 'human'
            ORDER BY a.trial_id, a.round
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        for r in rows:
            act_type = r["action_type"]
            target = r["target_agent"]
            msg = None
            if r["message_kind"] and r["message_kind"] != "none":
                msg = {
                    "kind": r["message_kind"],
                    "value": int(r["message_value"]) if r["message_value"] is not None else None,
                    "target": target,
                    "surface": r["message_surface"] or "",
                }

            completion_payload = {
                "action_type": act_type,
                "target": target if act_type in ["share", "communicate"] else None,
                "amount": 1 if act_type == "share" else None,
                "message": msg,
            }

            user_prompt = (
                f"Round {r['round']} of 20.\n"
                f"Scenario: {r['scenario'] or 'drought'}.\n"
                f"Your water: {float(r['resource_before']):.1f}.\n"
                "Decide your action. Respond only with the JSON object."
            )

            record = {
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": json.dumps(completion_payload)},
                ],
                "metadata": {
                    "trial_id": r["trial_id"],
                    "round": r["round"],
                    "latency_ms": r["decision_latency_ms"],
                },
            }
            records.append(record)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

    return output_path


if __name__ == "__main__":
    print(f"Initializing database at: {DEFAULT_DB_PATH}")
    init_db()
    synced, total = sync_all_logs_to_db()
    print(f"Synced {synced}/{total} JSONL trial logs to SQLite database.")
    csv_file = export_combined_dataset()
    print(f"Exported combined dataset to: {csv_file}")
    sft_file = export_sft_dataset()
    print(f"Exported SFT dataset to: {sft_file}")
    stats = get_db_summary()
    print(f"Summary: {stats}")

