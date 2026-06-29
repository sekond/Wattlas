"""German -> English translation layer for the German-source pipelines (MaStR,
SMARD). The SINGLE place where German field names and category labels are mapped
to English / canonical fuels.

Why this exists (CLAUDE.md landmines 9 & 11; docs/slices/SLICE_DE_WASTED_WIND.md §4):
MaStR and SMARD publish German labels ("Solare Strahlungsenergie", "Braunkohle",
"In Betrieb", "Windkraft auf See"). NO German string is allowed to reach the
frontend or the ENTSO-E pipeline. Every downstream module (build_mastr_capacity,
build_regional_balance) translates through here, so the mapping lives in one
audited place rather than being re-hardcoded per module.

Fuel outputs are the SAME canonical fuels as pipeline/fuels.py / frontend/fuels.js
(a fuel is always the same thing, with the same colour, everywhere). They are kept
as plain literals here so this module stays pure and dependency-free; a test
(test_de_fields.py) cross-checks them against fuels.FUEL_ORDER so the two cannot
drift.

Representation note to validate on first real fetch (landmine 12): open-mastr may
surface some of these catalog fields as German TEXT (handled here) or as numeric
catalog CODES. If Step 3 finds coded values, add a code->text map at the call site
or extend the dicts below — do not let a raw code or German label leak downstream.

Pure module: no I/O, no network, no third-party imports. Lookups are
whitespace/case/hyphen-insensitive so "Solare Strahlungsenergie" and
"SolareStrahlungsenergie" both resolve.
"""

from __future__ import annotations

# --- MaStR: Energieträger (energy carrier) -> canonical fuel -------------------
# Wind is intentionally NOT in this dict: it is resolved by mastr_fuel() together
# with the Lage (on land / at sea) field into "Wind onshore" / "Wind offshore".
MASTR_ENERGIETRAEGER: dict[str, str] = {
    "Solare Strahlungsenergie": "Solar",
    "Biomasse": "Biomass",
    "Wasser": "Hydro",
    "Geothermie": "Geothermal",
    "Kernenergie": "Nuclear",
    "Braunkohle": "Lignite",
    "Steinkohle": "Hard coal",
    "Erdgas": "Gas",
    "Grubengas": "Gas",            # coal-mine gas — a coal-derived stream
    "Mineralölprodukte": "Oil",
    "Mineraloelprodukte": "Oil",   # umlaut-free variant some exports use
    "Deponiegas": "Biomass",       # landfill gas
    "Klärgas": "Biomass",          # sewage gas
    "Klaergas": "Biomass",
    "Klärschlamm": "Other fossil", # sewage sludge
    "Nicht biogener Abfall": "Waste",
    "Biogener Abfall": "Biomass",
    "Andere Gase": "Other fossil",
    "Wärme": "Other",
    "Speicher": "Other",           # storage carrier (battery etc.)
}

# MaStR: Lage der Einheit (wind only) -> onshore/offshore.
MASTR_WIND_LAGE: dict[str, str] = {
    "Windkraft an Land": "onshore",
    "Windkraft auf See": "offshore",
}

# Offshore-wind detection (validated against the real bulk export, Step 3):
# the documented `Lage` field is EMPTY in the Gesamtdatenexport, so onshore/offshore
# cannot be read from it. Offshore units are instead identifiable because they sit in
# the German Exclusive Economic Zone (Bundesland "Ausschließliche Wirtschaftszone",
# which has no Landkreis) or carry a distance-to-coast. `is_offshore_wind()` checks
# all three signals so the split is right whichever the export populates.
OFFSHORE_BUNDESLAND = "Ausschließliche Wirtschaftszone"
WIND_OFFSHORE_LAGE = "Windkraft auf See"

# MaStR: EinheitBetriebsstatus (operating status) -> English.
MASTR_STATUS: dict[str, str] = {
    "In Betrieb": "Operating",
    "In Planung": "Planned",
    "Vorübergehend stillgelegt": "Temporarily shut down",
    "Endgültig stillgelegt": "Decommissioned",
    "Dauerhaft stillgelegt": "Decommissioned",
}

