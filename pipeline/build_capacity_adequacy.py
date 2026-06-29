"""Build the Capacity-cost / adequacy panel (v10 slice 8) OFFLINE by assembling
already-committed artefacts: mismatch.json (residual-load profile) and dunkelflaute.json
(low-renewable spells), plus a CURATED, CITED capacity-cost table. Writes
data/capacity_adequacy.json.

PURE / no network. Run: python pipeline/build_capacity_adequacy.py

The stress indicator reuses real Wattlas data. The cost figures are from a May-2026
cabinet bill PENDING Bundestag passage — labelled "not yet law", carried as a range with
a citation (the same discipline as the France cost stack), never as settled fact.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("wattlas.build_capacity_adequacy")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# CURATED capacity-mechanism cost — provisional (May-2026 cabinet bill, pending Bundestag).
COST = {
    "tender_gw": 12, "tender_duration_h": 10, "target_year": 2031,
    "status": "provisional — May-2026 cabinet bill, pending Bundestag passage (NOT YET LAW)",
    "source": "German federal capacity-mechanism bill (cabinet draft, May 2026)",
    # Up to ~€3bn in 2031, then up to ~€2.3bn/yr 2032-2045 (consumer levy, upper estimates).
    "levy_eur_bn": ([{"year": 2031, "eur_bn": 3.0}]
                    + [{"year": y, "eur_bn": 2.3} for y in range(2032, 2046)]),
}


def stress_summary(mismatch: dict, dunkel: dict) -> dict:
    """Residual-load and Dunkelflaute stress from existing artefacts. Pure; unit-tested."""
    resid = [v for v in mismatch.get("residual_load_gw", []) if v is not None]
    total = [v for v in mismatch.get("total_load_gw", []) if v is not None]
    summ = dunkel.get("summary", {})
    mix = dunkel.get("mix", {})
    vre = lambda m: round((m.get("wind", 0.0) or 0.0) + (m.get("solar", 0.0) or 0.0), 1)
    return {
        "peak_residual_gw": round(max(resid), 1) if resid else None,
        "peak_total_load_gw": round(max(total), 1) if total else None,
        "longest_spell_h": summ.get("longest_spell_h"),
        "spell_hours_year": summ.get("spell_hours_year"),
        "low_vre_hours_year": summ.get("low_vre_hours_year"),
        "vre_share_spell_pct": vre(mix.get("dunkelflaute", {})) if mix else None,
        "vre_share_normal_pct": vre(mix.get("normal", {})) if mix else None,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    mismatch = json.loads((DATA_DIR / "mismatch.json").read_text())
    dunkel = json.loads((DATA_DIR / "dunkelflaute.json").read_text())
    stress = stress_summary(mismatch, dunkel)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "zone": mismatch.get("zone", "DE_LU"),
        "source": "Wattlas Mismatch + Dunkelflaute (stress) + curated capacity-bill figures (cost)",
        "note": ("Stress indicator is real (residual load + Dunkelflaute spells). Cost figures "
                 "are provisional — a pending bill, not yet law — and carry a citation."),
        "stress": stress,
        "cost": COST,
    }
    (DATA_DIR / "capacity_adequacy.json").write_text(json.dumps(payload, indent=2))
    logger.info("wrote capacity_adequacy.json — peak residual %s GW, longest spell %s h (cost provisional)",
                stress["peak_residual_gw"], stress["longest_spell_h"])


if __name__ == "__main__":
    main()
