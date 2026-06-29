"""Build the Wholesale->Retail wedge (v10 slice 7) — the one v10 slice with a NEW
external source: Eurostat household electricity-price COMPONENTS (dataset nrg_pc_204_c).
Writes data/retail_wedge.json.

ISOLATED module (CLAUDE.md landmine #11): own fetch (Eurostat REST, open, no key), own
units, non-fatal — a Eurostat hiccup writes status:"unavailable" and the rest of the
pipeline is unaffected.

Units/methodology (landmine #12): values are EUR per kWh (NOT our wholesale €/MWh — a
different unit, stated). The dataset is ANNUAL averages (not hourly), so this is a slow-
moving decomposition, not a real-time one. Eurostat "geo" is the COUNTRY (e.g. DE), not
the DE-LU bidding zone — stated where it meets our zone-based wholesale data. The
"Energy and supply" component contains the wholesale cost PLUS the supplier margin — it is
not pure wholesale; labelled accordingly.
"""
from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("wattlas.build_retail_wedge")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_pc_204_c"

GEOS = ["DE", "FR", "ES", "NL", "NO"]
BAND = "KWH2500-4999"                 # household band DC (2 500-4 999 kWh/yr), the standard middle band
YEARS = ["2019", "2020", "2021", "2022", "2023", "2024"]
# top-level component code -> our output key
COMPONENTS = [("NRG_SUP", "energy"), ("NETC", "network"), ("TAX_FEE_LEV_CHRG", "taxes_levies")]


def _fetch_json() -> dict:
    params = [("format", "JSON"), ("lang", "EN"), ("nrg_cons", BAND), ("currency", "EUR")]
    params += [("geo", g) for g in GEOS]
    params += [("time", y) for y in YEARS]
    params += [("nrg_prc", c) for c, _ in COMPONENTS]
    url = BASE + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read())


def parse_jsonstat(d: dict) -> list[dict]:
    """Decode a Eurostat JSON-stat response into flat rows of {geo,time,nrg_prc,value}.
    Pure (no network) so it can be unit-tested on an inline fixture."""
    ids, size, value = d["id"], d["size"], d.get("value", {})
    inv = {dn: {pos: code for code, pos in d["dimension"][dn]["category"]["index"].items()} for dn in ids}
    strides = [1] * len(ids)
    for i in range(len(ids) - 2, -1, -1):
        strides[i] = strides[i + 1] * size[i + 1]
    rows = []
    for k, v in value.items():
        flat = int(k)
        coord = {dn: inv[dn][(flat // strides[i]) % size[i]] for i, dn in enumerate(ids)}
        coord["value"] = v
        rows.append(coord)
    return rows


def assemble(rows: list[dict]) -> dict:
    """rows -> {geo: [{period, energy, network, taxes_levies, total, currency}]}. Pure."""
    comp = dict(COMPONENTS)
    agg: dict = {}
    for r in rows:
        key = (r["geo"], r["time"])
        name = comp.get(r["nrg_prc"])
        if name is None:
            continue
        agg.setdefault(key, {})[name] = r["value"]
    out: dict = {}
    for (geo, time), c in sorted(agg.items()):
        energy = c.get("energy")
        if energy is None:
            continue
        parts = [c.get("energy"), c.get("network"), c.get("taxes_levies")]
        total = round(sum(x for x in parts if x is not None), 4)
        out.setdefault(geo, []).append({
            "period": time,
            "energy": round(energy, 4),
            "network": round(c["network"], 4) if c.get("network") is not None else None,
            "taxes_levies": round(c["taxes_levies"], 4) if c.get("taxes_levies") is not None else None,
            "total": total,
            "currency": "EUR/kWh",
        })
    return out


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    base = {
        "generated_at": generated_at,
        "source": "Eurostat nrg_pc_204_c (household electricity price components, band DC)",
        "currency": "EUR/kWh", "frequency": "annual",
        "components": {"energy": "Energy and supply (incl. wholesale + supplier margin)",
                       "network": "Network costs", "taxes_levies": "Taxes, fees, levies and charges"},
        "note": ("EUR per kWh (not our wholesale €/MWh); annual averages, not hourly; Eurostat "
                 "'geo' is the COUNTRY, not the DE-LU bidding zone. 'Energy and supply' includes "
                 "the wholesale cost plus the supplier margin, so it is not pure wholesale. The "
                 "2026 ~€6.5bn German grid-fee subsidy is cited policy context, not in this series."),
    }
    try:
        d = _fetch_json()
        countries = assemble(parse_jsonstat(d))
        if not countries:
            raise ValueError("no rows parsed")
    except Exception as e:  # isolated + non-fatal (landmine #11)
        logger.warning("Eurostat fetch/parse failed (%s) — writing status:unavailable", e)
        (DATA_DIR / "retail_wedge.json").write_text(json.dumps(
            {**base, "status": "unavailable", "countries": {}}, indent=2))
        return

    (DATA_DIR / "retail_wedge.json").write_text(json.dumps(
        {**base, "status": "ok", "geos_available": list(countries.keys()),
         "country_default": "DE" if "DE" in countries else next(iter(countries), None),
         "countries": countries}, indent=2))
    de = countries.get("DE", [])
    logger.info("wrote retail_wedge.json — %d countries; DE latest total €%.3f/kWh",
                len(countries), de[-1]["total"] if de else 0.0)


if __name__ == "__main__":
    main()
