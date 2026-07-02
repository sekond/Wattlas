"""Offline unit tests for the v10 "Value Layer" metrics — no network required.

Run: python -m pytest pipeline/test_v10_metrics.py -v
"""
from __future__ import annotations

import pandas as pd

from metrics import capture_metrics, cheapest_n_hours_savings, negative_price_episodes


def _hours(values, start="2025-07-02 00:00", tz="Europe/Berlin"):
    idx = pd.date_range(start=start, periods=len(values), freq="1h", tz=tz)
    return pd.Series(values, index=idx)


def _gen(cols: dict, start="2025-07-02 00:00", tz="Europe/Berlin"):
    n = len(next(iter(cols.values())))
    idx = pd.date_range(start=start, periods=n, freq="1h", tz=tz)
    return pd.DataFrame(cols, index=idx)


# ---------------------------------------------------------------- capture_metrics

def test_capture_metrics_cannibalization():
    # 4 hours, mean price = 45. Solar produces mostly in the negative hour, so its
    # capture price is far below baseload (value factor < 1) and most of its
    # generation lands in a negative-price hour. Wind spreads across dear hours, so
    # it earns above baseload.
    price = _hours([-5, 65, 40, 80])  # mean 45
    gen = _gen({
        "Solar": [80, 0, 20, 0],
        "Wind onshore": [10, 30, 20, 40],
        "Wind offshore": [5, 5, 5, 5],
    })
    out = capture_metrics(gen, price)
    assert set(out) == {"solar", "wind"}

    solar = out["solar"]
    assert solar["baseload"] == 45.0
    assert solar["capture"] == 4.0                 # (80*-5 + 20*40)/100
    assert solar["value_factor"] < 1.0             # earns less than baseload
    assert solar["neg_gen_share"] == 80.0          # 80 of 100 MWh in the neg hour

    wind = out["wind"]
    assert wind["value_factor"] > 1.0              # earns above baseload
    assert wind["neg_gen_share"] == 12.5           # 15 of 120 MWh in the neg hour
    assert len(solar["monthly"]) == 1              # single calendar month


def test_capture_metrics_empty():
    assert capture_metrics(pd.DataFrame(), _hours([1, 2])) == {}


# ------------------------------------------------------- negative_price_episodes

def test_negative_price_episodes_runs():
    # episodes of length 2 (h0-1), 3 (h3-5) and 1 (h8); 6 negative hours total
    price = _hours([-1, -2, 5, -3, -4, -5, 8, 9, -1, 7])
    out = negative_price_episodes(price)
    assert out["total_neg_hours"] == 6
    assert out["longest_episode_h"] == 3
    assert out["episodes"] == [
        {"length_hours": 1, "count": 1},
        {"length_hours": 2, "count": 1},
        {"length_hours": 3, "count": 1},
    ]
    assert out["max_in_one_day"] == 6              # all within one local day
    assert out["by_month"] == [{"month": "2025-07", "neg_hours": 6}]


def test_negative_price_episodes_none():
    out = negative_price_episodes(_hours([10, 20, 30]))
    assert out["total_neg_hours"] == 0
    assert out["episodes"] == []


# ------------------------------------------------------ cheapest_n_hours_savings

def test_cheapest_n_hours_savings_basic():
    # one day, prices 10/20/30/40 (mean 25). Charge 4 kWh in the cheapest 2 h
    # (10,20 -> mean 15) vs a flat 25 tariff.
    out = cheapest_n_hours_savings(_hours([10, 20, 30, 40]), kwh_per_day=4.0, n=2)
    assert out["days"] == 1
    assert out["flat_cost_eur"] == 36.5            # 25 * 0.004 MWh * 365
    assert out["optimized_cost_eur"] == 21.9       # 15 * 0.004 * 365
    assert out["annual_saving_eur"] == 14.6        # (0.1 - 0.06) * 365
    assert out["annual_saving_eur"] > 0


def test_cheapest_n_hours_savings_negative_prices_kept():
    # a negative cheapest hour means you are paid to charge -> bigger saving
    out = cheapest_n_hours_savings(_hours([-20, 20, 30, 40]), kwh_per_day=4.0, n=1)
    assert out["annual_saving_eur"] > 0
