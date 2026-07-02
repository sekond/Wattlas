"""Offline unit tests for pipeline/build_fr_nuclear_availability.py — no network.

Run: python -m pytest pipeline/test_fr_nuclear_availability.py -v
or:  python pipeline/test_fr_nuclear_availability.py
"""

from __future__ import annotations

from build_fr_nuclear_availability import (
    assemble_months, parse_intervals, monthly_available_gw, _parse_dt,
)

# Two monthly aggregation rows (MW): a winter peak and a summer dip; France exporting.
_ROWS = [
    {"month": "2025-05", "nuc": 34300, "hyd": 7500, "gas": 400, "eo": 4600, "sol": 4900,
     "bio": 800, "coal": 100, "oil": 100, "ech": -10000, "dem": 41900},   # summer dip
    {"month": "2025-01", "nuc": 52100, "hyd": 9700, "gas": 4000, "eo": 7700, "sol": 1400,
     "bio": 900, "coal": 300, "oil": 200, "ech": -9100, "dem": 66600},     # winter peak
]


def test_units_and_fields():
    out = assemble_months(_ROWS)
    assert [m["month"] for m in out] == ["2025-01", "2025-05"]   # chronological
    jan = out[0]
    assert jan["nuclear_gw"] == 52.1                              # MW -> GW
    assert jan["demand_gw"] == 66.6
    assert jan["other_gw"] == 1.4                                 # bio+coal+oil = 0.9+0.3+0.2
    assert jan["available_gw"] is None                           # OAuth pending


def test_net_export_sign():
    out = {m["month"]: m for m in assemble_months(_ROWS)}
    # ech_physiques < 0 means France is exporting -> net_export_gw > 0
    assert out["2025-05"]["net_export_gw"] == 10.0
    assert out["2025-01"]["net_export_gw"] == 9.1
    assert all(m["net_export_gw"] > 0 for m in out.values())     # exporter both months


def test_summer_dip_below_winter():
    out = {m["month"]: m for m in assemble_months(_ROWS)}
    assert out["2025-05"]["nuclear_gw"] < out["2025-01"]["nuclear_gw"]


def test_empty_safe():
    assert assemble_months([]) == []


# --- RTE OAuth available-capacity path (offline; inline fixtures) ------------- #

def test_assemble_months_with_available_map():
    out = {m["month"]: m for m in assemble_months(_ROWS, {"2025-01": 58.5})}
    assert out["2025-01"]["available_gw"] == 58.5      # filled from RTE map
    assert out["2025-05"]["available_gw"] is None      # absent from map -> still null


def test_parse_intervals_dedup_and_derive():
    # Same identifier twice: the higher version must win (avoid double-counting).
    # Third record omits unavailable_capacity -> derive it as installed - available.
    records = [
        {"identifier": "A", "version": 1, "affected_asset_or_unit_installed_capacity": 1000,
         "values": [{"start_date": "2025-06-01T00:00:00Z", "end_date": "2025-06-10T00:00:00Z",
                     "unavailable_capacity": 300}]},
        {"identifier": "A", "version": 2, "affected_asset_or_unit_installed_capacity": 1000,
         "values": [{"start_date": "2025-06-01T00:00:00Z", "end_date": "2025-06-10T00:00:00Z",
                     "unavailable_capacity": 400}]},   # supersedes v1
        {"identifier": "B", "version": 1, "affected_asset_or_unit_installed_capacity": 900,
         "values": [{"start_date": "2025-06-05T00:00:00Z", "end_date": "2025-06-06T00:00:00Z",
                     "available_capacity": 200}]},      # derive unavailable = 900 - 200 = 700
    ]
    intervals = parse_intervals(records)
    assert len(intervals) == 2                          # A deduped to one, plus B
    assert sorted(u for _s, _e, u in intervals) == [400.0, 700.0]


def test_monthly_available_gw_full_month_and_sum():
    installed = 63000.0
    whole_june = (_parse_dt("2025-05-01T00:00:00Z"), _parse_dt("2025-08-01T00:00:00Z"), 5000.0)
    out = monthly_available_gw([whole_june], installed, ["2025-06", "2025-09"])
    assert out["2025-06"] == 58.0                        # 63000 - 5000 out all month
    assert out["2025-09"] == 63.0                        # no overlap -> fully available
    # Two units out all month -> unavailability sums.
    out2 = monthly_available_gw(
        [whole_june, (_parse_dt("2025-05-01T00:00:00Z"), _parse_dt("2025-08-01T00:00:00Z"), 1000.0)],
        installed, ["2025-06"])
    assert out2["2025-06"] == 57.0                       # 63000 - 6000


def test_monthly_available_gw_time_weighted_partial():
    # 7200 MW out for a 240h window fully inside June (720h, no DST) -> mean 2400 MW.
    installed = 63000.0
    partial = (_parse_dt("2025-06-10T00:00:00Z"), _parse_dt("2025-06-20T00:00:00Z"), 7200.0)
    out = monthly_available_gw([partial], installed, ["2025-06"])
    assert out["2025-06"] == 60.6                        # 63000 - 7200*240/720 = 60600


def test_monthly_available_gw_handles_dst_month():
    # March has a spring-forward (743h, not 720). A constant full-month outage still
    # yields installed - u regardless of the odd hour count.
    installed = 63000.0
    whole_march = (_parse_dt("2025-02-15T00:00:00Z"), _parse_dt("2025-04-15T00:00:00Z"), 5000.0)
    out = monthly_available_gw([whole_march], installed, ["2025-03"])
    assert out["2025-03"] == 58.0


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} passed")
