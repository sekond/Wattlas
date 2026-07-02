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


def _gen_ptype(col) -> str:
    """Production-type name from an entsoe generation column (tuple or string)."""
    return col[0] if isinstance(col, tuple) else col


def _gen_is_aggregated(col) -> bool:
    """True for 'Actual Aggregated' (generation) columns, not 'Actual Consumption'."""
    return (col[-1] if isinstance(col, tuple) else "Actual Aggregated") == "Actual Aggregated"


def collapse_generation(gen: pd.DataFrame, local_tz: str = "Europe/Berlin") -> pd.DataFrame:
    """Collapse raw ENTSO-E generation into canonical-fuel columns (MW), hourly.

    Input: the wide DataFrame from `query_generation` whose columns are
    ('<production type>', 'Actual Aggregated'/'Actual Consumption') tuples. We
    keep only 'Actual Aggregated' (generation, not load), map each production
    type to a canonical fuel via fuels.FUEL_MAP, and sum types that share a fuel.

    Resamples to canonical hourly (landmine #3). Gaps are preserved, not faked
    (landmine #9): an hour where every fuel is missing stays NaN; `min_count=1`
    keeps a fuel NaN only when all its source columns are missing for that bucket.
    Columns are returned in canonical FUEL_ORDER, restricted to fuels present.
    Values stay in MW; the index stays tz-aware.
    """
    from fuels import FUEL_MAP, FUEL_ORDER

    if gen.empty:
        return pd.DataFrame()
    if gen.index.tz is None:
        raise ValueError("generation index must be timezone-aware")

    agg_cols = [c for c in gen.columns if _gen_is_aggregated(c)]
    groups: dict[str, list] = {}
    for c in agg_cols:
        groups.setdefault(FUEL_MAP.get(_gen_ptype(c), "Other"), []).append(c)

    fuel_df = pd.DataFrame(index=gen.index)
    for fuel, cols in groups.items():
        block = gen[cols].apply(pd.to_numeric, errors="coerce")
        fuel_df[fuel] = block.sum(axis=1, min_count=1)

    hourly = fuel_df.resample(CANONICAL_FREQ).mean().dropna(how="all")
    ordered = [f for f in FUEL_ORDER if f in hourly.columns]
    return hourly[ordered]


def fuel_profile_by_hour_gw(fuel_hourly_mw: pd.DataFrame, local_tz: str = "Europe/Berlin") -> dict:
    """Mean generation per local hour-of-day (0-23) for each fuel, in GW.

    Used by the Mix view's 'average day' stacked area. Returns {fuel: [24]} with
    None where no data fell in that hour (landmine #9). MW -> GW for display.
    """
    out: dict[str, list] = {}
    if fuel_hourly_mw.empty:
        return out
    local = fuel_hourly_mw.tz_convert(local_tz)
    hours = local.index.hour
    for fuel in fuel_hourly_mw.columns:
        prof: list = [None] * 24
        grp = (local[fuel] / 1000.0).groupby(hours).mean()
        for hour, mean in grp.items():
            prof[int(hour)] = round(float(mean), 2) if pd.notna(mean) else None
        out[fuel] = prof
    return out


def daily_generation_gw(fuel_hourly_mw: pd.DataFrame, local_tz: str = "Europe/Berlin") -> tuple[list, dict]:
    """Mean generation per local calendar day for each fuel, in GW.

    Returns (date_strings, {fuel: [values aligned to dates]}). A day with no data
    for a fuel is None. Mean (not sum) keeps units as average GW, comparable with
    the hour-of-day profile. Grouping is local-tz (landmine #4).
    """
    if fuel_hourly_mw.empty:
        return [], {}
    local = fuel_hourly_mw.tz_convert(local_tz)
    dates = sorted(set(local.index.date))
    date_strs = [str(d) for d in dates]
    days = local.index.date
    series: dict[str, list] = {}
    for fuel in fuel_hourly_mw.columns:
        grp = (local[fuel] / 1000.0).groupby(days).mean()
        series[fuel] = [
            round(float(grp[d]), 2) if (d in grp.index and pd.notna(grp[d])) else None
            for d in dates
        ]
    return date_strs, series


