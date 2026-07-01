"""Build the Mismatch view data: residual load by hour of the local day, for
DE-LU. Writes data/mismatch.json.

Run: python pipeline/build_mismatch.py            (fetches 12 months)
     python pipeline/build_mismatch.py --use-cache (offline, parquet cache)

The story: RESIDUAL LOAD = total demand minus wind+solar generation — the demand
that conventional plants and batteries must actually cover. It dips midday when
solar is abundant and peaks in the evening when solar vanishes but people are
home. That evening residual-load peak is what drives the evening price spike seen
in the Pulse view (~19:00). Residual load can legitimately go negative when
renewables exceed domestic load — we never clip it (landmine #6).

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

from metrics import mean_profile_by_hour, data_coverage
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
    from entsoe_client import make_entsoe_client  # retrying client (transient-5xx safe)

    token = os.environ.get("ENTSOE_API_TOKEN")
    if not token:
        sys.exit("ENTSOE_API_TOKEN not set. Copy .env.example to .env and fill it in.")
    client = make_entsoe_client(token)
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
    """Compute hour-of-day residual-load + total-load profiles; write JSON.

    Residual load = total load - wind+solar generation, per timestamp, in GW.
    It can legitimately be negative when renewables exceed domestic load
    (landmine #6) — never clipped. dropna aligns load and generation.
    """
    residual_gw = ((comp["load_mw"] - comp["renewable_mw"]) / 1000.0).dropna()
    total_load_gw = (comp["load_mw"] / 1000.0).dropna()  # MW -> GW

    residual_profile = mean_profile_by_hour(residual_gw, local_tz=LOCAL_TZ)
    total_profile = mean_profile_by_hour(total_load_gw, local_tz=LOCAL_TZ)

    # Period reflects complete days only (excludes the partial current day).
    cov_start, cov_end = data_coverage(comp["load_mw"].dropna(), local_tz=LOCAL_TZ)
    payload = {
        "zone": "DE_LU",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "period_start": cov_start,
        "period_end": cov_end,
        "hours": list(range(24)),
        "residual_load_gw": residual_profile,  # total load - (wind+solar), GW; may be negative
        "total_load_gw": total_profile,        # total actual load, GW
    }
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "mismatch.json").write_text(json.dumps(payload, indent=2))

    # Console confirmation: the peak should land in the evening, aligning with the
    # Pulse price peak (~19:00) — that alignment is the correctness check.
    pts = [(h, v) for h, v in enumerate(residual_profile) if v is not None]
    peak = max(pts, key=lambda x: x[1])
    trough = min(pts, key=lambda x: x[1])
    logger.info(
        "wrote data/mismatch.json — residual-load peak %02d:00 (%.1f GW), trough %02d:00 (%.1f GW)",
        peak[0], peak[1], trough[0], trough[1],
    )


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
