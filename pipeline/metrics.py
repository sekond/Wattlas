"""Pure metric computations for the Spread view.

Every function here takes data in and returns data out with no network or file
I/O, so they can be unit-tested offline. See CLAUDE.md data landmines before
editing — especially the resolution break, DST handling, and the
upper-bound nature of the arbitrage figure.
"""

from __future__ import annotations

import pandas as pd

CANONICAL_FREQ = "1h"  # we resample everything to hourly before computing daily metrics


def to_hourly(prices: pd.Series) -> pd.Series:
    """Resample a tz-aware price Series to a single canonical hourly resolution.

    Why: the German day-ahead market switched from hourly to quarter-hourly in
    October 2025 (CLAUDE.md landmine #3). A multi-month series therefore mixes
    resolutions. We average sub-hourly values within each hour so all downstream
    daily metrics are computed on a uniform grid. Hourly input is unchanged.

    The index must be tz-aware. We resample in the original tz; calendar-day
    grouping happens later in Europe/Berlin local time.
    """
    if prices.empty:
        return prices
    if prices.index.tz is None:
        raise ValueError("price index must be timezone-aware")
    # mean() over the hour; for already-hourly data this is a no-op per bucket
    return prices.resample(CANONICAL_FREQ).mean().dropna()


def daily_spreads(prices: pd.Series, local_tz: str = "Europe/Berlin") -> pd.DataFrame:
    """Compute per-day TB1, TB2, min/max/mean price and negative-hour count.

    Days are grouped by local calendar date (DST-aware: a day may have 23/24/25
    hours; CLAUDE.md landmine #4). Negative prices are kept as-is (landmine #6).

    Returns a DataFrame indexed by date (python date objects) with columns:
    tb1, tb2, min_price, max_price, mean_price, negative_hours, hours_observed.
    """
    hourly = to_hourly(prices)
    if hourly.empty:
        return pd.DataFrame(
            columns=[
                "tb1", "tb2", "min_price", "max_price",
                "mean_price", "negative_hours", "hours_observed",
            ]
        )

    local = hourly.tz_convert(local_tz)
    df = local.to_frame("price")
    df["date"] = df.index.date

    rows = []
    for date, grp in df.groupby("date"):
        p = grp["price"].sort_values()
        n = len(p)
        tb1 = float(p.iloc[-1] - p.iloc[0]) if n >= 1 else float("nan")
        # TB2 needs at least 4 hours to be meaningful; fall back to TB1 logic otherwise
        if n >= 4:
            tb2 = float(p.iloc[-2:].mean() - p.iloc[:2].mean())
        else:
            tb2 = tb1
        rows.append(
            {
                "date": date,
                "tb1": round(tb1, 2),
                "tb2": round(tb2, 2),
                "min_price": round(float(p.min()), 2),
                "max_price": round(float(p.max()), 2),
                "mean_price": round(float(p.mean()), 2),
                "negative_hours": int((p < 0).sum()),
                "hours_observed": int(n),
            }
        )

    out = pd.DataFrame(rows).set_index("date")
    return out


def perfect_arbitrage_revenue(
    prices: pd.Series,
    power_mw: float = 1.0,
    duration_h: int = 2,
    round_trip_efficiency: float = 1.0,
    local_tz: str = "Europe/Berlin",
) -> float:
    """UPPER-BOUND daily arbitrage revenue summed over the period, EUR per MW.

    THIS IS NOT ACHIEVABLE REVENUE (CLAUDE.md landmine #7). It assumes perfect
    next-day foresight, charges in the cheapest `duration_h` hours and discharges
    in the most expensive `duration_h` hours of each local day, ignores price
    impact, and (by default) ignores losses. The frontend MUST label it as an
    upper bound. Provided so users can see the theoretical ceiling, not a target.
    """
    hourly = to_hourly(prices)
    if hourly.empty:
        return 0.0
    local = hourly.tz_convert(local_tz)
    df = local.to_frame("price")
    df["date"] = df.index.date

    total = 0.0
    for _, grp in df.groupby("date"):
        p = grp["price"].sort_values()
        if len(p) < 2 * duration_h:
            continue
        charge_cost = p.iloc[: duration_h].sum() * power_mw
        discharge_rev = p.iloc[-duration_h:].sum() * power_mw * round_trip_efficiency
        total += float(discharge_rev - charge_cost)
    return round(total, 2)


