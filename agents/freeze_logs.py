"""Phase H — freeze the AI trial campaign into a versioned, checksummed dataset.

data/ai_logs/ is gitignored (it's thousands of files), so "freeze ai_logs_v1 and tag the commit"
can't mean committing the logs. Instead this writes:

  data/releases/ai_logs_<version>.zip    — every manifest "ok" trial + manifest.json (gitignored;
                                           share it out-of-band, e.g. a GitHub release asset)
  data/releases/ai_logs_<version>.json   — tracked: sha256 of the zip, per-cell counts, QA result,
                                           and the set of git SHAs that produced the trials

Commit the .json and tag that commit; anyone holding the zip can then verify it's the frozen
dataset. Refuses to freeze unless every included trial passes agents/qa_logs.py and no included
trial was produced from a dirty working tree (its git SHA wouldn't identify the code).

Only campaign trials (manifest entries) are included — scripted pilot logs from
agents/smoke_random.py live in the same directory but are not experimental data.

Usage:
    python -m agents.freeze_logs --version v1
    python -m agents.freeze_logs --version v1 --allow-dirty   # not for the paper dataset
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import zipfile
from datetime import datetime, timezone

from agents.qa_logs import qa_check_trial, summarize_trials

LOG_DIR = os.path.join("data", "ai_logs")
MANIFEST_PATH = os.path.join(LOG_DIR, "manifest.json")
RELEASE_DIR = os.path.join("data", "releases")


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def freeze(version: str, allow_dirty: bool = False) -> int:
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)
    entries = [e for e in manifest["trials"] if e.get("status") == "ok"]
    failed = [e["trial_id"] for e in manifest["trials"] if e.get("status") != "ok"]
    if not entries:
        print("No completed trials in the manifest — nothing to freeze.", file=sys.stderr)
        return 1

    problems: list[str] = []
    missing_provenance = [e["trial_id"] for e in entries if not e.get("git_sha")]
    dirty = [e["trial_id"] for e in entries if e.get("git_dirty")]
    if missing_provenance:
        problems.append(f"{len(missing_provenance)} trial(s) have no per-trial git_sha (re-run them)")
    if dirty and not allow_dirty:
        problems.append(f"{len(dirty)} trial(s) were produced from a dirty working tree")

    trials: list[list[dict]] = []
    paths: list[str] = []
    qa_failures = 0
    for e in entries:
        path = os.path.join(LOG_DIR, f"{e['trial_id']}.jsonl")
        if not os.path.exists(path):
            problems.append(f"missing log file for {e['trial_id']}")
            continue
        with open(path, encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        if qa_check_trial(rows, filepath=path):
            qa_failures += 1
        trials.append(rows)
        paths.append(path)
    if qa_failures:
        problems.append(f"{qa_failures} trial(s) fail agents/qa_logs.py")

    if problems:
        print("Refusing to freeze:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    os.makedirs(RELEASE_DIR, exist_ok=True)
    zip_path = os.path.join(RELEASE_DIR, f"ai_logs_{version}.zip")
    meta_path = os.path.join(RELEASE_DIR, f"ai_logs_{version}.json")
    if os.path.exists(meta_path):
        print(f"{meta_path} already exists — a frozen version is never overwritten.", file=sys.stderr)
        return 1

    # Fixed timestamps and sorted order so the same inputs always produce the same zip bytes.
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(paths) + [MANIFEST_PATH]:
            info = zipfile.ZipInfo(os.path.basename(path), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(path, "rb") as f:
                zf.writestr(info, f.read())

    summary = summarize_trials(trials)
    release = {
        "version": version,
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "zip": os.path.basename(zip_path),
        "zip_sha256": _sha256(zip_path),
        "n_trials": len(paths),
        "n_rows": sum(len(t) for t in trials),
        "excluded_failed_trials": failed,
        "qa_pass_rate": 1.0,
        "git_shas": sorted({e["git_sha"] for e in entries}),
        "prompt_file_sha256s": sorted({e.get("prompt_file_sha256") or "" for e in entries} - {""}),
        "models": sorted({e.get("model") or "" for e in entries} - {""}),
        "summary": summary,
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(release, f, indent=2)

    print(f"Froze {len(paths)} trials ({release['n_rows']} rows) -> {zip_path}")
    print(f"sha256 {release['zip_sha256']}")
    print(f"Commit {meta_path} and tag that commit ai_logs_{version}.")
    return 0


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", required=True, help='e.g. "v1"')
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()
    return freeze(args.version, allow_dirty=args.allow_dirty)


if __name__ == "__main__":
    raise SystemExit(_main())
