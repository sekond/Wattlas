"""Offline unit tests for pipeline/build_fr_nuclear_sites.py — no network.

Run: python -m pytest pipeline/test_fr_nuclear_sites.py -v
or:  python pipeline/test_fr_nuclear_sites.py
"""

from __future__ import annotations

from build_fr_nuclear_sites import FLEET, build_sites, fleet_totals

_FIXTURE = [
    {"name": "Small", "reactors": 2, "capacity_mw": 1800, "region": "Bretagne", "water": "coast", "lat": 48.0, "lon": -3.0},
    {"name": "Big",   "reactors": 6, "capacity_mw": 5460, "region": "Hauts-de-France", "water": "coast", "lat": 51.01, "lon": 2.13},
]


def test_build_sites_sorted_and_resolved():
    sites = build_sites(_FIXTURE)
    assert [s["name"] for s in sites] == ["Big", "Small"]      # capacity desc
    assert sites[0]["nuts_id"] == "FRE"                        # Hauts-de-France
    assert sites[1]["nuts_id"] == "FRH"                        # Bretagne
    assert set(sites[0]) == {"name", "region", "nuts_id", "reactors", "capacity_mw", "water", "lat", "lon"}


def test_unknown_region_raises():
    bad = [{"name": "X", "reactors": 1, "capacity_mw": 900, "region": "Atlantis", "water": "river", "lat": 47, "lon": 2}]
    try:
        build_sites(bad)
        assert False, "expected ValueError for unknown région"
    except ValueError:
        pass


def test_totals():
    t = fleet_totals(build_sites(_FIXTURE))
    assert t == {"sites": 2, "reactors": 8, "capacity_mw": 7260}


def test_real_fleet_plausible():
    sites = build_sites(FLEET)
    t = fleet_totals(sites)
    assert t["sites"] == 18
    assert t["reactors"] == 57                          # incl. Flamanville-3 EPR
    assert 60_000 <= t["capacity_mw"] <= 65_000         # ~63 GW
    # every région resolves to a NUTS-1 code on the basemap
    assert all(s["nuts_id"] and s["nuts_id"].startswith("FR") for s in sites)
    # the three biggest are the coastal/Moselle giants, each ~5+ GW
    assert [s["name"] for s in sites[:3]] == ["Gravelines", "Paluel", "Cattenom"]
    assert all(s["capacity_mw"] >= 5000 for s in sites[:3])
    # coordinates inside metropolitan France
    assert all(41 <= s["lat"] <= 51.5 and -5.5 <= s["lon"] <= 9.5 for s in sites)
    assert all(s["water"] in {"river", "coast", "estuary"} for s in sites)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} passed")
