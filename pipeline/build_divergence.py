"""Build the Divergence view data: monthly mean day-ahead prices for DE-LU and
its neighbouring bidding zones, plus the DE-LU vs FR spread. Writes
data/divergence.json.

Run: python pipeline/build_divergence.py            (fetches 12 months)
     python pipeline/build_divergence.py --use-cache (offline, parquet cache)

See CLAUDE.md for the data landmines. Bidding zones, not countries (landmine #2):
we compare DE_LU against its coupled neighbours.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import pandas as pd

from metrics import monthly_means
from build_spread import DATA_DIR, LOCAL_TZ

logger = logging.getLogger("wattlas.build_divergence")

# DE_LU plus its day-ahead-coupled neighbours (all confirmed to return data).
ZONES = ["DE_LU", "FR", "NL", "BE", "PL", "AT"]
CACHE = DATA_DIR / "_raw_zone_prices.parquet"


def fetch_zone_prices(start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Fetch day-ahead prices for every zone into one DataFrame (cols = zones)."""
    from entsoe import EntsoePandasClient

    token = os.environ.get("ENTSOE_API_TOKEN")
    if not token:
        sys.exit("ENTSOE_API_TOKEN not set. Copy .env.example to .env and fill it in.")
    client = EntsoePandasClient(api_key=token)

    cols = {}
    for zone in ZONES:
        logger.info("fetching day-ahead prices for %s", zone)
        cols[zone] = client.query_day_ahead_prices(zone, start=start, end=end)
    # Each zone Series is tz-aware; align on the union of timestamps.
    return pd.DataFrame(cols)


def build(zone_prices: pd.DataFrame) -> None:
    """Compute monthly means per zone + DE-FR spread and write divergence.json."""
    # monthly_means resamples each zone to hourly and groups by local month.
    series = {z: monthly_means(zone_prices[z].dropna(), local_tz=LOCAL_TZ) for z in ZONES}

    # Canonical month axis from DE_LU (the reference zone).
    months = [m["month"] for m in series["DE_LU"]]
    means = {z: {m["month"]: m["mean"] for m in series[z]} for z in ZONES}
    aligned = {z: [means[z].get(mo) for mo in months] for z in ZONES}

    # DE-LU minus FR per month (the headline divergence: nuclear vs renewables).
    de_fr_spread = [
        None if (aligned["DE_LU"][i] is None or aligned["FR"][i] is None)
        else round(aligned["DE_LU"][i] - aligned["FR"][i], 2)
        for i in range(len(months))
    ]

    idx_local = zone_prices.index.tz_convert(LOCAL_TZ)
    payload = {
        "zone": "DE_LU",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "period_start": str(idx_local.min().date()),
        "period_end": str(idx_local.max().date()),
        "zones": ZONES,
        "months": months,
        "series": aligned,
        "de_fr_spread": de_fr_spread,
    }
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "divergence.json").write_text(json.dumps(payload, indent=2))
    logger.info("wrote data/divergence.json (%d zones, %d months)", len(ZONES), len(months))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Divergence view JSON artefact.")
    parser.add_argument("--use-cache", action="store_true",
                        help="Re-use data/_raw_zone_prices.parquet instead of the API.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    logger.info("divergence build start (use_cache=%s)", args.use_cache)

    end = pd.Timestamp.now(tz=LOCAL_TZ).normalize()
    start = end - pd.DateOffset(months=12)

    if args.use_cache:
        if not CACHE.exists():
            logger.error("no cache at %s — run once without --use-cache first.", CACHE)
            sys.exit(1)
        zone_prices = pd.read_parquet(CACHE)
        logger.info("loaded %d rows x %d zones from cache (no API call)", *zone_prices.shape)
    else:
        zone_prices = fetch_zone_prices(start, end)
        zone_prices.to_parquet(CACHE)
        logger.info("fetched + cached %d rows x %d zones", *zone_prices.shape)

    build(zone_prices)
    logger.info("divergence build done")


if __name__ == "__main__":
    main()
