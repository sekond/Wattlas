"""Build per-zone Spread and Pulse data for the consolidated dashboard, computed
OFFLINE from the cached multi-zone day-ahead prices (data/_raw_zone_prices.parquet,
shared with build_divergence). Writes data/spread_by_zone.json and
data/pulse_by_zone.json.

Run: python pipeline/build_zone_views.py   (no API call; needs the zone-price cache)

Why: the standalone Spread/Pulse pages are DE-LU only, but the Phase 3 dashboard
lets the user switch zones. Rather than re-fetch, we reuse the zone-price cache we
already have to produce the same daily-spread and hour-of-day metrics for every
zone. Standalone pages keep using spread.json / pulse.json; the dashboard reads
these per-zone files. Same metric functions, so the numbers match.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import pandas as pd

from metrics import daily_spreads, data_coverage, price_by_hour_of_day, perfect_arbitrage_revenue
from build_spread import DATA_DIR, LOCAL_TZ, BATTERY
from build_divergence import ZONES, CACHE

logger = logging.getLogger("wattlas.build_zone_views")


def _spread_for_zone(prices: pd.Series) -> dict:
    daily = daily_spreads(prices, local_tz=LOCAL_TZ)
    days = [
        {
            "date": str(date),
            "tb1": row["tb1"], "tb2": row["tb2"],
            "negative_hours": int(row["negative_hours"]),
            "complete": int(row["hours_observed"]) >= 23,
        }
        for date, row in daily.iterrows()
    ]
    agg = daily[daily["hours_observed"] >= 23]
    if agg.empty:
        agg = daily
    cov_start, cov_end = data_coverage(prices, local_tz=LOCAL_TZ)
    summary = {
        "period_start": cov_start, "period_end": cov_end,
        "avg_daily_tb1": round(float(agg["tb1"].mean()), 1) if not agg.empty else 0,
        "total_negative_hours": int(agg["negative_hours"].sum()) if not agg.empty else 0,
        # Upper-bound arbitrage figure (CLAUDE.md #7) — always flagged as such.
        "perfect_arbitrage_eur_per_mw": perfect_arbitrage_revenue(
            prices, power_mw=BATTERY["power_mw"], duration_h=BATTERY["duration_h"],
            round_trip_efficiency=BATTERY["round_trip_efficiency"], local_tz=LOCAL_TZ),
        "perfect_arbitrage_is_upper_bound": True,
    }
    return {"days": days, "summary": summary}


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    if not CACHE.exists():
        logger.error("no zone-price cache at %s — run build_divergence.py first.", CACHE)
        raise SystemExit(1)
    zone_prices = pd.read_parquet(CACHE)
    logger.info("loaded zone-price cache %s (%d rows x %d zones)", CACHE, *zone_prices.shape)

    spread_zones, pulse_zones = {}, {}
    for z in ZONES:
        if z not in zone_prices.columns:
            continue
        s = zone_prices[z].dropna()
        if s.empty:
            continue
        spread_zones[z] = _spread_for_zone(s)
        cov_start, cov_end = data_coverage(s, local_tz=LOCAL_TZ)
        pulse_zones[z] = {
            "period_start": cov_start, "period_end": cov_end,
            **price_by_hour_of_day(s, local_tz=LOCAL_TZ),
        }
        logger.info("[%s] spread days=%d", z, len(spread_zones[z]["days"]))

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ref = "DE_LU" if "DE_LU" in spread_zones else next(iter(spread_zones), None)
    period = spread_zones[ref]["summary"] if ref else {"period_start": None, "period_end": None}

    (DATA_DIR / "spread_by_zone.json").write_text(json.dumps({
        "generated_at": generated_at, "zone_default": ref,
        "zones_available": list(spread_zones.keys()),
        "period_start": period["period_start"], "period_end": period["period_end"],
        "zones": spread_zones,
    }, indent=2))
    (DATA_DIR / "pulse_by_zone.json").write_text(json.dumps({
        "generated_at": generated_at, "zone_default": ref,
        "zones_available": list(pulse_zones.keys()),
        "period_start": period["period_start"], "period_end": period["period_end"],
        "zones": pulse_zones,
    }, indent=2))
    logger.info("wrote spread_by_zone.json + pulse_by_zone.json — zones: %s", list(spread_zones.keys()))


if __name__ == "__main__":
    main()
