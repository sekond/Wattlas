"""Offline unit tests for pipeline/build_fr_regional.py — no network.

Run: python -m pytest pipeline/test_fr_regional.py -v
or:  python pipeline/test_fr_regional.py
"""

from __future__ import annotations

from build_fr_regional import assemble_regions

# ODRÉ-shaped aggregation rows (MW): an exporter, an importer, an unmappable row.
_ROWS = [
    {"libelle_region": "Centre-Val de Loire", "code_insee_region": "24",
     "conso": 2000, "nuc": 7800, "ech": -6480},   # ech<0 => exporting
    {"libelle_region": "Île-de-France", "code_insee_region": "11",
     "conso": 7500, "nuc": 0, "ech": 7150},        # ech>0 => importing
    {"libelle_region": "Mars Colony", "code_insee_region": "99", "conso": 100, "nuc": 0, "ech": 0},
]


def test_net_balance_is_minus_exchanges_and_gen_identity():
    out = assemble_regions(_ROWS)
    cvl = next(r for r in out if r["nuts_id"] == "FRB")
    assert cvl["net_balance_gw"] == 6.48          # −ech (−(−6.48))
    assert cvl["consumption_gw"] == 2.0
    assert cvl["generation_gw"] == 8.48           # conso − ech = 2.0 − (−6.48)
    assert cvl["nuclear_gw"] == 7.8


def test_exporter_importer_signs_and_sort():
    out = assemble_regions(_ROWS)
    # unmappable row dropped; two régions remain, sorted exporter first
    assert [r["nuts_id"] for r in out] == ["FRB", "FR1"]
    assert out[0]["net_balance_gw"] > 0           # Centre-Val de Loire exports
    assert out[1]["net_balance_gw"] < 0           # Île-de-France imports
    assert out[1]["net_balance_gw"] == -7.15


def test_unmappable_region_skipped():
    out = assemble_regions(_ROWS)
    assert all(r["nuts_id"].startswith("FR") for r in out)
    assert all(r["name"] != "Mars Colony" for r in out)


def test_empty_safe():
    assert assemble_regions([]) == []


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} passed")
