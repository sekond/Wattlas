"""Build the Mismatch view data: wind+solar share of generation vs electricity
demand, by hour of the local day, for DE-LU. Writes data/mismatch.json.

Run: python pipeline/build_mismatch.py            (fetches 12 months)
     python pipeline/build_mismatch.py --use-cache (offline, parquet cache)

The story: variable renewables (wind+solar) peak midday while demand peaks in the
morning and evening — a timing mismatch. We report the *wind+solar share of
generation* (not all renewables) because those two are what drive the mismatch.

See CLAUDE.md for the data landmines (resolution resampling, local-tz grouping).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import pandas as pd

from metrics import mean_profile_by_hour
from build_spread import DATA_DIR, LOCAL_TZ

logger = logging.getLogger("wattlas.build_mismatch")

# Variable renewables that drive the timing mismatch.
RENEWABLE_TYPES = {"Solar", "Wind Onshore", "Wind Offshore"}
CACHE = DATA_DIR / "_raw_mismatch.parquet"


def _ptype(col) -> str:
    """Production-type name from an entsoe generation column (tuple or string)."""
    return col[0] if isinstance(col, tuple) else col


def _is_aggregated(col) -> bool:
    """True for 'Actual Aggregated' (generation) columns, not 'Actual Consumption'."""
    return (col[-1] if isinstance(col, tuple) else "Actual Aggregated") == "Actual Aggregated"


def _reduce_chunk(gen: pd.DataFrame, load) -> pd.DataFrame:
    """Reduce one window's generation + load to renewable_mw/total_mw/load_mw."""
    agg_cols = [c for c in gen.columns if _is_aggregated(c)]
    total = gen[agg_cols].sum(axis=1)
    ren_cols = [c for c in agg_cols if _ptype(c) in RENEWABLE_TYPES]
    renewable = gen[ren_cols].sum(axis=1)
    load_s = load["Actual Load"] if hasattr(load, "columns") else load
    return pd.DataFrame({"renewable_mw": renewable, "total_mw": total, "load_mw": load_s})


def fetch_components(start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Fetch generation + load and reduce to renewable_mw / total_mw / load_mw.

    Reducing here keeps the cache small and avoids parquet MultiIndex issues.
    Generation is fetched in MONTHLY CHUNKS: a full-year generation query (A75)
    times out at the ENTSO-E gateway (504), so we page through a month at a time
    and concatenate.
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
        logger.info("fetching generation + load %s -> %s", a.date(), b.date())
        gen = client.query_generation("DE_LU", start=a, end=b, psr_type=None)
        load = client.query_load("DE_LU", start=a, end=b)
        frames.append(_reduce_chunk(gen, load))
        a = b

    df = pd.concat(frames)
    # Drop any duplicate timestamps at chunk boundaries (keep first).
    df = df[~df.index.duplicated(keep="first")].sort_index()
    return df


def build(comp: pd.DataFrame) -> None:
    """Compute hour-of-day profiles for renewable share and demand; write JSON."""
    # Share per timestamp where there is generation, then averaged by hour.
    mask = comp["total_mw"] > 0
    share = comp.loc[mask, "renewable_mw"] / comp.loc[mask, "total_mw"] * 100.0
    load_gw = (comp["load_mw"] / 1000.0).dropna()  # MW -> GW for readability

    share_profile = mean_profile_by_hour(share, local_tz=LOCAL_TZ)
    demand_profile = mean_profile_by_hour(load_gw, local_tz=LOCAL_TZ)

    idx_local = comp.index.tz_convert(LOCAL_TZ)
    payload = {
        "zone": "DE_LU",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "period_start": str(idx_local.min().date()),
        "period_end": str(idx_local.max().date()),
        "hours": list(range(24)),
        "renewable_share_pct": share_profile,  # wind+solar as % of generation
        "demand_gw": demand_profile,
    }
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "mismatch.json").write_text(json.dumps(payload, indent=2))
    logger.info("wrote data/mismatch.json (24-hour profiles)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Mismatch view JSON artefact.")
    parser.add_argument("--use-cache", action="store_true",
                        help="Re-use data/_raw_mismatch.parquet instead of the API.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    logger.info("mismatch build start (use_cache=%s)", args.use_cache)

    end = pd.Timestamp.now(tz=LOCAL_TZ).normalize()
    start = end - pd.DateOffset(months=12)

    if args.use_cache:
        if not CACHE.exists():
            logger.error("no cache at %s — run once without --use-cache first.", CACHE)
            sys.exit(1)
        comp = pd.read_parquet(CACHE)
        logger.info("loaded %d rows from cache (no API call)", len(comp))
    else:
        comp = fetch_components(start, end)
        comp.to_parquet(CACHE)
        logger.info("fetched + cached %d rows", len(comp))

    build(comp)
    logger.info("mismatch build done")


if __name__ == "__main__":
    main()
