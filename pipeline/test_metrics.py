"""Offline unit tests for pipeline/metrics.py — no network required.

Run: python -m pytest pipeline/test_metrics.py -v
or:  python pipeline/test_metrics.py   (falls back to a simple runner)
"""

from __future__ import annotations

import pandas as pd

from metrics import (
    daily_spreads,
    negative_hours_by_month,
    perfect_arbitrage_revenue,
    price_by_hour_of_day,
    to_hourly,
)


def _hourly_series(values, start="2025-07-02 00:00", tz="Europe/Berlin"):
    idx = pd.date_range(start=start, periods=len(values), freq="1h", tz=tz)
    return pd.Series(values, index=idx)


def test_to_hourly_downsamples_quarter_hourly():
    # 8 quarter-hourly points = 2 hours; each hour should average its 4 points
    idx = pd.date_range("2025-11-01 00:00", periods=8, freq="15min", tz="Europe/Berlin")
    s = pd.Series([0, 2, 4, 6, 10, 10, 10, 10], index=idx)
    out = to_hourly(s)
    assert len(out) == 2
    assert out.iloc[0] == 3.0   # mean(0,2,4,6)
    assert out.iloc[1] == 10.0  # mean(10,10,10,10)


def test_to_hourly_requires_tz():
    naive = pd.Series([1, 2], index=pd.date_range("2025-01-01", periods=2, freq="1h"))
    try:
        to_hourly(naive)
        assert False, "expected ValueError for tz-naive index"
    except ValueError:
        pass


def test_tb1_tb2_basic():
    # 24 hours: min 0, max 100; two lowest 0,5; two highest 100,90
    vals = [0, 5, 20, 30, 40, 50, 60, 70, 80, 90, 100, 45,
            44, 43, 42, 41, 35, 36, 37, 38, 39, 25, 26, 27]
    df = daily_spreads(_hourly_series(vals))
    assert len(df) == 1
    row = df.iloc[0]
    assert row["tb1"] == 100.0           # 100 - 0
    assert row["tb2"] == (100 + 90) / 2 - (0 + 5) / 2  # 95 - 2.5 = 92.5
    assert row["negative_hours"] == 0
    assert row["hours_observed"] == 24


def test_negative_prices_counted_not_clipped():
    vals = [-50, -10, -1, 5] + [20] * 20
    df = daily_spreads(_hourly_series(vals))
    row = df.iloc[0]
    assert row["negative_hours"] == 3
    assert row["min_price"] == -50.0     # not floored at 0


def test_dst_long_day_has_25_hours():
    # 2025-10-26 is the autumn DST switch in Europe/Berlin (clocks back -> 25h day)
    idx = pd.date_range("2025-10-26 00:00", periods=25, freq="1h", tz="Europe/Berlin")
    assert len(idx) == 25  # sanity: pandas models the extra hour
    s = pd.Series(list(range(25)), index=idx)
    df = daily_spreads(s)
    row = df.iloc[0]
    assert row["hours_observed"] == 25


def test_perfect_arbitrage_is_positive_upper_bound():
    # cheapest 2h sum=5 (0+5), priciest 2h sum=190 (100+90) -> 185 per MW per day
    vals = [0, 5, 20, 30, 40, 50, 60, 70, 80, 90, 100, 45,
            44, 43, 42, 41, 35, 36, 37, 38, 39, 25, 26, 27]
    rev = perfect_arbitrage_revenue(_hourly_series(vals), duration_h=2)
    assert rev == 185.0


def test_negative_hours_by_month():
    vals_day1 = [-1, -1, 5] + [10] * 21   # 2 negative hours, July
    df = daily_spreads(_hourly_series(vals_day1, start="2025-07-02 00:00"))
    out = negative_hours_by_month(df)
    assert out == [{"month": "2025-07", "hours": 2}]


def test_spring_dst_short_day_has_23_hours():
    # 2025-03-30 is the spring DST switch in Europe/Berlin: clocks jump
    # 02:00 -> 03:00, so the day has only 23 hours (landmine #4). The pipeline
    # must not assume 24 values/day.
    idx = pd.date_range("2025-03-30 00:00", periods=23, freq="1h", tz="Europe/Berlin")
    assert len(idx) == 23  # sanity: pandas models the missing hour
    df = daily_spreads(pd.Series(list(range(23)), index=idx))
    assert df.iloc[0]["hours_observed"] == 23


def test_data_gap_day_counts_only_available_hours():
    # A day with a data gap: only 20 of ~24 hours present (landmine #8). Metrics
    # are computed on what exists; build() flags such a day complete=false
    # (asserted in test_build.py). Here we confirm the hour count and TB1.
    idx = pd.date_range("2025-07-02 00:00", periods=20, freq="1h", tz="Europe/Berlin")
    df = daily_spreads(pd.Series(list(range(20)), index=idx))
    assert df.iloc[0]["hours_observed"] == 20
    assert df.iloc[0]["tb1"] == 19.0  # max(19) - min(0)


def test_tb2_falls_back_to_tb1_under_4_hours():
    # TB2 = mean(top 2) - mean(bottom 2) needs >= 4 hours to be meaningful. With
    # fewer hours it falls back to TB1 = max - min (metrics.py / landmine #5).
    idx = pd.date_range("2025-07-02 00:00", periods=3, freq="1h", tz="Europe/Berlin")
    row = daily_spreads(pd.Series([10, 50, 30], index=idx)).iloc[0]
    assert row["hours_observed"] == 3
    assert row["tb1"] == 40.0           # 50 - 10
    assert row["tb2"] == row["tb1"]     # fallback, not mean-of-2 logic


def test_price_by_hour_of_day_weekday_weekend_split():
    # Two weekdays (Tue 2025-07-01, Wed 2025-07-02): day2 = day1 + 10 each hour.
    wd = pd.concat([
        _hourly_series(list(range(24)), start="2025-07-01 00:00"),
        _hourly_series([h + 10 for h in range(24)], start="2025-07-02 00:00"),
    ])
    # One weekend day (Sat 2025-07-05): price = 100 + h.
    we = _hourly_series([100 + h for h in range(24)], start="2025-07-05 00:00")
    out = price_by_hour_of_day(pd.concat([wd, we]))
    assert out["hours"] == list(range(24))
    assert out["weekday_mean"][0] == 5.0      # mean(0, 10)
    assert out["weekday_mean"][23] == 28.0     # mean(23, 33)
    assert out["weekend_mean"][0] == 100.0     # Saturday only
    assert out["weekend_mean"][23] == 123.0
    assert out["all_mean"][0] == round((0 + 10 + 100) / 3, 2)  # all three days at hour 0


def test_price_by_hour_of_day_empty_is_safe():
    empty = pd.Series([], dtype=float, index=pd.DatetimeIndex([], tz="Europe/Berlin"))
    out = price_by_hour_of_day(empty)
    assert out["hours"] == list(range(24))
    assert all(v is None for v in out["all_mean"])


def test_empty_input_does_not_crash():
    empty = pd.Series([], dtype=float, index=pd.DatetimeIndex([], tz="Europe/Berlin"))
    assert daily_spreads(empty).empty
    assert perfect_arbitrage_revenue(empty) == 0.0
    assert negative_hours_by_month(daily_spreads(empty)) == []


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} passed")
