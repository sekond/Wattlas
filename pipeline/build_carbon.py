"""Build the Carbon-intensity data: production-based grid carbon intensity
(gCO2eq/kWh) by zone, as an hour-of-day profile and a daily series, plus the
matching renewable share. Writes data/carbon.json.

Run: python pipeline/build_carbon.py            (reuses the generation cache)
     python pipeline/build_carbon.py --zones DE_LU FR

This is NOT a new external source. Carbon intensity is COMPUTED from the ENTSO-E
generation mix that build_mix.py already fetches (cached per zone as
_raw_generation_{zone}.parquet), using fixed per-fuel emission factors. That
keeps the app static and gives one consistent methodology across every zone.

Methodology (CLAUDE.md landmine #12): production-based — emissions are attributed
to generation INSIDE the zone, ignoring imports/exports. Factors are IPCC AR5
lifecycle medians (gCO2eq/kWh), lifecycle not combustion-only. Pumped-storage
discharge is excluded as a storage carrier. See pipeline/fuels.py for the table.

Sanity check the build prints: carbon intensity should fall as renewable share
rises, and France (nuclear) should read far lower than coal-heavy hours.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone

import pandas as pd

from metrics import (
    carbon_intensity_hourly,
    daily_mean_series,
    data_coverage,
    mean_profile_by_hour,
    renewable_share_hourly,
)
from build_spread import DATA_DIR, LOCAL_TZ
from build_mix import ZONES, cache_path
from fuels import EMISSION_FACTORS_GCO2_KWH, CARBON_METHODOLOGY

logger = logging.getLogger("wattlas.build_carbon")

# Renewables for the share metric (mirror of frontend RENEWABLE_FUELS).
RENEWABLE_FUELS = {
    "Biomass", "Geothermal", "Hydro", "Wind offshore", "Wind onshore",
    "Solar", "Other renewable",
}


def build(zone_frames: dict[str, pd.DataFrame]) -> None:
    """Compute carbon intensity + renewable share per zone; write carbon.json."""
    zones_out: dict[str, dict] = {}
    for zone, df in zone_frames.items():
        if df.empty:
            logger.warning("[%s] no generation cache — run build_mix.py first", zone)
            continue
        ci = carbon_intensity_hourly(df, EMISSION_FACTORS_GCO2_KWH)
        share = renewable_share_hourly(df, RENEWABLE_FUELS)
        if ci.empty:
            logger.warning("[%s] no usable carbon series", zone)
            continue

        days_ci, daily_ci = daily_mean_series(ci, local_tz=LOCAL_TZ)
        days_sh, daily_sh = daily_mean_series(share, local_tz=LOCAL_TZ)
        cov_start, cov_end = data_coverage(ci, local_tz=LOCAL_TZ, min_hours=20)
        # Round intensities to whole gCO2/kWh in the profile for display honesty.
        intensity_profile = [
            None if v is None else round(v) for v in mean_profile_by_hour(ci, local_tz=LOCAL_TZ)
        ]
        zones_out[zone] = {
            "period_start": cov_start,
            "period_end": cov_end,
            "hours": list(range(24)),
            "intensity_profile": intensity_profile,                  # gCO2/kWh per local hour
            "renewable_share_profile": mean_profile_by_hour(share, local_tz=LOCAL_TZ),
            "days": days_ci,
            "intensity_daily": [None if v is None else round(v) for v in daily_ci],
            "renewable_share_daily": daily_sh,
        }
        valid = [v for v in intensity_profile if v is not None]
        logger.info(
            "[%s] mean intensity %s gCO2/kWh (range %s-%s); %d days",
            zone, round(sum(valid) / len(valid)) if valid else "n/a",
            min(valid) if valid else "n/a", max(valid) if valid else "n/a", len(days_ci),
        )

    ref = "DE_LU" if "DE_LU" in zones_out else (next(iter(zones_out)) if zones_out else None)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "methodology": CARBON_METHODOLOGY,
        "factors_gco2_kwh": EMISSION_FACTORS_GCO2_KWH,
        "zone_default": ref,
        "zones_available": list(zones_out.keys()),
        "period_start": zones_out[ref]["period_start"] if ref else None,
        "period_end": zones_out[ref]["period_end"] if ref else None,
        "zones": zones_out,
    }
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "carbon.json").write_text(json.dumps(payload, indent=2))
    logger.info("wrote data/carbon.json — zones: %s", list(zones_out.keys()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the carbon-intensity JSON artefact.")
    parser.add_argument("--zones", nargs="+", default=ZONES,
                        help="Subset of zones (default: all). Needs the generation cache.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    logger.info("carbon build start (zones=%s)", args.zones)

    zone_frames = {}
    for z in args.zones:
        cache = cache_path(z)
        zone_frames[z] = pd.read_parquet(cache) if cache.exists() else pd.DataFrame()
    build(zone_frames)
    logger.info("carbon build done")


if __name__ == "__main__":
    main()
