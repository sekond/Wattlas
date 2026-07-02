"""Offline unit tests for v10 batch-3 slices (retail wedge, curtailment-€) — no network.

Run: python -m pytest pipeline/test_v10_batch3.py -v
"""
from __future__ import annotations

from build_retail_wedge import assemble, parse_jsonstat


def _fixture():
    return {
        "id": ["geo", "time", "nrg_prc"],
        "size": [1, 1, 3],
        "dimension": {
            "geo": {"category": {"index": {"DE": 0}}},
            "time": {"category": {"index": {"2024": 0}}},
            "nrg_prc": {"category": {"index": {"NRG_SUP": 0, "NETC": 1, "TAX_FEE_LEV_CHRG": 2}}},
        },
        "value": {"0": 0.16, "1": 0.11, "2": 0.11},
    }


def test_parse_jsonstat_decodes_coords():
    rows = parse_jsonstat(_fixture())
    assert {r["nrg_prc"]: r["value"] for r in rows} == {"NRG_SUP": 0.16, "NETC": 0.11, "TAX_FEE_LEV_CHRG": 0.11}
    assert all(r["geo"] == "DE" and r["time"] == "2024" for r in rows)


def test_assemble_wedge_totals():
    out = assemble(parse_jsonstat(_fixture()))
    assert list(out) == ["DE"]
    row = out["DE"][0]
    assert row["period"] == "2024"
    assert row["energy"] == 0.16 and row["network"] == 0.11 and row["taxes_levies"] == 0.11
    assert row["total"] == 0.38            # 0.16 + 0.11 + 0.11
    assert row["currency"] == "EUR/kWh"
