"""Offline tests for the last-updated manifest builder."""
from __future__ import annotations

import json
from pathlib import Path

from build_last_updated import latest_generated_at


def _write(d: Path, name: str, obj) -> None:
    (d / name).write_text(json.dumps(obj), encoding="utf-8")


def test_picks_most_recent_generated_at(tmp_path: Path):
    _write(tmp_path, "a.json", {"generated_at": "2026-06-20T00:00:00+00:00"})
    _write(tmp_path, "b.json", {"generated_at": "2026-06-29T07:10:55+00:00"})  # newest
    _write(tmp_path, "c.json", {"generated_at": "2026-06-22T12:00:00+00:00"})
    latest, counted = latest_generated_at(tmp_path)
    assert latest == "2026-06-29T07:10:55+00:00"
    assert counted == 3


def test_skips_files_without_or_with_bad_timestamp(tmp_path: Path):
    _write(tmp_path, "ok.json", {"generated_at": "2026-05-01T00:00:00+00:00"})
    _write(tmp_path, "no_ts.json", {"zone": "DE_LU"})          # no generated_at
    _write(tmp_path, "bad_ts.json", {"generated_at": "not-a-date"})
    (tmp_path / "broken.json").write_text("{not valid json", encoding="utf-8")
    latest, counted = latest_generated_at(tmp_path)
    assert latest == "2026-05-01T00:00:00+00:00"
    assert counted == 1  # only the one valid file counts


def test_excludes_the_manifest_itself(tmp_path: Path):
    _write(tmp_path, "last_updated.json", {"generated_at": "2099-01-01T00:00:00+00:00"})
    _write(tmp_path, "real.json", {"generated_at": "2026-06-29T00:00:00+00:00"})
    latest, counted = latest_generated_at(tmp_path)
    assert latest == "2026-06-29T00:00:00+00:00"  # manifest's own stamp ignored
    assert counted == 1


def test_none_when_no_timestamps(tmp_path: Path):
    _write(tmp_path, "x.json", {"foo": "bar"})
    latest, counted = latest_generated_at(tmp_path)
    assert latest is None and counted == 0