def carbon_intensity_hourly(
    fuel_hourly_mw: pd.DataFrame,
    factors: dict,
    exclude: tuple = ("Pumped storage",),
) -> pd.Series:
    """Production-based grid carbon intensity per hour, gCO2eq/kWh.

    intensity = Σ(generation_f · EF_f) / Σ(generation_f), a generation-weighted
    mean of the per-fuel factors (the MW unit cancels, so the result is g/kWh
    regardless of MW vs MWh). Production-based: emissions are attributed to
    generation inside the zone, ignoring imports/exports (carbon methodology
    note). Pumped-storage discharge is excluded as a storage carrier, not primary
    generation. Hours with no positive generation are dropped (no divide-by-zero).
    """
    if fuel_hourly_mw.empty:
        return pd.Series(dtype=float)
    cols = [c for c in fuel_hourly_mw.columns if c not in exclude]
    # Negative values would be reporting artefacts here; clip so they don't make
    # emissions or totals negative.
    gen = fuel_hourly_mw[cols].clip(lower=0)
    # A fuel that is NaN for an hour means "not reported / not generating" — treat
    # it as 0 for THAT fuel rather than voiding the whole hour. We must use
    # pandas' NaN-skipping row sums (not Python's sum(), which propagates NaN and
    # would discard every hour where any one fuel column is missing — e.g. France,
    # whose Hard coal series is reported only sporadically). min_count=1 keeps an
    # hour NaN only when every fuel is missing.
    factor_vec = pd.Series({c: float(factors.get(c, 700.0)) for c in cols})
    emissions = gen.mul(factor_vec, axis=1).sum(axis=1, min_count=1)
    total = gen.sum(axis=1, min_count=1)
    intensity = (emissions / total)[total > 0]
    return intensity.dropna()


def vre_hourly_mw(
    fuel_hourly_mw: pd.DataFrame,
    vre_fuels: tuple = ("Wind onshore", "Wind offshore", "Solar"),
) -> pd.Series:
    """Variable-renewable (wind + solar) generation per hour, MW.

    The input the Mismatch view subtracts from demand to get residual load. Fuels
    absent for a zone are skipped; an hour where every VRE fuel is missing stays
    NaN (min_count=1), so gaps propagate honestly rather than reading as zero.
    """
    if fuel_hourly_mw.empty:
        return pd.Series(dtype=float)
    cols = [c for c in fuel_hourly_mw.columns if c in vre_fuels]
    if not cols:
        return pd.Series(0.0, index=fuel_hourly_mw.index)
    return fuel_hourly_mw[cols].clip(lower=0).sum(axis=1, min_count=1)


def renewable_share_hourly(fuel_hourly_mw: pd.DataFrame, renewable_fuels: set) -> pd.Series:
    """Renewable share of generation per hour, in percent (0-100).

    share = Σ(renewable fuels) / Σ(all generation). Pairs with carbon intensity:
    as renewable share rises, production-based intensity should fall (the Phase 5
    sanity check). Hours with no positive generation are dropped.
    """
    if fuel_hourly_mw.empty:
        return pd.Series(dtype=float)
    gen = fuel_hourly_mw.clip(lower=0)
    ren_cols = [c for c in gen.columns if c in renewable_fuels]
    total = gen.sum(axis=1, min_count=1)
    ren = gen[ren_cols].sum(axis=1, min_count=1) if ren_cols else total * 0.0
    share = (100.0 * ren / total)[total > 0]
    return share.dropna()


def daily_mean_series(series: pd.Series, local_tz: str = "Europe/Berlin") -> tuple[list, list]:
    """Mean of a tz-aware Series per local calendar day -> (date_strings, values)."""
    if series.empty:
        return [], []
    local = series.tz_convert(local_tz)
    grp = local.groupby(local.index.date).mean()
    return [str(d) for d in grp.index], [round(float(v), 2) if pd.notna(v) else None for v in grp.values]


