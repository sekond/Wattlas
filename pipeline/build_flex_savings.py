"""Build per-zone dynamic-tariff flexibility savings (v10 slice) OFFLINE from the
cached multi-zone day-ahead prices (data/_raw_zone_prices.parquet). Writes
data/flex_savings.json.

UPPER BOUND (landmine #7): savings assume perfect foresight of which hours are
cheapest each day — exactly like the battery arbitrage figure. The frontend MUST
label them an upper bound, not an achievable number.

Run: python pipeline/build_flex_savings.py   (no API call; needs the zone-price cache)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import pandas as pd

from metrics import cheapest_n_hours_savings, data_coverage
from build_spread import DATA_DIR, LOCAL_TZ
from build_divergence import ZONES, CACHE

logger = logging.getLogger("wattlas.build_flex_savings")

# Illustrative shiftable-load presets: (label, daily energy kWh, cheapest-N-hour window).
PRESETS = [
    {"name": "EV", "kwh_per_day": 10.0, "window_h": 4},
    {"name": "Heat pump", "kwh_per_day": 8.0, "window_h": 6},
    {"name": "Home battery", "kwh_per_day": 12.0, "window_h": 3},
]


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
        cov_start, cov_end = data_coverage(s, local_tz=LOCAL_TZ)
        presets = []
        for p in PRESETS:
            r = cheapest_n_hours_savings(s, kwh_per_day=p["kwh_per_day"], n=p["window_h"], local_tz=LOCAL_TZ)
            presets.append({"name": p["name"], "window_h": p["window_h"], **r})
        zones[z] = {"period_start": cov_start, "period_end": cov_end, "presets": presets}
        logger.info("[%s] EV saving €%.0f/yr (upper bound)", z, presets[0]["annual_saving_eur"])

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ref = "DE_LU" if "DE_LU" in zones else next(iter(zones), None)
    (DATA_DIR / "flex_savings.json").write_text(json.dumps({
        "generated_at": generated_at,
        "zone_default": ref,
        "zones_available": list(zones.keys()),
        "source": "ENTSO-E day-ahead prices",
        "flat_tariff": "period mean price",
        # CLAUDE.md #7 — perfect-foresight upper bound, must be labelled in the UI.
        "perfect_foresight_is_upper_bound": True,
        "zones": zones,
    }, indent=2))
    logger.info("wrote flex_savings.json — zones: %s", list(zones.keys()))


if __name__ == "__main__":
    main()
