"""Build per-zone negative-price metrics (v10 slice) OFFLINE from the cached
multi-zone day-ahead prices (data/_raw_zone_prices.parquet, shared with
build_divergence). Writes data/negative_prices.json.

Run: python pipeline/build_negative_prices.py   (no API call; needs the zone-price cache)

Promotes negative prices to a first-class metric: hours per month, a calendar of
hours-per-day, and episode (run-length) duration. Counting is on the canonical
hourly grid (landmine #3); negative prices are never clipped (landmine #6).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import pandas as pd

from metrics import data_coverage, negative_price_episodes
from build_spread import DATA_DIR, LOCAL_TZ
from build_divergence import ZONES, CACHE

logger = logging.getLogger("wattlas.build_negative_prices")


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    if not CACHE.exists():
        logger.error("no zone-price cache at %s — run build_divergence.py first.", CACHE)
        raise SystemExit(1)
    zone_prices = pd.read_parquet(CACHE)
    logger.info("loaded zone-price cache %s (%d rows x %d zones)", CACHE, *zone_prices.shape)

    zones: dict = {}
    for z in ZONES:
        if z not in zone_prices.columns:
            continue
        s = zone_prices[z].dropna()
        if s.empty:
            continue
        ep = negative_price_episodes(s, local_tz=LOCAL_TZ)
        cov_start, cov_end = data_coverage(s, local_tz=LOCAL_TZ)
        zones[z] = {"period_start": cov_start, "period_end": cov_end, **ep}
        logger.info("[%s] neg_hours=%d longest=%dh max/day=%d",
                    z, ep["total_neg_hours"], ep["longest_episode_h"], ep["max_in_one_day"])

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ref = "DE_LU" if "DE_LU" in zones else next(iter(zones), None)
    (DATA_DIR / "negative_prices.json").write_text(json.dumps({
        "generated_at": generated_at,
        "zone_default": ref,
        "zones_available": list(zones.keys()),
        "source": "ENTSO-E day-ahead prices",
        "zones": zones,
    }, indent=2))
    logger.info("wrote negative_prices.json — zones: %s", list(zones.keys()))


if __name__ == "__main__":
    main()
