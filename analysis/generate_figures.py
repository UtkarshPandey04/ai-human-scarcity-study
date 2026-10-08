"""
generate_figures.py — Generate Publication-Quality Figures for Academic Paper

Creates vector/high-res figures saved in paper/figures/:
1. Fig 1 (fig1_behavioral_comparison.png): AI vs. Human key metrics across Calm, Drought, Trust.
2. Fig 2 (fig2_dose_response.png): Novelty N1 Scarcity Dose-Response Elasticity curves.
3. Fig 3 (fig3_distinguishability_roc.png): Novelty N3 ROC-AUC Distinguishability across scenarios.
4. Fig 4 (fig4_feature_importance.png): Random Forest Permutation Importance & Logistic Weights.

Usage:
    python -m analysis.generate_figures
"""

from __future__ import annotations

import json
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

FIGURES_DIR = os.path.join(PROJECT_ROOT, "paper", "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

# Styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
})


def plot_fig1_behavioral_comparison(df: pd.DataFrame):
    """Figure 1: Side-by-side metric comparison across Calm, Drought, and Trust."""
    metrics = [
        ("share_rate", "Sharing Rate", [0, 0.45]),
        ("hoard_rate", "Hoarding Rate", [0, 0.35]),
        ("society_gini", "Society Gini Index", [0, 0.6]),
        ("cooperation_rate", "Cooperation Rate", [0, 0.5]),
    ]
    scenarios = ["calm", "drought", "repeated_trust"]
    scenario_labels = ["Calm Baseline", "Drought Scarcity", "Repeated-Trust"]

    fig, axes = plt.subplots(1, 4, figsize=(16, 4.2), sharey=False)

    for ax, (m_col, m_title, ylim) in zip(axes, metrics):
        x = np.arange(len(scenarios))
        width = 0.35

        h_means = []
        h_stds = []
        a_means = []
        a_stds = []

        for sc in scenarios:
            sub = df[df["scenario"] == sc]
            h_sub = sub[sub["source"] == "human"][m_col].dropna()
            a_sub = sub[(sub["source"] == "ai") & (sub["arm"] != "llm_human_steered")][m_col].dropna()

            h_means.append(h_sub.mean() if len(h_sub) > 0 else 0)
            h_stds.append(h_sub.std() if len(h_sub) > 1 else 0)
            a_means.append(a_sub.mean() if len(a_sub) > 0 else 0)
            a_stds.append(a_sub.std() if len(a_sub) > 1 else 0)

        ax.bar(x - width/2, h_means, width, yerr=h_stds, label="Human", color="#2b5c8f", capsize=4, alpha=0.9)
        ax.bar(x + width/2, a_means, width, yerr=a_stds, label="AI Agent", color="#d95f02", capsize=4, alpha=0.9)

        ax.set_title(m_title, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(scenario_labels, rotation=15)
        ax.set_ylim(ylim)
        ax.grid(axis="y", linestyle="--", alpha=0.7)
        if ax == axes[0]:
            ax.legend(frameon=True)

    plt.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "fig1_behavioral_comparison.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Generated Figure 1: {out_path}")


def plot_fig2_dose_response(stats_json_path: str):
    """Figure 2: Scarcity Dose-Response Elasticity curves (Novelty N1)."""
    if not os.path.exists(stats_json_path):
        return

    with open(stats_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    dose_summary = data.get("dose_response", {}).get("severity_summary", [])
    if not dose_summary:
        return

    sevs = [r["severity"] for r in dose_summary]
    h_share = [r["human_share_rate"] for r in dose_summary]
    a_share = [r["ai_share_rate"] for r in dose_summary]
    h_hoard = [r["human_hoard_rate"] for r in dose_summary]
    a_hoard = [r["ai_hoard_rate"] for r in dose_summary]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    # Panel A: Sharing Rate
    ax1.plot(sevs, h_share, marker="o", linewidth=2.5, color="#2b5c8f", label="Human Participants")
    ax1.plot(sevs, a_share, marker="s", linewidth=2.5, linestyle="--", color="#d95f02", label="AI Agents")
    ax1.set_title("(A) Sharing Rate vs. Scarcity Severity", fontweight="bold")
    ax1.set_xlabel("Scarcity Severity parameter (g reduction)")
    ax1.set_ylabel("Sharing Rate (actions / round)")
    ax1.set_ylim([0.0, 0.4])
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend()

    # Panel B: Hoarding Rate
    ax2.plot(sevs, h_hoard, marker="o", linewidth=2.5, color="#2b5c8f", label="Human Participants")
    ax2.plot(sevs, a_hoard, marker="s", linewidth=2.5, linestyle="--", color="#d95f02", label="AI Agents")
    ax2.set_title("(B) Hoarding Rate vs. Scarcity Severity", fontweight="bold")
    ax2.set_xlabel("Scarcity Severity parameter (g reduction)")
    ax2.set_ylabel("Hoarding Rate (actions / round)")
    ax2.set_ylim([0.0, 0.3])
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend()

    plt.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "fig2_dose_response.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Generated Figure 2: {out_path}")


