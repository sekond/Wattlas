"""Build the curated electricity-cost comparison for the France-nuclear Panel 4:
"what does the power really cost?" — a symmetric, sourced €/MWh stack per technology.

    python pipeline/build_fr_costs.py

Writes data/fr_costs.json.

NOT A LIVE FEED (SLICE §2 Panel 4): this is the one section transcribed from published
studies, committed as static JSON. Each figure carries a **source** and the technology a
**range** — the real ranges are wide and assumption-dependent (cost of capital dominates
new nuclear). Central values are illustrative, not "the truth".

SYMMETRY IS A CREDIBILITY REQUIREMENT (landmine): the hidden-cost lens (waste &
decommissioning, system & integration, implicit support) is applied to **every**
technology, never nuclear alone. Nuclear's back-end is large in total (Cigéo ≈ €33–37bn)
but small per MWh and **provisioned** (the defensible critique is provision *adequacy*,
not "ignored" cost); renewables' system-integration costs rise with their share. Takes no
side — the point is that the ranking depends on what you count.

Sources: Lazard LCOE+ 2024 · Cour des comptes (EPR/EPR2) · ANDRA / Cigéo · OECD-NEA
system costs · IRENA. (Source lean: Lazard = US new-build; OECD-NEA = the Nuclear Energy
Agency.)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("build_fr_costs")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SOURCE = "Curated published estimates (not a live feed)"

# Stack components (in stacking order); "sticker price" shows only `plant`.
COMPONENTS = [
    {"key": "plant", "label": "Plant (LCOE)", "color": "#4a78a6",
     "note": "levelised plant-level cost (the headline 'sticker price')"},
    {"key": "waste", "label": "Waste & decommissioning", "color": "#c08a2e",
     "note": "back-end; large in total but small per MWh, and provisioned — not ignored"},
    {"key": "system", "label": "System & integration", "color": "#4aa6a0",
     "note": "firming, grid, balancing, storage; rises with variable-renewable share"},
    {"key": "support", "label": "Implicit support", "color": "#9a7fb0",
     "note": "historic feed-in tariffs / implicit public support"},
]
_COMPONENT_KEYS = [c["key"] for c in COMPONENTS]

# Curated central €/MWh per technology + components, a full-cost range, and sources.
TECHNOLOGIES = [
    {"name": "Solar (utility)", "plant": 55, "waste": 1, "system": 18, "support": 3,
     "sticker_range": [40, 65], "full_range": [60, 100],
     "sources": ["Lazard LCOE+ 2024", "OECD-NEA system costs", "IRENA"]},
    {"name": "Wind (onshore)", "plant": 50, "waste": 1, "system": 16, "support": 3,
     "sticker_range": [40, 75], "full_range": [55, 95],
     "sources": ["Lazard LCOE+ 2024", "OECD-NEA system costs", "IRENA"]},
    {"name": "Nuclear — existing fleet", "plant": 50, "waste": 5, "system": 1, "support": 3,
     "sticker_range": [45, 60], "full_range": [50, 70],
     "sources": ["Cour des comptes", "ANDRA / Cigéo"]},
    {"name": "Nuclear — new build (EPR2)", "plant": 110, "waste": 6, "system": 1, "support": 4,
     "sticker_range": [90, 150], "full_range": [100, 190],
     "sources": ["Cour des comptes (EPR/EPR2)", "OECD-NEA", "ANDRA / Cigéo"]},
]

TAKEAWAYS = {
    "sticker": "Sticker price: wind and solar beat new nuclear roughly two-to-one — "
               "and match France's amortised existing fleet.",
    "full": "Full cost: France's amortised fleet looks cheapest, renewables' system costs "
            "narrow their lead, and new nuclear stays priciest. The ranking depends on "
            "what you count.",
}
SOURCES = ["Lazard LCOE+ 2024", "Cour des comptes (EPR/EPR2)", "ANDRA / Cigéo",
           "OECD-NEA system costs", "IRENA"]


# --------------------------------------------------------------------------- #
# Pure, offline-testable
# --------------------------------------------------------------------------- #

def build_costs() -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": SOURCE, "unit": "EUR/MWh",
        "note": "Illustrative central values; ranges are wide and assumption-dependent. "
                "The hidden-cost lens is applied symmetrically to every technology; "
                "nuclear's back-end is provisioned, not ignored. Takes no side.",
        "components": COMPONENTS,
        "technologies": TECHNOLOGIES,
        "takeaways": TAKEAWAYS,
        "sources": SOURCES,
    }


def validate(costs: dict) -> None:
    """Enforce the credibility invariants: symmetric components on every technology, a
    full-cost total inside the stated range, sticker (plant) inside its range, and a
    source on every technology. Raises ValueError on any violation."""
    keys = [c["key"] for c in costs["components"]]
    assert keys == _COMPONENT_KEYS, f"component order changed: {keys}"
    for t in costs["technologies"]:
        for k in _COMPONENT_KEYS:                      # symmetric: every tech has every adder
            if k not in t or t[k] < 0:
                raise ValueError(f"{t['name']}: missing/negative component {k}")
        full = sum(t[k] for k in _COMPONENT_KEYS)
        lo, hi = t["full_range"]
        if not (lo <= full <= hi):
            raise ValueError(f"{t['name']}: full cost {full} outside range {t['full_range']}")
        slo, shi = t["sticker_range"]
        if not (slo <= t["plant"] <= shi):
            raise ValueError(f"{t['name']}: plant {t['plant']} outside sticker range {t['sticker_range']}")
        if not t.get("sources"):
            raise ValueError(f"{t['name']}: no source cited")


def build() -> dict:
    costs = build_costs()
    validate(costs)
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "fr_costs.json").write_text(
        json.dumps(costs, ensure_ascii=False, indent=0), encoding="utf-8")
    for t in costs["technologies"]:
        full = sum(t[k] for k in _COMPONENT_KEYS)
        log.info("  %-28s sticker €%d  full €%d/MWh  range %s",
                 t["name"], t["plant"], full, t["full_range"])
    return costs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    build()
