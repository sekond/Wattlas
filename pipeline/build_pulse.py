"""Build the Pulse view data: average DE-LU day-ahead price by hour of the local
day (weekday vs weekend), written to data/pulse.json.

Run: python pipeline/build_pulse.py            (fetches 12 months from ENTSO-E)
     python pipeline/build_pulse.py --use-cache (offline, reuses the raw-price
                                                 cache shared with build_spread)

See CLAUDE.md for the data landmines. This view reuses the same fetch + cache
plumbing as build_spread so it never hits the API twice for the same window.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone

import pandas as pd

from metrics import price_by_hour_of_day, data_coverage
# Reuse the shared fetch/cache plumbing — one source of truth for the raw series.
from build_spread import (
    DATA_DIR,
    LOCAL_TZ,
    RAW_CACHE,
    ZONE,
    fetch_prices,
    load_cache,
    save_cache,
)

logger = logging.getLogger("wattlas.build_pulse")


def build(prices: pd.Series) -> None:
    """Compute the hour-of-day rhythm and write data/pulse.json."""
    pulse = price_by_hour_of_day(prices, local_tz=LOCAL_TZ)

    # Period reflects complete days only (excludes the partial current day).
    cov_start, cov_end = data_coverage(prices, local_tz=LOCAL_TZ)
    payload = {
        "zone": ZONE,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "period_start": cov_start,
        "period_end": cov_end,
        **pulse,
    }

    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "pulse.json").write_text(json.dumps(payload, indent=2))
    logger.info(
        "wrote data/pulse.json (24 hours; %s to %s)",
        payload["period_start"], payload["period_end"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Pulse view JSON artefact.")
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Re-use the cached raw prices in data/_raw_prices.parquet instead of "
             "hitting the ENTSO-E API (shared with build_spread).",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger.info("pulse build start (use_cache=%s)", args.use_cache)

    end = pd.Timestamp.now(tz=LOCAL_TZ).normalize()
    start = end - pd.DateOffset(months=12)

    if args.use_cache:
        prices = load_cache()
        if prices is None:
            logger.error(
                "no cache at %s — run build_spread once without --use-cache first.", RAW_CACHE
            )
            sys.exit(1)
        logger.info("loaded %d rows from cache %s (no API call)", len(prices), RAW_CACHE)
    else:
        prices = fetch_prices(start, end)
        logger.info("fetched %d rows from ENTSO-E", len(prices))
        save_cache(prices)

    build(prices)
    logger.info("pulse build done")


if __name__ == "__main__":
    main()