def monthly_flow_stats(
    net_flow: pd.Series,
    cap_export: pd.Series,
    cap_import: pd.Series,
    local_tz: str = "Europe/Berlin",
    threshold: float = 0.9,
) -> list[dict]:
    """Monthly mean net flow and congestion fraction for one directed border.

    Sign convention (landmine #10): net_flow > 0 means power flows FROM the home
    zone TO the neighbour (export); < 0 means import. Congestion is per-direction:
    an export hour is congested when net_flow >= threshold * cap_export; an import
    hour when -net_flow >= threshold * cap_import. Capacity is often missing for
    some hours/borders — those hours simply don't count as congested (never error).

    All three series are resampled to canonical hourly and grouped by local month.
    Returns [{month, net_flow_mw, congestion_pct, hours}] aligned to months that
    have flow data. net_flow_mw is rounded MW; congestion_pct is 0-100.
    """
    net = to_hourly(net_flow)
    if net.empty:
        return []
    ce = to_hourly(cap_export) if cap_export is not None and not cap_export.empty else pd.Series(dtype=float)
    ci = to_hourly(cap_import) if cap_import is not None and not cap_import.empty else pd.Series(dtype=float)

    df = pd.DataFrame({"net": net})
    df["ce"] = ce.reindex(df.index)
    df["ci"] = ci.reindex(df.index)
    local = df.tz_convert(local_tz)
    # Per-hour congestion flag, per direction; missing capacity -> not congested.
    exp_cong = (local["net"] > 0) & (local["ce"] > 0) & (local["net"] >= threshold * local["ce"])
    imp_cong = (local["net"] < 0) & (local["ci"] > 0) & (-local["net"] >= threshold * local["ci"])
    local = local.assign(congested=(exp_cong | imp_cong))
    months = local.index.tz_localize(None).to_period("M")

    out = []
    for period, grp in local.groupby(months):
        n = len(grp)
        out.append({
            "month": str(period),
            "net_flow_mw": round(float(grp["net"].mean()), 1),
            "congestion_pct": round(100.0 * float(grp["congested"].sum()) / n, 1) if n else 0.0,
            "hours": int(n),
        })
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


# ----------------------------------------------------------------------------
# v10 "Value Layer" metrics — capture price, negative-price episodes, flexibility.
# All pure, tz-aware, resolution-break-safe and DST-safe like the functions above.
# ----------------------------------------------------------------------------

def capture_metrics(
    gen_fuel_hourly_mw: pd.DataFrame,
    price: pd.Series,
    groups: dict | None = None,
    local_tz: str = "Europe/Berlin",
) -> dict:
    """Generation-weighted capture price, baseload, value factor and negative-price
    generation share per renewable group, overall and by local month.

    capture  = Σ(gen·price) / Σ(gen) — the average price a fuel actually earns,
               weighted by how much it produces each hour.
    baseload = the simple (time-weighted) mean price over ALL hours of the period —
               what a flat baseload generator earns. The denominator is the whole
               period, not just generating hours, so solar's daytime cannibalization
               is not hidden.
    value_factor  = capture / baseload (below 1.0 = earns less than average because
                    it produces when everyone else does).
    neg_gen_share = share of the fuel's generation in hours with price < 0, percent.

    Generation and price are resampled to canonical hourly (landmine #3) and aligned
    on their common index. Negative prices are kept (landmine #6). Months are
    local-calendar (landmine #4). Returns {} if there is no overlap.

    `groups` maps an output label to the fuel columns to sum, e.g.
    {"solar": ["Solar"], "wind": ["Wind onshore", "Wind offshore"]} (the default).
    """
    groups = groups or {"solar": ["Solar"], "wind": ["Wind onshore", "Wind offshore"]}
    out: dict = {}
    if gen_fuel_hourly_mw.empty or price.empty:
        return out
    ph = to_hourly(price)
    gh = gen_fuel_hourly_mw
    if getattr(gh.index, "tz", None) is None:
        raise ValueError("generation index must be timezone-aware")
    gh = gh.resample(CANONICAL_FREQ).mean()
    idx = gh.index.intersection(ph.index)
    if len(idx) == 0:
        return out
    ph = ph.reindex(idx)
    gh = gh.reindex(idx)
    months = ph.index.tz_convert(local_tz).tz_localize(None).to_period("M")

    def _stats(gen: pd.Series, pser: pd.Series) -> dict | None:
        baseload = float(pser.mean()) if pser.notna().any() else None
        g = gen.clip(lower=0)
        m = g.notna() & pser.notna() & (g > 0)
        if baseload is None or not bool(m.any()):
            return None
        gg, pp = g[m], pser[m]
        gen_sum = float(gg.sum())
        if gen_sum <= 0:
            return None
        capture = float((gg * pp).sum() / gen_sum)
        neg_share = float(gg[pp < 0].sum() / gen_sum * 100.0)
        vf = capture / baseload if baseload != 0 else None
        return {
            "capture": round(capture, 1),
            "baseload": round(baseload, 1),
            "value_factor": round(vf, 3) if vf is not None else None,
            "neg_gen_share": round(neg_share, 1),
        }

    for label, cols in groups.items():
        present = [c for c in cols if c in gh.columns]
        if not present:
            continue
        gen = gh[present].clip(lower=0).sum(axis=1, min_count=1)
        overall = _stats(gen, ph)
        if overall is None:
            continue
        monthly = []
        for period in pd.unique(months):
            mask = (months == period)
            st = _stats(gen[mask], ph[mask])
            if st is not None:
                monthly.append({"month": str(period), **st})
        out[label] = {**overall, "monthly": monthly}
    return out


