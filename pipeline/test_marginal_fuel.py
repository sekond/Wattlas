"""Offline unit tests for the marginal-fuel model (v10 slice 9) — no network."""
from __future__ import annotations

from build_marginal_fuel import classify, gas_marginal_cost


def test_gas_marginal_cost():
    # 40/0.5 + 80*0.4 = 80 + 32 = 112
    assert gas_marginal_cost(40.0, eua_eur_t=80.0, eff=0.5, carbon=0.4) == 112.0


def test_classify_buckets():
    gmc = 100.0
    assert classify(120, gmc) == "gas"         # >= 0.85*gmc
    assert classify(90, gmc) == "gas"
    assert classify(-5, gmc) == "renewable"    # negative
    assert classify(10, gmc) == "renewable"    # < 0.25*gmc
    assert classify(50, gmc) == "other"        # in between
