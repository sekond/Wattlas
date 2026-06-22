"""French -> English translation layer for the French-source pipelines (RTE éCO2mix
via ODRÉ, RTE). The SINGLE place where French field names, generation-type labels and
région identifiers are mapped to English / canonical fuels and the basemap join key.

Why this exists (CLAUDE.md landmines 9 & 11; SLICE_FR_NUCLEAR.md §4): éCO2mix publishes
French labels ("nucléaire", "hydraulique", "éolien", "consommation", "ech_physiques")
and identifies régions by French name or INSEE code. NO French string is allowed to
reach the frontend or the other pipelines; every French-source builder translates
through here.

Fuel outputs are the SAME canonical fuels as pipeline/fuels.py (a test cross-checks
them, so the two cannot drift). The région crosswalk maps the éCO2mix INSEE code / name
to the **NUTS-1 code** the basemap (frontend/geo/regions_fr.topo.json) is keyed on.

Pure module: no I/O, no network, no third-party imports. Matching is accent- /
case- / separator-insensitive so "nucléaire" and "nucleaire", "Île-de-France" and
"ile de france" all resolve.
"""

from __future__ import annotations

import unicodedata


# --- éCO2mix régional: generation-type label -> canonical fuel -----------------
# The régional dataset reports combined "thermique" (fossil thermal); France's thermal
# fleet is predominantly gas, so we map it to Gas (documented approximation). Separate
# gaz/charbon/fioul are also accepted in case a finer feed is used. French wind is
# overwhelmingly onshore; "éolien en mer" is mapped to offshore when present.
ECO2MIX_GENERATION: dict[str, str] = {
    "nucleaire": "Nuclear",
    "thermique": "Gas",            # combined fossil thermal (mostly gas in FR)
    "gaz": "Gas",
    "charbon": "Hard coal",
    "fioul": "Oil",
    "eolien": "Wind onshore",
    "eolien terrestre": "Wind onshore",
    "eolien en mer": "Wind offshore",
    "solaire": "Solar",
    "hydraulique": "Hydro",
    "pompage": "Pumped storage",
    "bioenergies": "Biomass",
}

# Non-fuel éCO2mix columns -> English meaning. "ech_physiques" is the net physical
# exchange (sign convention validated at fetch: + = import); the builder derives the
# Panel-3 "imports" gap-filler from it.
ECO2MIX_FIELDS: dict[str, str] = {
    "consommation": "consumption",
    "ech_physiques": "exchanges",
    "solde": "balance",
}

# The 13 metropolitan régions: (INSEE code, NUTS-1 code, display name). NUTS-1 is the
# basemap join key (post-2016 reform — see frontend/geo/README.md). Display names are
# the official proper nouns (kept as-is; they are not translatable labels).
REGIONS: list[tuple[str, str, str]] = [
    ("11", "FR1", "Île-de-France"),
    ("24", "FRB", "Centre-Val de Loire"),
    ("27", "FRC", "Bourgogne-Franche-Comté"),
    ("28", "FRD", "Normandie"),
    ("32", "FRE", "Hauts-de-France"),
    ("44", "FRF", "Grand Est"),
    ("52", "FRG", "Pays de la Loire"),
    ("53", "FRH", "Bretagne"),
    ("75", "FRI", "Nouvelle-Aquitaine"),
    ("76", "FRJ", "Occitanie"),
    ("84", "FRK", "Auvergne-Rhône-Alpes"),
    ("93", "FRL", "Provence-Alpes-Côte d'Azur"),
    ("94", "FRM", "Corse"),
]
REGION_NUTS: list[str] = [nuts for _, nuts, _ in REGIONS]
REGION_NAME: dict[str, str] = {nuts: name for _, nuts, name in REGIONS}


def _norm(s: object) -> str:
    """Normalise for tolerant matching: strip accents, drop spaces / hyphens /
    underscores / apostrophes, casefold. 'Nucléaire', 'nucleaire' collide; so do
    'Île-de-France', 'ile de france'."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    for ch in (" ", "-", "_", ".", "'", "’", " "):
        s = s.replace(ch, "")
    return s.casefold()


_GEN_IDX = {_norm(k): v for k, v in ECO2MIX_GENERATION.items()}
_FIELD_IDX = {_norm(k): v for k, v in ECO2MIX_FIELDS.items()}
_REGION_IDX: dict[str, str] = {}
for _insee, _nuts, _name in REGIONS:
    _REGION_IDX[_norm(_insee)] = _nuts
    _REGION_IDX[_norm(_name)] = _nuts
    _REGION_IDX[_norm(_nuts)] = _nuts


def fr_fuel(label: object) -> str:
    """Canonical fuel for an éCO2mix generation-type label; unknown -> 'Other'
    (never raw French)."""
    return _GEN_IDX.get(_norm(label), "Other")


def fr_field(label: object) -> str:
    """English meaning of a non-fuel éCO2mix column; unknown -> 'Other'."""
    return _FIELD_IDX.get(_norm(label), "Other")


def region_nuts(key: object) -> str | None:
    """NUTS-1 code for a région given its INSEE code, French name, or NUTS code;
    None if unrecognised (the caller decides — never leak the raw French)."""
    return _REGION_IDX.get(_norm(key))


def region_name(nuts: object) -> str | None:
    """Display name for a NUTS-1 région code."""
    return REGION_NAME.get(str(nuts))
