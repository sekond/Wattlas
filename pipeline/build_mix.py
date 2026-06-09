"""Build the Mix view data: full generation breakdown by fuel type for DE-LU and
its neighbour zones, both as an average hour-of-day profile and as a daily series.
Writes data/mix.json.

Run: python pipeline/build_mix.py            (fetches 12 months for all zones)
     python pipeline/build_mix.py --use-cache (offline, per-zone parquet cache)
     python pipeline/build_mix.py --zones DE_LU FR   (subset)

The story (Phase 1): France's flat nuclear baseload vs Germany's volatile
wind+solar with gas/coal fill. A stacked area of the fuel mix makes the
structural contrast between two zones obvious at a glance.

Each zone's collapsed hourly fuel frame (canonical fuels, MW) is cached to its
own parquet — small and MultiIndex-free — and is ALSO the input build_carbon.py
reads, so generation is fetched once and reused. See CLAUDE.md landmines:
generation-by-type is gappy (#9); resample hourly (#3); group local-tz (#4);
zones are bidding zones, not countries (#2).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import pandas as pd

from metrics import collapse_generation, daily_generation_gw, fuel_profile_by_hour_gw, data_coverage
from build_spread import DATA_DIR, LOCAL_TZ
from fuels import FUEL_ORDER

logger = logging.getLogger("wattlas.build_mix")

# DE_LU plus its day-ahead-coupled neighbours (same set as Divergence).
ZONES = ["DE_LU", "FR", "NL", "BE", "PL", "AT"]


def cache_path(zone: str):
    """Per-zone collapsed-generation cache (canonical fuels, hourly MW)."""
    return DATA_DIR / f"_raw_generation_{zone}.parquet"


def fetch_generation(zone: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Fetch generation-per-type for a zone and collapse to canonical fuels (MW).

    Generation is fetched in MONTHLY CHUNKS: a full-year A75 query times out at
    the ENTSO-E gateway (504), so we page a month at a time (same approach as
    build_mismatch). Each chunk is collapsed immediately to keep memory + cache
    small and avoid parquet MultiIndex issues.
    """
    from entsoe import EntsoePandasClient

    token = os.environ.get("ENTSOE_API_TOKEN")
    if not token:
        sys.exit("ENTSOE_API_TOKEN not set. Copy .env.example to .env and fill it in.")
    client = EntsoePandasClient(api_key=token)

    frames = []
    a = start
    while a < end:
        b = min(a + pd.DateOffset(months=1), end)
        logger.info("[%s] fetching generation %s -> %s", zone, a.date(), b.date())
        try:
            gen = client.query_generation(zone, start=a, end=b, psr_type=None)
            frames.append(collapse_generation(gen, local_tz=LOCAL_TZ))
        except Exception as exc:  # a missing chunk must not kill the whole zone (#8)
            logger.warning("[%s] chunk %s-%s failed: %s", zone, a.date(), b.date(), exc)
        a = b

    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames)
    df = df[~df.index.duplicated(keep="first")].sort_index()
    # Re-order columns canonically across the concatenated chunks.
    return df[[f for f in FUEL_ORDER if f in df.columns]]


def load_zone(zone: str, start: pd.Timestamp, end: pd.Timestamp, use_cache: bool) -> pd.DataFrame:
    """Return a zone's collapsed hourly fuel frame, from cache or the API."""
    cache = cache_path(zone)
    if use_cache:
        if not cache.exists():
            logger.warning("[%s] no cache at %s — skipping", zone, cache)
            return pd.DataFrame()
        df = pd.read_parquet(cache)
        logger.info("[%s] loaded %d rows from cache", zone, len(df))
        return df
    df = fetch_generation(zone, start, end)
    if not df.empty:
        DATA_DIR.mkdir(exist_ok=True)
        df.to_parquet(cache)
        logger.info("[%s] fetched + cached %d rows, fuels: %s", zone, len(df), list(df.columns))
    return df


def build(zone_frames: dict[str, pd.DataFrame]) -> None:
    """Compute per-zone fuel profiles + daily series and write data/mix.json."""
    present_fuels: set[str] = set()
    zones_out: dict[str, dict] = {}

    for zone, df in zone_frames.items():
        if df.empty:
            logger.warning("[%s] no usable generation data", zone)
            continue
        present_fuels.update(df.columns)
        profile = fuel_profile_by_hour_gw(df, local_tz=LOCAL_TZ)
        days, daily = daily_generation_gw(df, local_tz=LOCAL_TZ)
        # MW->the data_coverage helper expects a Series; use total generation.
        total = df.sum(axis=1, min_count=1).dropna()
        cov_start, cov_end = data_coverage(total, local_tz=LOCAL_TZ, min_hours=20)
        zones_out[zone] = {
            "period_start": cov_start,
            "period_end": cov_end,
            "hours": list(range(24)),
            "profile_gw": profile,   # {fuel: [24]} mean GW per local hour
            "days": days,
            "daily_gw": daily,       # {fuel: [...]} mean GW per local day
        }
        logger.info("[%s] %d fuels, %d days", zone, len(profile), len(days))

    # Canonical fuel list restricted to those actually present anywhere.
    fuels = [f for f in FUEL_ORDER if f in present_fuels]
    # Overall period from DE_LU when available, else the first zone with data.
    ref = "DE_LU" if "DE_LU" in zones_out else (next(iter(zones_out)) if zones_out else None)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "zone_default": "DE_LU" if "DE_LU" in zones_out else ref,
        "zones_available": list(zones_out.keys()),
        "fuels": fuels,
        "period_start": zones_out[ref]["period_start"] if ref else None,
        "period_end": zones_out[ref]["period_end"] if ref else None,
        "zones": zones_out,
    }
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "mix.json").write_text(json.dumps(payload, indent=2))
    logger.info(
        "wrote data/mix.json — zones with data: %s; fuels: %s",
        list(zones_out.keys()), fuels,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Mix view JSON artefact.")
    parser.add_argument("--use-cache", action="store_true",
                        help="Re-use per-zone data/_raw_generation_*.parquet instead of the API.")
    parser.add_argument("--zones", nargs="+", default=ZONES,
                        help="Subset of zones to build (default: all).")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    logger.info("mix build start (use_cache=%s, zones=%s)", args.use_cache, args.zones)

    end = pd.Timestamp.now(tz=LOCAL_TZ).normalize()
    start = end - pd.DateOffset(months=12)

    zone_frames = {z: load_zone(z, start, end, args.use_cache) for z in args.zones}
    build(zone_frames)
    logger.info("mix build done")


if __name__ == "__main__":
    main()