def price_by_hour_of_day(prices: pd.Series, local_tz: str = "Europe/Berlin") -> dict:
    """Average day-ahead price for each hour of the local day (0-23).

    The Pulse view's core metric: it shows the daily *rhythm* of prices —
    typically a midday solar trough and an evening peak. Split into weekday
    (Mon-Fri) and weekend (Sat-Sun) because the demand shape differs.

    Resamples to canonical hourly first (landmine #3) and groups by local hour
    in Europe/Berlin (landmine #4). Returns a dict with 24-length lists; a slot
    is None if no data fell in that hour. Negative averages are kept (landmine
    #6). All values rounded to 2 dp.
    """
    out = {
        "hours": list(range(24)),
        "all_mean": [None] * 24,
        "weekday_mean": [None] * 24,
        "weekend_mean": [None] * 24,
    }
    hourly = to_hourly(prices)
    if hourly.empty:
        return out

    local = hourly.tz_convert(local_tz)
    df = local.to_frame("price")
    df["hour"] = df.index.hour
    df["is_weekend"] = df.index.dayofweek >= 5  # Sat=5, Sun=6

    def _fill(frame: pd.DataFrame, key: str) -> None:
        for hour, mean in frame.groupby("hour")["price"].mean().items():
            out[key][int(hour)] = round(float(mean), 2)

    _fill(df, "all_mean")
    _fill(df[~df["is_weekend"]], "weekday_mean")
    _fill(df[df["is_weekend"]], "weekend_mean")
    return out


def data_coverage(
    series: pd.Series, local_tz: str = "Europe/Berlin", min_hours: int = 23
) -> tuple[str | None, str | None]:
    """First and last local dates that have a COMPLETE day of data.

    A day counts as complete if it has >= min_hours after hourly resampling
    (23 allows the short spring-DST day; landmine #4). This deliberately excludes
    a partial leading/trailing day — notably "today", whose data is incomplete —
    so the period reported to the UI reflects real coverage, not the fetch window.

    Returns (first, last) as 'YYYY-MM-DD' strings, or (None, None) if no complete
    day exists.
    """
    hourly = to_hourly(series)
    if hourly.empty:
        return (None, None)
    local = hourly.tz_convert(local_tz)
    counts = local.groupby(local.index.date).size()
    complete = counts[counts >= min_hours]
    if complete.empty:
        return (None, None)
    return (str(min(complete.index)), str(max(complete.index)))


def monthly_means(prices: pd.Series, local_tz: str = "Europe/Berlin") -> list[dict]:
    """Mean price per calendar month (local tz). Core metric for the Divergence
    view, computed per bidding zone so zones can be compared month by month.

    Resamples to canonical hourly first (landmine #3); months are local-calendar
    (landmine #4). Values rounded to 2 dp.
    """
    hourly = to_hourly(prices)
    if hourly.empty:
        return []
    local = hourly.tz_convert(local_tz)
    # Group by local calendar month. Drop tz to local wall-time first so
    # to_period doesn't warn about discarding tzinfo (the conversion above
    # already put us in local time, so the month assignment is correct).
    months = local.index.tz_localize(None).to_period("M")
    grouped = local.groupby(months).mean()
    return [{"month": str(period), "mean": round(float(v), 2)} for period, v in grouped.items()]


def mean_profile_by_hour(series: pd.Series, local_tz: str = "Europe/Berlin") -> list:
    """Mean value for each hour of the local day (0-23). Generic profile used by
    the Mismatch view for both renewable-share and demand series.

    Resamples to canonical hourly first (landmine #3), groups by local hour
    (landmine #4). Returns a 24-length list; a slot is None if no data fell in
    that hour. Values rounded to 2 dp.
    """
    out = [None] * 24
    hourly = to_hourly(series)
    if hourly.empty:
        return out
    local = hourly.tz_convert(local_tz)
    for hour, mean in local.groupby(local.index.hour).mean().items():
        out[int(hour)] = round(float(mean), 2)
    return out


def negative_hours_by_month(daily: pd.DataFrame) -> list[dict]:
    """Aggregate negative-hour counts by calendar month from a daily DataFrame."""
    if daily.empty:
        return []
    s = pd.Series(
        daily["negative_hours"].values,
        index=pd.to_datetime(daily.index),
    )
    monthly = s.groupby(s.index.to_period("M")).sum()
    return [
        {"month": str(period), "hours": int(hours)}
        for period, hours in monthly.items()
    ]
