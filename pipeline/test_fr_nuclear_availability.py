"""Offline unit tests for pipeline/build_fr_nuclear_availability.py — no network.

Run: python -m pytest pipeline/test_fr_nuclear_availability.py -v
or:  python pipeline/test_fr_nuclear_availability.py
"""

from __future__ import annotations

from build_fr_nuclear_availability import assemble_months

# Two monthly aggregation rows (MW): a winter peak and a summer dip; France exporting.
_ROWS = [
    {"month": "2025-05", "nuc": 34300, "hyd": 7500, "gas": 400, "eo": 4600, "sol": 4900,
     "bio": 800, "coal": 100, "oil": 100, "ech": -10000, "dem": 41900},   # summer dip
    {"month": "2025-01", "nuc": 52100, "hyd": 9700, "gas": 4000, "eo": 7700, "sol": 1400,
     "bio": 900, "coal": 300, "oil": 200, "ech": -9100, "dem": 66600},     # winter peak
]


def test_units_and_fields():
    out = assemble_months(_ROWS)
    assert [m["month"] for m in out] == ["2025-01", "2025-05"]   # chronological
    jan = out[0]
    assert jan["nuclear_gw"] == 52.1                              # MW -> GW
    assert jan["demand_gw"] == 66.6
    assert jan["other_gw"] == 1.4                                 # bio+coal+oil = 0.9+0.3+0.2
    assert jan["available_gw"] is None                           # OAuth pending


def test_net_export_sign():
    out = {m["month"]: m for m in assemble_months(_ROWS)}
    # ech_physiques < 0 means France is exporting -> net_export_gw > 0
    assert out["2025-05"]["net_export_gw"] == 10.0
    assert out["2025-01"]["net_export_gw"] == 9.1
    assert all(m["net_export_gw"] > 0 for m in out.values())     # exporter both months


def test_summer_dip_below_winter():
    out = {m["month"]: m for m in assemble_months(_ROWS)}
    assert out["2025-05"]["nuclear_gw"] < out["2025-01"]["nuclear_gw"]


def test_empty_safe():
    assert assemble_months([]) == []


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} passed")
