"""
human_exemplars.py — Dynamic In-Context Learning (Few-Shot Steering) for LLMs

Retrieves empirical human decision trajectories from the SQLite database
(data/scarcity_study.db) and formats them into grounded few-shot exemplars.
This steers LLM agents to mirror human cooperation, strategic communication,
and scarcity coping mechanisms without modifying base model weights.
"""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any

from agents.environment import Observation

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DB_PATH = os.path.join(PROJECT_ROOT, "data", "scarcity_study.db")

# Fallback canonical human demonstrations if the database has not yet been populated
CANONICAL_HUMAN_EXEMPLARS = [
    {
        "context": "Severe Drought, Round 8, Low Pool Stock (12.0 / 30.0), Own Water: 3.0",
        "action": {
            "action_type": "share",
            "target": "A2",
            "amount": 1,
            "message": {
                "kind": "promise_share",
                "value": 1,
                "target": "A2",
                "surface": "Sharing 1 water so we both survive the drought.",
            },
        },
        "reasoning": "Human participant conserved the shared pool and stabilized vulnerable co-player.",
    },
    {
        "context": "Drought, Round 14, Pool Exhaustion (4.0 / 30.0), Own Water: 3.5",
        "action": {
            "action_type": "hoard",
            "target": None,
            "amount": None,
            "message": None,
        },
        "reasoning": "Human participant hoarded to consume minimal water (1.0 vs 2.0) and prevent pool collapse.",
    },
    {
        "context": "Abundant Water, Round 3, Pool Stock (25.0 / 30.0), Own Water: 2.0",
        "action": {
            "action_type": "gather",
            "target": None,
            "amount": None,
            "message": None,
        },
        "reasoning": "Human participant gathered sustainable water when commons capacity was safe.",
    },
]


def query_human_exemplars(
    obs: Observation | None = None,
    db_path: str = DEFAULT_DB_PATH,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Retrieve the most relevant human actions from the database to use as few-shot exemplars.

    Prioritizes:
    1. Human actions under similar conditions (drought, low water, cooperative sharing).
    2. Rich actions with communication messages and strategic sharing/hoarding.
    """
    if not os.path.exists(db_path):
        return CANONICAL_HUMAN_EXEMPLARS[:limit]

    exemplars: list[dict[str, Any]] = []

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query human actions with preference for non-trivial actions (share, communicate, hoard)
        query = """
            SELECT a.round, a.action_type, a.target_agent, a.message_kind,
                   a.message_value, a.message_surface, a.resource_before,
                   t.scenario, t.severity
            FROM actions a
            JOIN trials t ON a.trial_id = t.trial_id
            WHERE a.source = 'human'
            ORDER BY
                CASE 
                    WHEN a.action_type IN ('share', 'communicate') THEN 1
                    WHEN a.action_type = 'hoard' THEN 2
                    ELSE 3
                END ASC,
                a.round DESC
            LIMIT 50
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return CANONICAL_HUMAN_EXEMPLARS[:limit]

        for r in rows:
            act_type = r["action_type"]
            if act_type not in ["gather", "share", "hoard", "move", "skip", "communicate"]:
                continue

            target = r["target_agent"]
            msg = None
            if r["message_kind"] and r["message_kind"] != "none":
                msg = {
                    "kind": r["message_kind"],
                    "value": int(r["message_value"]) if r["message_value"] is not None else None,
                    "target": target,
                    "surface": r["message_surface"] or "",
                }

            act_dict: dict[str, Any] = {
                "action_type": act_type,
                "target": target if act_type in ["share", "communicate"] else None,
                "amount": 1 if act_type == "share" else None,
                "message": msg,
            }

            scenario_name = r["scenario"] or "scarcity"
            water_before = float(r["resource_before"]) if r["resource_before"] is not None else 2.0
            round_num = int(r["round"])

            exemplars.append({
                "context": f"Scenario: {scenario_name}, Round: {round_num}, Water Before: {water_before:.1f}",
                "action": act_dict,
                "reasoning": f"Observed human decision during {scenario_name} trial.",
            })

            if len(exemplars) >= limit:
                break

    except Exception:
        return CANONICAL_HUMAN_EXEMPLARS[:limit]

    return exemplars if exemplars else CANONICAL_HUMAN_EXEMPLARS[:limit]


def format_exemplars_prompt(exemplars: list[dict[str, Any]]) -> str:
    """Format human exemplars into a concise prompt block for LLM in-context learning."""
    if not exemplars:
        return ""

    lines = [
        "--- OBSERVED HUMAN BEHAVIOR DEMONSTRATIONS (from empirical human study trials) ---",
        "The following are actual strategic decisions made by human participants under scarcity:",
    ]

    for i, ex in enumerate(exemplars, 1):
        action_json = json.dumps(ex["action"], separators=(", ", ": "))
        lines.append(f"Human Demonstration #{i}:")
        lines.append(f"  Context: {ex['context']}")
        lines.append(f"  Decision: {action_json}")
        if "reasoning" in ex and ex["reasoning"]:
            lines.append(f"  Strategic Rationale: {ex['reasoning']}")

    lines.append(
        "Emulate the cooperative foresight, social reciprocity, and resource conservation "
        "observed in human players when making your decision."
    )
    lines.append("---------------------------------------------------------------------------------")
    return "\n".join(lines)
