"""
feature_extraction.py — Extract behavioral and societal feature vectors from trial logs

Parses JSONL trial logs (human and AI) into structured tabular data for:
- Statistical comparison (Mann-Whitney U tests, effect sizes)
- Distinguishability classification (human vs. AI)
- Novelty dose-response curves (cooperation/distinguishability vs. scarcity severity)

Metrics extracted per trial:
1. Focal Player Actions:
   - gather_rate, share_rate, hoard_rate, skip_rate, communicate_rate
   - total_shared_units, total_received_units
2. Focal Player Survival:
   - survived (0/1), rounds_survived, final_resource
3. Slotted Deception (Arithmetic Truthfulness):
   - stock_claims_count, deceptive_claims_count, deception_rate
4. Decision Latency:
   - mean_latency_ms, median_latency_ms
5. Society / Commons Metrics:
   - society_survival_rate (fraction of 5 players alive)
   - final_pool_stock
   - society_gini (Gini coefficient across 5 agents)
   - alliance_count (number of reciprocal sharing pairs)

Usage:
    python -m analysis.feature_extraction --output data/trial_features.csv
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

from common.config import NUM_PLAYERS
from human_interface.session_analysis import calculate_gini


def extract_trial_features(rows: list[dict[str, Any]], focal_id: str | None = None) -> dict[str, Any] | None:
    """Extract one feature row from a trial's action records."""
    if not rows:
        return None

    trial_id = rows[0].get("trial_id", "unknown")
    scenario = rows[0].get("scenario", "drought")
    source = rows[0].get("source", "ai")
    meta = rows[0].get("meta") or {}
    arm = meta.get("arm", "human" if source == "human" else "ai")
    seed = meta.get("seed", 0)
    severity = meta.get("severity", 0.7 if scenario == "drought" else 0.0)

    # Determine focal agent
    if focal_id is None:
        # If human trial, focal is the human row
        human_agents = [r["agent_id"] for r in rows if r.get("source") == "human"]
        if human_agents:
            focal_id = human_agents[0]
        else:
            # For AI trial, by convention A1 is focal
            focal_id = "A1"

    # Separate focal rows and all rows
    focal_rows = [r for r in rows if r["agent_id"] == focal_id]
    if not focal_rows:
        return None

    total_rounds = len(focal_rows)
    rounds_survived = sum(1 for r in focal_rows if r.get("alive", False))
    final_alive = focal_rows[-1].get("alive", False)
    final_resource = focal_rows[-1].get("resource_after", 0.0)

    # Action counts
    action_counts = {"gather": 0, "share": 0, "hoard": 0, "skip": 0, "communicate": 0}
    latencies = []
    total_shared = 0.0

    # Deception detection
    stock_claims = 0
    deceptive_claims = 0

    # Sharing network for alliance detection: (sender, target) -> count
    sharing_pairs: dict[tuple[str, str], int] = {}

    for r in rows:
        act = r.get("action_type")
        aid = r.get("agent_id")
        tgt = r.get("target_agent")
        if act == "share" and aid and tgt:
            sharing_pairs[(aid, tgt)] = sharing_pairs.get((aid, tgt), 0) + 1

    for r in focal_rows:
        act = r.get("action_type", "skip")
        if act in action_counts:
            action_counts[act] += 1

        if act == "share":
            # Share amount is resource_before - resource_after - cost
            shared_amt = max(1.0, (r.get("resource_before", 0) - r.get("resource_after", 0)))
            total_shared += shared_amt

        # Latency
        r_meta = r.get("meta") or {}
        lat = r_meta.get("decision_latency_ms")
        if lat is not None and lat >= 0:
            latencies.append(float(lat))

        # Check claim deception
        claim = r_meta.get("claim") or {}
        kind = claim.get("kind")
        val = claim.get("value")
        if kind == "claim_stock" and val is not None:
            stock_claims += 1
            res_before = r.get("resource_before")
            if res_before is not None and int(val) != int(res_before):
                deceptive_claims += 1

    deception_rate = (deceptive_claims / stock_claims) if stock_claims > 0 else 0.0
    mean_latency = (sum(latencies) / len(latencies)) if latencies else 0.0

    # Society-level metrics at final round
    final_round_num = max(r["round"] for r in rows)
    final_round_rows = [r for r in rows if r["round"] == final_round_num]
    final_resources = [r.get("resource_after", 0.0) for r in final_round_rows]
    society_survivors = sum(1 for r in final_round_rows if r.get("alive", False))
    society_survival_rate = society_survivors / max(1, len(final_round_rows))

    gini = calculate_gini(final_resources)

    # Alliances: mutual sharing between agent pairs
    alliances = 0
    checked_pairs = set()
    for (a, b) in sharing_pairs:
        if (b, a) in sharing_pairs and (b, a) not in checked_pairs and a != b:
            alliances += 1
            checked_pairs.add((a, b))

    return {
        "trial_id": trial_id,
        "source": source,
        "arm": arm,
        "scenario": scenario,
        "seed": seed,
        "severity": severity if severity is not None else 0.0,
        "focal_id": focal_id,
        "rounds_survived": rounds_survived,
        "survived": 1 if final_alive else 0,
        "final_resource": final_resource,
        "gather_rate": action_counts["gather"] / max(1, total_rounds),
        "share_rate": action_counts["share"] / max(1, total_rounds),
        "hoard_rate": action_counts["hoard"] / max(1, total_rounds),
        "skip_rate": action_counts["skip"] / max(1, total_rounds),
        "communicate_rate": action_counts["communicate"] / max(1, total_rounds),
        "total_shared": total_shared,
        "stock_claims_count": stock_claims,
        "deceptive_claims_count": deceptive_claims,
        "deception_rate": deception_rate,
        "mean_latency_ms": mean_latency,
        "society_survival_rate": society_survival_rate,
        "society_gini": gini,
        "alliance_count": alliances,
    }


