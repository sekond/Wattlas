"""Offline unit tests for pipeline/build_regional_balance.py — no network.

Run: python -m pytest pipeline/test_regional_balance.py -v
or:  python pipeline/test_regional_balance.py
"""

from __future__ import annotations

from build_regional_balance import assemble_days, to_avg_gw


def test_mwh_per_day_to_avg_gw():
    # 24,000 MWh over a day = 1,000 MW avg = 1.0 GW
    assert to_avg_gw(24000) == 1.0
    assert to_avg_gw(0) == 0.0
    assert to_avg_gw(285711) == 11.9   # the validated 50Hertz sample (285,711/24/1000 ≈ 11.9 GW)


def test_balance_sign_north_surplus_south_deficit():
    by_area = {
        # north: generation > load -> positive balance
        "50Hertz":    {"2026-06-20": {"gen_mwh": 285711, "load_mwh": 231883}},
        # south: load > generation -> negative balance
        "TransnetBW": {"2026-06-20": {"gen_mwh": 96000,  "load_mwh": 168000}},
    }
    days = assemble_days(by_area, ["50Hertz", "TransnetBW"])
    assert len(days) == 1
    d = days[0]
    assert d["date"] == "2026-06-20"
    assert d["balance_gw"]["50Hertz"] > 0      # surplus
    assert d["balance_gw"]["TransnetBW"] < 0   # deficit
    # balance == generation − load (in avg GW)
    assert d["balance_gw"]["50Hertz"] == round(d["generation_gw"]["50Hertz"] - d["load_gw"]["50Hertz"], 2)


def test_gaps_stay_gaps_not_zeros():
    # An area missing a date must be ABSENT that day, never zero-filled.
    by_area = {
        "50Hertz":    {"2026-06-19": {"gen_mwh": 100000, "load_mwh": 90000},
                       "2026-06-20": {"gen_mwh": 110000, "load_mwh": 95000}},
        "Amprion":    {"2026-06-20": {"gen_mwh": 80000,  "load_mwh": 140000}},  # only one day
    }
    days = assemble_days(by_area, ["50Hertz", "Amprion"])
    by_date = {d["date"]: d for d in days}
    assert "Amprion" not in by_date["2026-06-19"]["balance_gw"]   # gap, not 0
    assert "Amprion" in by_date["2026-06-20"]["balance_gw"]
    # days are sorted ascending
    assert [d["date"] for d in days] == ["2026-06-19", "2026-06-20"]


def test_missing_load_or_gen_skips_area():
    by_area = {"50Hertz": {"2026-06-20": {"gen_mwh": 100000, "load_mwh": None}}}
    days = assemble_days(by_area, ["50Hertz"])
    assert days == []   # no usable area that day -> no record


def test_empty_safe():
    assert assemble_days({}, ["50Hertz"]) == []


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} passed")