def negative_price_episodes(prices: pd.Series, local_tz: str = "Europe/Berlin") -> dict:
    """Promote negative prices to a first-class metric: hours per month, a calendar
    of hours-per-day, and the run-length of consecutive negative hours (episodes).

    Counting is on the canonical hourly grid (landmine #3) — quarter-hourly periods
    are collapsed first, so "hours" means hours, not 15-minute slots. Days/months
    are local-calendar (landmine #4). An episode is a run of consecutive negative
    hours one hour apart (a gap or a non-negative hour ends it).

    Returns {by_month, calendar, episodes:[{length_hours,count}], total_neg_hours,
    longest_episode_h, max_in_one_day}.
    """
    from collections import Counter

    out = {
        "by_month": [], "calendar": [], "episodes": [],
        "total_neg_hours": 0, "longest_episode_h": 0, "max_in_one_day": 0,
    }
    hourly = to_hourly(prices)
    if hourly.empty:
        return out
    local = hourly.tz_convert(local_tz)
    neg = local[local < 0]
    out["total_neg_hours"] = int(len(neg))
    if neg.empty:
        return out

    by_date = neg.groupby(neg.index.date).size()
    out["calendar"] = [{"date": str(d), "neg_hours": int(c)} for d, c in by_date.items()]
    out["max_in_one_day"] = int(by_date.max())

    by_month = neg.groupby(neg.index.tz_localize(None).to_period("M")).size()
    out["by_month"] = [{"month": str(p), "neg_hours": int(c)} for p, c in by_month.items()]

    runs, run = [], 1
    idx = neg.index
    for i in range(1, len(idx)):
        if (idx[i] - idx[i - 1]) == pd.Timedelta(hours=1):
            run += 1
        else:
            runs.append(run)
            run = 1
    runs.append(run)
    out["longest_episode_h"] = int(max(runs))
    out["episodes"] = [
        {"length_hours": int(L), "count": int(c)} for L, c in sorted(Counter(runs).items())
    ]
    return out


def cheapest_n_hours_savings(
    prices: pd.Series,
    kwh_per_day: float = 10.0,
    n: int = 4,
    local_tz: str = "Europe/Berlin",
) -> dict:
    """Annual saving from running a shiftable load (kwh_per_day) in the cheapest
    `n` hours of each local day instead of paying a flat tariff (the period's mean
    price).

    UPPER BOUND (landmine #7): assumes perfect foresight of which hours are
    cheapest, exactly like the battery arbitrage figure. Prices are €/MWh; the load
    is converted kWh -> MWh. Resampled to canonical hourly (landmine #3); days are
    local-calendar (landmine #4); negative prices are kept (landmine #6), so a load
    can be paid to consume. Annualised to 365 days from the observed days.

    Returns {annual_saving_eur, flat_cost_eur, optimized_cost_eur, days, n, kwh_per_day}.
    """
    zero = {
        "annual_saving_eur": 0.0, "flat_cost_eur": 0.0, "optimized_cost_eur": 0.0,
        "days": 0, "n": int(n), "kwh_per_day": round(float(kwh_per_day), 1),
    }
    hourly = to_hourly(prices)
    if hourly.empty:
        return zero
    local = hourly.tz_convert(local_tz)
    flat_price = float(local.mean())  # €/MWh, time-weighted over the period
    mwh_per_day = kwh_per_day / 1000.0
    df = local.to_frame("price")
    df["date"] = df.index.date

    opt_total, days = 0.0, 0
    for _, grp in df.groupby("date"):
        p = grp["price"].sort_values()
        if len(p) < n:
            continue
        opt_total += float(p.iloc[:n].mean()) * mwh_per_day
        days += 1
    if days == 0:
        return zero
    opt_per_day = opt_total / days
    flat_per_day = flat_price * mwh_per_day
    saving_per_day = flat_per_day - opt_per_day
    return {
        "annual_saving_eur": round(saving_per_day * 365.0, 2),
        "flat_cost_eur": round(flat_per_day * 365.0, 2),
        "optimized_cost_eur": round(opt_per_day * 365.0, 2),
        "days": int(days), "n": int(n), "kwh_per_day": round(float(kwh_per_day), 1),
    }
