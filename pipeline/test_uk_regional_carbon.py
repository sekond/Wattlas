"""Offline unit tests for pipeline/build_uk_regional_carbon.py — no network.

Run: python -m pytest pipeline/test_uk_regional_carbon.py -v
or:  python pipeline/test_uk_regional_carbon.py
"""

from __future__ import annotations

from build_uk_regional_carbon import compute

GEN = "2026-06-24T00:00:00+00:00"


def _region(rid, name, forecast, mix):
    return {"regionid": rid, "shortname": name,
            "intensity": {"forecast": forecast, "index": "low"},
            "generationmix": [{"fuel": f, "perc": p} for f, p in mix.items()]}


def _fixture():
    # Two 30-min periods. Region 1 (clean Scotland), region 7 (gas-heavy Wales), and
    # region 15 (England aggregate — must be IGNORED). Mix constant; intensity varies
    # so the mean is exact. Regions 2-6, 8-14 are absent (null handling).
    clean = {"wind": 80, "hydro": 10, "solar": 0, "gas": 5, "nuclear": 5}
    dirty = {"gas": 70, "wind": 20, "solar": 5, "nuclear": 5}
    return [
        {"from": "2026-06-10T00:00Z", "to": "2026-06-10T00:30Z", "regions": [
            _region(1, "North Scotland", 10, clean),
            _region(7, "South Wales", 300, dirty),
            _region(15, "England", 200, {"gas": 50}),
        ]},
        {"from": "2026-06-10T00:30Z", "to": "2026-06-10T01:00Z", "regions": [
            _region(1, "North Scotland", 20, clean),
            _region(7, "South Wales", 320, dirty),
            _region(15, "England", 210, {"gas": 50}),
        ]},
    ]


def test_fourteen_regions_aggregates_excluded():
    out = compute(_fixture(), GEN)
    ids = [r["regionid"] for r in out["regions"]]
    assert ids == list(range(1, 15))          # exactly 1-14, in order
    assert 15 not in ids and 18 not in ids     # England/Scotland/Wales/GB aggregates dropped


def test_intensity_is_mean_and_scotland_cleaner_than_wales():
    out = compute(_fixture(), GEN)
    by = {r["regionid"]: r for r in out["regions"]}
    assert by[1]["intensity"] == 15           # mean(10, 20)
    assert by[7]["intensity"] == 310          # mean(300, 320)
    assert by[1]["intensity"] < by[7]["intensity"]


def test_renewable_and_low_carbon_shares():
    out = compute(_fixture(), GEN)
    by = {r["regionid"]: r for r in out["regions"]}
    assert by[1]["renewable_pct"] == 90.0     # wind 80 + hydro 10 + solar 0
    assert by[1]["low_carbon_pct"] == 95.0    # + nuclear 5
    assert by[7]["renewable_pct"] == 25.0     # wind 20 + solar 5 (no hydro)
    assert by[7]["low_carbon_pct"] == 30.0    # + nuclear 5
    assert by[1]["mix"]["wind"] == 80.0


def test_missing_region_is_null_not_zero():
    out = compute(_fixture(), GEN)
    by = {r["regionid"]: r for r in out["regions"]}
    assert by[5]["intensity"] is None         # Yorkshire absent from fixture
    assert by[5]["renewable_pct"] is None
    assert by[5]["mix"] == {}


def test_methodology_units_and_period():
    out = compute(_fixture(), GEN)
    assert out["unit"] == "gCO2/kWh"
    assert "consumption-based" in out["methodology"]
    assert "Northern Ireland" in out["methodology"]
    assert out["basis"] == "forecast"
    assert out["period_start"] == "2026-06-10"


def test_empty_input_is_safe():
    out = compute([], GEN)
    assert len(out["regions"]) == 14
    assert all(r["intensity"] is None and r["mix"] == {} for r in out["regions"])
    assert out["period_start"] is None


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} passed")
