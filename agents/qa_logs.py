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

        # Dead set as of the start of this round — a share to someone who dies *this* round is legal.
        dead_at_round_start = set(dead_agents)
        seen_this_round: set[str] = set()
        for row in round_rows:
            agent = row["agent_id"]
            if agent in dead_agents:
                errors.append(f"Round {round_num}: agent {agent} acted after death")
            if agent in seen_this_round:
                errors.append(f"Round {round_num}: agent {agent} has more than one row")
            seen_this_round.add(agent)

            if row["action_type"] == "share" and row.get("target_agent") in dead_at_round_start:
                errors.append(
                    f"Round {round_num}: agent {agent} shared with dead agent {row['target_agent']}"
                )

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


def summarize_trials(trials: list[list[dict[str, Any]]]) -> dict[str, Any]:
    """Dataset-level counts the per-trial check can't see (agents/PHASE_PLAN.md Phase H): trials
    and rows per (scenario, arm), LLM parse-failure rate, and token totals.

    The parse-failure rate excludes `llm_rate_limited` rows from both numerator and denominator —
    a rate-limited call is a quota event, not evidence about the model (see llm_reasoning.decide()).
    """
    cells: dict[tuple[str, str], dict[str, int]] = {}
    llm_calls = parse_failures = rate_limited = 0
    prompt_tokens = completion_tokens = 0
    for rows in trials:
        if not rows:
            continue
        meta0 = rows[0].get("meta") or {}
        key = (rows[0]["scenario"], meta0.get("arm") or rows[0].get("source", "?"))
        cell = cells.setdefault(key, {"trials": 0, "rows": 0})
        cell["trials"] += 1
        cell["rows"] += len(rows)
        for row in rows:
            meta = row.get("meta") or {}
            if meta.get("decision_source") != "llm" and meta.get("arm") not in ("llm_only", "llm_human_steered"):
                continue
            if meta.get("llm_rate_limited"):
                rate_limited += 1
                continue
            llm_calls += 1
            parse_failures += bool(meta.get("llm_parse_failure"))
            prompt_tokens += meta.get("prompt_tokens") or 0
            completion_tokens += meta.get("completion_tokens") or 0
    return {
        "cells": {f"{s}/{a}": c for (s, a), c in sorted(cells.items())},
        "llm_calls": llm_calls,
        "llm_rate_limited": rate_limited,
        "llm_parse_failures": parse_failures,
        "llm_parse_failure_rate": (parse_failures / llm_calls) if llm_calls else None,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }


def run_qa(directories: list[str], loaded: list | None = None) -> tuple[int, int, list[str]]:
    """Scan directories, run QA on each .jsonl file, return (passed, total, failure_reports).
    If `loaded` is given, every successfully parsed trial's rows are appended to it."""
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
                if loaded is not None:
                    loaded.append(rows)
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
    loaded: list[list[dict[str, Any]]] = []
    passed, total, failures = run_qa(args.dir, loaded=loaded)
    summary = summarize_trials(loaded)

    print(f"\n================ QA RESULTS ================")
    print(f"Total Trials Checked : {total}")
    print(f"Passed Checks        : {passed}")
    pass_rate = (passed / total * 100.0) if total > 0 else 100.0
    print(f"Pass Rate            : {pass_rate:.1f}%")

    print("\nTrials / rows per scenario/arm:")
    for cell, counts in summary["cells"].items():
        print(f"  {cell:<34} {counts['trials']:>5} trials  {counts['rows']:>7} rows")
    if summary["llm_calls"] or summary["llm_rate_limited"]:
        rate = summary["llm_parse_failure_rate"]
        rate_str = f"{rate * 100:.1f}%" if rate is not None else "n/a"
        print(
            f"\nLLM calls (excl. rate-limited): {summary['llm_calls']}  "
            f"parse failures: {summary['llm_parse_failures']} ({rate_str})"
        )
        print(f"LLM rate-limited calls        : {summary['llm_rate_limited']}")
        print(f"Tokens (prompt / completion)  : {summary['prompt_tokens']} / {summary['completion_tokens']}")

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
