"""Offline test for pipeline/build_spread.build() — no network required.

Injects a fixture price Series into build() and asserts both JSON artefacts are
written with schema-correct keys (see data/schema.md), including correct handling
of an incomplete (data-gap) day.

Run: python pipeline/test_build.py
or:  python -m pytest pipeline/test_build.py -v
"""

from __future__ import annotations

import json
import pathlib
import tempfile

import pandas as pd

import build_spread

# Keys the data contract (data/schema.md) requires.
DAY_KEYS = {
    "date", "tb1", "tb2", "min_price", "max_price",
    "mean_price", "negative_hours", "hours_observed", "complete",
}
SUMMARY_KEYS = {
    "zone", "period_start", "period_end", "avg_daily_tb1", "widest_day",
    "total_negative_hours", "negative_hours_by_month", "yoy_tb1_change_pct",
    "perfect_arbitrage_eur_per_mw", "perfect_arbitrage_is_upper_bound",
    "battery_assumptions", "missing_days",
}


def _fixture_prices() -> pd.Series:
    """68 hourly tz-aware values: two full 24h days + one 20h (data-gap) day.

    Values cross zero so negative_hours is exercised. No network.
    """
    idx = pd.date_range("2025-07-01 00:00", periods=68, freq="1h", tz="Europe/Berlin")
    vals = [(i % 24) * 5 - 10 for i in range(68)]  # ranges -10..+105, negatives early each day
    return pd.Series(vals, index=idx)


def test_build_writes_schema_correct_json():
    prices = _fixture_prices()
    original_data_dir = build_spread.DATA_DIR
    try:
        with tempfile.TemporaryDirectory() as tmp:
            # Redirect output so we never clobber the real data/ files.
            build_spread.DATA_DIR = pathlib.Path(tmp)
            build_spread.build(prices.index.min(), prices.index.max(), prices=prices)

            spread = json.loads((build_spread.DATA_DIR / "spread.json").read_text())
            summary = json.loads((build_spread.DATA_DIR / "spread_summary.json").read_text())
    finally:
        build_spread.DATA_DIR = original_data_dir

    # spread.json shape
    assert spread["zone"] == "DE_LU"
    assert len(spread["days"]) == 3
    for day in spread["days"]:
        assert set(day.keys()) == DAY_KEYS

    # The 20-hour day must be kept but flagged incomplete (landmine #8).
    gap = next(d for d in spread["days"] if d["date"] == "2025-07-03")
    assert gap["hours_observed"] == 20
    assert gap["complete"] is False
    full = next(d for d in spread["days"] if d["date"] == "2025-07-01")
    assert full["complete"] is True

    # summary.json shape
    assert set(summary.keys()) == SUMMARY_KEYS
    assert summary["zone"] == "DE_LU"
    assert summary["widest_day"] is not None
    assert summary["perfect_arbitrage_is_upper_bound"] is True
    assert "2025-07-03" in summary["missing_days"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} passed")
