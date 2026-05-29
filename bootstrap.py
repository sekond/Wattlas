#!/usr/bin/env python3
"""Wattlas bootstrap — run this first.

Verifies the project is correctly assembled and the environment is ready, then
prints exactly what to do next. It does NOT fetch data or change your code; it's
a pre-flight check so Claude Code starts from a known-good state.

Usage:  python bootstrap.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# (path, must_exist, note)
EXPECTED = [
    ("CLAUDE.md", True, "instructions + domain landmines (auto-loaded by Claude Code)"),
    ("README.md", True, "human-facing overview"),
    ("requirements.txt", True, "Python dependencies"),
    (".env.example", True, "template for your ENTSO-E token"),
    ("data/schema.md", True, "pipeline<->frontend JSON contract"),
    ("data/spread.json", True, "sample data (lets the frontend run before any fetch)"),
    ("data/spread_summary.json", True, "sample summary"),
    ("pipeline/metrics.py", True, "pure, tested metric functions"),
    ("pipeline/build_spread.py", True, "fetch + orchestrate + write JSON"),
    ("pipeline/test_metrics.py", True, "offline unit tests"),
    ("frontend/index.html", True, "the static Spread view"),
    ("prompts/implementation_prompts.md", True, "the 6 build prompts"),
    ("RUN.md", True, "step-by-step runbook for Claude Code"),
]

GREEN, RED, YEL, DIM, OFF = "\033[92m", "\033[91m", "\033[93m", "\033[2m", "\033[0m"


def check(label: str, ok: bool, detail: str = "") -> bool:
    mark = f"{GREEN}OK{OFF}" if ok else f"{RED}MISSING{OFF}"
    line = f"  [{mark}] {label}"
    if detail:
        line += f"  {DIM}{detail}{OFF}"
    print(line)
    return ok


def main() -> int:
    print("\nWattlas pre-flight check\n" + "=" * 40)

    # 1. Structure
    print("\n1. Project files")
    all_present = True
    for rel, required, note in EXPECTED:
        exists = (ROOT / rel).exists()
        all_present &= check(rel, exists, note)
        if not exists and required:
            all_present = False

    # 2. Python version
    print("\n2. Environment")
    py_ok = sys.version_info >= (3, 10)
    check(f"Python {sys.version_info.major}.{sys.version_info.minor} (need >= 3.10)", py_ok)

    # 3. Dependencies
    deps = {"pandas": False, "entsoe": False, "pyarrow": False}
    for mod in deps:
        try:
            __import__(mod)
            deps[mod] = True
        except ImportError:
            pass
    for mod, ok in deps.items():
        check(f"{mod} importable", ok, "" if ok else "run: pip install -r requirements.txt")

    # 4. Token (presence only; never printed)
    print("\n3. ENTSO-E API token")
    env_file = ROOT / ".env"
    token_in_env = bool(os.environ.get("ENTSOE_API_TOKEN"))
    token_in_file = env_file.exists() and "ENTSOE_API_TOKEN=" in env_file.read_text() \
        and "your_token_here" not in env_file.read_text()
    token_ready = token_in_env or token_in_file
    check(".env exists", env_file.exists(), "" if env_file.exists() else "run: cp .env.example .env")
    check("token set", token_ready,
          "" if token_ready else "edit .env and paste your token (free from transparency.entsoe.eu)")

    # Verdict
    print("\n" + "=" * 40)
    deps_ok = all(deps.values())
    if all_present and py_ok and deps_ok:
        print(f"{GREEN}Structure and environment ready.{OFF}")
        if token_ready:
            print("You can fetch real data. Next: open RUN.md and start at Step 1.")
        else:
            print(f"{YEL}Frontend works on sample data now.{OFF} "
                  "To fetch real data, set your token (see above), then open RUN.md.")
        print("\nTry the frontend on sample data right now:")
        print(f"  {DIM}python -m http.server 8000{OFF}  then open  "
              f"{DIM}http://localhost:8000/frontend/index.html{OFF}")
        return 0
    else:
        print(f"{RED}Not ready.{OFF} Fix the items marked MISSING above, then re-run "
              "python bootstrap.py")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
