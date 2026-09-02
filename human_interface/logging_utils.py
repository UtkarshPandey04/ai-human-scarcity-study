"""
logging_utils.py — Group 1 (Sujal & Utkarsh)

Handles writing every human participant action to a JSONL log file
that matches data/LOGGING_SCHEMA.md exactly. This must stay in sync
with whatever Group 2 uses for AI trial logs.
"""

import json
import os
from datetime import datetime, timezone

LOG_DIR = os.path.join("data", "human_logs")


def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def log_action(
    trial_id: str,
    agent_id: str,
    round_num: int,
    scenario: str,
    action_type: str,
    resource_before: float,
    resource_after: float,
    alive: bool,
    target_agent: str | None = None,
    message_sent: str | None = None,
):
    """
    Append one action record to data/human_logs/<trial_id>.jsonl
    Matches the shared LOGGING_SCHEMA.md exactly — do not add/remove
    fields without agreeing with Group 2 first.
    """
    ensure_log_dir()

    record = {
        "trial_id": trial_id,
        "source": "human",
        "agent_id": agent_id,
        "round": round_num,
        "scenario": scenario,
        "action_type": action_type,
        "target_agent": target_agent,
        "message_sent": message_sent,
        "resource_before": resource_before,
        "resource_after": resource_after,
        "alive": alive,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    log_path = os.path.join(LOG_DIR, f"{trial_id}.jsonl")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return record


def load_trial_log(trial_id: str):
    """Read back a trial's full log as a list of dicts. Useful for the
    debrief screen or for quick local debugging."""
    log_path = os.path.join(LOG_DIR, f"{trial_id}.jsonl")
    if not os.path.exists(log_path):
        return []
    with open(log_path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