def plot_fig3_distinguishability(classifier_json_path: str):
    """Figure 3: Distinguishability ROC-AUC across Scarcity Levels (Novelty N3)."""
    if not os.path.exists(classifier_json_path):
        return

    with open(classifier_json_path, "r", encoding="utf-8") as f:
        chk = json.load(f)

    scenarios_data = chk.get("scarcity_dose_response", {})
    if not scenarios_data:
        return

    names = []
    lr_aucs = []
    rf_aucs = []

    label_map = {
        "All Scenarios (Overall)": "Pooled (All)",
        "Calm Condition (Severity = 0.0)": "Calm (Sev 0.0)",
        "Drought Condition (Severity = 0.7)": "Drought (Sev 0.7)",
        "Repeated-Trust Condition": "Repeated-Trust",
    }

    for orig_name, res in scenarios_data.items():
        names.append(label_map.get(orig_name, orig_name))
        lr_aucs.append(res["logistic_regression"].get("roc_auc", 0.5))
        rf_aucs.append(res["random_forest"].get("roc_auc", 0.5))

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(names))
    width = 0.35

    ax.bar(x - width/2, lr_aucs, width, label="Logistic Regression", color="#1f77b4", alpha=0.9)
    ax.bar(x + width/2, rf_aucs, width, label="Random Forest", color="#2ca02c", alpha=0.9)

    ax.axhline(0.5, color="gray", linestyle=":", label="Chance (AUC = 0.50)")
    ax.set_title("AI-Human Behavioral Distinguishability (ROC-AUC) Across Scenarios", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylabel("ROC-AUC Score")
    ax.set_ylim([0.4, 1.05])
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    ax.legend(loc="lower right")

    plt.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "fig3_distinguishability_roc.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Generated Figure 3: {out_path}")


def plot_fig4_feature_importance(classifier_json_path: str):
    """Figure 4: Feature Importance driving AI vs. Human Behavioral Divergence."""
    if not os.path.exists(classifier_json_path):
        return

    with open(classifier_json_path, "r", encoding="utf-8") as f:
        chk = json.load(f)

    rf_imp = chk.get("overall_rf", {}).get("feature_importance", {})
    lr_weights = chk.get("overall_logistic", {}).get("feature_importance", {})

    if not rf_imp:
        return

    # Sort by RF importance
    sorted_items = sorted(rf_imp.items(), key=lambda x: x[1], reverse=True)[:8]
    feats = [item[0].replace("_", " ").title() for item in sorted_items][::-1]
    rf_vals = [item[1] for item in sorted_items][::-1]
    lr_vals = [lr_weights.get(item[0], 0.0) for item in sorted_items][::-1]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Panel A: RF Permutation Importance
    ax1.barh(feats, rf_vals, color="#2ca02c", alpha=0.85)
    ax1.set_title("(A) Random Forest Permutation Importance", fontweight="bold")
    ax1.set_xlabel("Mean Decrease in Accuracy")
    ax1.grid(axis="x", linestyle="--", alpha=0.7)

    # Panel B: Logistic Regression Directional Weights
    colors = ["#2b5c8f" if w > 0 else "#d95f02" for w in lr_vals]
    ax2.barh(feats, lr_vals, color=colors, alpha=0.85)
    ax2.set_title("(B) Logistic Regression Standardized Weights", fontweight="bold")
    ax2.set_xlabel("Weight (Positive = More Human, Negative = More AI)")
    ax2.axvline(0.0, color="black", linestyle="-", linewidth=0.8)
    ax2.grid(axis="x", linestyle="--", alpha=0.7)

    plt.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "fig4_feature_importance.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Generated Figure 4: {out_path}")


def main():
    features_csv = os.path.join(PROJECT_ROOT, "data", "trial_features.csv")
    stats_json = os.path.join(PROJECT_ROOT, "data", "stats_summary.json")
    classifier_json = os.path.join(PROJECT_ROOT, "models", "distinguishability_classifier.json")

    if not os.path.exists(features_csv):
        print(f"Features file {features_csv} not found.")
        return

    df = pd.read_csv(features_csv)
    print("Generating academic publication figures...")

    plot_fig1_behavioral_comparison(df)
    plot_fig2_dose_response(stats_json)
    plot_fig3_distinguishability(classifier_json)
    plot_fig4_feature_importance(classifier_json)

    print(f"\nAll publication figures successfully created in: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
