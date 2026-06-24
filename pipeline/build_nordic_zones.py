"""Build the Nordic price-zones data: day-ahead prices for the 12 Nordic bidding
zones, with per-zone averages, monthly series, and within-country price gaps.
Writes data/nordic_prices.json.

Run: python pipeline/build_nordic_zones.py             (fetches 12 months)
     python pipeline/build_nordic_zones.py --use-cache (offline, parquet cache)

This is its OWN builder (CLAUDE.md landmine #11) — it reuses the shared ENTSO-E
client and the pure helpers in metrics.py, but is NOT entangled with
build_spread.py / build_divergence.py.

Data landmines this script is built around:
  * Bidding zones, not countries (#2): the Nordic zones are SE1-4, NO1-5, DK1-2,
    FI. EIC codes are taken from entsoe-py's Area enum (a wrong code yields
    plausible-but-wrong prices — the #1 failure mode for this slice).
  * Resolution break + DST (#3, #4): every zone is resampled to canonical hourly
    and grouped in its OWN local calendar (SE/NO/DK are CET; FI is EET, +1h), via
    metrics.to_hourly / monthly_means. Never assume 24 values per day.
  * Missing data (#8): a zone (or a month) with no data is recorded as null and
    never fabricated; one zone failing to fetch must not break the others.
  * Hydro context: Nordic prices are heavily hydro/reservoir- and weather-driven,
    so within-country divergence reflects wet/dry years as well as grid
    constraints — stated in the JSON note and surfaced by the frontend.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import pandas as pd

from metrics import data_coverage, monthly_means, to_hourly
from build_spread import DATA_DIR, LOCAL_TZ

logger = logging.getLogger("wattlas.build_nordic_zones")

# (entsoe-py Area code, display zone code, country, local tz). The display code is
# the join key shared with frontend/geo/nordic_zones.topo.json (props.code) and
# with the names below. SE/NO/DK clear in CET/CEST; FI in EET/EEST (+1h) — group
# each zone in its own local calendar (landmine #4).
ZONES: list[tuple[str, str, str, str]] = [
    ("SE_1", "SE1", "SE", "Europe/Stockholm"),
    ("SE_2", "SE2", "SE", "Europe/Stockholm"),
    ("SE_3", "SE3", "SE", "Europe/Stockholm"),
    ("SE_4", "SE4", "SE", "Europe/Stockholm"),
    ("NO_1", "NO1", "NO", "Europe/Oslo"),
    ("NO_2", "NO2", "NO", "Europe/Oslo"),
    ("NO_3", "NO3", "NO", "Europe/Oslo"),
    ("NO_4", "NO4", "NO", "Europe/Oslo"),
    ("NO_5", "NO5", "NO", "Europe/Oslo"),
    ("DK_1", "DK1", "DK", "Europe/Copenhagen"),
    ("DK_2", "DK2", "DK", "Europe/Copenhagen"),
    ("FI", "FI", "FI", "Europe/Helsinki"),
]
# Multi-zone countries get a within-country gap; FI is a single zone (no gap).
GAP_COUNTRIES = ["SE", "NO", "DK"]
ZONE_NAMES = {
    "SE1": "North (SE1)", "SE2": "North-central (SE2)", "SE3": "Central (SE3)", "SE4": "South (SE4)",
    "NO1": "East (NO1)", "NO2": "South (NO2)", "NO3": "Central (NO3)", "NO4": "North (NO4)", "NO5": "West (NO5)",
    "DK1": "West Denmark (DK1)", "DK2": "East Denmark (DK2)", "FI": "Finland (FI)",
}
TZ_BY_CODE = {code: tz for _ent, code, _c, tz in ZONES}

CACHE = DATA_DIR / "_raw_nordic_prices.parquet"


def fetch_zone_prices(start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Fetch day-ahead prices for every Nordic zone into one DataFrame (cols =
    display codes). A single zone failing is logged and recorded as an empty
    column — one bad zone must not sink the build (landmine #8)."""
    from entsoe import EntsoePandasClient

    token = os.environ.get("ENTSOE_API_TOKEN")
    if not token:
        sys.exit("ENTSOE_API_TOKEN not set. Copy .env.example to .env and fill it in.")
    client = EntsoePandasClient(api_key=token)

    cols: dict[str, pd.Series] = {}
    for ent, code, _country, _tz in ZONES:
        try:
            logger.info("fetching day-ahead prices for %s (%s)", code, ent)
            cols[code] = client.query_day_ahead_prices(ent, start=start, end=end)
        except Exception as exc:  # noqa: BLE001 - any per-zone failure degrades to "missing"
            logger.warning("zone %s (%s) failed: %s — recording as missing", code, ent, exc)
            cols[code] = pd.Series(dtype="float64")
    # Columns may be in different tz (FI is EET); pandas aligns on the union index
    # in UTC. Per-zone local grouping happens later via each zone's local_tz.
    return pd.DataFrame(cols)


