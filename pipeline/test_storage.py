"""Offline unit tests for pipeline/build_storage.py — no network.

Run: python -m pytest pipeline/test_storage.py -v
or:  python pipeline/test_storage.py
"""

from __future__ import annotations

from build_storage import battery_day, monthly_tb2, compute, BATTERY

GEN = "2026-06-24T00:00:00+00:00"


def test_battery_charges_cheapest_discharges_dearest():
    prof = [50.0] * 24
    prof[12], prof[13] = 10.0, 20.0     # cheapest two
    prof[19], prof[20] = 100.0, 90.0    # dearest two
    d = battery_day(prof, power_mw=1, duration_h=2, round_trip=0.85)
    assert d["charge_hours"] == [12, 13]
    assert d["discharge_hours"] == [19, 20]
    assert d["charge_mw"][12] == -1 and d["charge_mw"][13] == -1
    assert d["discharge_mw"][19] == 0.85 and d["discharge_mw"][20] == 0.85
    # captured = 0.85*(100+90) - (10+20) = 161.5 - 30
    assert d["captured_eur"] == 131.5


def test_captured_is_upper_bound_below_lossless():
    prof = [50.0] * 24
    prof[0], prof[1] = 0.0, 0.0
    prof[12], prof[13] = 200.0, 200.0
    lossless = battery_day(prof, 1, 2, 1.0)["captured_eur"]    # 1.0*(400) - 0 = 400
    real = battery_day(prof, 1, 2, 0.85)["captured_eur"]       # 0.85*400 - 0 = 340
    assert lossless == 400.0 and real == 340.0
    assert real < lossless                                     # efficiency loss pulls it below


def test_monthly_tb2_groups_and_means():
    days = [{"date": "2025-01-05", "tb2": 100.0}, {"date": "2025-01-20", "tb2": 200.0},
            {"date": "2025-02-10", "tb2": 60.0}, {"date": "2025-02-11", "tb2": None}]
    out = monthly_tb2(days)
    assert out == [{"month": "2025-01", "mean_tb2": 150.0}, {"month": "2025-02", "mean_tb2": 60.0}]


def test_compute_shape_and_labels():
    pulse = {"zone": "DE_LU", "period_start": "2025-06-23", "period_end": "2026-06-22",
             "all_mean": [50.0] * 24}
    pulse["all_mean"][13] = 10.0; pulse["all_mean"][19] = 100.0
    spread = {"days": [{"date": "2025-06-01", "tb2": 120.0}, {"date": "2025-07-01", "tb2": 80.0}]}
    out = compute(pulse, spread, GEN)
    assert out["battery"]["foresight"] == "perfect (upper bound)"
    assert out["unit_power"].startswith("MW") and out["unit_energy"].startswith("MWh")
    assert "upper bound" in out["note"].lower()
    assert out["spread"]["mean_tb2_eur_mwh"] == 100.0          # mean(120, 80)
    assert len(out["capacity"]) >= 12 and {"country", "year", "power_gw"} <= set(out["capacity"][0])
    assert out["day"]["captured_eur"] is not None


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} passed")
