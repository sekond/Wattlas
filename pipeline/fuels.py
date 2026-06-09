"""Canonical fuel taxonomy and CO2 emission factors — the SINGLE source of truth
for the Python pipeline (the frontend mirror is frontend/fuels.js).

Why this exists (CLAUDE.md landmine #9): generation-by-type is messy — many
ENTSO-E production categories, "other" buckets, and gaps. We collapse the raw
ENTSO-E `psr_type` names into a small, stable set of display fuels so every view
stacks the same categories in the same order with the same colours. A fuel is
always the same thing everywhere.

Emission factors (landmine #12) are production-based, IPCC AR5 (2014) WGIII
Annex III lifecycle MEDIAN values (gCO2eq/kWh), extended with the ElectricityMaps
defaults where AR5 omits a category (oil, "unknown thermal"). They are lifecycle,
not combustion-only — state that wherever they are shown.
"""

from __future__ import annotations

# Raw ENTSO-E production-type name -> canonical display fuel.
# Coal-derived gas (a small steel/coke byproduct stream) is folded into Gas.
# The two hydro reservoir/run-of-river types collapse to "Hydro"; pumped storage
# is kept separate because it is a storage carrier, not primary generation.
FUEL_MAP: dict[str, str] = {
    "Nuclear": "Nuclear",
    "Fossil Brown coal/Lignite": "Lignite",
    "Fossil Hard coal": "Hard coal",
    "Fossil Gas": "Gas",
    "Fossil Coal-derived gas": "Gas",
    "Fossil Oil": "Oil",
    "Fossil Oil shale": "Oil",
    "Fossil Peat": "Other fossil",
    "Biomass": "Biomass",
    "Waste": "Waste",
    "Geothermal": "Geothermal",
    "Hydro Water Reservoir": "Hydro",
    "Hydro Run-of-river and poundage": "Hydro",
    "Hydro Pumped Storage": "Pumped storage",
    "Marine": "Other renewable",
    "Wind Onshore": "Wind onshore",
    "Wind Offshore": "Wind offshore",
    "Solar": "Solar",
    "Other": "Other",
    "Other renewable": "Other renewable",
}

# Canonical stacking order: dirtiest/baseload at the bottom, variable renewables
# on top, "Other" last. Kept identical to the order in frontend/fuels.js.
FUEL_ORDER: list[str] = [
    "Nuclear",
    "Lignite",
    "Hard coal",
    "Gas",
    "Oil",
    "Other fossil",
    "Biomass",
    "Waste",
    "Geothermal",
    "Hydro",
    "Pumped storage",
    "Wind offshore",
    "Wind onshore",
    "Solar",
    "Other renewable",
    "Other",
]

# Production-based lifecycle CO2 factors, gCO2eq/kWh (see module docstring).
# Pumped storage is intentionally absent: its discharge is previously generated
# energy, so build_carbon.py excludes it from both numerator and denominator
# rather than double-counting it (carbon methodology note).
EMISSION_FACTORS_GCO2_KWH: dict[str, float] = {
    "Nuclear": 12.0,
    "Lignite": 820.0,        # IPCC AR5 coal median; lignite is dirtier in reality
    "Hard coal": 820.0,      # — both use the single AR5 coal median for one citation
    "Gas": 490.0,
    "Oil": 650.0,
    "Other fossil": 700.0,   # unknown thermal default (ElectricityMaps)
    "Biomass": 230.0,
    "Waste": 230.0,          # proxied to biomass; no AR5 value (approximate)
    "Geothermal": 38.0,
    "Hydro": 24.0,
    "Wind onshore": 11.0,
    "Wind offshore": 12.0,
    "Solar": 45.0,
    "Other renewable": 700.0,  # conservatively treated as thermal-unknown
    "Other": 700.0,
}

# Short, displayable methodology label (mirror in frontend/fuels.js).
CARBON_METHODOLOGY = (
    "Production-based, IPCC AR5 lifecycle median factors. Reflects electricity "
    "generated within the zone (imports/exports excluded); lifecycle, not "
    "combustion-only; standard per-fuel factors, not plant-level measurements."
)


def to_fuel(psr_type: str) -> str:
    """Map a raw ENTSO-E production-type name to a canonical fuel (default 'Other')."""
    return FUEL_MAP.get(psr_type, "Other")
