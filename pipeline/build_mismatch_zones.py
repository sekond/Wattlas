"""Build per-zone Mismatch data for the dashboard: residual-load and total-demand
hour-of-day profiles for DE-LU and its neighbours. Writes data/mismatch_by_zone.json.

Run: python pipeline/build_mismatch_zones.py            (fetches load per zone)
     python pipeline/build_mismatch_zones.py --use-cache (offline, parquet caches)

Residual load = demand − (wind + solar): the demand left for conventional plants
and batteries. Wind+solar comes FREE from the per-zone generation caches that
build_mix already wrote (_raw_generation_{zone}.parquet) — so this builder only
fetches the missing piece, per-zone LOAD (query_load, cheap). It therefore must
run AFTER build_mix in the pipeline (same dependency as build_carbon).

The standalone Mismatch page keeps using the DE-LU-only build_mismatch.py /
mismatch.json; this is the multi-zone artefact the dashboard reads, mirroring the
spread_by_zone / pulse_by_zone pattern. See CLAUDE.md landmines: hourly resampling
(#3), Europe/Berlin grouping (#4 — all these zones are Central European), gaps
stay gaps (#8). Zones are bidding zones, not countries (#2).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import pandas as pd

from metrics import to_hourly, vre_hourly_mw, mean_profile_by_hour, data_coverage
from build_spread import DATA_DIR, LOCAL_TZ
from build_mix import ZONES, cache_path as gen_cache_path

logger = logging.getLogger("wattlas.build_mismatch_zones")


def load_cache_path(zone: str):
    return DATA_DIR / f"_raw_load_{zone}.parquet"


def fetch_load(zone: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """Actual total load for a zone (MW, tz-aware). Cached per zone for offline re-runs."""
    from entsoe_client import make_entsoe_client  # retrying client (transient-5xx safe)

    token = os.environ.get("ENTSOE_API_TOKEN")
    if not token:
        sys.exit("ENTSOE_API_TOKEN not set. Copy .env.example to .env and fill it in.")
    client = make_entsoe_client(token)
    logger.info("[%s] fetching load", zone)
    load = client.query_load(zone, start=start, end=end)
    # query_load returns a DataFrame with an 'Actual Load' column (or a Series).
    return load["Actual Load"] if hasattr(load, "columns") else load


def zone_profiles(gen: pd.DataFrame, load_mw: pd.Series) -> tuple[list, list]:
    """Residual-load and total-demand hour-of-day profiles (GW) for one zone.

    residual = load − (wind + solar), aligned in UTC then grouped by local hour.
    Both are hourly-resampled first (landmine #3). Residual is NOT clipped — it
    can go negative when renewables exceed demand (a real, interesting signal).
    """
    vre_mw = vre_hourly_mw(gen)                          # already hourly, UTC index
    load_hourly = to_hourly(load_mw).tz_convert("UTC")   # align both in UTC
    residual_gw = ((load_hourly - vre_mw) / 1000.0).dropna()
    total_gw = (load_hourly / 1000.0).dropna()
    residual_profile = mean_profile_by_hour(residual_gw, local_tz=LOCAL_TZ)
    total_profile = mean_profile_by_hour(total_gw, local_tz=LOCAL_TZ)
    return residual_profile, total_profile


def build(use_cache: bool, start: pd.Timestamp, end: pd.Timestamp) -> None:
    zones_out: dict[str, dict] = {}
    for zone in ZONES:
        gpath = gen_cache_path(zone)
        if not gpath.exists():
            logger.warning("[%s] no generation cache (%s) — run build_mix first; skipping", zone, gpath.name)
            continue
        gen = pd.read_parquet(gpath)

        lpath = load_cache_path(zone)
        if use_cache:
            if not lpath.exists():
                logger.warning("[%s] no load cache — skipping", zone)
                continue
            load_mw = pd.read_parquet(lpath)["load"]
        else:
            try:
                load_mw = fetch_load(zone, start, end)
            except Exception as exc:  # a zone without load must not kill the rest (#8)
                logger.warning("[%s] load fetch failed: %s — skipping", zone, type(exc).__name__)
                continue
            DATA_DIR.mkdir(exist_ok=True)
            load_mw.to_frame("load").to_parquet(lpath)

        residual_profile, total_profile = zone_profiles(gen, load_mw)
        cov_start, cov_end = data_coverage(load_mw.dropna(), local_tz=LOCAL_TZ)
        zones_out[zone] = {
            "period_start": cov_start,
            "period_end": cov_end,
            "hours": list(range(24)),
            "residual_load_gw": residual_profile,   # demand − wind − solar, GW; may be negative
            "total_load_gw": total_profile,         # total actual load, GW
        }
        pts = [(h, v) for h, v in enumerate(residual_profile) if v is not None]
        if pts:
            peak = max(pts, key=lambda x: x[1])
            logger.info("[%s] residual peak %02d:00 (%.1f GW)", zone, peak[0], peak[1])

    ref = "DE_LU" if "DE_LU" in zones_out else (next(iter(zones_out)) if zones_out else None)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "zone_default": ref,
        "zones_available": list(zones_out.keys()),
        "period_start": zones_out[ref]["period_start"] if ref else None,
        "period_end": zones_out[ref]["period_end"] if ref else None,
        "zones": zones_out,
    }
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "mismatch_by_zone.json").write_text(json.dumps(payload, indent=2))
    logger.info("wrote data/mismatch_by_zone.json — zones: %s", list(zones_out.keys()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the per-zone Mismatch JSON artefact.")
    parser.add_argument("--use-cache", action="store_true",
                        help="Re-use per-zone load caches + generation caches instead of the API.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    logger.info("mismatch-by-zone build start (use_cache=%s)", args.use_cache)

    end = pd.Timestamp.now(tz=LOCAL_TZ).normalize()
    start = end - pd.DateOffset(months=12)
    build(args.use_cache, start, end)
    logger.info("mismatch-by-zone build done")


if __name__ == "__main__":
    main()
