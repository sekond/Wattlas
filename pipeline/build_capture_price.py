"""Build per-zone capture price / value factor (v10 slice) OFFLINE from two caches:
per-zone generation (data/_raw_generation_{zone}.parquet, from build_mix, already
collapsed to canonical fuels) and per-zone day-ahead prices
(data/_raw_zone_prices.parquet, from build_divergence). Writes data/capture_price.json.

Run AFTER build_mix.py and build_divergence.py — it reads their caches, no API call.

Generation-weighted capture price ÷ time-weighted baseload = value factor, per
renewable group (solar, wind), with the share of generation in negative-price hours.
Generation and price are resampled to ONE canonical hourly resolution before
weighting (landmine #3 — the Oct-2025 quarter-hourly break would otherwise corrupt
the weighting); negative prices are kept (landmine #6).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import pandas as pd

from metrics import capture_metrics
from build_spread import DATA_DIR, LOCAL_TZ
from build_divergence import ZONES, CACHE as PRICE_CACHE
from build_mix import cache_path as gen_cache_path

logger = logging.getLogger("wattlas.build_capture_price")


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    if not PRICE_CACHE.exists():
        logger.error("no zone-price cache at %s — run build_divergence.py first.", PRICE_CACHE)
        raise SystemExit(1)
    zone_prices = pd.read_parquet(PRICE_CACHE)
    logger.info("loaded zone-price cache %s (%d rows x %d zones)", PRICE_CACHE, *zone_prices.shape)

    zones: dict = {}
    for z in ZONES:
        gcache = gen_cache_path(z)
        if z not in zone_prices.columns or not gcache.exists():
            logger.warning("[%s] missing price or generation cache — skipping", z)
            continue
        price = zone_prices[z].dropna()
        gen = pd.read_parquet(gcache)
        if price.empty or gen.empty:
            continue
        cm = capture_metrics(gen, price, local_tz=LOCAL_TZ)
        if not cm:
            logger.warning("[%s] no capture metrics (no solar/wind overlap)", z)
            continue
        zones[z] = cm
        logger.info("[%s] solar VF=%s wind VF=%s",
                    z, cm.get("solar", {}).get("value_factor"), cm.get("wind", {}).get("value_factor"))

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ref = "DE_LU" if "DE_LU" in zones else next(iter(zones), None)
    (DATA_DIR / "capture_price.json").write_text(json.dumps({
        "generated_at": generated_at,
        "zone_default": ref,
        "zones_available": list(zones.keys()),
        "source": "ENTSO-E generation + day-ahead prices",
        "method": "generation-weighted capture price / time-weighted baseload (value factor)",
        "groups": {"solar": ["Solar"], "wind": ["Wind onshore", "Wind offshore"]},
        # Roadmap anchors are CITED 2025 context, not these computed values (landmine #7 spirit).
        "context_note": ("Anchor figures from the consolidated roadmap (DE solar capture "
                         "~50-60% of baseload; ~16% of solar at negative prices; 573 negative "
                         "hours, 2025) are cited context, not the values computed here."),
        "zones": zones,
    }, indent=2))
    logger.info("wrote capture_price.json — zones: %s", list(zones.keys()))


if __name__ == "__main__":
    main()
