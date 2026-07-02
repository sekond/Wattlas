"""Build UK regional carbon: per-region grid carbon intensity (gCO2/kWh) + generation
mix for the 14 GB DNO regions, from the NESO Carbon Intensity API. Writes
data/uk_regional_carbon.json.

Run: python pipeline/build_uk_regional_carbon.py            (fetches ~14 days)
     python pipeline/build_uk_regional_carbon.py --use-cache (offline, JSON cache)

ISOLATED module (CLAUDE.md landmine #11): the NESO Carbon Intensity API is open (no
key), GB only, with its own units and methodology — not entangled with the ENTSO-E,
German or French pipelines.

Landmines this script is built around:
  * GB ≠ UK (#10/spec): NESO covers Great Britain only; Northern Ireland (all-island
    SEM) is excluded. Stated in the JSON + UI.
  * Methodology in writing (#12): these figures are **consumption-based** (the carbon
    of electricity *used* in a region, imports included) — NOT the site's existing
    production-based carbon view. Units are gCO2/kWh. Never mix the two.
  * Forecast basis: NESO's *regional* intensity is forecast-based (the wind-dominated
    northern regions can read ~0). We average over a recent window and label it.
  * Gaps honest (#8): a region/period with no value is null, never fabricated.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import mean

import requests

from build_spread import DATA_DIR

logger = logging.getLogger("wattlas.build_uk_regional_carbon")

API = "https://api.carbonintensity.org.uk"
# regionid 1-14 are the GB DNO regions (the basemap); 15-18 are England/Scotland/
# Wales/GB aggregates and are deliberately skipped.
REGION_IDS = list(range(1, 15))
RENEWABLE = ("wind", "solar", "hydro")   # variable renewables + hydro
# Canonical region names (match frontend/geo/uk_dno.topo.json `name` and the API shortnames).
NAMES = {
    1: "North Scotland", 2: "South Scotland", 3: "North West England", 4: "North East England",
    5: "Yorkshire", 6: "North Wales & Merseyside", 7: "South Wales", 8: "West Midlands",
    9: "East Midlands", 10: "East England", 11: "South West England", 12: "South England",
    13: "London", 14: "South East England",
}
CACHE = DATA_DIR / "_raw_uk_carbon.json"   # gitignored (data/_raw_*)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%MZ")


def fetch_periods(start: datetime, end: datetime) -> list[dict]:
    """All 30-min regional periods in [start, end), fetched in <=13-day chunks (the
    API's range limit)."""
    periods: list[dict] = []
    cur = start
    while cur < end:
        chunk_end = min(cur + timedelta(days=13), end)
        url = f"{API}/regional/intensity/{_iso(cur)}/{_iso(chunk_end)}"
        logger.info("fetching %s .. %s", _iso(cur), _iso(chunk_end))
        resp = requests.get(url, headers={"Accept": "application/json"}, timeout=60)
        resp.raise_for_status()
        periods.extend(resp.json().get("data", []))
        cur = chunk_end
    return periods


def compute(periods: list[dict], generated_at: str) -> dict:
    """Pure transform: NESO 30-min periods -> uk_regional_carbon.json payload. No
    network or file I/O, so it is unit-tested offline."""
    ints: dict[int, list[float]] = defaultdict(list)
    mixes: dict[int, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    froms: list[str] = []
    for p in periods:
        if p.get("from"):
            froms.append(p["from"])
        for r in p.get("regions", []):
            rid = r.get("regionid")
            if rid not in NAMES:          # skip the England/Scotland/Wales/GB aggregates
                continue
            f = (r.get("intensity") or {}).get("forecast")
            if f is not None:
                ints[rid].append(f)
            for g in r.get("generationmix", []):
                if g.get("perc") is not None:
                    mixes[rid][g["fuel"]].append(g["perc"])

    regions = []
    for rid in REGION_IDS:
        iv = ints.get(rid, [])
        intensity = round(mean(iv)) if iv else None
        mix = {fuel: round(mean(vals), 1) for fuel, vals in mixes.get(rid, {}).items() if vals}
        renewable = round(sum(mix.get(f, 0.0) for f in RENEWABLE), 1) if mix else None
        low_carbon = round((renewable or 0.0) + mix.get("nuclear", 0.0), 1) if mix else None
        regions.append({
            "regionid": rid, "name": NAMES[rid],
            "intensity": intensity,            # mean gCO2/kWh (integer), null if no data
            "renewable_pct": renewable,        # wind + solar + hydro
            "low_carbon_pct": low_carbon,      # renewable + nuclear
            "mix": mix,                        # mean % per fuel
        })
    return {
        "generated_at": generated_at,
        "unit": "gCO2/kWh",
        "methodology": ("NESO regional Carbon Intensity API, consumption-based (the carbon of "
                        "electricity used in each region, imports included). Great Britain only "
                        "— excludes Northern Ireland. Regional values are forecast-based; means "
                        "over a recent ~2-week window. renewable_pct = wind + solar + hydro."),
        "basis": "forecast",
        "period_start": min(froms)[:10] if froms else None,
        "period_end": max(froms)[:10] if froms else None,
        "regions": regions,
    }


def build(periods: list[dict]) -> None:
    """Compute the payload, write the JSON, and log cleanest->dirtiest for the sanity-check."""
    payload = compute(periods, datetime.now(timezone.utc).isoformat(timespec="seconds"))
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "uk_regional_carbon.json").write_text(json.dumps(payload, indent=2))
    logger.info("wrote data/uk_regional_carbon.json (%d regions, %s..%s)",
                len(payload["regions"]), payload["period_start"], payload["period_end"])
    logger.info("regional carbon intensity (gCO2/kWh), clean -> dirty:")
    ranked = sorted((r for r in payload["regions"] if r["intensity"] is not None),
                    key=lambda r: r["intensity"])
    for r in ranked:
        logger.info("    %2d %-24s %4d  (renewable %s%%)", r["regionid"], r["name"], r["intensity"], r["renewable_pct"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the UK regional-carbon JSON artefact.")
    parser.add_argument("--use-cache", action="store_true", help="Re-use data/_raw_uk_carbon.json.")
    parser.add_argument("--days", type=int, default=14, help="Trailing window length (days).")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    logger.info("uk regional carbon build start (use_cache=%s, days=%d)", args.use_cache, args.days)

    if args.use_cache:
        if not CACHE.exists():
            logger.error("no cache at %s — run once without --use-cache first.", CACHE)
            sys.exit(1)
        periods = json.loads(CACHE.read_text())
        logger.info("loaded %d periods from cache (no API call)", len(periods))
    else:
        end = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=args.days)
        try:
            periods = fetch_periods(start, end)
        except requests.RequestException as exc:
            logger.error("NESO Carbon Intensity API fetch failed: %s", exc)
            sys.exit(1)
        CACHE.write_text(json.dumps(periods))
        logger.info("fetched + cached %d periods", len(periods))

    build(periods)
    logger.info("uk regional carbon build done")


if __name__ == "__main__":
    main()
