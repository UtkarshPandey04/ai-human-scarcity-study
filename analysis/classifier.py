"""
classifier.py — AI vs. Human Behavioral Distinguishability Classifier

Novelty N3 Implementation:
Tests whether human participants can be distinguished from AI agents based
purely on behavioral signatures under resource scarcity.

Methodology:
- Extracts rich behavioral feature vectors (gather_rate, share_rate, hoard_rate,
  hoarding_index, deception_rate, society_gini, alliance_count, total_shared, etc.)
- Evaluates both Logistic Regression (L2 regularized) and Random Forest via Stratified K-Fold CV.
- Reports: Accuracy, ROC-AUC, F1-Score, Precision, Recall.
- Extracts model interpretability:
  * Logistic Regression standardized feature coefficients (odds ratios)
  * Random Forest permutation feature importance
- Novelty N3: Distinguishability as a Function of Scarcity Severity:
  * Fits and evaluates classifiers across Calm (Severity 0.0) vs. Drought (Severity 0.7)
  * Verifies the core thesis: AI and human behavior diverge sharply under severe scarcity.
- Exports model checkpoint to models/distinguishability_classifier.json

Usage:
    python -m analysis.classifier
    python -m analysis.classifier --features data/trial_features.csv
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from analysis.feature_extraction import extract_all_features

MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

FEATURE_COLUMNS = [
    "share_rate",
    "hoard_rate",
    "hoarding_index",
    "gather_rate",
    "cooperation_rate",
    "deception_rate",
    "total_shared",
    "society_gini",
    "alliance_count",
    "society_survival_rate",
]


def evaluate_classifier_cv(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list[str],
    model_type: str = "logistic",
    n_splits: int = 5,
    random_state: int = 42,
) -> dict[str, Any]:
    """Perform Stratified K-Fold cross-validation and compute performance metrics."""
    n_samples = len(y)
    n_pos = int(np.sum(y == 1))
    n_neg = int(np.sum(y == 0))

    if n_pos < 2 or n_neg < 2:
        return {"error": f"Insufficient class balance (Pos: {n_pos}, Neg: {n_neg})"}

    k_folds = min(n_splits, min(n_pos, n_neg))
    if k_folds < 2:
        k_folds = 2

    skf = StratifiedKFold(n_splits=k_folds, shuffle=True, random_state=random_state)

    preds_all = np.zeros(n_samples)
    scores_all = np.zeros(n_samples)

    for train_idx, test_idx in skf.split(X, y):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        scaler = StandardScaler()
        X_train_norm = scaler.fit_transform(X_train)
        X_test_norm = scaler.transform(X_test)

        if model_type == "rf":
            model = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=random_state)
        else:
            model = LogisticRegression(C=1.0, max_iter=500, random_state=random_state)

        model.fit(X_train_norm, y_train)

        probs = model.predict_proba(X_test_norm)[:, 1]
        preds = model.predict(X_test_norm)

        scores_all[test_idx] = probs
        preds_all[test_idx] = preds

    acc = float(accuracy_score(y, preds_all))
    try:
        auc = float(roc_auc_score(y, scores_all))
    except Exception:
        auc = 0.5
    f1 = float(f1_score(y, preds_all, zero_division=0))
    prec = float(precision_score(y, preds_all, zero_division=0))
    rec = float(recall_score(y, preds_all, zero_division=0))
    cm = confusion_matrix(y, preds_all).tolist()

    # Train full model on all data for feature importance
    scaler_full = StandardScaler()
    X_full_norm = scaler_full.fit_transform(X)

    if model_type == "rf":
        full_model = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=random_state)
        full_model.fit(X_full_norm, y)
        perm = permutation_importance(full_model, X_full_norm, y, n_repeats=10, random_state=random_state)
        importances = dict(zip(feature_names, [float(v) for v in perm.importances_mean]))
    else:
        full_model = LogisticRegression(C=1.0, max_iter=500, random_state=random_state)
        full_model.fit(X_full_norm, y)
        importances = dict(zip(feature_names, [float(c) for c in full_model.coef_[0]]))

    return {
        "model_type": model_type,
        "n_samples": n_samples,
        "n_human": n_pos,
        "n_ai": n_neg,
        "cv_folds": k_folds,
        "accuracy": acc,
        "roc_auc": auc,
        "f1_score": f1,
        "precision": prec,
        "recall": rec,
        "confusion_matrix": cm,
        "feature_importance": importances,
    }


def evaluate_dose_response_distinguishability(
    df: pd.DataFrame,
    feature_names: list[str] = FEATURE_COLUMNS,
) -> dict[str, Any]:
    """Novelty N3: Evaluate distinguishability across Scarcity Severity levels."""
    severity_results = {}

    subsets = [
        ("All Scenarios (Overall)", df),
        ("Calm Condition (Severity = 0.0)", df[df["scenario"] == "calm"]),
        ("Drought Condition (Severity = 0.7)", df[df["scenario"] == "drought"]),
        ("Repeated-Trust Condition", df[df["scenario"] == "repeated_trust"]),
    ]

    for name, sub in subsets:
        clean_sub = sub[
            sub["source"].isin(["human", "ai"]) &
            (sub["arm"] != "llm_human_steered")
        ].copy()

        # Check features exist
        cols = [c for c in feature_names if c in clean_sub.columns]
        if len(cols) == 0:
            continue

        X_raw = clean_sub[cols].fillna(0.0).values
        y_raw = (clean_sub["source"] == "human").astype(int).values

        if len(np.unique(y_raw)) < 2:
            continue

        res_lr = evaluate_classifier_cv(X_raw, y_raw, cols, model_type="logistic")
        res_rf = evaluate_classifier_cv(X_raw, y_raw, cols, model_type="rf")

        severity_results[name] = {
            "logistic_regression": res_lr,
            "random_forest": res_rf,
        }

    return severity_results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--features",
        default="data/trial_features.csv",
        help="Path to trial features CSV",
    )
    parser.add_argument(
        "--output-checkpoint",
        default=os.path.join(MODELS_DIR, "distinguishability_classifier.json"),
        help="Path to save trained classifier checkpoint",
    )
    args = parser.parse_args()

    if os.path.exists(args.features):
        df = pd.read_csv(args.features)
    else:
        print(f"Features file {args.features} not found. Extracting features directly from logs...")
        features = extract_all_features(["data/human_logs", "data/ai_logs"])
        df = pd.DataFrame(features)
        df.to_csv(args.features, index=False)

    print(f"Loaded {len(df)} trials for Distinguishability Classifier.")

    # 1. Overall Evaluation
    valid_df = df[
        df["source"].isin(["human", "ai"]) &
        (df["arm"] != "llm_human_steered")
    ].copy()

    cols = [c for c in FEATURE_COLUMNS if c in valid_df.columns]
    X = valid_df[cols].fillna(0.0).values
    y = (valid_df["source"] == "human").astype(int).values

    print(f"Evaluating Overall Distinguishability (N={len(y)}, Human={np.sum(y==1)}, AI={np.sum(y==0)})...")
    res_lr = evaluate_classifier_cv(X, y, cols, model_type="logistic")
    res_rf = evaluate_classifier_cv(X, y, cols, model_type="rf")

    print("\n" + "=" * 80)
    print("DISTINGUISHABILITY CLASSIFIER RESULTS (OVERALL)")
    print("=" * 80)
    print(f"Logistic Regression: CV Accuracy = {res_lr['accuracy'] * 100:.1f}% | ROC-AUC = {res_lr['roc_auc']:.3f} | F1 = {res_lr['f1_score']:.3f}")
    print(f"Random Forest       : CV Accuracy = {res_rf['accuracy'] * 100:.1f}% | ROC-AUC = {res_rf['roc_auc']:.3f} | F1 = {res_rf['f1_score']:.3f}")

    print("\n--- Top Distinguishing Features (Logistic Regression Weights) ---")
    sorted_lr = sorted(res_lr["feature_importance"].items(), key=lambda x: abs(x[1]), reverse=True)
    for feat, w in sorted_lr:
        direction = "More Human (+)" if w > 0 else "More AI (-)"
        print(f"  {feat:<22}: {w:+.4f}  [{direction}]")

    print("\n--- Top Distinguishing Features (Random Forest Permutation Importance) ---")
    sorted_rf = sorted(res_rf["feature_importance"].items(), key=lambda x: x[1], reverse=True)
    for feat, imp in sorted_rf:
        print(f"  {feat:<22}: {imp:.4f}")

    # 2. Novelty N3: Distinguishability across Scarcity Conditions
    print("\n" + "=" * 80)
    print("NOVELTY N3: DISTINGUISHABILITY AS A FUNCTION OF SCARCITY SEVERITY")
    print("=" * 80)
    dose_results = evaluate_dose_response_distinguishability(df, cols)

    for name, res in dose_results.items():
        lr_auc = res["logistic_regression"].get("roc_auc", 0.0)
        lr_acc = res["logistic_regression"].get("accuracy", 0.0)
        rf_auc = res["random_forest"].get("roc_auc", 0.0)
        rf_acc = res["random_forest"].get("accuracy", 0.0)
        print(f"\n[{name}]")
        print(f"  - Logistic Regression: AUC = {lr_auc:.3f} | Accuracy = {lr_acc * 100:.1f}%")
        print(f"  - Random Forest      : AUC = {rf_auc:.3f} | Accuracy = {rf_acc * 100:.1f}%")

    # 3. Save model checkpoint
    checkpoint_payload = {
        "overall_logistic": res_lr,
        "overall_rf": res_rf,
        "scarcity_dose_response": dose_results,
        "feature_columns": cols,
    }
    with open(args.output_checkpoint, "w", encoding="utf-8") as f:
        json.dump(checkpoint_payload, f, indent=2)
    print(f"\nSaved classifier checkpoint to: {args.output_checkpoint}")


if __name__ == "__main__":
    main()
