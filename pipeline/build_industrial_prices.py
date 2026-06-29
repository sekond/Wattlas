"""Build the Industrial electricity-price comparison (v10 slice 10 — thin DATA layer)
from Eurostat nrg_pc_205_c (non-household price components). Writes
data/industrial_prices.json.

Reuses the JSON-stat parser + component assembler from build_retail_wedge (the same open
Eurostat REST API, no key) — only the dataset and consumption band differ. Industrial
band IC (500-1 999 MWh/yr), a representative mid-industrial consumer. Isolated, non-fatal.

SCOPE (CLAUDE.md honesty): this is the part of "industrial competitiveness" Wattlas can
honestly source — wholesale/retail industrial PRICE. Corporate strategy, utility M&A,
PPAs, financing and capital-markets themes stay OUT of scope (industrial.html states that
boundary). Units: EUR/kWh, ANNUAL; Eurostat "geo" is the COUNTRY, not the DE-LU zone.
"""
from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from build_retail_wedge import GEOS, YEARS, assemble, parse_jsonstat

logger = logging.getLogger("wattlas.build_industrial_prices")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_pc_205_c"
BAND = "MWH500-1999"   # industrial band IC (500-1 999 MWh/yr)


def _fetch_json() -> dict:
    params = [("format", "JSON"), ("lang", "EN"), ("nrg_cons", BAND), ("currency", "EUR")]
    params += [("geo", g) for g in GEOS]
    params += [("time", y) for y in YEARS]
    params += [("nrg_prc", c) for c in ("NRG_SUP", "NETC", "TAX_FEE_LEV_CHRG")]
    url = BASE + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read())


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    base = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Eurostat nrg_pc_205_c (industrial electricity price components, band IC 500-1 999 MWh)",
        "currency": "EUR/kWh", "frequency": "annual", "band": "IC (500-1 999 MWh/yr)",
        "components": {"energy": "Energy and supply", "network": "Network costs",
                       "taxes_levies": "Taxes, fees, levies and charges"},
        "note": ("EUR/kWh, annual; Eurostat 'geo' is the COUNTRY, not the DE-LU bidding zone. "
                 "This is the PRICE layer of industrial competitiveness only — corporate strategy, "
                 "M&A, PPAs and capital-markets themes are out of Wattlas's data scope."),
    }
    try:
        countries = assemble(parse_jsonstat(_fetch_json()))
        if not countries:
            raise ValueError("no rows parsed")
    except Exception as e:  # isolated + non-fatal
        logger.warning("Eurostat industrial fetch/parse failed (%s) — status:unavailable", e)
        (DATA_DIR / "industrial_prices.json").write_text(json.dumps(
            {**base, "status": "unavailable", "countries": {}}, indent=2))
        return

    (DATA_DIR / "industrial_prices.json").write_text(json.dumps(
        {**base, "status": "ok", "geos_available": list(countries.keys()),
         "country_default": "DE" if "DE" in countries else next(iter(countries), None),
         "countries": countries}, indent=2))
    de = countries.get("DE", [])
    logger.info("wrote industrial_prices.json — %d countries; DE latest total €%.3f/kWh",
                len(countries), de[-1]["total"] if de else 0.0)


if __name__ == "__main__":
    main()
