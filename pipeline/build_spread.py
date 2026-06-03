"""Build the Spread view data: fetch DE-LU day-ahead prices, compute metrics,
write data/spread.json and data/spread_summary.json.

Run: python pipeline/build_spread.py
Offline re-run from the cached raw prices (no API call):
     python pipeline/build_spread.py --use-cache

Requires ENTSOE_API_TOKEN in the environment (see .env.example). Free token
from your ENTSO-E account: https://transparency.entsoe.eu

See CLAUDE.md for the data landmines this script is built around.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from metrics import (
    daily_spreads,
    data_coverage,
    negative_hours_by_month,
    perfect_arbitrage_revenue,
)

ZONE = "DE_LU"
LOCAL_TZ = "Europe/Berlin"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
# Raw fetched prices are cached here so re-runs (--use-cache) don't re-hit the
# API. Gitignored: it is a local convenience artefact, not committed data.
RAW_CACHE = DATA_DIR / "_raw_prices.parquet"

logger = logging.getLogger("wattlas.build_spread")

# v1 battery assumptions for the UPPER-BOUND arbitrage figure (CLAUDE.md #7)
BATTERY = {
    "power_mw": 1,
    "duration_h": 2,
    "round_trip_efficiency": 1.0,
    "foresight": "perfect",
}


def fetch_prices(start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """Fetch day-ahead prices for ZONE between start and end (tz-aware Series).

    Isolated so it can be swapped for a fixture in tests. Imported lazily so the
    rest of the module (and the unit tests) don't require the entsoe package.
    """
    from entsoe import EntsoePandasClient  # noqa: WPS433 (lazy import on purpose)

    token = os.environ.get("ENTSOE_API_TOKEN")
    if not token:
        sys.exit("ENTSOE_API_TOKEN not set. Copy .env.example to .env and fill it in.")

    client = EntsoePandasClient(api_key=token)
    logger.info("fetching %s day-ahead prices %s -> %s", ZONE, start.date(), end.date())
    return client.query_day_ahead_prices(ZONE, start=start, end=end)


def _infer_resolution(prices: pd.Series) -> str:
    """Human-readable summary of the native sampling resolution(s) present.

    The German market switched hourly -> quarter-hourly in Oct 2025 (landmine
    #3), so a 12-month series legitimately mixes resolutions. We log this so the
    resampling step is observable, not silent.
    """
    if len(prices) < 3:
        return "unknown"
    deltas = prices.index.to_series().diff().dropna()
    if deltas.empty:
        return "unknown"
    counts = deltas.value_counts()
    parts = [f"{int(d.total_seconds() // 60)}min x{n}" for d, n in counts.items()]
    return "mixed[" + ", ".join(parts) + "]" if len(counts) > 1 else parts[0]


def save_cache(prices: pd.Series) -> None:
    """Persist the raw (pre-resample) price Series to parquet for offline re-runs."""
    DATA_DIR.mkdir(exist_ok=True)
    # to_frame keeps the tz-aware DatetimeIndex; pyarrow preserves the timezone.
    prices.to_frame("price").to_parquet(RAW_CACHE)
    logger.info("cached %d raw rows -> %s", len(prices), RAW_CACHE)


def load_cache() -> pd.Series | None:
    """Load the cached raw price Series, or None if no cache exists."""
    if not RAW_CACHE.exists():
        return None
    df = pd.read_parquet(RAW_CACHE)
    return df["price"]


def build(start: pd.Timestamp, end: pd.Timestamp, prices: pd.Series | None = None) -> None:
    """Compute metrics and write the JSON artefacts.

    `prices` may be injected (tests / cache); otherwise fetched from ENTSO-E.
    """
    if prices is None:
        prices = fetch_prices(start, end)

    logger.info("input rows: %d | native resolution: %s", len(prices), _infer_resolution(prices))

    daily = daily_spreads(prices, local_tz=LOCAL_TZ)
    logger.info("resampled to hourly and computed metrics for %d calendar days", len(daily))

    # Flag incomplete days: anything with fewer than 23 hours is suspect
    # (a normal short DST day has 23). We mark <23 as incomplete data gaps but
    # KEEP them in the output (complete: false) rather than dropping them, so the
    # frontend can render gaps honestly (landmine #8).
    days_payload = []
    missing_days = []
    for date, row in daily.iterrows():
        complete = int(row["hours_observed"]) >= 23
        if not complete:
            missing_days.append(str(date))
        days_payload.append(
            {
                "date": str(date),
                "tb1": row["tb1"],
                "tb2": row["tb2"],
                "min_price": row["min_price"],
                "max_price": row["max_price"],
                "mean_price": row["mean_price"],
                "negative_hours": int(row["negative_hours"]),
                "hours_observed": int(row["hours_observed"]),
                "complete": complete,
            }
        )

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    spread = {
        "zone": ZONE,
        "generated_at": generated_at,
        "days": days_payload,
    }

    # Summary. Headline figures are computed over COMPLETE days only, so a
    # partial day (e.g. today, or a data gap) can't skew the average or totals.
    # The incomplete days are still present in spread.json (complete: false) and
    # listed in missing_days; they're just excluded from the aggregates.
    agg = daily[daily["hours_observed"] >= 23]
    if agg.empty:  # nothing complete yet — fall back so we still emit numbers
        agg = daily
    if not daily.empty:
        widest_idx = agg["tb1"].idxmax()
        # Report coverage over COMPLETE days only, so the partial current day
        # doesn't make the period claim data we don't have.
        cov_start, cov_end = data_coverage(prices, local_tz=LOCAL_TZ)
        summary = {
            "zone": ZONE,
            "period_start": cov_start,
            "period_end": cov_end,
            "avg_daily_tb1": round(float(agg["tb1"].mean()), 1),
            "widest_day": {
                "date": str(widest_idx),
                "tb1": float(agg.loc[widest_idx, "tb1"]),
            },
            "total_negative_hours": int(agg["negative_hours"].sum()),
            "negative_hours_by_month": negative_hours_by_month(agg),
            "yoy_tb1_change_pct": None,  # populate when >2 years of data is fetched
            "perfect_arbitrage_eur_per_mw": perfect_arbitrage_revenue(
                prices,
                power_mw=BATTERY["power_mw"],
                duration_h=BATTERY["duration_h"],
                round_trip_efficiency=BATTERY["round_trip_efficiency"],
                local_tz=LOCAL_TZ,
            ),
            "perfect_arbitrage_is_upper_bound": True,
            "battery_assumptions": BATTERY,
            "missing_days": missing_days,
        }
    else:
        summary = {
            "zone": ZONE,
            "period_start": None,
            "period_end": None,
            "avg_daily_tb1": 0,
            "widest_day": None,
            "total_negative_hours": 0,
            "negative_hours_by_month": [],
            "yoy_tb1_change_pct": None,
            "perfect_arbitrage_eur_per_mw": 0,
            "perfect_arbitrage_is_upper_bound": True,
            "battery_assumptions": BATTERY,
            "missing_days": [],
        }

    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "spread.json").write_text(json.dumps(spread, indent=2))
    (DATA_DIR / "spread_summary.json").write_text(json.dumps(summary, indent=2))
    logger.info(
        "wrote %d days to data/spread.json (%d incomplete: %s)",
        len(days_payload), len(missing_days), missing_days or "none",
    )
    logger.info("wrote summary to data/spread_summary.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Spread view JSON artefacts.")
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Re-use the cached raw prices in data/_raw_prices.parquet instead of "
             "hitting the ENTSO-E API. Run once without this flag to populate the cache.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger.info("build start (use_cache=%s)", args.use_cache)

    # Default: last ~12 months ending today, in local tz.
    end = pd.Timestamp.now(tz=LOCAL_TZ).normalize()
    start = end - pd.DateOffset(months=12)

    if args.use_cache:
        prices = load_cache()
        if prices is None:
            logger.error(
                "no cache at %s — run once without --use-cache to populate it.", RAW_CACHE
            )
            sys.exit(1)
        logger.info("loaded %d rows from cache %s (no API call)", len(prices), RAW_CACHE)
    else:
        prices = fetch_prices(start, end)
        logger.info("fetched %d rows from ENTSO-E", len(prices))
        save_cache(prices)

    build(start, end, prices=prices)
    logger.info("build done")


if __name__ == "__main__":
    main()
