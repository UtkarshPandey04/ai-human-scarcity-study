"""CLI: run one full trial with every player driven by agents/llm_reasoning.py — the Gate E demo
("one full drought trial runs end-to-end on LLM decisions, logs validate, parse-failure rate under
2%"). Logs are tagged `meta.arm = "llm_only"`, matching the ablation-arm naming Phase F will reuse
for the real trial campaign — this file is that arm's first, single-trial proof it works, not the
campaign itself (that's agents/run_ai_trials.py, Phase G).

Every round makes up to NUM_PLAYERS real API calls, so this costs real tokens/latency — don't loop
this the way agents/smoke_random.py loops random trials.

Usage: python -m agents.llm_trial --scenario drought --seed 0 --provider groq
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone

from agents.environment import ScarcityEnv
from agents.llm_reasoning import decide
from common.schema import validate_trial

LOG_DIR = os.path.join("data", "ai_logs")


def run_trial(
    scenario: str, seed: int, provider: str | None = None, model: str | None = None, trial_index: int = 0
) -> tuple[list[dict], dict]:
    env = ScarcityEnv(scenario=scenario, seed=seed)
    obs = env.reset()

    trial_id = f"{scenario}_ai_llm_{provider or 'default'}_{seed:03d}_{trial_index:03d}"
    timestamp = datetime.now(timezone.utc).isoformat()

    rows: list[dict] = []
    total_calls = 0
    parse_failures = 0  # excludes rate-limited calls — see the note on llm_rate_limited below
    rate_limited = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0

    done = False
    while not done:
        actions = {}
        decision_meta: dict[str, dict] = {}
        for pid, o in obs.items():
            if not env.players[pid].alive:
                continue
            action, meta = decide(o, provider=provider, model=model)
            actions[pid] = action
            decision_meta[pid] = meta
            total_calls += 1
            if meta.get("llm_parse_failure"):
                if meta.get("llm_rate_limited"):
                    rate_limited += 1
                else:
                    parse_failures += 1
            total_prompt_tokens += meta.get("prompt_tokens", 0) or 0
            total_completion_tokens += meta.get("completion_tokens", 0) or 0

        obs, done, log_rows = env.step(actions)
        for row in log_rows:
            m = decision_meta.get(row["agent_id"], {})
            row["trial_id"] = trial_id
            row["source"] = "ai"
            row["timestamp"] = timestamp
            row["meta"] = {
                "seed": seed,
                "arm": "llm_only",
                "model": m.get("model"),
                "severity": None,
                "decision_source": "llm",
                "llm_parse_failure": m.get("llm_parse_failure"),
                # Kept separate from llm_parse_failure — a rate-limited call isn't evidence the
                # model produced bad output, it's evidence this project ran out of quota. See
                # agents/llm_reasoning.py::decide()'s docstring. Filter this out before computing
                # any parse-failure-rate figure for the paper.
                "llm_rate_limited": m.get("llm_rate_limited", False),
                "prompt_tokens": m.get("prompt_tokens"),
                "completion_tokens": m.get("completion_tokens"),
            }
            rows.append(row)

    non_rate_limited_calls = total_calls - rate_limited
    stats = {
        "trial_id": trial_id,
        "total_calls": total_calls,
        "parse_failures": parse_failures,
        "rate_limited": rate_limited,
        "parse_failure_rate": (parse_failures / non_rate_limited_calls) if non_rate_limited_calls else 0.0,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
    }
    return rows, stats


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
    parser.add_argument("--provider", default=None, help="groq | gemini (defaults to LLM_PROVIDER env)")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    rows, stats = run_trial(args.scenario, args.seed, provider=args.provider, model=args.model)
    validate_trial(rows)
    path = write_trial(rows)

    print(f"OK   {path} ({len(rows)} rows)")
    print(f"Total LLM calls:     {stats['total_calls']}")
    print(f"Rate-limited:        {stats['rate_limited']} (excluded from parse-failure rate below)")
    print(f"Parse failures:      {stats['parse_failures']} ({stats['parse_failure_rate']:.1%})")
    print(f"Prompt tokens:       {stats['total_prompt_tokens']}")
    print(f"Completion tokens:   {stats['total_completion_tokens']}")
    print(f"Gate E (<2% parse failure rate, excluding rate limits): "
          f"{'PASS' if stats['parse_failure_rate'] < 0.02 else 'FAIL'}")
    if stats["rate_limited"]:
        print("⚠ Some calls hit a provider rate limit this run — see llm_rate_limited in the "
              "log's meta if you need to know exactly which rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
