"""Offline unit tests for v10 batch-2 slices (storage cannibalization, locational
signal, capacity adequacy) — no network required.

Run: python -m pytest pipeline/test_v10_batch2.py -v
"""
from __future__ import annotations

from build_storage import cannibalization_curve
from build_locational_signal import assemble_monthly
from build_capacity_adequacy import stress_summary


def test_cannibalization_monotonic():
    out = cannibalization_curve(base_spread=100.0, base_per_mw_eur_yr=10000,
                                base_gw=5, scenarios=[5, 10, 20, 40])
    spreads = [r["modelled_spread"] for r in out]
    assert spreads == sorted(spreads, reverse=True)          # non-increasing
    assert out[0]["modelled_spread"] == 100.0                # factor 1 at base_gw
    assert out[0]["assumed_gw"] == 5
    assert out[-1]["per_mw_arbitrage_eur_yr"] < out[0]["per_mw_arbitrage_eur_yr"]


def test_assemble_monthly():
    bal = [
        {"date": "2025-07-01", "balance_gw": {"50Hertz": 4, "TenneT": 1, "Amprion": -2, "TransnetBW": -3}},
        {"date": "2025-07-15", "balance_gw": {"50Hertz": 2, "TenneT": 1, "Amprion": -1, "TransnetBW": -2}},
    ]
    cur = [{"date": "2025-07-01", "curtailed_mwh": 1000}, {"date": "2025-07-02", "curtailed_mwh": 500}]
    out = assemble_monthly(bal, cur)
    assert len(out) == 1
    r = out[0]
    assert r["month"] == "2025-07"
    assert r["north_surplus_gw"] == 4.0      # ((4+1)+(2+1))/2
    assert r["south_deficit_gw"] == -4.0     # ((-2-3)+(-1-2))/2
    assert r["redispatch_gwh"] == 1.5        # (1000+500)/1000
    assert r["congestion_index"] == 4.0      # min(4.0, 4.0)


def test_stress_summary():
    mismatch = {"residual_load_gw": [10, 40.5, 20], "total_load_gw": [30, 60.4, 40]}
    dunkel = {
        "summary": {"longest_spell_h": 52, "spell_hours_year": 52, "low_vre_hours_year": 510},
        "mix": {"dunkelflaute": {"wind": 4.7, "solar": 4.2}, "normal": {"wind": 31.7, "solar": 16.9}},
    }
    s = stress_summary(mismatch, dunkel)
    assert s["peak_residual_gw"] == 40.5
    assert s["peak_total_load_gw"] == 60.4
    assert s["longest_spell_h"] == 52
    assert s["vre_share_spell_pct"] == 8.9     # 4.7 + 4.2
    assert s["vre_share_normal_pct"] == 48.6   # 31.7 + 16.9
