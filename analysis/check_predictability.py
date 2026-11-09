"""
check_predictability.py — Comprehensive Model Predictability Audit

Audits and reports predictability metrics for both study models:
1. Model 1 (Distinguishability Classifier - Novelty N3):
   - Human vs. AI trial-level classification
   - 5-Fold Stratified CV Accuracy, ROC-AUC, Brier score, Precision, Recall, F1,
     Confusion Matrix, Majority Baseline Floor, and Empirical Gain.
2. Model 2 (Human Behavioral Policy - Imitation Learning):
   - Multi-class action prediction P(action | state) across human decision steps
   - Cross-Validation & Out-of-sample Test Accuracy, Cross-Entropy Loss,
     Baseline Majority Action Floor, and Gain over Baseline.
   - Per-action precision, recall, F1, support, and full confusion matrix.
   - Comparative benchmark against non-linear ensemble models (Random Forest, Gradient Boosting).

Usage:
    python -m analysis.check_predictability
    python -m analysis.check_predictability --json
    python -m analysis.check_predictability --db data/scarcity_study.db
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.database import DEFAULT_DB_PATH, get_connection, init_db
from analysis.train_models import ACTION_MAP, FEATURE_COLUMNS, INV_ACTION_MAP


def evaluate_model_1_classifier(db_path: str = DEFAULT_DB_PATH) -> dict[str, Any]:
    """Audit predictability of the Distinguishability Classifier (Human vs. AI)."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cols = ", ".join(FEATURE_COLUMNS)
        cursor.execute("PRAGMA table_info(trial_features)")
        col_names = [col_row["name"] for col_row in cursor.fetchall()]
        pilot_clause = " AND (pilot IS NULL OR pilot = 0)" if "pilot" in col_names else ""
        cursor.execute(
            f"SELECT source, {cols} FROM trial_features "
            f"WHERE source IN ('human', 'ai') AND (arm IS NULL OR arm != 'llm_human_steered'){pilot_clause}"
        )
        rows = cursor.fetchall()

    if len(rows) < 10:
        return {"error": f"Insufficient trial features in database (found {len(rows)})."}

    X_raw = []
    y_raw = []
    for r in rows:
        X_raw.append([float(r[c] or 0.0) for c in FEATURE_COLUMNS])
        y_raw.append(1 if r["source"] == "human" else 0)

    X = np.array(X_raw, dtype=np.float64)
    y = np.array(y_raw, dtype=np.int64)
    n_samples, n_features = X.shape
    n_human = int(np.sum(y == 1))
    n_ai = int(np.sum(y == 0))

    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, brier_score_loss, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
    from sklearn.model_selection import StratifiedKFold
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    X_norm = scaler.fit_transform(X)

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_pred_cv = np.zeros(n_samples, dtype=np.int64)
    y_prob_cv = np.zeros(n_samples, dtype=np.float64)

    for train_idx, val_idx in skf.split(X_norm, y):
        clf = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, random_state=42)
        clf.fit(X_norm[train_idx], y[train_idx])
        y_prob_cv[val_idx] = clf.predict_proba(X_norm[val_idx])[:, 1]
        y_pred_cv[val_idx] = clf.predict(X_norm[val_idx])

    cv_acc = float(accuracy_score(y, y_pred_cv))
    cv_auc = float(roc_auc_score(y, y_prob_cv))
    cv_brier = float(brier_score_loss(y, y_prob_cv))
    cv_prec = float(precision_score(y, y_pred_cv, zero_division=0))
    cv_rec = float(recall_score(y, y_pred_cv, zero_division=0))
    cv_f1 = float(f1_score(y, y_pred_cv, zero_division=0))

    cm = confusion_matrix(y, y_pred_cv)
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

    majority_floor = float(max(n_human, n_ai) / n_samples)
    gain_over_floor = float(cv_acc - majority_floor)

    # Train full model to inspect feature weights
    clf_full = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, random_state=42)
    clf_full.fit(X_norm, y)
    weights = {FEATURE_COLUMNS[i]: float(clf_full.coef_[0, i]) for i in range(n_features)}
    sorted_weights = dict(sorted(weights.items(), key=lambda item: abs(item[1]), reverse=True))

    return {
        "n_samples": n_samples,
        "n_human": n_human,
        "n_ai": n_ai,
        "cv_accuracy": cv_acc,
        "cv_auc": cv_auc,
        "brier_score": cv_brier,
        "precision": cv_prec,
        "recall": cv_rec,
        "f1_score": cv_f1,
        "majority_floor": majority_floor,
        "gain_over_floor": gain_over_floor,
        "confusion_matrix": {
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
            "matrix": cm.tolist(),
        },
        "feature_weights_ranked": sorted_weights,
    }


