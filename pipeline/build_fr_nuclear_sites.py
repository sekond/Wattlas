"""Build the geocoded French nuclear fleet for the France-nuclear Panel 1:
one record per site (reactors, net capacity, région, water, coordinates).

    python pipeline/build_fr_nuclear_sites.py

Writes data/fr_nuclear_sites.json.

ISOLATION (CLAUDE.md landmine #11): its OWN pipeline module, isolated from the
ENTSO-E and German (SMARD/MaStR) pipelines. Uses fr_fields for région→NUTS.

SOURCE & VINTAGE (landmine: "fleet count drifts"): the fleet is small and stable, so
it is a committed, attributed source list rather than a fragile registry fetch (the
slice spec allows this). Figures are net capacity (MW), compiled from public site data
/ RTE / IAEA PRIS, current to 2025. **Fessenheim** (closed 2020) is excluded;
**Flamanville-3** (EPR, grid-connected 2024) is INCLUDED — so the fleet here is
**18 sites / 57 reactors / ~63 GW**, slightly above the older "56 reactors / 61 GW"
figure. Confirm against a live source before publishing; the user sanity-checks totals.

Coordinates for the fleet are public. Site names and région names are proper nouns.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import fr_fields

log = logging.getLogger("build_fr_nuclear_sites")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SOURCE = "Public site data / RTE / IAEA PRIS (compiled), net MW"
AS_OF = "2025"

# Curated fleet: name, reactors, net capacity (MW), région (French name → NUTS via
# fr_fields), water body type, latitude, longitude. Operating sites only.
FLEET: list[dict] = [
    {"name": "Gravelines",    "reactors": 6, "capacity_mw": 5460, "region": "Hauts-de-France",           "water": "coast",   "lat": 51.015, "lon": 2.136},
    {"name": "Paluel",        "reactors": 4, "capacity_mw": 5320, "region": "Normandie",                 "water": "coast",   "lat": 49.858, "lon": 0.635},
    {"name": "Cattenom",      "reactors": 4, "capacity_mw": 5200, "region": "Grand Est",                 "water": "river",   "lat": 49.416, "lon": 6.218},
    {"name": "Flamanville",   "reactors": 3, "capacity_mw": 4300, "region": "Normandie",                 "water": "coast",   "lat": 49.536, "lon": -1.882},
    {"name": "Tricastin",     "reactors": 4, "capacity_mw": 3660, "region": "Auvergne-Rhône-Alpes",      "water": "river",   "lat": 44.330, "lon": 4.732},
    {"name": "Cruas",         "reactors": 4, "capacity_mw": 3660, "region": "Auvergne-Rhône-Alpes",      "water": "river",   "lat": 44.633, "lon": 4.757},
    {"name": "Blayais",       "reactors": 4, "capacity_mw": 3640, "region": "Nouvelle-Aquitaine",        "water": "estuary", "lat": 45.256, "lon": -0.693},
    {"name": "Chinon",        "reactors": 4, "capacity_mw": 3620, "region": "Centre-Val de Loire",       "water": "river",   "lat": 47.230, "lon": 0.170},
    {"name": "Bugey",         "reactors": 4, "capacity_mw": 3580, "region": "Auvergne-Rhône-Alpes",      "water": "river",   "lat": 45.798, "lon": 5.271},
    {"name": "Dampierre",     "reactors": 4, "capacity_mw": 3560, "region": "Centre-Val de Loire",       "water": "river",   "lat": 47.733, "lon": 2.516},
    {"name": "Chooz",         "reactors": 2, "capacity_mw": 3000, "region": "Grand Est",                 "water": "river",   "lat": 50.090, "lon": 4.789},
    {"name": "Civaux",        "reactors": 2, "capacity_mw": 2990, "region": "Nouvelle-Aquitaine",        "water": "river",   "lat": 46.457, "lon": 0.653},
    {"name": "Saint-Alban",   "reactors": 2, "capacity_mw": 2670, "region": "Auvergne-Rhône-Alpes",      "water": "river",   "lat": 45.404, "lon": 4.755},
    {"name": "Penly",         "reactors": 2, "capacity_mw": 2660, "region": "Normandie",                 "water": "coast",   "lat": 49.976, "lon": 1.212},
    {"name": "Belleville",    "reactors": 2, "capacity_mw": 2620, "region": "Centre-Val de Loire",       "water": "river",   "lat": 47.510, "lon": 2.875},
    {"name": "Golfech",       "reactors": 2, "capacity_mw": 2620, "region": "Occitanie",                 "water": "river",   "lat": 44.107, "lon": 0.845},
    {"name": "Nogent",        "reactors": 2, "capacity_mw": 2620, "region": "Grand Est",                 "water": "river",   "lat": 48.515, "lon": 3.518},
    {"name": "Saint-Laurent", "reactors": 2, "capacity_mw": 1830, "region": "Centre-Val de Loire",       "water": "river",   "lat": 47.720, "lon": 1.578},
]


# --------------------------------------------------------------------------- #
# Pure, offline-testable assembly
# --------------------------------------------------------------------------- #

def build_sites(fleet: list[dict]) -> list[dict]:
    """Validate and normalise the fleet into the committed shape, sorted by capacity
    (largest first). Resolves each région name to its NUTS-1 code via fr_fields."""
    out = []
    for f in sorted(fleet, key=lambda x: -x["capacity_mw"]):
        if f["capacity_mw"] <= 0 or f["reactors"] <= 0:
            raise ValueError(f"implausible site: {f['name']}")
        nuts = fr_fields.region_nuts(f["region"])
        if nuts is None:
            raise ValueError(f"unknown région for {f['name']}: {f['region']}")
        out.append({
            "name": f["name"], "region": f["region"], "nuts_id": nuts,
            "reactors": int(f["reactors"]), "capacity_mw": round(f["capacity_mw"]),
            "water": f["water"], "lat": round(f["lat"], 3), "lon": round(f["lon"], 3),
        })
    return out


def fleet_totals(sites: list[dict]) -> dict:
    """National roll-up for the Panel-1 KPIs (rounded)."""
    return {
        "sites": len(sites),
        "reactors": sum(s["reactors"] for s in sites),
        "capacity_mw": sum(s["capacity_mw"] for s in sites),
    }


# --------------------------------------------------------------------------- #
# I/O
# --------------------------------------------------------------------------- #

def build() -> dict:
    sites = build_sites(FLEET)
    totals = fleet_totals(sites)
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": SOURCE, "as_of": AS_OF, "unit": "MW",
        "fleet_total": totals,
        "sites": sites,
    }
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "fr_nuclear_sites.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")

    log.info("Fleet: %d sites, %d reactors, %.1f GW total",
             totals["sites"], totals["reactors"], totals["capacity_mw"] / 1000)
    log.info("Biggest sites: %s", ", ".join(
        f"{s['name']} {s['capacity_mw']/1000:.1f} GW" for s in sites[:3]))
    by_region: dict[str, int] = {}
    for s in sites:
        by_region[s["region"]] = by_region.get(s["region"], 0) + s["capacity_mw"]
    log.info("Top régions by hosted capacity: %s", ", ".join(
        f"{r} {mw/1000:.1f} GW" for r, mw in sorted(by_region.items(), key=lambda x: -x[1])[:4]))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    build()
