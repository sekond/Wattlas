"""Offline unit tests for pipeline/build_nordic_zones.py — no network.

Run: python -m pytest pipeline/test_nordic_zones.py -v
or:  python pipeline/test_nordic_zones.py
"""

from __future__ import annotations

import pandas as pd

from build_nordic_zones import compute, ZONES

GEN = "2026-01-01T00:00:00+00:00"
ALL_CODES = [code for _e, code, _c, _t in ZONES]


def _fixture() -> pd.DataFrame:
    """Constant price per zone over Jan+Feb 2025. The UTC window sits safely inside
    both month boundaries (even after the +1h/+2h shift to CET/EET) so the local
    month grouping is exactly {2025-01, 2025-02} for every zone. Five zones are
    deliberately ABSENT to exercise null handling. Constant values make every
    monthly mean and avg exact regardless of DST/tz details."""
    idx = pd.date_range("2025-01-02 00:00", "2025-02-27 00:00", freq="1h",
                        tz="UTC", inclusive="left")
    vals = {"SE1": 10.0, "SE4": 70.0, "NO2": 60.0, "NO4": 15.0,
            "DK1": 55.0, "DK2": 65.0, "FI": 40.0}   # SE2/SE3/NO1/NO3/NO5 omitted
    return pd.DataFrame({k: pd.Series(v, index=idx) for k, v in vals.items()})


def test_all_twelve_zones_present_and_shaped():
    out = compute(_fixture(), GEN)
    assert [z["code"] for z in out["zones"]] == ALL_CODES
    for z in out["zones"]:
        assert set(z) == {"code", "country", "name", "avg_price", "months"}
        assert len(z["months"]) == len(out["months"])
    assert out["unit"] == "EUR/MWh"
    assert out["generated_at"] == GEN


def test_month_axis_is_exactly_two_months():
    out = compute(_fixture(), GEN)
    assert out["months"] == ["2025-01", "2025-02"]


def test_avg_prices_and_north_cheaper_than_south():
    out = compute(_fixture(), GEN)
    avg = {z["code"]: z["avg_price"] for z in out["zones"]}
    assert avg["SE1"] == 10.0 and avg["SE4"] == 70.0      # SE: north < south
    assert avg["NO4"] == 15.0 and avg["NO2"] == 60.0      # NO: north < south
    assert avg["FI"] == 40.0
    assert avg["SE1"] < avg["SE4"]                        # the headline gradient


def test_missing_zone_is_null_not_zero():
    out = compute(_fixture(), GEN)
    se2 = next(z for z in out["zones"] if z["code"] == "SE2")
    assert se2["avg_price"] is None
    assert se2["months"] == [None, None]


def test_within_country_gap_is_max_minus_min():
    out = compute(_fixture(), GEN)
    w = out["within_country_gap"]
    assert w["SE"] == {"months": [60.0, 60.0], "avg_gap": 60.0}   # 70 - 10
    assert w["NO"] == {"months": [45.0, 45.0], "avg_gap": 45.0}   # 60 - 15
    assert w["DK"] == {"months": [10.0, 10.0], "avg_gap": 10.0}   # 65 - 55
    assert "FI" not in w                                          # single zone, no gap


def test_period_reflects_real_coverage():
    out = compute(_fixture(), GEN)
    assert out["period_start"] == "2025-01-02"     # first complete local day
    assert out["period_end"] is not None
    assert out["period_start"] <= out["period_end"]


def test_empty_input_is_safe():
    out = compute(pd.DataFrame(), GEN)
    assert len(out["zones"]) == 12
    assert all(z["avg_price"] is None and z["months"] == [] for z in out["zones"])
    assert out["months"] == []
    assert out["period_start"] is None and out["period_end"] is None
    assert out["within_country_gap"]["SE"] == {"months": [], "avg_gap": None}


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} passed")
