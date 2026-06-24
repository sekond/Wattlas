"""Offline unit tests for pipeline/build_iberian_blackout.py — no network.

Run: python -m pytest pipeline/test_iberian_blackout.py -v
or:  python pipeline/test_iberian_blackout.py
"""

from __future__ import annotations

import pandas as pd

from build_iberian_blackout import assemble_timeline, compute, MILESTONES, OFFICIAL

GEN = "2026-06-24T00:00:00+00:00"


def _fixture():
    idx = pd.date_range("2025-04-28 10:00", periods=5, freq="1h", tz="Europe/Madrid")
    es = [26000.0, 26000.0, 26000.0, 3000.0, 5000.0]   # collapse between 12:00 and 13:00
    pt = [5000.0, 5000.0, float("nan"), 800.0, 1200.0]  # a gap to exercise null handling
    return pd.DataFrame({"ES": es, "PT": pt}, index=idx)


def test_timeline_in_gw_and_gaps_null():
    tl = assemble_timeline(_fixture())
    assert len(tl) == 5
    assert tl[0]["es_load_gw"] == 26.0 and tl[3]["es_load_gw"] == 3.0   # MW -> GW
    assert tl[2]["pt_load_gw"] is None                                  # gap stays null, not zero


def test_summary_pre_event_and_trough():
    out = compute(_fixture(), GEN)
    s = out["summary"]
    assert s["pre_event_load_gw"]["ES"] == 26.0      # peak before 12:33
    assert s["trough_load_gw"]["ES"] == 3.0          # min in the outage afternoon
    assert s["pre_event_load_gw"]["PT"] == 5.0
    assert s["trough_load_gw"]["PT"] == 0.8          # PT collapses to near zero


def test_sourced_milestones_and_no_asserted_cause():
    out = compute(_fixture(), GEN)
    assert out["event_date"] == "2025-04-28" and out["zones"] == ["ES", "PT"]
    assert len(out["milestones"]) == len(MILESTONES) >= 8
    assert out["milestones"][0]["t"].startswith("2025-04-28T12:33")     # the collapse moment
    # cause is CITED to the official report, never asserted by Wattlas
    off = out["official"]
    assert off["report_url"].startswith("https://www.entsoe.eu/")
    assert "combination" in off["conclusion"].lower() and "single" in off["conclusion"].lower()
    assert off["quote"]                                                 # the non-blame quote
    # the page must not carry a Wattlas-asserted top-level cause
    assert "cause" not in out
    assert "does not assert a cause" in out["note"]


def test_sources_present():
    out = compute(_fixture(), GEN)
    assert len(out["sources"]) >= 3
    assert any("entsoe" in s["url"].lower() for s in out["sources"])


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} passed")
