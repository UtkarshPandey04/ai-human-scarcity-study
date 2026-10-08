"""Command runner for this repo. Run with `python tasks.py <task>`.

Using this instead of a Makefile: `make` isn't installed on every team member's machine (this repo
is developed on Windows), and a stdlib-only Python script needs nothing extra installed to run.
PHASE_PLAN.md refers to these as `make validate` etc. for brevity — read that as `python tasks.py
validate`.
"""

from __future__ import annotations

import os
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
    return subprocess.call(
        [sys.executable, "-m", "agents.smoke_random", "--scenario", "drought", "--seed", "0"]
    )


def pilot() -> int:
    """Phase B: generate the pilot AI logs needed for the MSE-1 EDA deliverable.

    ~20 trials per scenario across the random / cooperator / free_rider / tit_for_tat policies —
    enough spread in behaviour that action-distribution and survival-rate plots aren't degenerate.
    """
    scenarios = ["calm", "drought", "repeated_trust"]
    policies = ["random", "cooperator", "free_rider", "tit_for_tat"]
    trials_per_policy = 5  # 4 policies * 5 trials * 3 scenarios = 60 pilot trials

    exit_code = 0
    for scenario in scenarios:
        for policy in policies:
            exit_code |= subprocess.call(
                [
                    sys.executable,
                    "-m",
                    "agents.smoke_random",
                    "--scenario",
                    scenario,
                    "--policy",
                    policy,
                    "--seed",
                    "0",
                    "--trials",
                    str(trials_per_policy),
                ]
            )
    return exit_code


def train_rl() -> int:
    """Phase D: train the shared PPO reflex policy on `calm` and save it to models/.

    Not run as part of `validate` — real training takes minutes, not milliseconds. Extra CLI args
    are passed straight through, e.g. `python tasks.py train_rl --timesteps 50000`.
    """
    return subprocess.call([sys.executable, "-m", "agents.rl_policy", "train", *sys.argv[2:]])


def gate_d() -> int:
    """Phase D: evaluate the trained policy against a random baseline on held-out seeds — the
    actual Gate D check from agents/PHASE_PLAN.md. Requires `train_rl` to have been run first.
    """
    return subprocess.call([sys.executable, "-m", "agents.rl_policy", "evaluate", *sys.argv[2:]])


def trials() -> int:
    """Phase G: run the full AI trial campaign."""
    print("agents.run_ai_trials not implemented yet — see agents/PHASE_PLAN.md Phase G")
    return 1


def qa_logs() -> int:
    """Run Quality Assurance and game invariant validation on all trial logs."""
    return subprocess.call([sys.executable, "-m", "agents.qa_logs", *sys.argv[2:]])



def features() -> int:
    """Extract behavioral and societal feature vectors from trial logs."""
    return subprocess.call([sys.executable, "-m", "analysis.feature_extraction", *sys.argv[2:]])


def classify() -> int:
    """Train and evaluate the distinguishability classifier (Human vs. AI)."""
    return subprocess.call([sys.executable, "-m", "analysis.classifier", *sys.argv[2:]])


def stats() -> int:
    """Run non-parametric statistical hypothesis tests (Mann-Whitney U, Cliff's delta, dose-response)."""
    return subprocess.call([sys.executable, "-m", "analysis.stats_tests", *sys.argv[2:]])


def qualitative() -> int:
    """Extract and analyze qualitative transcript excerpts comparing human and AI behaviors."""
    return subprocess.call([sys.executable, "-m", "analysis.qualitative_analysis", *sys.argv[2:]])


def figures() -> int:
    """Generate camera-ready publication figures (Fig 1 - Fig 4)."""
    return subprocess.call([sys.executable, "-m", "analysis.generate_figures", *sys.argv[2:]])


def joint_analysis() -> int:
    """Run complete Phase 3 Joint Analysis pipeline end-to-end."""
    print("=== RUNNING PHASE 3 JOINT ANALYSIS SUITE ===")
    steps = [
        ("Step 1: Feature Extraction", ["-m", "analysis.feature_extraction"]),
        ("Step 2: Statistical Hypothesis Testing", ["-m", "analysis.stats_tests"]),
        ("Step 3: Distinguishability Classifier (Novelty N3)", ["-m", "analysis.classifier"]),
        ("Step 4: Qualitative Excerpts Extraction", ["-m", "analysis.qualitative_analysis"]),
        ("Step 5: Publication Figures Generation", ["-m", "analysis.generate_figures"]),
    ]
    for label, cmd in steps:
        print(f"\n>>> {label}...")
        code = subprocess.call([sys.executable, *cmd])
        if code != 0:
            print(f"FAILED at {label} with code {code}")
            return code
    print("\n[SUCCESS] Phase 3 Joint Analysis pipeline completed successfully!")
    return 0


