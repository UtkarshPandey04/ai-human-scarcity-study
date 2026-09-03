"""Command runner for this repo. Run with `python tasks.py <task>`.

Using this instead of a Makefile: `make` isn't installed on every team member's machine (this repo
is developed on Windows), and a stdlib-only Python script needs nothing extra installed to run.
PHASE_PLAN.md refers to these as `make validate` etc. for brevity — read that as `python tasks.py
validate`.
"""

from __future__ import annotations

import subprocess
import sys


def validate() -> int:
    """Run the schema self-tests (tests/test_schema.py)."""
    return subprocess.call(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", ".", "-v"]
    )


def validate_logs() -> int:
    """Validate JSONL trial log files passed as extra args, e.g.
    `python tasks.py validate_logs data/ai_logs/drought_ai_001.jsonl`
    """
    paths = sys.argv[2:]
    if not paths:
        print("usage: python tasks.py validate_logs <path.jsonl> [more.jsonl ...]")
        return 1
    return subprocess.call([sys.executable, "-m", "common.schema", *paths])


def smoke() -> int:
    """Phase B: run a short random-agent trial and validate its output."""
    print("agents.smoke_random not implemented yet — see agents/PHASE_PLAN.md Phase B")
    return 1


def pilot() -> int:
    """Phase B: generate the pilot AI logs needed for the MSE-1 EDA deliverable."""
    print("pilot logs not implemented yet — see agents/PHASE_PLAN.md Phase B")
    return 1


def trials() -> int:
    """Phase G: run the full AI trial campaign."""
    print("agents.run_ai_trials not implemented yet — see agents/PHASE_PLAN.md Phase G")
    return 1


TASKS = {
    "validate": validate,
    "validate_logs": validate_logs,
    "smoke": smoke,
    "pilot": pilot,
    "trials": trials,
}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in TASKS:
        print(f"usage: python tasks.py <{'|'.join(TASKS)}>")
        return 1
    return TASKS[sys.argv[1]]()


if __name__ == "__main__":
    raise SystemExit(main())
