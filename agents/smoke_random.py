"""CLI: run one or more trials with every player on a named co-player policy and write
schema-valid JSONL logs to data/ai_logs/.

Two uses:
  1. Gate B demo — a single trial proving the environment produces valid logs end to end.
  2. MSE-1 pilot logs (agents/PHASE_PLAN.md Phase B milestone) — run enough trials to give the
     coursework EDA real distributions instead of hypothetical ones.

No LLM or RL policy involved yet (that's Phase D/E); every player, including the notional "focal"
one, runs a fixed agents/coplayers.py policy. Logs are tagged `meta.arm = "scripted"` so they're
never mistaken for a real experimental arm.

Usage:
    python -m agents.smoke_random --scenario drought --seed 0
    python -m agents.smoke_random --scenario calm --seed 0 --policy cooperator --trials 20
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone

from agents.coplayers import get_policy
from agents.environment import ScarcityEnv
from common.schema import validate_trial

LOG_DIR = os.path.join("data", "ai_logs")


def run_trial(scenario: str, seed: int, policy_name: str, trial_index: int = 0) -> list[dict]:
    """Play one full trial and return schema-ready rows (source/timestamp/meta already filled)."""
    env = ScarcityEnv(scenario=scenario, seed=seed)
    policies = {pid: get_policy(policy_name, seed=seed + i) for i, pid in enumerate(env.player_ids)}

    obs = env.reset()
    # policy_name is part of the id: without it, two calls that only differ by --policy produce
    # identical filenames and silently overwrite each other's logs (caught in Phase B testing —
    # see PHASE_PLAN.md; a real run across multiple policies at the same seed lost 45 of 60
    # trials to this before the fix).
    trial_id = f"{scenario}_ai_{policy_name}_{seed:03d}_{trial_index:03d}"
    timestamp = datetime.now(timezone.utc).isoformat()

    rows: list[dict] = []
    done = False
    while not done:
        actions = {pid: policies[pid].act(o) for pid, o in obs.items() if env.players[pid].alive}
        obs, done, log_rows = env.step(actions)
        for row in log_rows:
            row["trial_id"] = trial_id
            row["source"] = "ai"
            row["timestamp"] = timestamp
            row["meta"] = {"seed": seed, "arm": "scripted", "policy": policy_name, "severity": None}
            rows.append(row)

    return rows


def write_trial(rows: list[dict]) -> str:
    os.makedirs(LOG_DIR, exist_ok=True)
    trial_id = rows[0]["trial_id"]
    path = os.path.join(LOG_DIR, f"{trial_id}.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    return path


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default="drought")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--policy", default="random", choices=["cooperator", "free_rider", "tit_for_tat", "random"]
    )
    parser.add_argument(
        "--trials", type=int, default=1, help="number of trials to run, seeds start at --seed"
    )
    args = parser.parse_args()

    written = []
    for i in range(args.trials):
        seed = args.seed + i
        rows = run_trial(args.scenario, seed, args.policy, trial_index=i)
        validate_trial(rows)
        path = write_trial(rows)
        written.append(path)
        print(f"OK   {path} ({len(rows)} rows)")

    print(f"\n{len(written)} trial(s) written to {LOG_DIR}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
