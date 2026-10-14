"""
Pilot generator for AI-side deception data — NOT part of the official campaign.

Why this exists: agents/smoke_random.py (the only script that has ever actually written to
data/ai_logs/) runs every seat on the SAME scripted policy, and until today, env.step() never
threaded a player's claim (meta.claim) into the log row at all for AI-only trials — so even a
StrategicDeceiver co-player's false claims were invisible to analysis/feature_extraction.py's
deception detector. Both gaps are now patched (agents/environment.py, agents/smoke_random.py,
agents/hybrid_trial.py in this checkout).

This script proves the fix works end-to-end and produces a real, schema-valid, heterogeneous-
roster dataset: one scripted policy in the focal (A1) seat, StrategicDeceiver always present among
the 4 co-players, across all 3 scenarios and a severity sweep, so deception_rate is non-zero and
measurable per analysis/feature_extraction.py's existing logic.

Tagged meta.arm = "scripted" (schema-valid) but meta.policy = "mixed_roster_pilot" and
meta.pilot = True, and every file name carries the "pilot_deception" marker — so it is NOT
confusable with real agents/run_ai_trials.py (Phase G) campaign data, and the train_models.py /
classifier.py / stats_tests.py queries should keep excluding it (see the "arm='scripted'
exclusion" patch proposed alongside this).

Usage: python seed_deception_pilot.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

REPO = "/home/claude/utkarshpandey04/ai-human-scarcity-study"
sys.path.insert(0, REPO)
os.chdir(REPO)

from agents.coplayers import get_policy
from agents.environment import ScarcityEnv, DEFAULT_SEVERITY
from common.schema import validate_trial

OUT_DIR = "/tmp/claude-0/-home-claude/bd55217a-8e79-5a52-a158-6fcca40c7403/scratchpad/deception_seed/out"
os.makedirs(OUT_DIR, exist_ok=True)

# Focal seat (A1) rotates through these non-deceiver policies so the focal row stays comparable to
# the existing scripted-pilot convention; A2 is always the deceiver so every trial has a genuine
# false-claim source; A3-A5 fill out a believable mixed society rather than four clones.
FOCAL_POLICIES = ["cooperator", "free_rider", "tit_for_tat", "random"]
COPLAYER_ROSTER = ["deceiver", "cooperator", "free_rider", "tit_for_tat"]  # for A2..A5

SCENARIOS = ["calm", "drought", "repeated_trust"]
SEVERITIES = [0.0, 0.3, 0.5, 0.7, 0.9]
SEEDS_PER_CELL = 2  # keep this pilot small; it's a proof + a seed, not the real campaign


def run_one(scenario: str, severity: float, seed: int, focal_policy: str, trial_index: int) -> list[dict]:
    player_ids = ["A1", "A2", "A3", "A4", "A5"]
    env = ScarcityEnv(scenario=scenario, seed=seed, severity=severity, player_ids=player_ids)
    policy_names = [focal_policy] + COPLAYER_ROSTER
    policies = {pid: get_policy(name, seed=seed + i + 1) for i, (pid, name) in enumerate(zip(player_ids, policy_names))}

    obs = env.reset()
    trial_id = f"{scenario}_ai_pilot_deception_sev{round(severity*100):03d}_{seed:03d}_{trial_index:03d}"
    timestamp = datetime.now(timezone.utc).isoformat()

    rows: list[dict] = []
    done = False
    while not done:
        actions = {pid: policies[pid].act(o) for pid, o in obs.items() if env.players[pid].alive}
        obs, done, log_rows = env.step(actions)
        for row in log_rows:
            claim = row.pop("_claim", None)
            row["trial_id"] = trial_id
            row["source"] = "ai"
            row["timestamp"] = timestamp
            row["meta"] = {
                "seed": seed,
                "arm": "scripted",
                "policy": "mixed_roster_pilot",
                "roster": {pid: name for pid, name in zip(player_ids, policy_names)},
                "severity": severity,
                "claim": claim,
                "pilot": True,
                "pilot_note": "deception seed data, not Phase G campaign — exclude from classifier training by default",
            }
            rows.append(row)
    return rows


def main() -> None:
    written = []
    total_claims = 0
    total_deceptive = 0
    for scenario in SCENARIOS:
        for severity in SEVERITIES:
            if scenario != "drought" and severity not in (0.0, 0.7):
                # keep the pilot small: full severity sweep only where it's scenario-relevant
                # (drought); calm/repeated_trust just get the two anchor points.
                continue
            for seed in range(SEEDS_PER_CELL):
                focal_policy = FOCAL_POLICIES[seed % len(FOCAL_POLICIES)]
                rows = run_one(scenario, severity, seed, focal_policy, trial_index=seed)
                validate_trial(rows)
                for r in rows:
                    c = (r.get("meta") or {}).get("claim")
                    if c and c.get("kind") == "claim_stock" and c.get("value") is not None:
                        total_claims += 1
                        if int(c["value"]) != int(r.get("resource_before", 0)):
                            total_deceptive += 1
                trial_id = rows[0]["trial_id"]
                path = os.path.join(OUT_DIR, f"{trial_id}.jsonl")
                with open(path, "w", encoding="utf-8") as f:
                    for row in rows:
                        f.write(json.dumps(row) + "\n")
                written.append(path)

    print(f"{len(written)} pilot trials written to {OUT_DIR}")
    print(f"claim_stock messages: {total_claims}, of which deceptive (value != resource_before): {total_deceptive}")
    rate = (total_deceptive / total_claims) if total_claims else 0.0
    print(f"pilot deception_rate overall: {rate:.1%}")


if __name__ == "__main__":
    main()