def extract_all_features(directories: list[str]) -> list[dict[str, Any]]:
    """Scan directories for .jsonl trial files and extract all feature rows."""
    all_features = []
    for d in directories:
        if not os.path.exists(d):
            continue
        for fpath in glob.glob(os.path.join(d, "*.jsonl")):
            if "turing_judgments" in fpath or "manifest" in fpath:
                continue
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    rows = [json.loads(line) for line in f if line.strip()]
                feat = extract_trial_features(rows)
                if feat:
                    all_features.append(feat)
            except Exception as e:
                print(f"Warning: could not extract features from {fpath}: {e}")

    return all_features


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dirs",
        nargs="*",
        default=["data/human_logs", "data/ai_logs"],
        help="Directories containing JSONL logs",
    )
    parser.add_argument(
        "--output",
        default="data/trial_features.csv",
        help="Path to save extracted CSV features",
    )
    args = parser.parse_args()

    features = extract_all_features(args.dirs)
    print(f"Extracted {len(features)} trial feature vectors.")

    if not features:
        print("No feature vectors extracted.")
        return 0

    # Write CSV
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    keys = list(features[0].keys())
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(",".join(keys) + "\n")
        for row in features:
            f.write(",".join(str(row.get(k, "")) for k in keys) + "\n")

    print(f"Features saved successfully to: {args.output}")

    # Summary table
    print("\n--- Summary by Source / Arm ---")
    arms: dict[str, list[dict[str, Any]]] = {}
    for feat in features:
        key = f"{feat['source']}_{feat['scenario']}"
        arms.setdefault(key, []).append(feat)

    for k, rows in sorted(arms.items()):
        n = len(rows)
        surv = sum(r["survived"] for r in rows) / n
        share = sum(r["share_rate"] for r in rows) / n
        hoard = sum(r["hoard_rate"] for r in rows) / n
        decept = sum(r["deception_rate"] for r in rows) / n
        gini = sum(r["society_gini"] for r in rows) / n
        print(f"[{k}] (N={n:2d}): Survival={surv:.2f} | ShareRate={share:.2f} | HoardRate={hoard:.2f} | DeceptionRate={decept:.2f} | Gini={gini:.2f}")


if __name__ == "__main__":
    main()