def compute(zone_prices: pd.DataFrame, generated_at: str) -> dict:
    """Pure transform: fetched prices -> nordic_prices.json payload. No network or
    file I/O, so it is unit-tested offline (test_nordic_zones.py)."""
    monthly_by_code: dict[str, dict[str, float]] = {}
    avg_by_code: dict[str, float | None] = {}
    cov_starts: list[str] = []
    cov_ends: list[str] = []

    for _ent, code, _country, tz in ZONES:
        series = (zone_prices[code].dropna() if code in zone_prices.columns
                  else pd.Series(dtype="float64"))
        hourly = to_hourly(series)
        avg_by_code[code] = round(float(hourly.mean()), 1) if not hourly.empty else None
        monthly_by_code[code] = {m["month"]: m["mean"] for m in monthly_means(series, local_tz=tz)}
        start, end = data_coverage(series, local_tz=tz)
        if start:
            cov_starts.append(start)
        if end:
            cov_ends.append(end)

    # Canonical month axis = the union of months any zone reported, chronological.
    months = sorted({mo for d in monthly_by_code.values() for mo in d})

    zones_out = [
        {
            "code": code,
            "country": country,
            "name": ZONE_NAMES[code],
            "avg_price": avg_by_code[code],
            "months": [monthly_by_code[code].get(mo) for mo in months],
        }
        for _ent, code, country, _tz in ZONES
    ]

    # Within-country gap = spread between the dearest and cheapest zone of a
    # country, per month (max - min across its zones with data that month). A
    # month with fewer than two zones reporting is null, not zero (landmine #8).
    within: dict[str, dict] = {}
    codes_by_country = {c: [z["code"] for z in zones_out if z["country"] == c] for c in GAP_COUNTRIES}
    for country, codes in codes_by_country.items():
        gaps: list[float | None] = []
        for mo in months:
            vals = [monthly_by_code[c][mo] for c in codes if mo in monthly_by_code[c]]
            gaps.append(round(max(vals) - min(vals), 1) if len(vals) >= 2 else None)
        present = [g for g in gaps if g is not None]
        within[country] = {
            "months": gaps,
            "avg_gap": round(sum(present) / len(present), 1) if present else None,
        }

    return {
        "generated_at": generated_at,
        "unit": "EUR/MWh",
        "note": ("Day-ahead prices per bidding zone (ENTSO-E). Nordic prices are "
                 "heavily hydro/reservoir- and weather-driven, so within-country "
                 "divergence reflects wet/dry years as well as grid constraints. "
                 "within_country_gap is the spread between a country's dearest and "
                 "cheapest zone per month (max - min)."),
        "period_start": min(cov_starts) if cov_starts else None,
        "period_end": max(cov_ends) if cov_ends else None,
        "months": months,
        "zones": zones_out,
        "within_country_gap": within,
    }


def build(zone_prices: pd.DataFrame) -> None:
    """Compute the payload and write data/nordic_prices.json; log per-zone averages
    for the user sanity-check (north should read cheaper than south)."""
    payload = compute(zone_prices, datetime.now(timezone.utc).isoformat(timespec="seconds"))
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "nordic_prices.json").write_text(json.dumps(payload, indent=2))
    logger.info("wrote data/nordic_prices.json (%d zones, %d months, %s..%s)",
                len(payload["zones"]), len(payload["months"]),
                payload["period_start"], payload["period_end"])
    logger.info("per-zone average price (EUR/MWh), cheap -> dear:")
    ranked = sorted((z for z in payload["zones"] if z["avg_price"] is not None),
                    key=lambda z: z["avg_price"])
    for z in ranked:
        logger.info("    %-3s %6.1f  (%s)", z["code"], z["avg_price"], z["country"])
    for z in (z for z in payload["zones"] if z["avg_price"] is None):
        logger.info("    %-3s    n/a  (%s) — no data", z["code"], z["country"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Nordic price-zones JSON artefact.")
    parser.add_argument("--use-cache", action="store_true",
                        help="Re-use data/_raw_nordic_prices.parquet instead of the API.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    logger.info("nordic build start (use_cache=%s)", args.use_cache)

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
    logger.info("nordic build done")


if __name__ == "__main__":
    main()
