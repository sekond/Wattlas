"""Offline unit tests for pipeline/build_dunkelflaute.py — no network.

Run: python -m pytest pipeline/test_dunkelflaute.py -v
or:  python pipeline/test_dunkelflaute.py
"""

from __future__ import annotations

import pandas as pd

from build_dunkelflaute import detect_spells, compute

GEN = "2026-06-24T00:00:00+00:00"


def test_detect_spells_finds_sustained_low_run():
    # 4 high, 10 low, 4 high. With a 3h rolling mean, the interior of the low block
    # stays below the threshold; the boundaries average up and drop out.
    share = pd.Series([50.0] * 4 + [2.0] * 10 + [50.0] * 4)
    runs = detect_spells(share, threshold=10, min_hours=3, roll_window=3)
    assert len(runs) == 1
    a, b = runs[0]
    assert (b - a) == 8 and 4 <= a <= 6        # interior of the low block


def test_no_spell_when_above_threshold():
    share = pd.Series([40.0] * 18)
    assert detect_spells(share, threshold=10, min_hours=3, roll_window=3) == []


def _fixture_df():
    idx = pd.date_range("2026-01-01", periods=30, freq="1h", tz="Europe/Berlin")
    win = lambda lo, hi: [lo if 10 <= h < 20 else hi for h in range(30)]   # hours 10-19 are the spell
    df = pd.DataFrame(index=idx)
    df["wind"] = win(1000, 20000)
    df["solar"] = win(500, 5000)
    df["gas"] = win(45000, 25000)
    df["coal"] = win(3000, 5000)
    df["nuclear"] = 4000
    df["hydro"] = 1000
    df["biomass"] = 3000
    df["other"] = 500
    df["load"] = 60000
    df["price"] = win(300.0, 60.0)
    return df


def test_compute_detects_event_and_mix():
    out = compute(_fixture_df(), 10, 3, GEN, roll_window=3, pad=2)
    assert out["threshold_pct"] == 10
    assert out["summary"]["spell_count"] >= 1
    assert out["summary"]["spell_hours_year"] > 0
    w = out["worst_event"]
    assert w and w["min_vre_pct"] < 10 and w["peak_price"] == 300.0
    assert len(w["hours"]) == len(w["wind"]) == len(w["price"])      # aligned series
    # gas dominates the spell mix; net imports are positive (importing) during the spell
    mix = out["mix"]["dunkelflaute"]
    assert max(mix, key=lambda k: mix[k] if k != "net_import_pct" else -1) == "gas"
    assert mix["net_import_pct"] > 0


def test_units_are_gw_and_imports_close_balance():
    out = compute(_fixture_df(), 10, 3, GEN, roll_window=3, pad=0)
    w = out["worst_event"]
    # wind during the spell ~1 GW (1000 MW -> GW); demand 60 GW
    assert all(v is None or v < 5 for v in w["wind"])      # GW, not MW
    assert all(v is None or 55 <= v <= 65 for v in w["demand"])


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} passed")
