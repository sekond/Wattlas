"""Offline unit tests for pipeline/fr_fields.py — no network required.

Run: python -m pytest pipeline/test_fr_fields.py -v
or:  python pipeline/test_fr_fields.py
"""

from __future__ import annotations

import json
from pathlib import Path

import fuels
from fr_fields import (
    ECO2MIX_GENERATION,
    REGION_NUTS,
    fr_field,
    fr_fuel,
    region_name,
    region_nuts,
)

_CANON = set(fuels.FUEL_ORDER)
_BASEMAP = Path(__file__).resolve().parent.parent / "frontend" / "geo" / "regions_fr.topo.json"


def test_generation_fuels():
    assert fr_fuel("nucleaire") == "Nuclear"
    assert fr_fuel("hydraulique") == "Hydro"
    assert fr_fuel("eolien") == "Wind onshore"
    assert fr_fuel("eolien en mer") == "Wind offshore"
    assert fr_fuel("solaire") == "Solar"
    assert fr_fuel("thermique") == "Gas"        # combined fossil thermal (mostly gas)
    assert fr_fuel("pompage") == "Pumped storage"
    assert fr_fuel("bioenergies") == "Biomass"


def test_accent_and_case_tolerant():
    assert fr_fuel("nucléaire") == "Nuclear"
    assert fr_fuel("Nucléaire") == "Nuclear"
    assert fr_fuel("éolien") == "Wind onshore"
    assert fr_fuel("HYDRAULIQUE") == "Hydro"


def test_unknown_fuel_is_other_not_french():
    assert fr_fuel("licorne") == "Other"
    assert fr_fuel(None) == "Other"
    assert fr_fuel("") == "Other"


def test_region_by_insee_name_and_nuts():
    assert region_nuts("11") == "FR1"            # INSEE code
    assert region_nuts("Île-de-France") == "FR1"  # accented name
    assert region_nuts("ile de france") == "FR1"  # de-accented, spaced
    assert region_nuts("24") == "FRB"
    assert region_nuts("Centre-Val de Loire") == "FRB"
    assert region_nuts("Provence-Alpes-Côte d'Azur") == "FRL"
    assert region_nuts("FRK") == "FRK"           # already a NUTS code
    assert region_nuts("Atlantis") is None       # unknown -> None, never raw French


def test_all_13_regions_resolve():
    insees = ["11", "24", "27", "28", "32", "44", "52", "53", "75", "76", "84", "93", "94"]
    assert len({region_nuts(i) for i in insees}) == 13
    assert all(region_nuts(i) is not None for i in insees)


def test_region_nuts_match_the_committed_basemap():
    # The crosswalk's NUTS codes must exactly equal the basemap's régions, so Step 5
    # can join fr_regional.json to the choropleth with no orphans either way.
    topo = json.loads(_BASEMAP.read_text(encoding="utf-8"))
    base = {g["properties"]["NUTS_ID"] for g in topo["objects"]["regions"]["geometries"]}
    assert set(REGION_NUTS) == base, f"crosswalk vs basemap mismatch: {set(REGION_NUTS) ^ base}"


def test_region_name_lookup():
    assert region_name("FR1") == "Île-de-France"
    assert region_name("FRM") == "Corse"
    assert region_name("ZZ") is None


def test_field_translation():
    assert fr_field("consommation") == "consumption"
    assert fr_field("ech_physiques") == "exchanges"
    assert fr_field("solde") == "balance"
    assert fr_field("inconnu") == "Other"


def test_generation_outputs_are_canonical_fuels():
    for fuel in ECO2MIX_GENERATION.values():
        assert fuel in _CANON, f"éCO2mix maps to non-canonical fuel: {fuel}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} passed")
