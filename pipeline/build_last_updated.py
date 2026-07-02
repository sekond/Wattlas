#!/usr/bin/env python3
"""Write data/last_updated.json — the site-wide "data last updated" stamp.

Every builder stamps its output with `generated_at`. This scans data/*.json for
the MOST RECENT one and records it in a tiny manifest the frontend (nav.js) reads
to show "Data updated <date>" on every page. Because the daily GitHub Action runs
this after the view builders and commits the result, the indicator tracks the
refresh automatically — no hand-edited date.

It only reads committed JSON (no network, no token), so it is safe to run locally.
"""
from __future__ import annotations

import glob
import json
from datetime import datetime
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
OUT_NAME = "last_updated.json"


def latest_generated_at(data_dir: Path, exclude: str = OUT_NAME) -> tuple[str | None, int]:
    """Return (most-recent generated_at ISO string, count of files that had one).

    Pure and testable: pass any directory of JSON files. Files without a valid
    `generated_at` are skipped; the manifest itself is excluded.
    """
    latest_dt: datetime | None = None
    latest_str: str | None = None
    counted = 0
    for path in sorted(Path(data_dir).glob("*.json")):
        if path.name == exclude:
            continue
        try:
            g = json.loads(path.read_text(encoding="utf-8")).get("generated_at")
        except (ValueError, OSError, AttributeError):
            continue
        if not g:
            continue
        try:
            dt = datetime.fromisoformat(g)
        except (ValueError, TypeError):
            continue
        counted += 1
        if latest_dt is None or dt > latest_dt:
            latest_dt, latest_str = dt, g
    return latest_str, counted


def main() -> int:
    latest, counted = latest_generated_at(DATA)
    if latest is None:
        print("no generated_at found in data/*.json — manifest not written")
        return 1
    payload = {
        "generated_at": latest,
        "sources_counted": counted,
        "note": "Most recent generated_at across data/*.json — the site-wide "
                "'data last updated' stamp read by the frontend (nav.js).",
    }
    (DATA / OUT_NAME).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote data/{OUT_NAME}: {latest} (from {counted} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
