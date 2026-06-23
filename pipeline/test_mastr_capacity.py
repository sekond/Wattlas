"""Offline unit tests for pipeline/build_mastr_capacity.py — no network, no DB.

Run: python -m pytest pipeline/test_mastr_capacity.py -v
or:  python pipeline/test_mastr_capacity.py
"""

from __future__ import annotations

import pandas as pd

from build_mastr_capacity import (
    aggregate_by_landkreis,
    national_totals,
    normalise_units,
    top_clusters_by_fuel,
)

# Small inline fixture in the raw open-mastr *_extended shape (German values).
_FIXTURE = pd.DataFrame([
    # name, Energietraeger, Lage, status, Nettonennleistung(kW), AGS, Landkreis, Bundesland, Kuestenentfernung, lat, lon
    ["WEA A", "Wind", None, "In Betrieb", 3000, "01060017", "Segeberg", "Schleswig-Holstein", None, 54.0, 10.30],
    ["WEA B", "Wind", None, "In Betrieb", 2000, "01060020", "Segeberg", "Schleswig-Holstein", None, 54.03, 10.32],
    ["Offshore X", "Wind", None, "In Betrieb", 15000, None, None, "Ausschließliche Wirtschaftszone", 35, 54.5, 6.5],
    ["Solarpark Z", "Solare Strahlungsenergie", None, "In Betrieb", 845000, "09162000", "München", "Bayern", None, 48.1, 11.6],
    ["Planned wind", "Wind", None, "In Planung", 5000, "01060099", "Segeberg", "Schleswig-Holstein", None, 54.2, 10.1],
    ["Bio plant", "Biomasse", None, "In Betrieb", 4000, "09162001", "München", "Bayern", None, 48.2, 11.5],
], columns=[
    "NameStromerzeugungseinheit", "Energietraeger", "Lage", "EinheitBetriebsstatus",
    "Nettonennleistung", "Gemeindeschluessel", "Landkreis", "Bundesland",
    "Kuestenentfernung", "Breitengrad", "Laengengrad",
])

_KREIS_TO_NUTS = {"01060": "DEF0E", "09162": "DE212"}
_NUTS_TO_NAME = {"DEF0E": "Segeberg", "DE212": "München, Landkreis"}


def _units():
    return normalise_units(_FIXTURE)


def test_normalise_filters_and_converts():
    u = _units()
    # "In Planung" dropped; 5 operating units remain (2 onshore, 1 offshore, 1 solar, 1 bio)
    assert len(u) == 5
    assert "Planned wind" not in set(u["name"])
    # kW -> MW
    assert u.loc[u["name"] == "WEA A", "mw"].iat[0] == 3.0
    assert u.loc[u["name"] == "Solarpark Z", "mw"].iat[0] == 845.0


def test_offshore_classified_and_has_no_kreis():
    u = _units()
    off = u[u["name"] == "Offshore X"].iloc[0]
    assert off["fuel"] == "Wind offshore"   # via EEZ Bundesland + coast distance
    assert pd.isna(off["kreis5"])           # at sea -> no Landkreis
    on = u[u["name"] == "WEA A"].iloc[0]
    assert on["fuel"] == "Wind onshore"
    assert on["kreis5"] == "01060"


def test_aggregate_sums_per_landkreis_per_fuel():
    rows = aggregate_by_landkreis(_units(), _KREIS_TO_NUTS, _NUTS_TO_NAME)
    by_ags = {r["ags"]: r for r in rows}
    # Segeberg: two onshore turbines 3 + 2 = 5 MW; no solar/offshore
    assert by_ags["01060"]["wind_onshore_mw"] == 5
    assert by_ags["01060"]["wind_offshore_mw"] == 0
    assert by_ags["01060"]["solar_mw"] == 0
    assert by_ags["01060"]["nuts_id"] == "DEF0E"
    assert by_ags["01060"]["name"] == "Segeberg"
    # München: 845 MW solar; biomass is NOT a Panel-1 fuel so it does not appear
    assert by_ags["09162"]["solar_mw"] == 845
    assert by_ags["09162"]["wind_onshore_mw"] == 0
    # sorted by ags
    assert [r["ags"] for r in rows] == ["01060", "09162"]


def test_offshore_and_biomass_excluded_from_landkreise():
    rows = aggregate_by_landkreis(_units(), _KREIS_TO_NUTS, _NUTS_TO_NAME)
    total_offshore = sum(r["wind_offshore_mw"] for r in rows)
    assert total_offshore == 0   # the only offshore unit is at sea -> no Landkreis
    # biomass contributes to no Panel-1 field
    assert all(set(r) == {"ags", "nuts_id", "name", "wind_onshore_mw",
                          "wind_offshore_mw", "solar_mw"} for r in rows)


def test_clusters_by_fuel_grouped_and_split():
    cl = top_clusters_by_fuel(_units(), n=12)
    assert set(cl) == {"wind", "solar"}
    # wind: WEA A + WEA B fall in one cell -> one Segeberg cluster (5 MW, 2 units);
    # the offshore turbine is its own cell. Sorted by MW desc.
    wind = cl["wind"]
    assert [w["name"] for w in wind] == ["Offshore", "Segeberg"]
    assert wind[0]["fuel"] == "Wind offshore" and wind[0]["units"] == 1
    seg = wind[1]
    assert seg["mw"] == 5 and seg["units"] == 2 and seg["fuel"] == "Wind onshore"
    # solar: one München park; biomass is not a Panel-1 fuel and is excluded
    assert [s["name"] for s in cl["solar"]] == ["München"]
    assert cl["solar"][0]["mw"] == 845 and cl["solar"][0]["fuel"] == "Solar"


def test_national_totals_include_offshore():
    nat = national_totals(_units())
    # onshore 3+2=5, offshore 15 (counted nationally even though it has no Landkreis),
    # solar 845. Biomass is not a Panel-1 fuel so it is absent.
    assert nat == {"wind_onshore_mw": 5, "wind_offshore_mw": 15, "solar_mw": 845}


def test_empty_safe():
    empty = pd.DataFrame(columns=_FIXTURE.columns)
    u = normalise_units(empty)
    assert u.empty
    assert aggregate_by_landkreis(u, _KREIS_TO_NUTS, _NUTS_TO_NAME) == []
    assert top_clusters_by_fuel(u) == {"wind": [], "solar": []}
    assert national_totals(u) == {"wind_onshore_mw": 0, "wind_offshore_mw": 0, "solar_mw": 0}


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} passed")