def evaluate_model_2_policy(db_path: str = DEFAULT_DB_PATH) -> dict[str, Any]:
    """Audit predictability of the Human Behavioral Policy (Imitation Learning)."""
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
        return {"error": f"Insufficient human action steps (found {len(rows)})."}

    POLICY_FEATURE_NAMES = [
        "bias", "round_norm", "resource_norm", "is_drought", "severity",
        "surplus", "critical", "comm_window", "drought_pressure"
    ]

    X_list = []
    y_list = []
    for r in rows:
        act_idx = ACTION_MAP.get(r["action_type"], 0)
        rnd = float(r["round"])
        rnd_norm = rnd / 10.0
        res = float(r["resource_before"] or 5.0)
        res_norm = res / 10.0
        is_drought = 1.0 if (r["scenario"] == "drought" and rnd == 6) else 0.0
        sev = float(r["severity"] or (0.7 if r["scenario"] == "drought" else 0.0))
        surplus = max(0.0, res - 3.0) / 10.0
        critical = 1.0 if res <= 2.0 else 0.0
        comm_window = 1.0 if int(rnd) in (2, 4, 5) else 0.0
        drought_pressure = is_drought * (1.0 - res_norm)

        feat = [1.0, rnd_norm, res_norm, is_drought, sev, surplus, critical, comm_window, drought_pressure]
        X_list.append(feat)
        y_list.append(act_idx)

    X = np.array(X_list, dtype=np.float64)
    y = np.array(y_list, dtype=np.int64)
    n_samples, n_features = X.shape

    action_counts = {k: int(np.sum(y == v)) for k, v in ACTION_MAP.items()}
    majority_act_floor = float(max(action_counts.values()) / n_samples)

    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, log_loss
    from sklearn.model_selection import StratifiedKFold, train_test_split

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

    # 1. Linear Multi-class Policy (Production Architecture)
    clf_linear = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, random_state=42)
    clf_linear.fit(X_tr, y_tr)
    y_te_prob = clf_linear.predict_proba(X_te)
    y_te_pred = clf_linear.predict(X_te)

    linear_acc = float(accuracy_score(y_te, y_te_pred))
    all_classes = list(range(len(ACTION_MAP)))
    # If some class is missing from y_tr, expand prob matrix to 5 columns
    if y_te_prob.shape[1] < len(ACTION_MAP):
        expanded_prob = np.zeros((len(y_te), len(ACTION_MAP)))
        for idx_cls, c in enumerate(clf_linear.classes_):
            expanded_prob[:, c] = y_te_prob[:, idx_cls]
        y_te_prob = expanded_prob
    linear_loss = float(log_loss(y_te, y_te_prob, labels=all_classes))
    linear_gain = float(linear_acc - majority_act_floor)

    # 5-Fold Stratified Cross-Validation on Linear Policy
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_preds = np.zeros(n_samples, dtype=np.int64)
    for tr_idx, va_idx in skf.split(X, y):
        lr_fold = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, random_state=42)
        lr_fold.fit(X[tr_idx], y[tr_idx])
        cv_preds[va_idx] = lr_fold.predict(X[va_idx])
    linear_cv_acc = float(accuracy_score(y, cv_preds))

    # Per-action metrics on test set
    per_action = {}
    for act_name, code in ACTION_MAP.items():
        mask_true = (y_te == code)
        sup = int(np.sum(mask_true))
        if sup > 0:
            rec = float(np.mean(y_te_pred[mask_true] == code))
            mask_pred = (y_te_pred == code)
            prec = float(np.mean(y_te[mask_pred] == code)) if np.sum(mask_pred) > 0 else 0.0
            f1 = float(2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
            per_action[act_name] = {
                "support": sup,
                "precision": prec,
                "recall": rec,
                "f1": f1,
            }
        else:
            per_action[act_name] = {"support": 0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

    cm_5x5 = confusion_matrix(y_te, y_te_pred, labels=list(range(len(ACTION_MAP)))).tolist()

    # 2. Non-linear Benchmark Baselines (Forest & Boosting)
    rf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    rf.fit(X_tr, y_tr)
    rf_acc = float(accuracy_score(y_te, rf.predict(X_te)))

    gb = GradientBoostingClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
    gb.fit(X_tr, y_tr)
    gb_acc = float(accuracy_score(y_te, gb.predict(X_te)))

    return {
        "n_samples": n_samples,
        "majority_floor": majority_act_floor,
        "action_counts": action_counts,
        "linear_policy": {
            "test_accuracy": linear_acc,
            "cv_accuracy": linear_cv_acc,
            "gain_over_floor": linear_gain,
            "log_loss": linear_loss,
            "per_action": per_action,
            "confusion_matrix": cm_5x5,
        },
        "non_linear_benchmarks": {
            "random_forest_accuracy": rf_acc,
            "gradient_boosting_accuracy": gb_acc,
        },
    }


def run_audit(db_path: str = DEFAULT_DB_PATH, verbose: bool = True) -> dict[str, Any]:
    """Execute complete predictability audit across both models."""
    if verbose:
        print("=" * 72)
        print("          AI-HUMAN SCARCITY STUDY: MODEL PREDICTABILITY AUDIT           ")
        print("=" * 72)
        print(f"Database: {db_path}\n")

    m1 = evaluate_model_1_classifier(db_path)
    m2 = evaluate_model_2_policy(db_path)

    results = {
        "model_1_classifier": m1,
        "model_2_policy": m2,
    }

    if verbose:
        print("=" * 72)
        print(" MODEL 1: DISTINGUISHABILITY CLASSIFIER (NOVELTY N3)")
        print(" Distinguishes Human vs. AI trials from behavioral feature vectors")
        print("=" * 72)
        if "error" in m1:
            print(f"Error: {m1['error']}")
        else:
            print(f"• Total Banked Trials: {m1['n_samples']} ({m1['n_human']} Human, {m1['n_ai']} AI)")
            print(f"• 5-Fold Stratified CV Accuracy: {m1['cv_accuracy'] * 100:.2f}%")
            print(f"• Majority Class Baseline Floor: {m1['majority_floor'] * 100:.2f}%")
            print(f"• Empirical Gain Over Floor:     +{m1['gain_over_floor'] * 100:.2f}%")
            print(f"• Area Under ROC Curve (AUC):    {m1['cv_auc']:.4f}")
            print(f"• Brier Calibration Score (MSE): {m1['brier_score']:.4f}")
            print(f"• Precision (Human):             {m1['precision'] * 100:.2f}%")
            print(f"• Recall (Human):                {m1['recall'] * 100:.2f}%")
            print(f"• F1 Score:                      {m1['f1_score'] * 100:.2f}%")
            print(f"• Confusion Matrix:")
            cm = m1["confusion_matrix"]
            print(f"    - True Negatives (AI correctly flagged as AI):       {cm['tn']}")
            print(f"    - False Positives (AI falsely flagged as Human):     {cm['fp']}")
            print(f"    - False Negatives (Human falsely flagged as AI):     {cm['fn']}")
            print(f"    - True Positives (Human correctly flagged as Human): {cm['tp']}")
            print("• Top Distinguishing Behavioral Signatures (Learned Weights):")
            for feat, weight in list(m1["feature_weights_ranked"].items())[:5]:
                sign = "+" if weight > 0 else "-"
                print(f"    {sign} {feat:<18} : {weight:+.4f}")

        print("\n" + "=" * 72)
        print(" MODEL 2: HUMAN BEHAVIORAL POLICY (IMITATION LEARNING)")
        print(" Multi-class state-to-action predictor P(action | state)")
        print("=" * 72)
        if "error" in m2:
            print(f"Error: {m2['error']}")
        else:
            lp = m2["linear_policy"]
            nl = m2["non_linear_benchmarks"]
            print(f"• Total Human Decision Steps: {m2['n_samples']}")
            print(f"• Majority Action Baseline (Always Gather): {m2['majority_floor'] * 100:.2f}%")
            print(f"• Multi-class Policy Test Accuracy:         {lp['test_accuracy'] * 100:.2f}%")
            print(f"• 5-Fold Stratified CV Accuracy:            {lp['cv_accuracy'] * 100:.2f}%")
            print(f"• Empirical Gain Over Baseline Floor:       +{lp['gain_over_floor'] * 100:.2f}%")
            print(f"• Cross-Entropy Log Loss:                   {lp['log_loss']:.4f}")
            print("\n• Per-Action Predictability Breakdown (Held-out Test Steps):")
            print(f"  {'Action':<14} | {'Support':<8} | {'Precision':<10} | {'Recall':<10} | {'F1':<8}")
            print("  " + "-" * 58)
            for act_name, metrics in lp["per_action"].items():
                print(
                    f"  {act_name:<14} | {metrics['support']:<8} | "
                    f"{metrics['precision'] * 100:>8.1f}% | {metrics['recall'] * 100:>8.1f}% | "
                    f"{metrics['f1'] * 100:>6.1f}%"
                )

            print("\n• Architecture Predictability Comparison:")
            print(f"  - Linear Softmax Policy (Inference Engine):  {lp['test_accuracy'] * 100:.2f}%")
            print(f"  - Random Forest Non-linear Benchmark:       {nl['random_forest_accuracy'] * 100:.2f}%")
            print(f"  - Gradient Boosting Non-linear Benchmark:   {nl['gradient_boosting_accuracy'] * 100:.2f}%")

        print("=" * 72)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Check model predictability metrics.")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to SQLite database")
    parser.add_argument("--json", action="store_true", help="Output raw JSON results")
    args = parser.parse_args()

    results = run_audit(db_path=args.db, verbose=not args.json)
    if args.json:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
