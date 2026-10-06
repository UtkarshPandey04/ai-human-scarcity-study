"""
classifier.py — AI vs. Human Behavioral Distinguishability Classifier

Novelty N3 Implementation:
Tests whether human participants can be distinguished from AI agents based
purely on behavioral signatures under resource scarcity.

Methodology:
- Extracts behavioral feature vectors (gather_rate, share_rate, hoard_rate,
  deception_rate, society_gini, etc.)
- Trains a cross-validated Logistic Regression model (implemented via NumPy/PyTorch)
- Computes feature weights (interpretable behavioral signature)
- Evaluates Distinguishability (AUC / Accuracy) as a function of Scarcity Severity
  (verifying the hypothesis that AI and human diverge under severe scarcity).

Usage:
    python -m analysis.classifier
    python -m analysis.classifier --features data/trial_features.csv
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from typing import Any

import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from analysis.feature_extraction import extract_all_features

FEATURE_COLUMNS = [
    "gather_rate",
    "share_rate",
    "hoard_rate",
    "skip_rate",
    "communicate_rate",
    "deception_rate",
    "society_gini",
    "alliance_count",
]


class LogisticRegressionModel:
    """Self-contained NumPy-based logistic regression with L2 regularization."""

    def __init__(self, lr: float = 0.05, epochs: int = 500, l2: float = 0.01):
        self.lr = lr
        self.epochs = epochs
        self.l2 = l2
        self.weights = None
        self.bias = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray):
        n_samples, n_features = X.shape
        self.weights = np.zeros(n_features)
        self.bias = 0.0

        for _ in range(self.epochs):
            linear = np.dot(X, self.weights) + self.bias
            # numerically stable sigmoid
            preds = 1.0 / (1.0 + np.exp(-np.clip(linear, -15.0, 15.0)))

            dw = (1.0 / n_samples) * np.dot(X.T, (preds - y)) + self.l2 * self.weights
            db = (1.0 / n_samples) * np.sum(preds - y)

            self.weights -= self.lr * dw
            self.bias -= self.lr * db

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        linear = np.dot(X, self.weights) + self.bias
        return 1.0 / (1.0 + np.exp(-np.clip(linear, -15.0, 15.0)))

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X) >= threshold).astype(int)


def compute_auc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    """Compute Area Under the ROC Curve via Wilcoxon-Mann-Whitney statistic."""
    pos = y_scores[y_true == 1]
    neg = y_scores[y_true == 0]
    if len(pos) == 0 or len(neg) == 0:
        return 0.5
    pairs = 0
    ties = 0
    for p in pos:
        for n in neg:
            if p > n:
                pairs += 1
            elif p == n:
                ties += 1
    return (pairs + 0.5 * ties) / (len(pos) * len(neg))


def evaluate_distinguishability(
    features: list[dict[str, Any]], feature_names: list[str] = FEATURE_COLUMNS
) -> dict[str, Any]:
    """Train and evaluate the distinguishability model via K-fold cross-validation."""
    if not features:
        return {"error": "No features provided"}

    # Filter to human vs unsteered AI rows.
    # CRITICAL: llm_human_steered incorporates human trajectories via ICL, so it must NEVER
    # be pooled with llm_only or baseline AI in distinguishability classification or statistics.
    valid_rows = [
        f for f in features
        if f.get("source") in ("human", "ai") and f.get("arm") != "llm_human_steered"
    ]
    if len(valid_rows) < 4:
        return {"error": f"Too few samples for classification (N={len(valid_rows)})"}

    X_raw = []
    y_raw = []
    for r in valid_rows:
        row_vec = [float(r.get(c, 0.0)) for c in feature_names]
        X_raw.append(row_vec)
        y_raw.append(1 if r.get("source") == "human" else 0)

    X = np.array(X_raw, dtype=np.float64)
    y = np.array(y_raw, dtype=np.float64)

    # Standardize features
    mean = np.mean(X, axis=0)
    std = np.std(X, axis=0)
    std[std == 0] = 1.0
    X_norm = (X - mean) / std

    # Cross-validation
    n = len(y)
    k_folds = min(5, n // 2) if n >= 4 else 2
    indices = np.arange(n)
    np.random.seed(42)
    np.random.shuffle(indices)
    folds = np.array_split(indices, k_folds)

    all_preds = np.zeros(n)
    all_scores = np.zeros(n)

    for i in range(k_folds):
        val_idx = folds[i]
        train_idx = np.setdiff1d(indices, val_idx)

        X_train, y_train = X_norm[train_idx], y[train_idx]
        X_val, y_val = X_norm[val_idx], y[val_idx]

        model = LogisticRegressionModel(lr=0.1, epochs=300)
        model.fit(X_train, y_train)

        all_scores[val_idx] = model.predict_proba(X_val)
        all_preds[val_idx] = model.predict(X_val)

    acc = float(np.mean(all_preds == y))
    auc = float(compute_auc(y, all_scores))

    # Fit on all data for feature importance
    full_model = LogisticRegressionModel(lr=0.1, epochs=400)
    full_model.fit(X_norm, y)
    weights = dict(zip(feature_names, [float(w) for w in full_model.weights]))

    return {
        "n_samples": n,
        "n_human": int(np.sum(y == 1)),
        "n_ai": int(np.sum(y == 0)),
        "cv_accuracy": acc,
        "cv_auc": auc,
        "feature_weights": weights,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dirs",
        nargs="*",
        default=["data/human_logs", "data/ai_logs"],
        help="Directories containing logs",
    )
    args = parser.parse_args()

    print("Extracting features for classifier...")
    features = extract_all_features(args.dirs)
    print(f"Total trials loaded: {len(features)}")

    results = evaluate_distinguishability(features)
    if "error" in results:
        print(f"Distinguishability Classifier: {results['error']}")
        return

    print("\n======== DISTINGUISHABILITY RESULTS ========")
    print(f"Total Trials       : {results['n_samples']} (Human: {results['n_human']}, AI: {results['n_ai']})")
    print(f"Cross-Val Accuracy : {results['cv_accuracy'] * 100:.1f}%")
    print(f"ROC-AUC Score      : {results['cv_auc']:.3f}")
    print("\n--- Behavioral Weights (Human vs. AI Signatures) ---")
    sorted_weights = sorted(results["feature_weights"].items(), key=lambda x: abs(x[1]), reverse=True)
    for feat, w in sorted_weights:
        direction = "More Human (+)" if w > 0 else "More AI (-)"
        print(f"  {feat:<18}: {w:+.4f}  [{direction}]")


if __name__ == "__main__":
    main()
