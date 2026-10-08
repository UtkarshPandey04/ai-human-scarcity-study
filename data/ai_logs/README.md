# data/ai_logs — AI trial logs

Raw logs are **not committed** (thousands of files; regenerate them, or get the frozen archive).
The frozen paper dataset is `data/releases/ai_logs_<version>.zip`; its sha256, per-cell counts,
QA result and the git SHAs that produced it are in the tracked `data/releases/ai_logs_<version>.json`.

## What's in this directory

| Files | Produced by | Experimental data? |
|---|---|---|
| `<scenario>_ai_<arm>_sev<NNN>_<seed>_<idx>.jsonl` | `python tasks.py trials` (`agents/run_ai_trials.py`) | **Yes** — campaign trials, arms `hybrid` / `rl_only` / `llm_only` |
| `manifest.json` | same | Index of campaign trials: status, arm, severity, seed, matched-seed flag, model, LLM calls, parse failures, rate-limited calls, and per-trial `git_sha` / `git_dirty` / `prompt_file_sha256` |
| `<scenario>_ai_<policy>_<seed>_<idx>.jsonl` (policy = cooperator, free_rider, random, tit_for_tat) | `python tasks.py pilot` (`agents/smoke_random.py`) | **No** — scripted pilot logs (`meta.arm = "scripted"`) for smoke tests and the MSE-1 EDA |

`sev<NNN>` is severity × 100 (`sev070` = 0.7). Seeds 0–29 are the matched seeds shared with human
sessions (`common/config.py: MATCHED_SEEDS`); `meta.matched_seed` marks them.

## Row format

One JSON object per player per round, in the shared schema (`LOGGING_SCHEMA.md`,
`common/schema.py`). AI-specific `meta` fields:

- `decision_source` — `rl` or `llm` (which layer of the hybrid acted)
- `llm_parse_failure` — the LLM's output failed validation twice; the player skipped
- `llm_rate_limited` — the provider refused the call for quota. **Exclude these rows from any
  parse-failure rate** (`agents/qa_logs.py` already does)
- `prompt_tokens`, `completion_tokens`, `model`, `severity`, `seed`, `arm`, `matched_seed`

## Checking and freezing

```
python tasks.py qa_logs --dir data/ai_logs     # invariants + per-cell counts
python tasks.py freeze_ai_logs --version v1    # refuses unless every campaign trial passes QA
```

Logs produced before the share/survival-cost step-order fix (merged from `group1-human-study`,
2026-10-07) fail the stock-continuity check and must not be used.
