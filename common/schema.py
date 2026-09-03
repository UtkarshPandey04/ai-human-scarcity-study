"""Shared logging schema validator — the single source both branches import.

Group 1 should call `validate_row()` inside `human_interface/logging_utils.log_action()` before
every write. Group 2 calls it from `agents/*.py` before writing AI trial logs. Mirrors
`LOGGING_SCHEMA.md` (repo root) — if the two ever disagree, this file wins for anything that's
code-enforced and the .md wins for anything descriptive; fix the drift, don't pick a side and
move on.

`meta` is optional for now, so Group 1's already-shipped logs (which predate the `meta` block
proposed in INTEGRATION_ISSUES.md #6) still pass unchanged. Once both branches adopt it, tighten
the required top-level fields to include it.

No external dependencies (no `jsonschema`) — this project doesn't need the dependency yet, and
adding one speculatively is exactly what the roadmap says not to do.
"""

from __future__ import annotations

from typing import Any

SOURCES = {"ai", "human"}
ACTION_TYPES = {"gather", "share", "hoard", "move", "skip", "communicate"}

# Keep in sync with common/config.py SCENARIOS.
SCENARIOS = {"calm", "drought", "repeated_trust"}

# Values for meta.arm — "human" covers focal-player-substitution human trials; the AI ablation
# arms are defined in agents/PHASE_PLAN.md Phase F.
ARMS = {"rl_only", "llm_only", "hybrid", "human"}

MESSAGE_KINDS = {"claim_stock", "promise_share", "request", "accuse", "none"}

# field -> type or tuple of types accepted by isinstance()
REQUIRED_FIELDS: dict[str, Any] = {
    "trial_id": str,
    "source": str,
    "agent_id": str,
    "round": int,
    "scenario": str,
    "action_type": str,
    "resource_before": (int, float),
    "resource_after": (int, float),
    "alive": bool,
    "timestamp": str,
}

# present-or-absent, but if present may be the given type or None
NULLABLE_FIELDS: dict[str, Any] = {
    "target_agent": str,
    "message_sent": str,
}


class SchemaError(ValueError):
    """Raised by validate_row/validate_trial on a malformed log row."""


def validate_row(row: dict[str, Any]) -> None:
    """Raise SchemaError if `row` does not conform to LOGGING_SCHEMA.md.

    Unknown extra top-level fields are accepted silently (forward-compatible); a missing `meta`
    block is accepted entirely (backward-compatible with logs written before it existed).
    """
    if not isinstance(row, dict):
        raise SchemaError(f"row must be a dict, got {type(row).__name__}")

    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in row:
            raise SchemaError(f"missing required field: {field!r}")
        value = row[field]
        # bool is a subclass of int in Python; only "alive" should ever accept bool.
        if expected_type is not bool and isinstance(value, bool):
            raise SchemaError(f"field {field!r} must be {expected_type}, got bool")
        if not isinstance(value, expected_type):
            raise SchemaError(
                f"field {field!r} must be {expected_type}, got {type(value).__name__}"
            )

    for field, expected_type in NULLABLE_FIELDS.items():
        if field in row and row[field] is not None and not isinstance(row[field], expected_type):
            raise SchemaError(
                f"field {field!r} must be {expected_type} or null, "
                f"got {type(row[field]).__name__}"
            )

    if row["source"] not in SOURCES:
        raise SchemaError(f"source must be one of {sorted(SOURCES)}, got {row['source']!r}")

    if row["action_type"] not in ACTION_TYPES:
        raise SchemaError(
            f"action_type must be one of {sorted(ACTION_TYPES)}, got {row['action_type']!r}"
        )

    if row["scenario"] not in SCENARIOS:
        raise SchemaError(f"scenario must be one of {sorted(SCENARIOS)}, got {row['scenario']!r}")

    if row["round"] < 1:
        raise SchemaError(f"round must be >= 1, got {row['round']}")

    if row["action_type"] in ("share", "communicate") and row.get("target_agent") is None:
        raise SchemaError(f"action_type {row['action_type']!r} requires a non-null target_agent")

    meta = row.get("meta")
    if meta is not None:
        _validate_meta(meta)


def _validate_meta(meta: dict[str, Any]) -> None:
    if not isinstance(meta, dict):
        raise SchemaError(f"meta must be a dict, got {type(meta).__name__}")

    if meta.get("arm") is not None and meta["arm"] not in ARMS:
        raise SchemaError(f"meta.arm must be one of {sorted(ARMS)}, got {meta['arm']!r}")

    if meta.get("seed") is not None and not isinstance(meta["seed"], int):
        raise SchemaError("meta.seed must be an int")

    severity = meta.get("severity")
    if severity is not None:
        if isinstance(severity, bool) or not isinstance(severity, (int, float)):
            raise SchemaError("meta.severity must be a number")
        if not (0 <= severity <= 1):
            raise SchemaError(f"meta.severity must be in [0, 1], got {severity}")

    latency = meta.get("decision_latency_ms")
    if latency is not None:
        if isinstance(latency, bool) or not isinstance(latency, (int, float)):
            raise SchemaError("meta.decision_latency_ms must be a number")
        if latency < 0:
            raise SchemaError(f"meta.decision_latency_ms must be >= 0, got {latency}")

    claim = meta.get("claim")
    if claim is not None:
        _validate_claim(claim)


def _validate_claim(claim: dict[str, Any]) -> None:
    if not isinstance(claim, dict):
        raise SchemaError(f"meta.claim must be a dict, got {type(claim).__name__}")

    kind = claim.get("kind", "none")
    if kind not in MESSAGE_KINDS:
        raise SchemaError(f"meta.claim.kind must be one of {sorted(MESSAGE_KINDS)}, got {kind!r}")

    value = claim.get("value")
    if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
        raise SchemaError("meta.claim.value must be a number or null")


def validate_trial(rows: list[dict[str, Any]]) -> None:
    """Validate every row in a trial, plus cross-row invariants:

    - every row individually passes validate_row()
    - round numbers never go backwards for a given agent
    - no agent has an action logged after it was previously marked not alive
    """
    if not rows:
        raise SchemaError("trial has no rows")

    for row in rows:
        validate_row(row)

    last_round: dict[str, int] = {}
    dead: set[str] = set()
    for row in rows:
        agent = row["agent_id"]
        if agent in dead:
            raise SchemaError(
                f"agent {agent!r} has an action logged after being marked not alive "
                f"(round {row['round']})"
            )
        if agent in last_round and row["round"] < last_round[agent]:
            raise SchemaError(
                f"agent {agent!r} round number went backwards "
                f"({last_round[agent]} -> {row['round']})"
            )
        last_round[agent] = row["round"]
        if not row["alive"]:
            dead.add(agent)


def _main() -> int:
    """CLI: `python -m common.schema path/to/trial.jsonl [more.jsonl ...]`
    Validates each file as one trial and prints a pass/fail summary.
    """
    import json
    import sys

    paths = sys.argv[1:]
    if not paths:
        print("usage: python -m common.schema path/to/trial.jsonl [more.jsonl ...]")
        return 1

    exit_code = 0
    for path in paths:
        try:
            with open(path, encoding="utf-8") as f:
                rows = [json.loads(line) for line in f if line.strip()]
            validate_trial(rows)
        except (SchemaError, OSError, json.JSONDecodeError) as exc:
            print(f"FAIL {path}: {exc}")
            exit_code = 1
        else:
            print(f"OK   {path} ({len(rows)} rows)")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(_main())
