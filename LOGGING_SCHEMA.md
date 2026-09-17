# Shared Logging Schema

Every action taken — by an AI agent or a human participant — must be logged as one JSON object matching this exact structure. Both `agents/` (Group 2) and `human_interface/` (Group 1) write to this schema so `analysis/` can process both log sets identically.

```json
{
  "trial_id": "drought_round_human_003",
  "source": "human",
  "agent_id": "P07",
  "round": 6,
  "scenario": "drought",
  "action_type": "share",
  "target_agent": "P02",
  "message_sent": "Take less today, I'll pay you back",
  "resource_before": 4,
  "resource_after": 6,
  "alive": true,
  "timestamp": "2026-09-02T10:32:00"
}
```

## Field definitions

| Field | Type | Notes |
|---|---|---|
| `trial_id` | string | `<scenario>_<source>_<sequence>`, e.g. `drought_human_003` |
| `source` | string | `"ai"` or `"human"` |
| `agent_id` | string | `A1`-style for AI, `P01`-style for human participants |
| `round` | int | 1-indexed round number |
| `scenario` | string | `"calm"`, `"drought"`, `"repeated_trust"` |
| `action_type` | string | one of: `gather`, `share`, `hoard`, `move`, `skip`, `communicate` |
| `target_agent` | string or null | required for `share`/`communicate`, null otherwise |
| `message_sent` | string or null | free text if `communicate`/`share` includes a message, else null |
| `resource_before` | number | resource level before this action |
| `resource_after` | number | resource level after this action |
| `alive` | bool | agent's survival status after this round |
| `timestamp` | string | ISO 8601 |

## Extended fields — `meta` (proposed, not yet adopted)

A nested `meta` object, so the top level never needs renegotiating again as the analysis needs more
context per row. **Optional for now** — omitting it entirely is valid, so existing logs keep
passing. See `INTEGRATION_ISSUES.md` #6 for why each field exists.

```json
"meta": {
  "severity": 0.7,             // scarcity level for this trial, in [0, 1] — the dose-response sweep
  "seed": 42,                  // matched between the human arm and the AI arm for this trial
  "arm": "hybrid",             // "rl_only" | "llm_only" | "hybrid" | "human"
  "model": "gpt-4o-mini",      // null for human rows
  "decision_latency_ms": 4210, // time to decide, ms — humans and AI both
  "claim": {                   // the structured Message slot, once ACTIONS.md's communicate lands
    "kind": "claim_stock",
    "value": 1,
    "target": "A2",
    "surface": "I only have 1 left, please spare some"
  }
}
```

`common/schema.py` is the enforced version of this — treat it as authoritative over this document
for anything code-checked.

## Rules
- Never change this schema on only one branch — both groups must agree first.
- File output: one JSON object per line (JSONL) in `data/human_logs/<trial_id>.jsonl` or `data/ai_logs/<trial_id>.jsonl`.
- Validate every row with `common.schema.validate_row()` before writing it — don't hand-roll the check.
