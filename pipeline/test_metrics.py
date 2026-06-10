"""Offline unit tests for pipeline/metrics.py — no network required.

Run: python -m pytest pipeline/test_metrics.py -v
or:  python pipeline/test_metrics.py   (falls back to a simple runner)
"""

from __future__ import annotations

import pandas as pd

from metrics import (
    carbon_intensity_hourly,
    collapse_generation,
    daily_generation_gw,
    daily_mean_series,
    daily_spreads,
    data_coverage,
    fuel_profile_by_hour_gw,
    mean_profile_by_hour,
    monthly_means,
    negative_hours_by_month,
    perfect_arbitrage_revenue,
    price_by_hour_of_day,
    renewable_share_hourly,
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


def test_monthly_means():
    # 48 hourly values in July, all = 10 -> July mean 10. Add 24h in August = 20.
    jul = _hourly_series([10] * 48, start="2025-07-01 00:00")
    aug = _hourly_series([20] * 24, start="2025-08-01 00:00")
    out = monthly_means(pd.concat([jul, aug]))
    assert out == [{"month": "2025-07", "mean": 10.0}, {"month": "2025-08", "mean": 20.0}]


def test_mean_profile_by_hour():
    # Two days; hour h = h on day1, h+10 on day2 -> profile[h] = h+5.
    s = pd.concat([
        _hourly_series(list(range(24)), start="2025-07-01 00:00"),
        _hourly_series([h + 10 for h in range(24)], start="2025-07-02 00:00"),
    ])
    prof = mean_profile_by_hour(s)
    assert len(prof) == 24
    assert prof[0] == 5.0
    assert prof[23] == 28.0


def test_data_coverage_excludes_partial_trailing_day():
    # Two full days then a partial "today" of only 5 hours — the partial day
    # must not extend the reported coverage (the bug this guards against).
    s = pd.concat([
        _hourly_series([10] * 24, start="2025-07-01 00:00"),
        _hourly_series([10] * 24, start="2025-07-02 00:00"),
        _hourly_series([10] * 5, start="2025-07-03 00:00"),
    ])
    first, last = data_coverage(s)
    assert first == "2025-07-01"
    assert last == "2025-07-02"   # NOT 2025-07-03


def test_data_coverage_empty():
    empty = pd.Series([], dtype=float, index=pd.DatetimeIndex([], tz="Europe/Berlin"))
    assert data_coverage(empty) == (None, None)


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


# --- Phase 1/5: generation mix + carbon intensity ------------------------------

def _gen_fixture(n_hours=4, start="2025-07-02 00:00", tz="Europe/Berlin"):
    """A small raw-ENTSO-E-style generation frame: tuple columns, tz-aware index.
    Two solar-ish sources to test that types mapping to one fuel are summed, and
    one 'Actual Consumption' column that must be ignored."""
    idx = pd.date_range(start=start, periods=n_hours, freq="1h", tz=tz)
    return pd.DataFrame({
        ("Solar", "Actual Aggregated"): [10.0] * n_hours,
        ("Fossil Hard coal", "Actual Aggregated"): [20.0] * n_hours,
        ("Fossil Brown coal/Lignite", "Actual Aggregated"): [30.0] * n_hours,
        ("Hydro Pumped Storage", "Actual Consumption"): [5.0] * n_hours,  # must be dropped
    }, index=idx)


def test_collapse_generation_drops_consumption_and_orders_fuels():
    out = collapse_generation(_gen_fixture())
    # Consumption column gone; only generation fuels remain.
    assert "Pumped storage" not in out.columns
    assert set(out.columns) == {"Solar", "Hard coal", "Lignite"}
    # Canonical order: Lignite, Hard coal before Solar.
    assert list(out.columns) == ["Lignite", "Hard coal", "Solar"]
    assert out["Solar"].iloc[0] == 10.0


def test_collapse_generation_sums_types_to_same_fuel():
    # Two hard-coal-ish columns should sum into one "Gas" via the coal-derived map.
    idx = pd.date_range("2025-07-02 00:00", periods=2, freq="1h", tz="Europe/Berlin")
    gen = pd.DataFrame({
        ("Fossil Gas", "Actual Aggregated"): [100.0, 100.0],
        ("Fossil Coal-derived gas", "Actual Aggregated"): [10.0, 10.0],
    }, index=idx)
    out = collapse_generation(gen)
    assert list(out.columns) == ["Gas"]
    assert out["Gas"].iloc[0] == 110.0


def test_collapse_generation_requires_tz():
    naive = pd.DataFrame(
        {("Solar", "Actual Aggregated"): [1.0]},
        index=pd.date_range("2025-01-01", periods=1, freq="1h"),
    )
    try:
        collapse_generation(naive)
        assert False, "expected ValueError for tz-naive index"
    except ValueError:
        pass


def test_fuel_profile_and_daily_in_gw():
    # Solar at 10 MW all day -> profile/daily = 0.01 GW; units convert MW->GW.
    out = collapse_generation(_gen_fixture(n_hours=24))
    prof = fuel_profile_by_hour_gw(out)
    assert prof["Solar"][0] == 0.01   # 10 MW = 0.01 GW
    days, daily = daily_generation_gw(out)
    assert len(days) == 1
    assert daily["Solar"][0] == prof["Solar"][0]


def test_carbon_intensity_pure_solar_is_solar_factor():
    # Only solar generating -> intensity == solar emission factor (45).
    idx = pd.date_range("2025-07-02 00:00", periods=3, freq="1h", tz="Europe/Berlin")
    gen = pd.DataFrame({("Solar", "Actual Aggregated"): [50.0, 50.0, 50.0]}, index=idx)
    fuels = collapse_generation(gen)
    ci = carbon_intensity_hourly(fuels, {"Solar": 45.0})
    assert round(ci.iloc[0], 1) == 45.0


def test_carbon_intensity_weighted_mix():
    # 100 MW gas (490) + 100 MW solar (45) -> mean of the two factors weighted by MW.
    idx = pd.date_range("2025-07-02 00:00", periods=1, freq="1h", tz="Europe/Berlin")
    gen = pd.DataFrame({
        ("Fossil Gas", "Actual Aggregated"): [100.0],
        ("Solar", "Actual Aggregated"): [100.0],
    }, index=idx)
    fuels = collapse_generation(gen)
    ci = carbon_intensity_hourly(fuels, {"Gas": 490.0, "Solar": 45.0})
    assert round(ci.iloc[0], 1) == round((490.0 + 45.0) / 2, 1)  # equal MW -> simple mean


def test_carbon_intensity_excludes_pumped_storage():
    # Pumped storage must not affect intensity (excluded as a carrier).
    idx = pd.date_range("2025-07-02 00:00", periods=1, freq="1h", tz="Europe/Berlin")
    gen = pd.DataFrame({
        ("Solar", "Actual Aggregated"): [100.0],
        ("Hydro Pumped Storage", "Actual Aggregated"): [100.0],
    }, index=idx)
    fuels = collapse_generation(gen)
    ci = carbon_intensity_hourly(fuels, {"Solar": 45.0, "Pumped storage": 999.0})
    assert round(ci.iloc[0], 1) == 45.0  # pumped storage ignored


def test_carbon_intensity_skips_missing_fuel_not_whole_hour():
    # Regression: a fuel that is NaN for an hour must be treated as 0, not void
    # the hour (France's Hard coal is reported only sporadically). Hour 0 has gas
    # only; hour 1 adds NaN hard coal — both hours must yield an intensity.
    idx = pd.date_range("2025-07-02 00:00", periods=2, freq="1h", tz="Europe/Berlin")
    fuels = pd.DataFrame({"Gas": [100.0, 100.0], "Hard coal": [float("nan"), float("nan")]}, index=idx)
    ci = carbon_intensity_hourly(fuels, {"Gas": 490.0, "Hard coal": 820.0})
    assert len(ci) == 2                 # NOT dropped to 0 hours
    assert round(ci.iloc[0], 1) == 490.0  # missing hard coal counts as 0 gen


def test_vre_hourly_mw():
    # Wind + solar summed per hour; non-VRE fuels (gas) ignored; gaps preserved.
    from metrics import vre_hourly_mw
    idx = pd.date_range("2025-07-02 00:00", periods=2, freq="1h", tz="Europe/Berlin")
    gen = pd.DataFrame({
        ("Solar", "Actual Aggregated"): [10.0, 20.0],
        ("Wind Onshore", "Actual Aggregated"): [5.0, 5.0],
        ("Fossil Gas", "Actual Aggregated"): [100.0, 100.0],
    }, index=idx)
    vre = vre_hourly_mw(collapse_generation(gen))
    assert vre.iloc[0] == 15.0 and vre.iloc[1] == 25.0


def test_renewable_share_hourly():
    # 30 MW renewable (solar) of 60 MW total -> 50%.
    idx = pd.date_range("2025-07-02 00:00", periods=1, freq="1h", tz="Europe/Berlin")
    gen = pd.DataFrame({
        ("Solar", "Actual Aggregated"): [30.0],
        ("Fossil Gas", "Actual Aggregated"): [30.0],
    }, index=idx)
    fuels = collapse_generation(gen)
    share = renewable_share_hourly(fuels, {"Solar"})
    assert round(share.iloc[0], 1) == 50.0


def test_daily_mean_series():
    s = _hourly_series([10.0] * 24, start="2025-07-02 00:00")
    days, vals = daily_mean_series(s)
    assert days == ["2025-07-02"]
    assert vals == [10.0]


def test_monthly_flow_stats_direction_and_congestion():
    from metrics import monthly_flow_stats
    idx = pd.date_range("2025-07-01 00:00", periods=4, freq="1h", tz="Europe/Berlin")
    # Net export of 900 MW against an export capacity of 1000 -> 90% = congested.
    net = pd.Series([900.0, 900.0, -200.0, -200.0], index=idx)  # 2 export, 2 import hours
    cap_exp = pd.Series([1000.0] * 4, index=idx)
    cap_imp = pd.Series([1000.0] * 4, index=idx)
    out = monthly_flow_stats(net, cap_exp, cap_imp, threshold=0.9)
    assert len(out) == 1
    row = out[0]
    assert row["month"] == "2025-07"
    assert row["net_flow_mw"] == round((900 + 900 - 200 - 200) / 4, 1)  # 350.0
    assert row["congestion_pct"] == 50.0  # the 2 export hours hit 90% of capacity


def test_monthly_flow_stats_no_capacity_means_no_congestion():
    from metrics import monthly_flow_stats
    idx = pd.date_range("2025-07-01 00:00", periods=2, freq="1h", tz="Europe/Berlin")
    net = pd.Series([5000.0, 5000.0], index=idx)  # huge flow but no capacity known
    out = monthly_flow_stats(net, pd.Series(dtype=float), pd.Series(dtype=float))
    assert out[0]["congestion_pct"] == 0.0  # can't be congested without a capacity reference


def test_flows_assemble_coerces_index_with_empty_ntc():
    # Regression for the CI P0 (issue #19): a border with no published NTC yields
    # an empty capacity Series; pd.DataFrame(cols) then collapses the union index
    # to a plain object Index, which later crashed to_hourly(). _assemble must
    # restore a tz-aware DatetimeIndex so monthly_flow_stats works on the result.
    from build_flows import _assemble
    from metrics import monthly_flow_stats
    idx = pd.date_range("2025-01-01", periods=4, freq="1h", tz="UTC")
    cols = {
        "PL_net": pd.Series([100.0, -50.0, 100.0, -50.0], index=idx),
        "PL_cap_exp": pd.Series(dtype=float),   # no NTC published (the trigger)
        "PL_cap_imp": pd.Series(dtype=float),
    }
    df = _assemble(cols)
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.tz is not None
    # And the downstream metric no longer raises on this frame.
    out = monthly_flow_stats(df["PL_net"].dropna(), pd.Series(dtype=float), pd.Series(dtype=float))
    assert out and out[0]["congestion_pct"] == 0.0


def test_generation_metrics_empty_safe():
    empty = pd.DataFrame()
    assert collapse_generation(empty).empty
    assert fuel_profile_by_hour_gw(empty) == {}
    assert daily_generation_gw(empty) == ([], {})
    assert carbon_intensity_hourly(empty, {}).empty
    assert renewable_share_hourly(empty, set()).empty


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} passed")
