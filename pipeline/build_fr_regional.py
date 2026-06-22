"""Build the French régional net-balance data for the France-nuclear Panel 2:
per-région generation − consumption (the éCO2mix *solde*), exporters vs importers.

    python pipeline/build_fr_regional.py

Writes data/fr_regional.json.

ISOLATION (CLAUDE.md landmine #11): its OWN module, isolated from the ENTSO-E and
German pipelines. Source: RTE **éCO2mix régional** via ODRÉ (Opendatasoft, open, no
key). French labels are translated through fr_fields.

NET BALANCE without a fabricated flow (SLICE §2 Panel-2 note + landmine): France is one
bidding zone, so a région's surplus/deficit is a PHYSICAL balance, and there is no clean
inter-régional flow matrix. We use the published **physical exchange** (`ech_physiques`,
+ = net import): by the éCO2mix energy identity
    consumption = generation + imports  ⇒  net_balance = generation − consumption = −ech_physiques.
So net_balance and generation are derived from numeric fields only — which also dodges a
data quirk (the `eolien` column is typed as text in this dataset and can't be aggregated
server-side; summing production types is unnecessary anyway).

UNITS (landmine #12): éCO2mix values are MW (instantaneous power per 30-min step);
we average over a 12-month window and convert to **GW**. Grouped by the dataset's own
timestamps; aggregation is server-side. **Corse** is a separate non-interconnected zone
and is absent from éCO2mix régional → it renders as "no data", never zero (landmine #8).
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import fr_fields

log = logging.getLogger("build_fr_regional")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ODRE = ("https://odre.opendatasoft.com/api/explore/v2.1/catalog/"
        "datasets/eco2mix-regional-cons-def/records")
SOURCE = "RTE éCO2mix régional via ODRÉ (Opendatasoft)"
WINDOW_DAYS = 365


# --------------------------------------------------------------------------- #
# Pure, offline-testable assembly
# --------------------------------------------------------------------------- #

def assemble_regions(rows: list[dict]) -> list[dict]:
    """Turn the ODRÉ per-région aggregation rows into the JSON records (GW, rounded),
    sorted net-exporter → net-importer. Each row has avg consommation / nucleaire /
    ech_physiques (MW). Régions that don't map to a NUTS-1 code are skipped."""
    out = []
    for x in rows:
        nuts = fr_fields.region_nuts(x.get("code_insee_region")) or fr_fields.region_nuts(x.get("libelle_region"))
        if nuts is None:
            continue
        conso = (x.get("conso") or 0) / 1000.0
        nuc = (x.get("nuc") or 0) / 1000.0
        ech = (x.get("ech") or 0) / 1000.0      # + = net import
        net = -ech                              # generation − consumption
        gen = conso - ech                       # = generation (the identity)
        out.append({
            "nuts_id": nuts,
            "name": fr_fields.region_name(nuts) or x.get("libelle_region"),
            "insee": str(x.get("code_insee_region")),
            "nuclear_gw": round(nuc, 2),
            "generation_gw": round(gen, 2),
            "consumption_gw": round(conso, 2),
            "net_balance_gw": round(net, 2),
        })
    out.sort(key=lambda r: -r["net_balance_gw"])
    return out


# --------------------------------------------------------------------------- #
# ODRÉ I/O
# --------------------------------------------------------------------------- #

def _get(params: dict) -> dict:
    url = ODRE + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Wattlas pipeline)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def fetch_regions() -> tuple[list[dict], str, str]:
    """Per-région 12-month averages from éCO2mix régional. Returns (rows, start, end)."""
    # latest consolidated timestamp, then a 365-day window ending there
    latest = _get({"select": "max(date_heure) as m", "limit": "1"})["results"][0]["m"]
    end = datetime.fromisoformat(latest).date()
    start = end - timedelta(days=WINDOW_DAYS)
    rows = _get({
        "select": "avg(consommation) as conso, avg(nucleaire) as nuc, avg(ech_physiques) as ech",
        "group_by": "libelle_region, code_insee_region",
        "where": f"date_heure >= date'{start}' and date_heure < date'{end}'",
        "limit": "20",
    })["results"]
    return rows, start.isoformat(), end.isoformat()


def build() -> dict:
    rows, start, end = fetch_regions()
    regions = assemble_regions(rows)
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": SOURCE, "unit": "GW",
        "period_start": start, "period_end": end,
        "note": "net_balance = generation − consumption = −physical exchanges (the éCO2mix "
                "solde). France is one bidding zone, so this is a physical balance, not a "
                "regional price. Corse (non-interconnected zone) is absent → no data.",
        "regions": regions,
    }
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "fr_regional.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")

    exporters = [r for r in regions if r["net_balance_gw"] > 0]
    log.info("Régions: %d (%d exporters, %d importers) over %s..%s",
             len(regions), len(exporters), len(regions) - len(exporters), start, end)
    for r in regions:
        log.info("  %-26s net %+5.2f GW  (gen %.1f, conso %.1f, nuclear %.1f)",
                 r["name"], r["net_balance_gw"], r["generation_gw"], r["consumption_gw"], r["nuclear_gw"])
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    build()
