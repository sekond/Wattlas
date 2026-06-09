"""Build the multi-year history for the Time-investigation layer (Phase 6):
several years of DE-LU daily spread metrics, plus monthly, yearly, seasonal
(month-of-year) aggregates and the year-on-year TB1 change. Writes
data/spread_history.json.

Run: python pipeline/build_history.py             (fetches ~3 years of prices)
     python pipeline/build_history.py --years 3
     python pipeline/build_history.py --use-cache  (offline, parquet cache)

Only PRICES are fetched (cheap, one query type), so the longer history stays
small and static. The history spans more DST transitions and crosses the Oct-2025
hourly->quarter-hourly resolution break — the same resampling discipline applies
(CLAUDE.md landmines #3, #4, #14). Prices are fetched in 6-month chunks because a
multi-year single query is rejected by the gateway.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import pandas as pd

from metrics import daily_spreads, negative_hours_by_month
from build_spread import DATA_DIR, LOCAL_TZ, ZONE

logger = logging.getLogger("wattlas.build_history")

CACHE = DATA_DIR / "_raw_prices_history.parquet"


def fetch_history(start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """Fetch DE-LU day-ahead prices over a multi-year window in 6-month chunks."""
    from entsoe import EntsoePandasClient

    token = os.environ.get("ENTSOE_API_TOKEN")
    if not token:
        sys.exit("ENTSOE_API_TOKEN not set. Copy .env.example to .env and fill it in.")
    client = EntsoePandasClient(api_key=token)

    frames = []
    a = start
    while a < end:
        b = min(a + pd.DateOffset(months=6), end)
        logger.info("fetching %s prices %s -> %s", ZONE, a.date(), b.date())
        try:
            frames.append(client.query_day_ahead_prices(ZONE, start=a, end=b))
        except Exception as exc:  # a missing window must not abort the whole history
            logger.warning("chunk %s-%s failed: %s", a.date(), b.date(), exc)
        a = b
    if not frames:
        return pd.Series(dtype=float)
    s = pd.concat(frames)
    return s[~s.index.duplicated(keep="first")].sort_index()


def build(prices: pd.Series) -> None:
    """Compute daily/monthly/yearly/seasonal aggregates + YoY; write JSON."""
    daily = daily_spreads(prices, local_tz=LOCAL_TZ)
    # Keep only complete days for the aggregates (23/24/25h ok; DST landmine #4).
    daily = daily[daily["hours_observed"] >= 23]
    if daily.empty:
        logger.error("no complete days in history window")
        return

    idx = pd.to_datetime(daily.index)
    tb1 = pd.Series(daily["tb1"].values, index=idx)
    neg = pd.Series(daily["negative_hours"].values, index=idx)

    # Daily series (compact: date, tb1, negative hours) for zoomable charts.
    days = [
        {"date": str(d.date()), "tb1": round(float(t), 1), "neg": int(n)}
        for d, t, n in zip(idx, tb1.values, neg.values)
    ]

    # Monthly + yearly means.
    monthly = [
        {"month": str(p), "avg_tb1": round(float(v), 1)}
        for p, v in tb1.groupby(tb1.index.to_period("M")).mean().items()
    ]
    yearly = [
        {"year": str(p), "avg_tb1": round(float(v), 1),
         "neg_hours": int(neg.groupby(neg.index.to_period("Y")).sum().get(p, 0))}
        for p, v in tb1.groupby(tb1.index.to_period("Y")).mean().items()
    ]

    # Seasonal: month-of-year (1-12) mean TB1 averaged across all years — reveals
    # the summer-solar / winter structure independent of year.
    seasonal = [
        {"month": int(m), "avg_tb1": round(float(v), 1)}
        for m, v in tb1.groupby(tb1.index.month).mean().items()
    ]

    # YoY: last 12 complete months vs the prior 12. None if <24 months of history.
    yoy = None
    end = idx.max()
    last_start = end - pd.DateOffset(months=12)
    prev_start = end - pd.DateOffset(months=24)
    last = tb1[(tb1.index > last_start) & (tb1.index <= end)]
    prev = tb1[(tb1.index > prev_start) & (tb1.index <= last_start)]
    if len(prev) > 30 and prev.mean() != 0:
        yoy = round(100.0 * (last.mean() - prev.mean()) / prev.mean(), 1)

    payload = {
        "zone": ZONE,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "period_start": str(idx.min().date()),
        "period_end": str(idx.max().date()),
        "years_covered": sorted({d.year for d in idx}),
        "days": days,
        "monthly": monthly,
        "yearly": yearly,
        "seasonal": seasonal,                 # month-of-year 1-12
        "negative_hours_by_month": negative_hours_by_month(daily),
        "yoy_tb1_change_pct": yoy,            # last 12mo vs prior 12mo
    }
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "spread_history.json").write_text(json.dumps(payload, indent=2))
    logger.info(
        "wrote data/spread_history.json — %d days, %d years (%s), YoY TB1 %s%%",
        len(days), len(payload["years_covered"]), payload["years_covered"],
        yoy if yoy is not None else "n/a",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the multi-year spread history JSON.")
    parser.add_argument("--years", type=int, default=3, help="Years of history to fetch (default 3).")
    parser.add_argument("--use-cache", action="store_true",
                        help="Re-use data/_raw_prices_history.parquet instead of the API.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    logger.info("history build start (use_cache=%s, years=%d)", args.use_cache, args.years)

    end = pd.Timestamp.now(tz=LOCAL_TZ).normalize()
    start = end - pd.DateOffset(years=args.years)

    if args.use_cache:
        if not CACHE.exists():
            logger.error("no cache at %s — run once without --use-cache first.", CACHE)
            sys.exit(1)
        prices = pd.read_parquet(CACHE)["price"]
        logger.info("loaded %d rows from cache", len(prices))
    else:
        prices = fetch_history(start, end)
        if prices.empty:
            logger.error("no price data fetched")
            sys.exit(1)
        DATA_DIR.mkdir(exist_ok=True)
        prices.to_frame("price").to_parquet(CACHE)
        logger.info("fetched + cached %d rows", len(prices))

    build(prices)
    logger.info("history build done")


if __name__ == "__main__":
    main()
