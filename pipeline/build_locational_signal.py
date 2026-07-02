"""Build the Locational / market-design signal (v10 slice 6) OFFLINE by assembling
already-committed artefacts: de_regional_balance.json (SMARD control-area balance) and
curtailment.json (netztransparenz redispatch volume). Writes data/locational_signal.json.

PURE / no network. Run: python pipeline/build_locational_signal.py

THE FRAMING RULE (CLAUDE.md landmine #2): the north-south bottleneck is INTERNAL to the
single DE-LU bidding zone, so it appears in NEITHER cross-border flows NOR zonal prices.
The evidence is the control-area balance + redispatch volume. This view computes NO
simulated split price. The contested split economics are carried as a cited RANGE.
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("wattlas.build_locational_signal")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# North surplus zones vs south/west deficit zones (matches the wasted-wind deep-dive).
NORTH = ("50Hertz", "TenneT")
SOUTH = ("Amprion", "TransnetBW")


def assemble_monthly(balance_days: list[dict], curtail_days: list[dict]) -> list[dict]:
    """Per local month: mean north surplus / south deficit (GW) from control-area
    balance, redispatch volume (GWh) from curtailment, and a congestion index =
    min(north surplus, |south deficit|) — the power that is long in the north AND
    short in the south, i.e. cannot move. Pure; unit-tested."""
    north, south = defaultdict(list), defaultdict(list)
    for d in balance_days:
        m = d.get("date", "")[:7]
        bal = d.get("balance_gw", {})
        if not m or not bal:
            continue
        north[m].append(sum(bal.get(a, 0.0) for a in NORTH))
        south[m].append(sum(bal.get(a, 0.0) for a in SOUTH))
    redispatch = defaultdict(float)
    for d in curtail_days:
        m = d.get("date", "")[:7]
        if m:
            redispatch[m] += float(d.get("curtailed_mwh", 0.0) or 0.0)

    out = []
    for m in sorted(north):
        ns = sum(north[m]) / len(north[m])
        sd = sum(south[m]) / len(south[m])
        out.append({
            "month": m,
            "north_surplus_gw": round(ns, 2),
            "south_deficit_gw": round(sd, 2),
            "redispatch_gwh": round(redispatch.get(m, 0.0) / 1000.0, 1),
            "congestion_index": round(max(0.0, min(ns, -sd)), 2),
        })
    return out


# Contested bidding-zone economics — carried as a cited RANGE, never resolved.
CONTEXT = {
    "decision": "Single DE-LU bidding zone RETAINED; Aktionsplan Gebotszone (15 Dec 2025).",
    "de5_redispatch_meur": -613, "de5_welfare_meur": 339, "de5_vintage": "2019 data",
    "academic_dissent": "Other studies find <€3/MWh average split spreads — small.",
    "stance": "Wattlas shows the physical mismatch the debate is about; it takes no side "
              "and computes no split-zone price.",
}


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    bal = json.loads((DATA_DIR / "de_regional_balance.json").read_text())
    cur = json.loads((DATA_DIR / "curtailment.json").read_text())
    curtail_days = cur.get("days", []) if isinstance(cur, dict) else []
    monthly = assemble_monthly(bal.get("days", []), curtail_days)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "SMARD control-area balance + netztransparenz redispatch (assembled)",
        "unit": "GW (balance), GWh (redispatch)",
        "note": ("North-south congestion is INTERNAL to the DE-LU zone — it shows in neither "
                 "cross-border flows nor zonal prices. Evidence is control-area balance + "
                 "redispatch. No split-zone price is computed."),
        "north_areas": list(NORTH), "south_areas": list(SOUTH),
        "monthly": monthly,
        "context": CONTEXT,
        "curtailment_available": bool(curtail_days),
    }
    (DATA_DIR / "locational_signal.json").write_text(json.dumps(payload, indent=2))
    logger.info("wrote locational_signal.json — %d months, redispatch %s",
                len(monthly), "yes" if curtail_days else "unavailable")


if __name__ == "__main__":
    main()
