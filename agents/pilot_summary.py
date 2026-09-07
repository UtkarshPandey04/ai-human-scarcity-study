"""Summarize data/ai_logs/*.jsonl into a committed markdown report.

The raw logs are gitignored (regeneratable via `python tasks.py pilot`) but the MSE-1 EDA
deliverable needs real numbers, not hypothetical ones — see agents/PHASE_PLAN.md Phase B. This
produces the three things MSE-1(TODO) asks for: an action-type distribution, resource-over-rounds,
and survival rate, broken down by scenario since that's the axis the whole study cares about.

Usage: python -m agents.pilot_summary [--out data/pilot_summary.md]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from collections import defaultdict

LOG_DIR = os.path.join("data", "ai_logs")
DEFAULT_OUT = os.path.join("data", "pilot_summary.md")


def load_rows() -> list[dict]:
    rows = []
    for path in sorted(glob.glob(os.path.join(LOG_DIR, "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            rows.extend(json.loads(line) for line in f if line.strip())
    return rows


def summarize(rows: list[dict]) -> str:
    scenarios = sorted({r["scenario"] for r in rows})
    action_types = sorted({r["action_type"] for r in rows})

    lines = ["# AI Pilot Log Summary", ""]
    lines.append(
        f"Generated from `data/ai_logs/*.jsonl` — {len(rows)} action rows across "
        f"{len({r['trial_id'] for r in rows})} trials, {len(scenarios)} scenarios. "
        "Every player runs a fixed `agents/coplayers.py` policy (random / cooperator / "
        "free_rider / tit_for_tat) — no LLM or RL policy involved yet. Regenerate with "
        "`python tasks.py pilot && python -m agents.pilot_summary`."
    )
    lines.append("")

    # --- Action-type distribution, overall and per scenario ---
    lines.append("## Action distribution")
    lines.append("")
    header = "| Scenario | " + " | ".join(action_types) + " | Total |"
    sep = "|---|" + "---|" * (len(action_types) + 1)
    lines.append(header)
    lines.append(sep)
    for scenario in ["ALL", *scenarios]:
        subset = rows if scenario == "ALL" else [r for r in rows if r["scenario"] == scenario]
        counts = defaultdict(int)
        for r in subset:
            counts[r["action_type"]] += 1
        cells = " | ".join(str(counts[a]) for a in action_types)
        lines.append(f"| {scenario} | {cells} | {len(subset)} |")
    lines.append("")

    # --- Survival rate per scenario: fraction of (trial, agent) pairs alive at their last row ---
    lines.append("## Survival rate by scenario")
    lines.append("")
    lines.append("| Scenario | Agent-trials | Survived | Survival rate |")
    lines.append("|---|---|---|---|")
    for scenario in scenarios:
        subset = [r for r in rows if r["scenario"] == scenario]
        last_row_per_agent: dict[tuple[str, str], dict] = {}
        for r in subset:
            key = (r["trial_id"], r["agent_id"])
            prev = last_row_per_agent.get(key)
            if prev is None or r["round"] >= prev["round"]:
                last_row_per_agent[key] = r
        total = len(last_row_per_agent)
        survived = sum(1 for r in last_row_per_agent.values() if r["alive"])
        rate = (survived / total * 100) if total else 0.0
        lines.append(f"| {scenario} | {total} | {survived} | {rate:.1f}% |")
    lines.append("")

    # --- Mean resource by round, per scenario (a rough line-chart-in-a-table) ---
    lines.append("## Mean resource_after by round")
    lines.append("")
    for scenario in scenarios:
        subset = [r for r in rows if r["scenario"] == scenario]
        by_round: dict[int, list[float]] = defaultdict(list)
        for r in subset:
            by_round[r["round"]].append(r["resource_after"])
        rounds = sorted(by_round)
        lines.append(f"**{scenario}**")
        lines.append("")
        lines.append("| Round | Mean resource_after | n |")
        lines.append("|---|---|---|")
        for rnd in rounds:
            values = by_round[rnd]
            mean = sum(values) / len(values)
            lines.append(f"| {rnd} | {mean:.2f} | {len(values)} |")
        lines.append("")

    return "\n".join(lines)


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    rows = load_rows()
    if not rows:
        print(f"No logs found in {LOG_DIR}/ — run `python tasks.py pilot` first.")
        return 1

    report = summarize(rows)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Wrote {args.out} ({len(rows)} rows summarized)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
