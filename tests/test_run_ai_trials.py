"""Fast tests for agents/run_ai_trials.py.
Covers build_grid dimensioning, Manifest tracking, RateLimiter, ThreadSafeRLModel,
and CLI spec parsing without invoking live network models.
"""

import os
import tempfile
import time
import unittest
from unittest.mock import MagicMock

from agents.run_ai_trials import (
    Manifest,
    RateLimiter,
    ThreadSafeRLModel,
    _parse_float_list,
    _parse_int_set,
    _parse_str_list,
    build_grid,
)


class TestBuildGrid(unittest.TestCase):
    def test_primary_grid_dimensions(self):
        scenarios = ["calm", "drought"]
        severities = [0.0, 0.7]
        coplayer_modes = ["standard", "deceptive"]
        primary_seeds = 3

        specs = build_grid(
            scenarios=scenarios,
            severities=severities,
            coplayer_modes=coplayer_modes,
            primary_arm="rl_only",
            primary_provider=None,
            primary_model=None,
            primary_seeds=primary_seeds,
            ablation_arms=[],
            ablation_severities=[],
            ablation_seeds=0,
            matched_seeds={0, 1},
        )
        expected_count = len(scenarios) * len(severities) * len(coplayer_modes) * primary_seeds
        self.assertEqual(len(specs), expected_count)

        # Verify matched_seeds flag
        matched = [s for s in specs if s["matched_seed"]]
        unmatched = [s for s in specs if not s["matched_seed"]]
        self.assertGreater(len(matched), 0)
        self.assertGreater(len(unmatched), 0)

    def test_ablation_grid_dimensions(self):
        specs = build_grid(
            scenarios=["calm"],
            severities=[0.0],
            coplayer_modes=["standard"],
            primary_arm="hybrid",
            primary_provider="groq",
            primary_model="llama-3.3-70b-versatile",
            primary_seeds=2,
            ablation_arms=["rl_only", "llm_only"],
            ablation_severities=[0.0, 0.7],
            ablation_seeds=2,
            matched_seeds=set(),
        )
        # Primary: 1 scenario * 1 severity * 1 coplayer_mode * 2 seeds = 2
        # Ablation: 1 scenario * 2 severities * 2 arms * 1 coplayer_mode * 2 seeds = 8
        self.assertEqual(len(specs), 10)


class TestThreadSafeRLModel(unittest.TestCase):
    def test_predict_delegates_to_wrapped_model(self):
        fake = MagicMock()
        fake.predict.return_value = (0, None)
        wrapped = ThreadSafeRLModel(fake)
        result = wrapped.predict([1, 2, 3])
        self.assertEqual(result, (0, None))
        fake.predict.assert_called_once_with([1, 2, 3])


class TestRateLimiter(unittest.TestCase):
    def test_unthrottled_when_zero(self):
        limiter = RateLimiter(calls_per_second=0)
        t0 = time.monotonic()
        for _ in range(5):
            limiter.acquire()
        t1 = time.monotonic()
        self.assertLess(t1 - t0, 0.1)


class TestManifest(unittest.TestCase):
    def test_manifest_records_and_checks_done(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mpath = os.path.join(tmpdir, "manifest.json")
            manifest = Manifest(mpath, run_metadata={"test": True})
            dummy_file = os.path.join(tmpdir, "trial1.jsonl")
            with open(dummy_file, "w") as f:
                f.write("{}\n")

            self.assertFalse(manifest.is_done("trial_001", dummy_file))

            manifest.record(
                {
                    "trial_id": "trial_001",
                    "status": "ok",
                    "path": dummy_file,
                }
            )
            self.assertTrue(manifest.is_done("trial_001", dummy_file))

            # Re-read manifest from disk
            manifest2 = Manifest(mpath, run_metadata={})
            self.assertTrue(manifest2.is_done("trial_001", dummy_file))


class TestSpecParsing(unittest.TestCase):
    def test_parse_str_list(self):
        self.assertEqual(_parse_str_list(" calm, drought , repeated_trust "), ["calm", "drought", "repeated_trust"])
        self.assertEqual(_parse_str_list(""), [])

    def test_parse_float_list(self):
        self.assertEqual(_parse_float_list("0.0, 0.3, 0.7"), [0.0, 0.3, 0.7])

    def test_parse_int_set(self):
        self.assertEqual(_parse_int_set("0-3, 5, 8-9"), {0, 1, 2, 3, 5, 8, 9})


if __name__ == "__main__":
    unittest.main()
