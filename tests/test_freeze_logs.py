"""Self-tests for agents/freeze_logs.py, run against a temp directory so they never touch data/."""

import io
import json
import os
import shutil
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from agents import freeze_logs
from agents.smoke_random import run_trial


class FreezeLogsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.log_dir = os.path.join(self.tmp, "ai_logs")
        os.makedirs(self.log_dir)
        self.patches = [
            mock.patch.object(freeze_logs, "LOG_DIR", self.log_dir),
            mock.patch.object(freeze_logs, "MANIFEST_PATH", os.path.join(self.log_dir, "manifest.json")),
            mock.patch.object(freeze_logs, "RELEASE_DIR", os.path.join(self.tmp, "releases")),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, n=2, **entry_overrides):
        entries = []
        for seed in range(n):
            rows = run_trial("drought", seed, "cooperator")
            tid = rows[0]["trial_id"]
            with open(os.path.join(self.log_dir, f"{tid}.jsonl"), "w", encoding="utf-8") as f:
                f.writelines(json.dumps(r) + "\n" for r in rows)
            entry = {"trial_id": tid, "status": "ok", "git_sha": "abc123", "git_dirty": False, "model": None}
            entry.update(entry_overrides)
            entries.append(entry)
        with open(freeze_logs.MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump({"run_metadata": {}, "trials": entries}, f)

    def _freeze(self, **kw):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
            code = freeze_logs.freeze("vtest", **kw)
        return code, err.getvalue()

    def test_freezes_clean_trials_with_checksum(self):
        self._write()
        code, _ = self._freeze()
        self.assertEqual(code, 0)
        meta_path = os.path.join(freeze_logs.RELEASE_DIR, "ai_logs_vtest.json")
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        self.assertEqual(meta["n_trials"], 2)
        self.assertEqual(meta["git_shas"], ["abc123"])
        zip_path = os.path.join(freeze_logs.RELEASE_DIR, meta["zip"])
        self.assertEqual(freeze_logs._sha256(zip_path), meta["zip_sha256"])
        with zipfile.ZipFile(zip_path) as zf:
            self.assertIn("manifest.json", zf.namelist())

    def test_refuses_dirty_trials(self):
        self._write(git_dirty=True)
        code, err = self._freeze()
        self.assertEqual(code, 1)
        self.assertIn("dirty", err)

    def test_refuses_qa_failure(self):
        self._write(n=1)
        path = next(p for p in os.listdir(self.log_dir) if p.endswith(".jsonl"))
        full = os.path.join(self.log_dir, path)
        with open(full, encoding="utf-8") as f:
            rows = [json.loads(line) for line in f]
        rows[-1]["resource_before"] += 7
        with open(full, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows)
        code, err = self._freeze()
        self.assertEqual(code, 1)
        self.assertIn("qa_logs", err)

    def test_never_overwrites_a_frozen_version(self):
        self._write()
        self.assertEqual(self._freeze()[0], 0)
        code, err = self._freeze()
        self.assertEqual(code, 1)
        self.assertIn("never overwritten", err)


if __name__ == "__main__":
    unittest.main()
