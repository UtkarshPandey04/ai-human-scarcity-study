"""
test_analysis.py — Unit Tests for Phase 3 Joint Analysis Suite

Tests:
1. Feature extraction correctness (action rates, hoarding index, deception rate)
2. Statistical testing calculations (Cliff's Delta, Mann-Whitney U wrapper, effect size interpretation)
3. Distinguishability classification cross-validation
4. Qualitative excerpt extraction
"""

import unittest
import numpy as np

from analysis.feature_extraction import extract_trial_features
from analysis.stats_tests import cliffs_delta, interpret_effect_size, run_two_group_comparison
from analysis.classifier import evaluate_classifier_cv


class TestAnalysisSuite(unittest.TestCase):

    def test_cliffs_delta_perfect_separation(self):
        x = np.array([10.0, 11.0, 12.0])
        y = np.array([1.0, 2.0, 3.0])
        delta = cliffs_delta(x, y)
        self.assertEqual(delta, 1.0)
        self.assertEqual(interpret_effect_size(delta), "Large")

    def test_cliffs_delta_inverted_separation(self):
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([10.0, 11.0, 12.0])
        delta = cliffs_delta(x, y)
        self.assertEqual(delta, -1.0)
        self.assertEqual(interpret_effect_size(delta), "Large")

    def test_cliffs_delta_zero(self):
        x = np.array([5.0, 5.0])
        y = np.array([5.0, 5.0])
        delta = cliffs_delta(x, y)
        self.assertEqual(delta, 0.0)
        self.assertEqual(interpret_effect_size(delta), "Negligible")

    def test_two_group_comparison(self):
        human = np.array([0.5, 0.6, 0.55, 0.7, 0.65])
        ai = np.array([0.1, 0.15, 0.2, 0.1, 0.12])
        res = run_two_group_comparison(human, ai, "share_rate", "Sharing Rate")
        self.assertIn("p_value", res)
        self.assertLess(res["p_value"], 0.05)
        self.assertEqual(res["effect_magnitude"], "Large")
        self.assertGreater(res["cliffs_delta"], 0.8)

    def test_classifier_cv_synthetic(self):
        np.random.seed(42)
        # Synthetic separated dataset
        X = np.vstack([
            np.random.normal(loc=1.0, scale=0.2, size=(10, 4)),
            np.random.normal(loc=-1.0, scale=0.2, size=(10, 4)),
        ])
        y = np.array([1]*10 + [0]*10)
        feats = ["f1", "f2", "f3", "f4"]

        res = evaluate_classifier_cv(X, y, feats, model_type="logistic", n_splits=3)
        self.assertGreaterEqual(res["accuracy"], 0.8)
        self.assertGreaterEqual(res["roc_auc"], 0.8)
        self.assertIn("f1", res["feature_importance"])

    def test_extract_trial_features(self):
        mock_rows = [
            {
                "trial_id": "test_trial",
                "round": 1,
                "agent_id": "A1",
                "source": "human",
                "action_type": "gather",
                "resource_before": 5.0,
                "resource_after": 7.0,
                "alive": True,
                "meta": {"arm": "human", "severity": 0.5},
            },
            {
                "trial_id": "test_trial",
                "round": 1,
                "agent_id": "A2",
                "source": "ai",
                "action_type": "skip",
                "resource_before": 5.0,
                "resource_after": 4.0,
                "alive": True,
            },
        ]
        feat = extract_trial_features(mock_rows, focal_id="A1")
        self.assertIsNotNone(feat)
        self.assertEqual(feat["trial_id"], "test_trial")
        self.assertEqual(feat["gather_rate"], 1.0)
        self.assertIn("hoarding_index", feat)
        self.assertIn("cooperation_rate", feat)


if __name__ == "__main__":
    unittest.main()
