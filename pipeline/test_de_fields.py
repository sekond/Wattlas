"""Offline unit tests for pipeline/de_fields.py — no network required.

Run: python -m pytest pipeline/test_de_fields.py -v
or:  python pipeline/test_de_fields.py   (falls back to a simple runner)
"""

from __future__ import annotations

import fuels
from de_fields import (
    CONTROL_AREA_ORDER,
    MASTR_ENERGIETRAEGER,
    OFFSHORE_BUNDESLAND,
    SMARD_GENERATION,
    control_area,
    is_offshore_wind,
    mastr_fuel,
    mastr_is_operating,
    mastr_status,
    smard_fuel,
)

_CANON = set(fuels.FUEL_ORDER)


def test_wind_split_by_lage():
    assert mastr_fuel("Wind", "Windkraft an Land") == "Wind onshore"
    assert mastr_fuel("Wind", "Windkraft auf See") == "Wind offshore"


def test_wind_defaults_to_onshore_without_lage():
    # Most German wind is onshore; missing/unknown Lage must not become "Other".
    assert mastr_fuel("Wind") == "Wind onshore"
    assert mastr_fuel("Wind", None) == "Wind onshore"
    assert mastr_fuel("Wind", "irgendwas") == "Wind onshore"


def test_offshore_detected_via_eez_bundesland():
    # The real bulk export leaves Lage empty; offshore is the EEZ Bundesland or a
    # distance-to-coast (validated Step 3).
    assert is_offshore_wind(bundesland=OFFSHORE_BUNDESLAND) is True
    assert is_offshore_wind(bundesland="Niedersachsen") is False
    assert is_offshore_wind(kuestenentfernung=30) is True
    assert is_offshore_wind(kuestenentfernung=0) is False
    assert is_offshore_wind(kuestenentfernung=None) is False
    assert is_offshore_wind() is False
    # routed through mastr_fuel with the real signals
    assert mastr_fuel("Wind", bundesland=OFFSHORE_BUNDESLAND) == "Wind offshore"
    assert mastr_fuel("Wind", bundesland="Schleswig-Holstein") == "Wind onshore"


def test_mastr_common_fuels():
    assert mastr_fuel("Solare Strahlungsenergie") == "Solar"
    assert mastr_fuel("Braunkohle") == "Lignite"
    assert mastr_fuel("Steinkohle") == "Hard coal"
    assert mastr_fuel("Erdgas") == "Gas"
    assert mastr_fuel("Kernenergie") == "Nuclear"
    assert mastr_fuel("Biomasse") == "Biomass"
    assert mastr_fuel("Wasser") == "Hydro"


def test_normalisation_is_tolerant():
    # Whitespace, case and the umlaut-free Energieträger variant all resolve.
    assert mastr_fuel("SolareStrahlungsenergie") == "Solar"
    assert mastr_fuel("solare  strahlungsenergie") == "Solar"
    assert mastr_fuel("Mineraloelprodukte") == "Oil"
    assert mastr_fuel("Mineralölprodukte") == "Oil"


def test_unknown_carrier_is_other_not_german():
    assert mastr_fuel("Flux-Kompensator") == "Other"
    assert mastr_fuel(None) == "Other"
    assert mastr_fuel("") == "Other"


def test_operating_filter():
    assert mastr_is_operating("In Betrieb") is True
    assert mastr_is_operating("InBetrieb") is True          # tolerant
    assert mastr_is_operating("In Planung") is False
    assert mastr_is_operating("Endgültig stillgelegt") is False
    assert mastr_is_operating("Vorübergehend stillgelegt") is False
    assert mastr_is_operating(None) is False


def test_status_translation():
    assert mastr_status("In Betrieb") == "Operating"
    assert mastr_status("In Planung") == "Planned"
    assert mastr_status("Endgültig stillgelegt") == "Decommissioned"
    assert mastr_status("Dauerhaft stillgelegt") == "Decommissioned"
    assert mastr_status("unbekannt") == "Unknown"           # never German


def test_smard_generation_mapping():
    assert smard_fuel("Wind Offshore") == "Wind offshore"
    assert smard_fuel("Wind Onshore") == "Wind onshore"
    assert smard_fuel("Photovoltaik") == "Solar"
    assert smard_fuel("Braunkohle") == "Lignite"
    assert smard_fuel("Pumpspeicher") == "Pumped storage"
    assert smard_fuel("Sonstige Erneuerbare") == "Other renewable"
    assert smard_fuel("Irgendwas") == "Other"               # unknown -> Other


def test_control_area_normalisation():
    assert control_area("50Hertz") == "50Hertz"
    assert control_area("50Hertz Transmission") == "50Hertz"
    assert control_area("TenneT TSO") == "TenneT"
    assert control_area("Amprion") == "Amprion"
    assert control_area("TransnetBW") == "TransnetBW"
    assert control_area("ELES") == "Other"                  # not a German TSO
    assert set(CONTROL_AREA_ORDER) == {"50Hertz", "TenneT", "Amprion", "TransnetBW"}


def test_outputs_are_canonical_fuels():
    # Every fuel this module can emit must be a real canonical fuel (no drift vs
    # fuels.py / fuels.js). Covers both dict values and the wind-split outputs.
    for fuel in MASTR_ENERGIETRAEGER.values():
        assert fuel in _CANON, f"MaStR maps to non-canonical fuel: {fuel}"
    for fuel in SMARD_GENERATION.values():
        assert fuel in _CANON, f"SMARD maps to non-canonical fuel: {fuel}"
    assert mastr_fuel("Wind", "Windkraft an Land") in _CANON
    assert mastr_fuel("Wind", "Windkraft auf See") in _CANON
    assert mastr_fuel("unknown") in _CANON                  # "Other" is canonical


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} passed")