# --- SMARD: generation-type label (German) -> canonical fuel -------------------
SMARD_GENERATION: dict[str, str] = {
    "Braunkohle": "Lignite",
    "Steinkohle": "Hard coal",
    "Erdgas": "Gas",
    "Kernenergie": "Nuclear",
    "Pumpspeicher": "Pumped storage",
    "Sonstige Konventionelle": "Other fossil",
    "Wind Offshore": "Wind offshore",
    "Wind Onshore": "Wind onshore",
    "Photovoltaik": "Solar",
    "Wasserkraft": "Hydro",
    "Biomasse": "Biomass",
    "Sonstige Erneuerbare": "Other renewable",
}

# --- SMARD: control area (Regelzone) -> canonical short TSO name ---------------
# Closed set of four German TSOs. Variants (legal-entity suffixes) fold to the
# short name used everywhere else in the slice.
CONTROL_AREAS: dict[str, str] = {
    "50Hertz": "50Hertz",
    "50Hertz Transmission": "50Hertz",
    "TenneT": "TenneT",
    "TenneT TSO": "TenneT",
    "Amprion": "Amprion",
    "TransnetBW": "TransnetBW",
}

# Canonical names, in the north->south order the slice presents them.
CONTROL_AREA_ORDER: list[str] = ["50Hertz", "TenneT", "Amprion", "TransnetBW"]


def _norm(s: object) -> str:
    """Normalise a label for tolerant matching: drop whitespace, casefold, strip
    hyphens and dots. So 'Solare Strahlungsenergie', 'SolareStrahlungsenergie' and
    'solare strahlungsenergie' all collide on one key."""
    if s is None:
        return ""
    return "".join(str(s).split()).casefold().replace("-", "").replace(".", "")


_ENERGIETRAEGER_IDX = {_norm(k): v for k, v in MASTR_ENERGIETRAEGER.items()}
_LAGE_IDX = {_norm(k): v for k, v in MASTR_WIND_LAGE.items()}
_STATUS_IDX = {_norm(k): v for k, v in MASTR_STATUS.items()}
_SMARD_IDX = {_norm(k): v for k, v in SMARD_GENERATION.items()}
_CONTROL_IDX = {_norm(k): v for k, v in CONTROL_AREAS.items()}
_WIND = _norm("Wind")


def is_offshore_wind(lage: object = None, bundesland: object = None,
                     kuestenentfernung: object = None) -> bool:
    """True if a MaStR wind unit is offshore. Checks, in order: the Lage field
    (if ever populated), the Exclusive Economic Zone Bundesland, and a positive
    distance-to-coast. Defaults to onshore (False) — most German wind is onshore."""
    if _norm(lage) == _norm(WIND_OFFSHORE_LAGE):
        return True
    if _norm(bundesland) == _norm(OFFSHORE_BUNDESLAND):
        return True
    try:
        if kuestenentfernung is not None and float(kuestenentfernung) > 0:
            return True
    except (TypeError, ValueError):
        pass
    return False


def mastr_fuel(energietraeger: object, lage: object = None,
               bundesland: object = None, kuestenentfernung: object = None) -> str:
    """Canonical fuel for a MaStR unit. Wind is split into onshore/offshore via
    is_offshore_wind() (Lage / EEZ Bundesland / coast distance), defaulting to
    onshore. Anything unrecognised -> 'Other' (never German)."""
    key = _norm(energietraeger)
    if key == _WIND:
        return ("Wind offshore" if is_offshore_wind(lage, bundesland, kuestenentfernung)
                else "Wind onshore")
    return _ENERGIETRAEGER_IDX.get(key, "Other")


def mastr_status(status: object) -> str:
    """English operating status; unknown -> 'Unknown' (never German)."""
    return _STATUS_IDX.get(_norm(status), "Unknown")


def mastr_is_operating(status: object) -> bool:
    """True only for units 'In Betrieb'. Used to filter the capacity aggregation
    (we count operating plants, not planned or decommissioned ones)."""
    return _STATUS_IDX.get(_norm(status)) == "Operating"


def smard_fuel(label: object) -> str:
    """Canonical fuel for a SMARD generation-type label; unknown -> 'Other'."""
    return _SMARD_IDX.get(_norm(label), "Other")


def control_area(name: object) -> str:
    """Canonical short TSO name for a SMARD control area; unknown -> 'Other'."""
    return _CONTROL_IDX.get(_norm(name), "Other")