def pilot_human() -> int:
    """Run pilot human-arm trials across matched seeds to test the focal substitution pipeline."""
    from common.actions import Action, ActionType, Message, MessageKind
    from common.config import MATCHED_SEEDS, NUM_PLAYERS
    from agents.environment import ScarcityEnv
    from agents.coplayers import get_policy
    from common.schema import validate_trial
    import json
    from datetime import datetime, timezone

    scenarios = ["calm", "drought", "repeated_trust"]
    seeds = [0, 1, 2, 3, 4]
    os.makedirs(os.path.join("data", "human_logs"), exist_ok=True)
    coplayer_ids = [f"A{i}" for i in range(2, NUM_PLAYERS + 1)]
    coplayer_types = ["cooperator", "free_rider", "tit_for_tat", "random"]

    print(f"Generating pilot human trials ({len(scenarios)} scenarios x {len(seeds)} seeds)...")
    for scenario in scenarios:
        for seed in seeds:
            focal_id = f"P{seed:04d}"
            player_ids = [focal_id] + coplayer_ids
            env = ScarcityEnv(scenario=scenario, seed=seed, player_ids=player_ids)
            coplayers = {
                pid: get_policy(coplayer_types[i], seed=seed + i + 1)
                for i, pid in enumerate(coplayer_ids)
            }
            obs = env.reset()
            trial_id = f"{scenario}_human_pilot_{seed:03d}"
            timestamp = datetime.now(timezone.utc).isoformat()
            trial_rows = []
            done = False

            while not done:
                r = env.round
                # Human proxy strategy: gathers, shares with A2 if surplus, hoards in drought, communicates
                if scenario == "drought" and r == 6:
                    human_action = Action(type=ActionType.HOARD)
                elif r % 3 == 0 and env.players[focal_id].resource > 4:
                    human_action = Action(
                        type=ActionType.SHARE,
                        target="A2",
                        amount=1,
                        message=Message(kind=MessageKind.PROMISE_SHARE, value=1, target="A2", surface="Sharing 1 water"),
                    )
                elif r == 2:
                    human_action = Action(
                        type=ActionType.COMMUNICATE,
                        target="all",
                        message=Message(kind=MessageKind.CLAIM_STOCK, value=int(env.players[focal_id].resource), target="all", surface="Reporting current water"),
                    )
                else:
                    human_action = Action(type=ActionType.GATHER)

                actions = {focal_id: human_action}
                for pid in coplayer_ids:
                    if env.players[pid].alive:
                        actions[pid] = coplayers[pid].act(obs[pid])

                obs, done, rows = env.step(actions)
                for row in rows:
                    row["trial_id"] = trial_id
                    row["timestamp"] = timestamp
                    if row["agent_id"] == focal_id:
                        row["source"] = "human"
                        row["meta"] = {
                            "arm": "human",
                            "seed": seed,
                            "severity": 0.7 if scenario == "drought" else 0.0,
                            "decision_latency_ms": 2450,
                            "claim": {"kind": "claim_stock", "value": int(row["resource_before"]), "target": "all"} if r == 2 else None,
                        }
                    else:
                        pol = coplayer_types[coplayer_ids.index(row["agent_id"])]
                        row["source"] = "ai"
                        row["meta"] = {"arm": "human", "seed": seed, "policy": pol}
                    trial_rows.append(row)

            validate_trial(trial_rows)
            out_path = os.path.join("data", "human_logs", f"{trial_id}.jsonl")
            with open(out_path, "w", encoding="utf-8") as f:
                for row in trial_rows:
                    f.write(json.dumps(row) + "\n")
            print(f"  OK {out_path} ({len(trial_rows)} rows)")

    print("Pilot human trial generation complete! [DONE]")
    return 0



def sync_db() -> int:
    """Sync all JSONL trial logs to SQLite database (data/scarcity_study.db)."""
    return subprocess.call([sys.executable, "-m", "common.database", *sys.argv[2:]])


def train() -> int:
    """Train ML models (Distinguishability Classifier + Human Behavioral Policy) from database."""
    return subprocess.call([sys.executable, "-m", "analysis.train_models", *sys.argv[2:]])


def export_data() -> int:
    """Export unified combined dataset (trials, demographics, features) to CSV."""
    from common.database import export_combined_dataset
    path = export_combined_dataset()
    print(f"Combined dataset exported to: {path}")
    return 0


def export_sft() -> int:
    """Export human trial actions as Supervised Fine-Tuning JSONL dataset (data/llm_sft_dataset.jsonl)."""
    from common.database import export_sft_dataset
    path = export_sft_dataset()
    print(f"LLM SFT dataset exported to: {path}")
    return 0


def test_exemplars() -> int:
    """Demonstrate dynamic human exemplar retrieval and prompt generation for LLMs."""
    from agents.environment import Observation, OtherPlayerView
    from common.actions import ActionType
    from agents.human_exemplars import query_human_exemplars, format_exemplars_prompt

    obs = Observation(
        player_id="A1",
        round=10,
        total_rounds=20,
        scenario="drought",
        is_drought=True,
        own_resource=3.0,
        own_alive=True,
        received_share_last_round=0.0,
        pool_stock=8.0,
        pool_capacity=30.0,
        others=(OtherPlayerView(player_id="A2", alive=True, last_action=ActionType.GATHER, last_action_target=None),),
    )
    exemplars = query_human_exemplars(obs, limit=2)
    prompt = format_exemplars_prompt(exemplars)
    print("=== DYNAMIC HUMAN IN-CONTEXT LEARNING PROMPT BLOCK ===")
    print(prompt)
    print("======================================================")
    print(f"Retrieved {len(exemplars)} human exemplars successfully [DONE]")
    return 0


TASKS = {
    "validate": validate,
    "validate_logs": validate_logs,
    "smoke": smoke,
    "pilot": pilot,
    "pilot_human": pilot_human,
    "train_rl": train_rl,
    "gate_d": gate_d,
    "trials": trials,
    "qa_logs": qa_logs,
    "features": features,
    "classify": classify,
    "stats": stats,
    "qualitative": qualitative,
    "figures": figures,
    "joint_analysis": joint_analysis,
    "sync_db": sync_db,
    "train": train,
    "export_data": export_data,
    "export_sft": export_sft,
    "test_exemplars": test_exemplars,
}




def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in TASKS:
        print(f"usage: python tasks.py <{'|'.join(TASKS)}>")
        return 1
    return TASKS[sys.argv[1]]()


if __name__ == "__main__":
    raise SystemExit(main())

