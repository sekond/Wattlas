"""Offline unit tests for pipeline/build_uk_constraints.py — no network.

Run: python -m pytest pipeline/test_uk_constraints.py -v
or:  python pipeline/test_uk_constraints.py
"""

from __future__ import annotations

from build_uk_constraints import aggregate_monthly, _payload

GEN = "2026-06-24T00:00:00+00:00"

# Daily Constraint-Breakdown rows. Includes a non-thermal column (must be ignored),
# a malformed date row (skipped), and an empty-value row.
CSV_A = (
    "Date,Thermal constraints cost,Thermal constraints volume,Voltage constraints cost\n"
    "2025-01-05,1000000,5000,999\n"
    "2025-01-20,2000000,7000,1\n"
    "2025-02-10,500000,3000,0\n"
)
CSV_B = (
    "Date,Thermal constraints cost,Thermal constraints volume\n"
    "2025-02-15,1500000,4000\n"
    "not-a-date,123,456\n"
    "2025-03-01,,\n"
)


def test_monthly_thermal_sums_and_units():
    months = aggregate_monthly([CSV_A, CSV_B])
    by = {m["month"]: m for m in months}
    assert by["2025-01"]["cost_gbp_m"] == 3.0    # (1e6 + 2e6) / 1e6
    assert by["2025-01"]["volume_gwh"] == 12.0   # (5000 + 7000) / 1e3
    assert by["2025-02"]["cost_gbp_m"] == 2.0    # 0.5e6 + 1.5e6
    assert by["2025-02"]["volume_gwh"] == 7.0    # 3000 + 4000


def test_months_sorted_and_bad_rows_skipped():
    months = aggregate_monthly([CSV_A, CSV_B])
    assert [m["month"] for m in months] == ["2025-01", "2025-02", "2025-03"]
    assert "not-a-date"[:7] not in {m["month"] for m in months}   # malformed date dropped


def test_non_thermal_columns_ignored():
    # The voltage column (999) must not leak into the thermal cost.
    months = aggregate_monthly([CSV_A])
    jan = next(m for m in months if m["month"] == "2025-01")
    assert jan["cost_gbp_m"] == 3.0   # not 3.001


def test_payload_ok_totals_and_peak():
    months = aggregate_monthly([CSV_A, CSV_B])
    p = _payload(months, GEN)
    assert p["status"] == "ok" and p["currency"] == "GBP"
    assert p["totals"]["cost_gbp_m"] == 5.0       # 3 + 2 + 0
    assert p["totals"]["volume_gwh"] == 19.0      # 12 + 7 + 0
    assert p["totals"]["peak_month"] == "2025-01"
    assert "B6" in p["note"] and "not energy discarded by choice" in p["note"]


def test_payload_unavailable_when_empty():
    p = _payload([], GEN)
    assert p["status"] == "unavailable"
    assert p["months"] == []


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} passed")
