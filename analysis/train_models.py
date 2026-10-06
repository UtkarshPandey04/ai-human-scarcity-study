"""
train_models.py — Train Machine Learning Models on Collected Human & AI Data

Integrates with the SQLite database (data/scarcity_study.db) to train:
1. Model A (Distinguishability Classifier):
   - Novelty N3: Distinguishes Human vs. AI trials from behavioral feature vectors.
   - Outputs: Accuracy, ROC-AUC, feature importance ranking.
   - Checkpoint: models/distinguishability_classifier.json

2. Model B (Human Behavior Clone Policy):
   - Behavioral Cloning / Imitation Learning: Learns human decision-making policy
     p(action | state) directly from human session logs in the database.
   - Outputs: Cross-entropy loss, action prediction accuracy, action priors.
   - Checkpoint: models/human_clone_policy.json
   - Inference API: HumanClonePolicy class compatible with agents/coplayers.py

Usage:
    python -m analysis.train_models
    python -m analysis.train_models --model both
    python -m analysis.train_models --model classifier
    python -m analysis.train_models --model human_policy
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from typing import Any

import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.actions import Action, ActionType
from common.database import DEFAULT_DB_PATH, get_connection, init_db, sync_all_logs_to_db

MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

FEATURE_COLUMNS = [
    "gather_rate",
    "share_rate",
    "hoard_rate",
    "skip_rate",
    "communicate_rate",
    "total_shared",
    "deception_rate",
    "mean_latency_ms",
    "society_gini",
    "alliance_count",
]

ACTION_MAP = {
    "gather": 0,
    "share": 1,
    "hoard": 2,
    "skip": 3,
    "communicate": 4,
}
INV_ACTION_MAP = {v: k for k, v in ACTION_MAP.items()}


# =====================================================================
# 1. MODEL A: DISTINGUISHABILITY CLASSIFIER (HUMAN VS. AI)
# =====================================================================

def compute_auc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
    pos = y_scores[y_true == 1]
    neg = y_scores[y_true == 0]
    if len(pos) == 0 or len(neg) == 0:
        return 0.5
    pairs = sum(1 for p in pos for n in neg if p > n) + 0.5 * sum(1 for p in pos for n in neg if p == n)
    return pairs / (len(pos) * len(neg))


def train_distinguishability_classifier(db_path: str = DEFAULT_DB_PATH) -> dict[str, Any]:
    """Train regularized logistic regression model to distinguish human from AI trials."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cols = ", ".join(FEATURE_COLUMNS)
        cursor.execute(f"SELECT source, {cols} FROM trial_features WHERE source IN ('human', 'ai')")
        rows = cursor.fetchall()

    if len(rows) < 4:
        return {"error": f"Insufficient data: only {len(rows)} trials found in database."}

    X_raw = []
    y_raw = []
    for r in rows:
        X_raw.append([float(r[col] or 0.0) for col in FEATURE_COLUMNS])
        y_raw.append(1 if r["source"] == "human" else 0)

    X = np.array(X_raw, dtype=np.float64)
    y = np.array(y_raw, dtype=np.float64)
    n_samples, n_features = X.shape

    # Standardize
    mean = np.mean(X, axis=0)
    std = np.std(X, axis=0)
    std[std == 0] = 1.0
    X_norm = (X - mean) / std

    # Cross-validation
    k_folds = min(5, max(2, n_samples // 3))
    indices = np.arange(n_samples)
    np.random.seed(42)
    np.random.shuffle(indices)
    folds = np.array_split(indices, k_folds)

    cv_scores = np.zeros(n_samples)
    cv_preds = np.zeros(n_samples)

    for i in range(k_folds):
        val_idx = folds[i]
        train_idx = np.setdiff1d(indices, val_idx)

        X_tr, y_tr = X_norm[train_idx], y[train_idx]
        X_va = X_norm[val_idx]

        w = np.zeros(n_features)
        b = 0.0
        lr = 0.08
        l2 = 0.01

        for _ in range(400):
            lin = np.dot(X_tr, w) + b
            p = 1.0 / (1.0 + np.exp(-np.clip(lin, -15.0, 15.0)))
            dw = (1.0 / len(y_tr)) * np.dot(X_tr.T, (p - y_tr)) + l2 * w
            db = (1.0 / len(y_tr)) * np.sum(p - y_tr)
            w -= lr * dw
            b -= lr * db

        val_lin = np.dot(X_va, w) + b
        val_p = 1.0 / (1.0 + np.exp(-np.clip(val_lin, -15.0, 15.0)))
        cv_scores[val_idx] = val_p
        cv_preds[val_idx] = (val_p >= 0.5).astype(int)

    acc = float(np.mean(cv_preds == y))
    auc = float(compute_auc(y, cv_scores))

    # Train full model for saving
    w_full = np.zeros(n_features)
    b_full = 0.0
    for _ in range(500):
        lin = np.dot(X_norm, w_full) + b_full
        p = 1.0 / (1.0 + np.exp(-np.clip(lin, -15.0, 15.0)))
        dw = (1.0 / n_samples) * np.dot(X_norm.T, (p - y)) + 0.01 * w_full
        db = (1.0 / n_samples) * np.sum(p - y)
        w_full -= 0.08 * dw
        b_full -= 0.08 * db

    weights_dict = {col: float(w_full[idx]) for idx, col in enumerate(FEATURE_COLUMNS)}

    checkpoint = {
        "model_type": "distinguishability_logistic_regression",
        "feature_columns": FEATURE_COLUMNS,
        "feature_means": mean.tolist(),
        "feature_stds": std.tolist(),
        "weights": w_full.tolist(),
        "bias": float(b_full),
        "cv_accuracy": acc,
        "cv_auc": auc,
        "n_samples": n_samples,
        "n_human": int(np.sum(y == 1)),
        "n_ai": int(np.sum(y == 0)),
    }

    chk_path = os.path.join(MODELS_DIR, "distinguishability_classifier.json")
    with open(chk_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)

    return {
        "accuracy": acc,
        "auc": auc,
        "n_samples": n_samples,
        "n_human": int(np.sum(y == 1)),
        "n_ai": int(np.sum(y == 0)),
        "feature_weights": weights_dict,
        "checkpoint_path": chk_path,
    }


# =====================================================================
# 2. MODEL B: HUMAN BEHAVIOR CLONE POLICY (IMITATION LEARNING)
# =====================================================================

def softmax(x: np.ndarray) -> np.ndarray:
    e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e_x / np.sum(e_x, axis=-1, keepdims=True)


def train_human_behavior_policy(db_path: str = DEFAULT_DB_PATH) -> dict[str, Any]:
    """Train a multi-class policy model p(action | state) on human participant actions."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT a.round, a.action_type, a.resource_before, t.scenario, t.severity
            FROM actions a
            JOIN trials t ON a.trial_id = t.trial_id
            WHERE a.source = 'human' AND a.action_type IN ('gather', 'share', 'hoard', 'skip', 'communicate')
            """
        )
        rows = cursor.fetchall()

    if len(rows) < 10:
        return {"error": f"Need at least 10 human action steps to train policy, found {len(rows)}."}

    X_list = []
    y_list = []

    for r in rows:
        act_idx = ACTION_MAP.get(r["action_type"], 0)
        rnd_norm = float(r["round"]) / 10.0
        res_norm = float(r["resource_before"] or 5.0) / 10.0
        is_drought = 1.0 if (r["scenario"] == "drought" and r["round"] == 6) else 0.0
        sev = float(r["severity"] or (0.7 if r["scenario"] == "drought" else 0.0))

        feat = [1.0, rnd_norm, res_norm, is_drought, sev]
        X_list.append(feat)
        y_list.append(act_idx)

    X = np.array(X_list, dtype=np.float64)
    y = np.array(y_list, dtype=np.int64)
    n_samples, n_features = X.shape
    num_classes = len(ACTION_MAP)

    # One-hot encoding
    Y_onehot = np.zeros((n_samples, num_classes))
    Y_onehot[np.arange(n_samples), y] = 1.0

    # Train-test split (80/20)
    indices = np.arange(n_samples)
    np.random.seed(42)
    np.random.shuffle(indices)
    split = int(0.8 * n_samples)
    tr_idx, te_idx = indices[:split], indices[split:]

    X_tr, Y_tr = X[tr_idx], Y_onehot[tr_idx]
    X_te, y_te = X[te_idx], y[te_idx]

    # Initialize weights
    W = np.zeros((n_features, num_classes))
    lr = 0.05
    epochs = 600

    losses = []
    for epoch in range(epochs):
        logits = np.dot(X_tr, W)
        probs = softmax(logits)

        # Cross-entropy loss with L2
        loss = -np.mean(np.sum(Y_tr * np.log(np.clip(probs, 1e-10, 1.0)), axis=1)) + 0.005 * np.sum(W ** 2)
        losses.append(float(loss))

        grad = (1.0 / len(X_tr)) * np.dot(X_tr.T, (probs - Y_tr)) + 0.01 * W
        W -= lr * grad

    # Test accuracy
    te_logits = np.dot(X_te, W)
    te_preds = np.argmax(te_logits, axis=1)
    test_acc = float(np.mean(te_preds == y_te)) if len(y_te) > 0 else 1.0

    # Full fit
    W_full = np.zeros((n_features, num_classes))
    for _ in range(700):
        logits = np.dot(X, W_full)
        probs = softmax(logits)
        grad = (1.0 / n_samples) * np.dot(X.T, (probs - Y_onehot)) + 0.01 * W_full
        W_full -= lr * grad

    # Action priors
    action_counts = {k: int(np.sum(y == v)) for k, v in ACTION_MAP.items()}

    checkpoint = {
        "model_type": "human_behavior_clone_policy",
        "action_map": ACTION_MAP,
        "input_features": ["bias", "round_norm", "resource_norm", "is_drought", "severity"],
        "weights": W_full.tolist(),
        "n_samples": n_samples,
        "test_accuracy": test_acc,
        "action_counts": action_counts,
        "final_loss": losses[-1],
    }

    chk_path = os.path.join(MODELS_DIR, "human_clone_policy.json")
    with open(chk_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)

    return {
        "n_samples": n_samples,
        "test_accuracy": test_acc,
        "action_counts": action_counts,
        "checkpoint_path": chk_path,
        "weights": W_full,
    }


class HumanClonePolicy:
    """An autonomous policy driven by the trained human clone model."""

    def __init__(self, checkpoint_path: str | None = None):
        if checkpoint_path is None:
            checkpoint_path = os.path.join(MODELS_DIR, "human_clone_policy.json")

        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Model checkpoint not found at {checkpoint_path}. Run training first.")

        with open(checkpoint_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.weights = np.array(data["weights"])
        self.action_map = data["action_map"]
        self.inv_action_map = {v: k for k, v in self.action_map.items()}

    def act(self, obs: Any) -> Action:
        """Predict human-like action given an environment Observation."""
        rnd_norm = float(obs.round) / 10.0
        res_norm = float(obs.own_resource) / 10.0
        is_drought_val = 1.0 if obs.is_drought else 0.0
        sev = 0.7 if obs.is_drought else 0.0

        x = np.array([1.0, rnd_norm, res_norm, is_drought_val, sev])
        logits = np.dot(x, self.weights)
        probs = softmax(logits)

        # Sample or take argmax
        action_idx = int(np.argmax(probs))
        action_name = self.inv_action_map.get(action_idx, "gather")

        if action_name == "share":
            alive_others = [o for o in obs.others if o.alive]
            target = alive_others[0].player_id if alive_others else "A2"
            return Action(type=ActionType.SHARE, target=target, amount=1)
        elif action_name == "hoard":
            return Action(type=ActionType.HOARD)
        elif action_name == "communicate":
            return Action(type=ActionType.COMMUNICATE, target="all")
        elif action_name == "skip":
            return Action(type=ActionType.SKIP)
        else:
            return Action(type=ActionType.GATHER)


def train_all_models_summary() -> dict[str, Any]:
    """Train both models and return structured metrics dictionary for UI consumption."""
    sync_all_logs_to_db()
    res_cls = train_distinguishability_classifier()
    res_pol = train_human_behavior_policy()
    return {
        "classifier": res_cls,
        "policy": res_pol,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        choices=["both", "classifier", "human_policy"],
        default="both",
        help="Which model(s) to train",
    )
    args = parser.parse_args()

    print(f"Syncing logs to database ({DEFAULT_DB_PATH})...")
    sync_all_logs_to_db()

    if args.model in ("both", "classifier"):
        print("\n--- Training Model 1: AI vs. Human Distinguishability Classifier ---")
        res1 = train_distinguishability_classifier()
        if "error" in res1:
            print(f"Error: {res1['error']}")
        else:
            print(f"Trials Loaded       : {res1['n_samples']} (Human: {res1['n_human']}, AI: {res1['n_ai']})")
            print(f"CV Accuracy         : {res1['accuracy'] * 100:.1f}%")
            print(f"ROC-AUC Score       : {res1['auc']:.3f}")
            print(f"Saved Checkpoint    : {res1['checkpoint_path']}")
            print("\nTop Behavioral Signatures:")
            sorted_w = sorted(res1["feature_weights"].items(), key=lambda x: abs(x[1]), reverse=True)
            for feat, val in sorted_w[:5]:
                sign = "More Human (+)" if val > 0 else "More AI (-)"
                print(f"  {feat:<18}: {val:+.4f}  [{sign}]")

    if args.model in ("both", "human_policy"):
        print("\n--- Training Model 2: Human Behavior Clone Policy (Imitation Learning) ---")
        res2 = train_human_behavior_policy()
        if "error" in res2:
            print(f"Error: {res2['error']}")
        else:
            print(f"Human Action Steps  : {res2['n_samples']}")
            print(f"Test Set Accuracy   : {res2['test_accuracy'] * 100:.1f}%")
            print(f"Action Counts       : {res2['action_counts']}")
            print(f"Saved Checkpoint    : {res2['checkpoint_path']}")
            print("Policy ready for simulation as an autonomous agent! [OK]")


if __name__ == "__main__":
    main()
