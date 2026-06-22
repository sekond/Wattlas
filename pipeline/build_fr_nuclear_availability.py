"""Build the French nuclear availability/output data for the France-nuclear Panel 3:
monthly nuclear output over the year (the maintenance dip) and what moves alongside it.

    python pipeline/build_fr_nuclear_availability.py

Writes data/fr_nuclear_availability.json.

ISOLATION (CLAUDE.md landmine #11): its OWN module. Source: RTE **éCO2mix national** via
ODRÉ (open, no key). Monthly server-side aggregation; values MW → **GW**.

OUTPUT, not available-capacity (landmine — block B distinction): "available capacity"
(how much COULD run) needs the RTE generation-unit-unavailability feed (OAuth2). Without
those credentials we degrade to **output** (how much DID run) — `available_gw` is null.
See memory `rte-oauth-pending`.

HONEST FRAMING (not the mockup): the real data shows nuclear output dips in spring/summer
(refuelling + maintenance, concentrated in the lower-demand months **by design**), but
France remains a **net exporter every month** (`ech_physiques` < 0) because summer demand
also falls and solar rises — so imports do NOT "fill the gap" at monthly resolution. We
therefore show the seasonal output dip and the net-export line, and reserve the heatwave
river-cooling story (event-scale, not monthly) for the annotated copy — never fabricated.
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("build_fr_nuclear_availability")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ODRE = ("https://odre.opendatasoft.com/api/explore/v2.1/catalog/"
        "datasets/eco2mix-national-cons-def/records")
SOURCE = "RTE éCO2mix national via ODRÉ (Opendatasoft)"
WINDOW_MONTHS = 24


# --------------------------------------------------------------------------- #
# Pure, offline-testable assembly
# --------------------------------------------------------------------------- #

def assemble_months(rows: list[dict]) -> list[dict]:
    """Monthly rows (MW averages) -> the JSON months (GW, rounded), chronological.
    `net_export_gw` = −ech_physiques (+ = France exporting). `available_gw` is null
    until the RTE unavailability feed (OAuth) is wired."""
    out = []
    for x in sorted(rows, key=lambda r: r["month"]):
        g = lambda k: (x.get(k) or 0) / 1000.0
        out.append({
            "month": x["month"],
            "nuclear_gw": round(g("nuc"), 2),
            "hydro_gw": round(g("hyd"), 2),
            "gas_gw": round(g("gas"), 2),
            "wind_gw": round(g("eo"), 2),
            "solar_gw": round(g("sol"), 2),
            "other_gw": round(g("bio") + g("coal") + g("oil"), 2),
            "demand_gw": round(g("dem"), 2),
            "net_export_gw": round(-g("ech"), 2),   # + = net exporter
            "available_gw": None,                   # needs RTE OAuth (degraded to output)
        })
    return out


def installed_nuclear_gw() -> float:
    """National installed nuclear capacity (GW) from the committed fleet, for context."""
    p = DATA_DIR / "fr_nuclear_sites.json"
    if p.exists():
        return round(json.loads(p.read_text(encoding="utf-8"))["fleet_total"]["capacity_mw"] / 1000, 1)
    return 0.0


# --------------------------------------------------------------------------- #
# ODRÉ I/O
# --------------------------------------------------------------------------- #

def _get(params: dict) -> dict:
    url = ODRE + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Wattlas pipeline)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def fetch_months() -> list[dict]:
    """Monthly national averages of the generation mix + exchanges + demand (MW)."""
    select = ("avg(nucleaire) as nuc, avg(hydraulique) as hyd, avg(gaz) as gas, "
              "avg(eolien) as eo, avg(solaire) as sol, avg(bioenergies) as bio, "
              "avg(charbon) as coal, avg(fioul) as oil, avg(ech_physiques) as ech, "
              "avg(consommation) as dem")
    return _get({
        "select": select,
        "group_by": "date_format(date_heure, 'yyyy-MM') as month",
        "order_by": "month desc", "limit": str(WINDOW_MONTHS),
    })["results"]


def build() -> dict:
    months = assemble_months(fetch_months())
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": SOURCE, "unit": "GW",
        "installed_nuclear_gw": installed_nuclear_gw(),
        "available_note": "available_gw is null: 'available capacity' needs the RTE OAuth "
                          "unavailability feed; degraded to output (éCO2mix).",
        "period_start": months[0]["month"] if months else None,
        "period_end": months[-1]["month"] if months else None,
        "months": months,
    }
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "fr_nuclear_availability.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")

    if months:
        nuc = [m["nuclear_gw"] for m in months]
        lo = min(months, key=lambda m: m["nuclear_gw"]); hi = max(months, key=lambda m: m["nuclear_gw"])
        exporting = sum(1 for m in months if m["net_export_gw"] > 0)
        log.info("Months: %d (%s..%s), installed nuclear %.1f GW",
                 len(months), out["period_start"], out["period_end"], out["installed_nuclear_gw"])
        log.info("Nuclear output: low %.1f GW (%s), high %.1f GW (%s)",
                 lo["nuclear_gw"], lo["month"], hi["nuclear_gw"], hi["month"])
        log.info("Net exporter in %d/%d months (France exports even during the summer dip)",
                 exporting, len(months))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    build()
