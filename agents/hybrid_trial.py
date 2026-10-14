"""CLI: run one full trial with every player driven by a HybridAgent — the Gate F demo ("all three
arms run a trial each with no code change — the arm is a CLI flag"). This is Phase F's proof the
routing works end to end; agents/run_ai_trials.py (Phase G) is what sweeps this across the real
seed/scenario/model grid.

`rl_only` and `hybrid` need a trained checkpoint (`python tasks.py train_rl` first). `llm_only`
makes real API calls, same cost caveat as agents/llm_trial.py.

Usage: python -m agents.hybrid_trial --scenario drought --seed 0 --arm hybrid
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agents.coplayers import get_policy
from agents.environment import DEFAULT_SEVERITY, ScarcityEnv
from agents.hybrid_agent import HybridAgent, load_rl_model
from common.actions import MessageKind
from common.schema import validate_trial

LOG_DIR = os.path.join("data", "ai_logs")


def build_trial_id(
    scenario: str,
    arm: str,
    severity: float,
    seed: int,
    trial_index: int = 0,
    coplayer_mode: str = "standard",
) -> str:
    """Shared trial-id/filename format. Includes `severity` and `coplayer_mode` so the Phase G
    grid doesn't collide on disk when sweeping across scenarios, arms, severities, rosters, and seeds.
    """
    sev_bucket = f"sev{round(severity * 100):03d}"
    roster_tag = f"_{coplayer_mode}" if coplayer_mode and coplayer_mode != "standard" else ""
    return f"{scenario}_ai_{arm}{roster_tag}_{sev_bucket}_{seed:03d}_{trial_index:03d}"


def run_trial(
    scenario: str,
    seed: int,
    arm: str,
    provider: str | None = None,
    model: str | None = None,
    model_path: str | None = None,
    trial_index: int = 0,
    severity: float = DEFAULT_SEVERITY,
    rl_model: object | None = None,
    coplayer_mode: str = "standard",
) -> tuple[list[dict], dict]:
    """`rl_model` may be passed in pre-loaded (agents/run_ai_trials.py shares one loaded checkpoint
    across an entire campaign rather than reloading it from disk per trial)."""
    needs_rl = rl_model is not None or model_path is not None or arm in ("rl_only", "hybrid")
    if rl_model is None and needs_rl:
        rl_model = load_rl_model(**({"model_path": model_path} if model_path else {}))
    agent = HybridAgent(arm=arm, rl_model=rl_model, provider=provider, model=model)

    focal_id = "A1"
    coplayer_ids = ["A2", "A3", "A4", "A5"]
    player_ids = [focal_id] + coplayer_ids
    env = ScarcityEnv(
        scenario=scenario,
        seed=seed,
        severity=severity,
        player_ids=player_ids,
    )
    rosters = {
        "standard": ["cooperator", "free_rider", "tit_for_tat", "random"],
        "deceptive": ["cooperator", "free_rider", "tit_for_tat", "deceiver"],
        "llm_ecology": ["llm_groq", "llm_gemini", "tit_for_tat", "llm_auto"],
    }
    if coplayer_mode not in rosters:
        raise ValueError(f"unknown coplayer_mode {coplayer_mode!r}, must be one of {list(rosters.keys())}")
    roster = rosters[coplayer_mode]
    coplayers = {
        pid: get_policy(roster[i], seed=seed + i + 1)
        for i, pid in enumerate(coplayer_ids)
    }

    obs = env.reset()

    trial_id = build_trial_id(
        scenario, arm, severity, seed, trial_index, coplayer_mode=coplayer_mode
    )
    timestamp = datetime.now(timezone.utc).isoformat()

    rows: list[dict] = []
    decision_source_counts = {"rl": 0, "llm": 0}
    llm_calls = 0
    parse_failures = 0  # excludes rate-limited calls — see agents/llm_reasoning.py::decide()
    rate_limited = 0

    done = False
    while not done:
        actions = {}
        decision_meta: dict[str, dict] = {}
        for pid, o in obs.items():
            if not env.players[pid].alive:
                continue
            if pid == focal_id:
                action, meta = agent.decide(o)
                actions[pid] = action
                decision_meta[pid] = meta
                decision_source_counts[meta["decision_source"]] += 1
                if meta["decision_source"] == "llm":
                    llm_calls += 1
                    if meta.get("llm_parse_failure"):
                        if meta.get("llm_rate_limited"):
                            rate_limited += 1
                        else:
                            parse_failures += 1
            else:
                action = coplayers[pid].act(o)
                actions[pid] = action
                policy_name = roster[coplayer_ids.index(pid)]
                decision_meta[pid] = {
                    "decision_source": "coplayer",
                    "policy": policy_name,
                }

        obs, done, log_rows = env.step(actions)
        for row in log_rows:
            claim = row.pop("_claim", None)
            m = decision_meta.get(row["agent_id"], {})
            row["trial_id"] = trial_id
            row["source"] = "ai"
            row["timestamp"] = timestamp
            row_meta = {
                "seed": seed,
                "arm": arm,
                "coplayer_mode": coplayer_mode,
                "severity": severity,
                "decision_source": m.get("decision_source"),
                "claim": claim,
            }
            if row["agent_id"] == focal_id:
                row_meta.update(
                    {
                        "model": m.get("model"),
                        "llm_parse_failure": m.get("llm_parse_failure", False),
                        "llm_rate_limited": m.get("llm_rate_limited", False),
                        "prompt_tokens": m.get("prompt_tokens"),
                        "completion_tokens": m.get("completion_tokens"),
                    }
                )
            else:
                row_meta["policy"] = m.get("policy")

            row["meta"] = row_meta
            rows.append(row)

    stats = {
        "trial_id": trial_id,
        "arm": arm,
        "coplayer_mode": coplayer_mode,
        "decision_source_counts": decision_source_counts,
        "llm_calls": llm_calls,
        "parse_failures": parse_failures,
        "rate_limited": rate_limited,
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
    parser.add_argument("--arm", required=True, choices=["rl_only", "llm_only", "hybrid"])
    parser.add_argument("--provider", default=None, help="groq | gemini (llm_only/hybrid only)")
    parser.add_argument("--model", default=None)
    parser.add_argument("--model-path", default=None, help="RL checkpoint (rl_only/hybrid only)")
    parser.add_argument(
        "--severity", type=float, default=DEFAULT_SEVERITY, help="ambient scarcity dose in [0, 1]"
    )
    parser.add_argument(
        "--coplayer-mode",
        default="standard",
        choices=["standard", "deceptive", "llm_ecology"],
        help="co-player roster preset",
    )
    args = parser.parse_args()

    rows, stats = run_trial(
        args.scenario,
        args.seed,
        args.arm,
        provider=args.provider,
        model=args.model,
        model_path=args.model_path,
        severity=args.severity,
        coplayer_mode=args.coplayer_mode,
    )
    validate_trial(rows)
    path = write_trial(rows)

    print(f"OK   {path} ({len(rows)} rows)")
    print(f"Arm:                 {stats['arm']}")
    print(f"Coplayer Mode:       {stats['coplayer_mode']}")
    print(f"Decisions by source: {stats['decision_source_counts']}")
    if stats["llm_calls"]:
        non_rate_limited = stats["llm_calls"] - stats["rate_limited"]
        rate = (stats["parse_failures"] / non_rate_limited) if non_rate_limited else 0.0
        print(f"LLM calls:           {stats['llm_calls']} (parse failures: {stats['parse_failures']}, {rate:.1%}"
              f"; rate-limited: {stats['rate_limited']}, excluded from that rate)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
