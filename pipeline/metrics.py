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
