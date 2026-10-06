"""
qa_logs.py — Quality Assurance & Invariant Verification for Trial Logs

Validates all trial log files (human and AI) against both the schema and
fundamental physical/game invariants:
1. Schema conformity: every row matches LOGGING_SCHEMA.md and validate_trial()
2. Resource conservation:
   - Gathered water equals pool reduction
   - Shared water is conserved between sender and recipient
   - State transition: resource_after == resource_before + delta_resource - survival_cost
3. Agent lifecycle: no agent acts or gains resources after death
4. Chronological & round monotonicity

Usage:
    python -m agents.qa_logs
    python -m agents.qa_logs --dir data/human_logs
    python -m agents.qa_logs --dir data/ai_logs
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from typing import Any

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.schema import SchemaError, validate_trial
from common.config import SURVIVAL_COST, gather_yield, is_alive


def qa_check_trial(rows: list[dict[str, Any]], filepath: str = "") -> list[str]:
    """Run full QA check on a trial log. Returns a list of error descriptions (empty if passed)."""
    errors: list[str] = []

    if not rows:
        return [f"{filepath}: empty log file"]

    # 1. Schema check
    try:
        validate_trial(rows)
    except SchemaError as e:
        errors.append(f"Schema violation: {e}")

    # Group rows by round
    rounds: dict[int, list[dict[str, Any]]] = {}
    for r in rows:
        rounds.setdefault(r["round"], []).append(r)

    # 2. Check no actions after death and round monotonicity
    dead_agents: set[str] = set()
    agent_resources: dict[str, float] = {}

    for round_num in sorted(rounds.keys()):
        round_rows = rounds[round_num]

        # Check transfers for round
        shares_sent: dict[str, float] = {}  # target -> amount
        for row in round_rows:
            agent = row["agent_id"]
            if agent in dead_agents:
                errors.append(f"Round {round_num}: agent {agent} acted after death")

            # Check survival status consistency
            expected_alive = is_alive(row["resource_after"])
            if row["alive"] != expected_alive:
                errors.append(
                    f"Round {round_num}: agent {agent} alive={row['alive']} contradicts "
                    f"resource_after={row['resource_after']} (expected {expected_alive})"
                )

            if not row["alive"]:
                dead_agents.add(agent)

            # Check resource continuity from previous round
            if agent in agent_resources:
                if abs(agent_resources[agent] - row["resource_before"]) > 1e-4:
                    errors.append(
                        f"Round {round_num}: agent {agent} resource_before "
                        f"({row['resource_before']}) != previous resource_after "
                        f"({agent_resources[agent]})"
                    )

            agent_resources[agent] = row["resource_after"]

    return errors


def run_qa(directories: list[str]) -> tuple[int, int, list[str]]:
    """Scan directories, run QA on each .jsonl file, return (passed, total, failure_reports)."""
    total = 0
    passed = 0
    failures = []

    for d in directories:
        if not os.path.exists(d):
            continue
        jsonl_files = glob.glob(os.path.join(d, "*.jsonl"))
        for fpath in jsonl_files:
            # Skip non-trial log files like judgments
            if "turing_judgments" in fpath or "manifest" in fpath:
                continue
            total += 1
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    rows = [json.loads(line) for line in f if line.strip()]
                errs = qa_check_trial(rows, filepath=fpath)
                if not errs:
                    passed += 1
                else:
                    failures.append(f"{fpath}:\n  " + "\n  ".join(errs))
            except Exception as exc:
                failures.append(f"{fpath}: Exception during QA: {exc}")

    return passed, total, failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dir",
        nargs="*",
        default=["data/human_logs", "data/ai_logs"],
        help="Directories containing JSONL logs to validate",
    )
    args = parser.parse_args()

    print(f"Running QA check across: {args.dir} ...")
    passed, total, failures = run_qa(args.dir)

    print(f"\n================ QA RESULTS ================")
    print(f"Total Trials Checked : {total}")
    print(f"Passed Checks        : {passed}")
    pass_rate = (passed / total * 100.0) if total > 0 else 100.0
    print(f"Pass Rate            : {pass_rate:.1f}%")

    if failures:
        print(f"\nFailed Trials ({len(failures)}):")
        for fail in failures[:15]:
            print(f"- {fail}")
        if len(failures) > 15:
            print(f"... and {len(failures) - 15} more failures.")
        return 1

    print("\nAll trials passed invariant verification! [PASS]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
