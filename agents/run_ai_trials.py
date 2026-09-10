"""Phase G — the AI trial campaign. Sweeps the real grid (scenario x severity x arm x seed, plus
model for the primary arm) via agents/hybrid_trial.run_trial, writing one JSONL file per trial to
data/ai_logs/ and one entry per trial to data/ai_logs/manifest.json.

Budget shape, from agents/PHASE_PLAN.md Phase G: the full grid only runs on the arm that mirrors
the human protocol (--primary-arm, default "hybrid") at --primary-seeds seeds per (scenario,
severity) cell. The ablation arms (rl_only, llm_only) get a cheaper grid: every scenario, but only
at --ablation-severities (default the two endpoints, 0.0 and 0.7) and fewer seeds.

Usage:
    python -m agents.run_ai_trials --dry-run                      # print the planned grid, no runs
    python -m agents.run_ai_trials --primary-seeds 5 --ablation-seeds 2 --limit 20   # small real batch
    python -m agents.run_ai_trials                                 # the full budgeted campaign

Resumable: a trial already present in the manifest with status "ok" and an existing log file on
disk is skipped. Re-running the same command after an interruption picks up where it left off.

Rate-limited: --rate-limit caps LLM calls/second across the whole worker pool (agents.llm_client's
provider-agnostic hook), because that's the one real cost here — see PHASE_PLAN.md's "Budget
discipline" constraint and the live Gemini free-tier exhaustion documented in Phase F.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from agents.environment import POOL_CAPACITY, POOL_GROWTH_RATE
from agents.hybrid_trial import build_trial_id, run_trial, write_trial
from common.config import (
    DROUGHT_ROUND,
    GATHER_DROUGHT,
    GATHER_NORMAL,
    NUM_PLAYERS,
    SCENARIOS,
    START_WATER,
    SURVIVAL_COST,
    TOTAL_ROUNDS,
)
from common.schema import validate_trial

LOG_DIR = os.path.join("data", "ai_logs")
MANIFEST_PATH = os.path.join(LOG_DIR, "manifest.json")

DEFAULT_SEVERITIES = (0.0, 0.3, 0.5, 0.7, 0.9)
DEFAULT_ABLATION_SEVERITIES = (0.0, 0.7)
DEFAULT_ABLATION_ARMS = ("rl_only", "llm_only")


class ThreadSafeRLModel:
    """Wraps a loaded SB3 PPO model so `.predict()` calls from multiple worker threads are
    serialized. SB3 isn't documented thread-safe, but predict() is fast (no network I/O) so this
    lock is never a real bottleneck — unlike locking around a whole `hybrid`-arm trial, which would
    also serialize that trial's LLM calls and defeat the worker pool's entire purpose."""

    def __init__(self, model):
        self._model = model
        self._lock = threading.Lock()

    def predict(self, *args, **kwargs):
        with self._lock:
            return self._model.predict(*args, **kwargs)


class RateLimiter:
    """Fixed-interval throttle shared across the worker pool. Simpler than a token bucket — this
    project doesn't need burst allowance, just a hard ceiling on calls/second so a free-tier quota
    (e.g. Gemini's, see PHASE_PLAN.md Phase F) can't be blown through by concurrent workers."""

    def __init__(self, calls_per_second: float):
        self._min_interval = 1.0 / calls_per_second if calls_per_second > 0 else 0.0
        self._lock = threading.Lock()
        self._next_allowed = 0.0

    def acquire(self) -> None:
        if self._min_interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            wait = self._next_allowed - now
            if wait > 0:
                time.sleep(wait)
                now = time.monotonic()
            self._next_allowed = now + self._min_interval


def build_grid(
    scenarios: list[str],
    severities: list[float],
    primary_arm: str,
    primary_provider: str | None,
    primary_model: str | None,
    primary_seeds: int,
    ablation_arms: list[str],
    ablation_severities: list[float],
    ablation_seeds: int,
    matched_seeds: set[int],
) -> list[dict]:
    """Returns a list of trial specs (plain dicts, not yet run). Kept separate from execution so
    --dry-run can print the plan without touching the network or the filesystem."""
    specs: list[dict] = []

    for scenario in scenarios:
        for severity in severities:
            for seed in range(primary_seeds):
                specs.append(
                    {
                        "scenario": scenario,
                        "severity": severity,
                        "arm": primary_arm,
                        "provider": primary_provider,
                        "model": primary_model,
                        "seed": seed,
                        "matched_seed": seed in matched_seeds,
                    }
                )

    for scenario in scenarios:
        for severity in ablation_severities:
            for arm in ablation_arms:
                provider = primary_provider if arm != "rl_only" else None
                model = primary_model if arm != "rl_only" else None
                for seed in range(ablation_seeds):
                    specs.append(
                        {
                            "scenario": scenario,
                            "severity": severity,
                            "arm": arm,
                            "provider": provider,
                            "model": model,
                            "seed": seed,
                            "matched_seed": seed in matched_seeds,
                        }
                    )

    return specs


def _git_sha() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (subprocess.CalledProcessError, OSError):
        return None


def _prompt_file_hash() -> str | None:
    """Sha256 of agents/llm_reasoning.py, as a cheap proxy for "which prompt version produced this
    trial" — PHASE_PLAN.md Phase G asks the manifest to record this so a reviewer asking which
    model/prompt version produced a result has an answer."""
    path = os.path.join(os.path.dirname(__file__), "llm_reasoning.py")
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def _env_config_snapshot() -> dict:
    return {
        "num_players": NUM_PLAYERS,
        "total_rounds": TOTAL_ROUNDS,
        "drought_round": DROUGHT_ROUND,
        "start_water": START_WATER,
        "survival_cost": SURVIVAL_COST,
        "gather_normal": GATHER_NORMAL,
        "gather_drought": GATHER_DROUGHT,
        "pool_capacity": POOL_CAPACITY,
        "pool_growth_rate": POOL_GROWTH_RATE,
    }


class Manifest:
    """data/ai_logs/manifest.json — one entry per attempted trial. Read-modify-write under a lock
    so concurrent workers can append safely; written atomically (temp file + os.replace) so a crash
    mid-write can't corrupt it. This is also what makes the campaign resumable: a trial with an "ok"
    entry and an existing log file on disk is skipped on the next run.
    """

    def __init__(self, path: str, run_metadata: dict):
        self.path = path
        self.run_metadata = run_metadata
        self._lock = threading.Lock()
        self.entries: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        for entry in data.get("trials", []):
            self.entries[entry["trial_id"]] = entry

    def is_done(self, trial_id: str, log_path: str) -> bool:
        entry = self.entries.get(trial_id)
        return bool(entry) and entry.get("status") == "ok" and os.path.exists(log_path)

    def record(self, entry: dict) -> None:
        with self._lock:
            self.entries[entry["trial_id"]] = entry
            self._flush()

    def _flush(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        payload = {
            "run_metadata": self.run_metadata,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "trials": list(self.entries.values()),
        }
        tmp_path = f"{self.path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp_path, self.path)


def run_campaign(
    specs: list[dict],
    manifest: Manifest,
    rl_model,
    workers: int,
    limit: int | None,
) -> dict:
    pending = [
        s
        for s in specs
        if not manifest.is_done(
            build_trial_id(s["scenario"], s["arm"], s["severity"], s["seed"]),
            os.path.join(LOG_DIR, build_trial_id(s["scenario"], s["arm"], s["severity"], s["seed"]) + ".jsonl"),
        )
    ]
    skipped = len(specs) - len(pending)
    if limit is not None:
        pending = pending[:limit]

    counts = {"ok": 0, "failed": 0, "skipped_already_done": skipped, "llm_calls": 0, "parse_failures": 0}

    def _run_one(spec: dict) -> None:
        trial_id = build_trial_id(spec["scenario"], spec["arm"], spec["severity"], spec["seed"])
        try:
            rows, stats = run_trial(
                spec["scenario"],
                spec["seed"],
                spec["arm"],
                provider=spec["provider"],
                model=spec["model"],
                severity=spec["severity"],
                rl_model=rl_model,
            )
            validate_trial(rows)
            for row in rows:
                row["meta"]["matched_seed"] = spec["matched_seed"]
            path = write_trial(rows)
            manifest.record(
                {
                    "trial_id": trial_id,
                    "status": "ok",
                    "path": path,
                    "scenario": spec["scenario"],
                    "severity": spec["severity"],
                    "arm": spec["arm"],
                    "provider": spec["provider"],
                    "model": stats.get("model"),
                    "seed": spec["seed"],
                    "matched_seed": spec["matched_seed"],
                    "decision_source_counts": stats["decision_source_counts"],
                    "llm_calls": stats["llm_calls"],
                    "parse_failures": stats["parse_failures"],
                    "rate_limited": stats["rate_limited"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            counts["ok"] += 1
            counts["llm_calls"] += stats["llm_calls"]
            counts["parse_failures"] += stats["parse_failures"]
            print(f"OK   {trial_id} ({len(rows)} rows, {stats['llm_calls']} LLM calls)")
        except Exception as exc:  # noqa: BLE001 - one bad trial must not kill the campaign
            manifest.record(
                {
                    "trial_id": trial_id,
                    "status": "failed",
                    "error": str(exc),
                    "scenario": spec["scenario"],
                    "severity": spec["severity"],
                    "arm": spec["arm"],
                    "seed": spec["seed"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            counts["failed"] += 1
            print(f"FAIL {trial_id}: {exc}", file=sys.stderr)

    if not pending:
        print(f"Nothing to do — {skipped} trial(s) already done.")
        return counts

    print(f"Running {len(pending)} trial(s) ({skipped} already done, skipped) with {workers} worker(s)...")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_run_one, spec) for spec in pending]
        for f in as_completed(futures):
            f.result()  # re-raise anything _run_one didn't already catch (shouldn't happen)

    return counts


def _parse_float_list(raw: str) -> list[float]:
    return [float(x) for x in raw.split(",") if x.strip()]


def _parse_str_list(raw: str) -> list[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]


def _parse_int_set(raw: str | None) -> set[int]:
    if not raw:
        return set()
    return {int(x) for x in raw.split(",") if x.strip()}


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenarios", default=",".join(SCENARIOS))
    parser.add_argument("--severities", default=",".join(str(s) for s in DEFAULT_SEVERITIES))
    parser.add_argument("--primary-arm", default="hybrid", choices=["rl_only", "llm_only", "hybrid"])
    parser.add_argument("--primary-provider", default="groq")
    parser.add_argument("--primary-model", default=None)
    parser.add_argument("--primary-seeds", type=int, default=100)
    parser.add_argument("--ablation-arms", default=",".join(DEFAULT_ABLATION_ARMS))
    parser.add_argument(
        "--ablation-severities", default=",".join(str(s) for s in DEFAULT_ABLATION_SEVERITIES)
    )
    parser.add_argument("--ablation-seeds", type=int, default=30)
    parser.add_argument("--matched-seeds", default=None, help="comma-separated seed ints agreed with Group 1")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--rate-limit", type=float, default=2.0, help="max LLM calls/second, 0 = unthrottled")
    parser.add_argument("--rl-model-path", default=None, help="defaults to agents.rl_policy.DEFAULT_MODEL_PATH")
    parser.add_argument("--limit", type=int, default=None, help="run at most this many pending trials")
    parser.add_argument("--dry-run", action="store_true", help="print the planned grid and exit; no runs")
    args = parser.parse_args()

    scenarios = _parse_str_list(args.scenarios)
    for s in scenarios:
        if s not in SCENARIOS:
            parser.error(f"unknown scenario {s!r}, must be one of {SCENARIOS}")

    specs = build_grid(
        scenarios=scenarios,
        severities=_parse_float_list(args.severities),
        primary_arm=args.primary_arm,
        primary_provider=args.primary_provider,
        primary_model=args.primary_model,
        primary_seeds=args.primary_seeds,
        ablation_arms=_parse_str_list(args.ablation_arms),
        ablation_severities=_parse_float_list(args.ablation_severities),
        ablation_seeds=args.ablation_seeds,
        matched_seeds=_parse_int_set(args.matched_seeds),
    )

    est_llm_calls = sum(
        NUM_PLAYERS * TOTAL_ROUNDS
        for s in specs
        if s["arm"] in ("llm_only", "hybrid")  # hybrid's real rate is lower; this is a ceiling
    )
    print(f"Planned grid: {len(specs)} trial(s); worst-case LLM calls if every round is social: {est_llm_calls}")
    by_arm: dict[str, int] = {}
    for s in specs:
        by_arm[s["arm"]] = by_arm.get(s["arm"], 0) + 1
    print(f"By arm: {by_arm}")

    if args.dry_run:
        return 0

    rl_model = None
    if any(s["arm"] in ("rl_only", "hybrid") for s in specs):
        from agents.hybrid_agent import load_rl_model

        kwargs = {"model_path": args.rl_model_path} if args.rl_model_path else {}
        rl_model = ThreadSafeRLModel(load_rl_model(**kwargs))

    if args.rate_limit > 0:
        from agents import llm_client

        limiter = RateLimiter(args.rate_limit)
        llm_client.set_rate_limiter(limiter.acquire)

    run_metadata = {
        "git_sha": _git_sha(),
        "prompt_file_sha256": _prompt_file_hash(),
        "env_config": _env_config_snapshot(),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "args": vars(args),
    }
    manifest = Manifest(MANIFEST_PATH, run_metadata)

    counts = run_campaign(specs, manifest, rl_model, workers=args.workers, limit=args.limit)

    print(
        f"Done. ok={counts['ok']} failed={counts['failed']} "
        f"skipped_already_done={counts['skipped_already_done']} "
        f"llm_calls={counts['llm_calls']} parse_failures={counts['parse_failures']}"
    )
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(_main())
