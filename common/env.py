"""Minimal .env loader — stdlib only, no python-dotenv dependency (per the Phase A rule: don't add
a package for something a dozen lines of stdlib already does).

Only sets a variable if it isn't already in the environment (`setdefault`), so a real exported
shell/CI env var always wins over whatever's in `.env` — `.env` is a local-dev convenience, not a
source of truth once something is deployed.
"""

from __future__ import annotations

import os


def load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # An empty value (`FOO=`) means "not provided" — same as the line being absent —
            # not "explicitly set to empty string". Setting it anyway would shadow a code
            # default via os.environ.get(key, default), since .get() only falls back when the
            # key is *absent*, not when it's empty. Caught live: a blank GROQ_MODEL= line in
            # .env silently broke both providers by sending model="" instead of falling back.
            if key and value:
                os.environ.setdefault(key, value)
