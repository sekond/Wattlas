"""Build UK constraint payments: monthly thermal-constraint cost (GBP) and volume
(GWh) from the NESO "Constraint Breakdown" dataset. Writes data/uk_constraints.json.

Run: python pipeline/build_uk_constraints.py              (fetches recent years)
     python pipeline/build_uk_constraints.py --use-cache  (offline, cached CSVs)

ISOLATED module (CLAUDE.md landmine #11): NESO Constraint Breakdown (open, no key),
separate from every other pipeline.

Methodology (landmine #12 — state it in writing):
  * The "Thermal constraints" cost/volume is the cost of managing thermal boundary
    constraints. The dominant one is the B6 Scotland-England boundary, whose cost is
    overwhelmingly **turning Scottish wind down and replacement generation up** — i.e.
    the constraint-payment story. It is a *managed grid-stability cost*, NOT energy
    discarded by choice, and NOT pure curtailed-wind GWh (the volume is the balancing-
    action volume of the thermal constraint). Labelled as such in the JSON + UI.
  * Currency GBP (reported as GBP million); volume MWh -> GWh. Figures are revised by
    NESO over time. Great Britain.
  * If the source is unavailable, write a status:"unavailable" artefact with empty
    months (the frontend renders an "awaiting source" state) — never fabricate.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone

import requests

from build_spread import DATA_DIR

logger = logging.getLogger("wattlas.build_uk_constraints")

PKG_URL = "https://api.neso.energy/api/3/action/package_show?id=constraint-breakdown"
DATE_COL = "Date"
COST_COL = "Thermal constraints cost"      # GBP, daily
VOL_COL = "Thermal constraints volume"     # MWh, daily
CACHE = DATA_DIR / "_raw_uk_constraints.json"   # gitignored (data/_raw_*)
SOURCE = "NESO Constraint Breakdown — Thermal constraints (open data portal)"


def aggregate_monthly(csv_texts: list[str]) -> list[dict]:
    """Pure: daily Constraint-Breakdown CSV rows -> monthly thermal cost (£m) + volume
    (GWh). Sums the thermal columns by calendar month (YYYY-MM); other constraint
    categories (voltage/inertia/largest-loss) are ignored. Unit-tested offline."""
    acc: dict[str, dict[str, float]] = defaultdict(lambda: {"cost": 0.0, "vol": 0.0})
    for text in csv_texts:
        for row in csv.DictReader(io.StringIO(text)):
            month = (row.get(DATE_COL) or "")[:7]
            if not re.fullmatch(r"\d{4}-\d{2}", month):
                continue
            try:
                acc[month]["cost"] += float(row.get(COST_COL) or 0)
                acc[month]["vol"] += float(row.get(VOL_COL) or 0)
            except ValueError:
                continue
        # next file
    # NESO signs thermal volume as NET down-regulation (turning wind down = negative
    # MWh), so the monthly sum is negative; store its magnitude (the scale of
    # curtailment/constraint action) and label it as down-regulation in the note.
    return [
        {"month": m,
         "cost_gbp_m": round(acc[m]["cost"] / 1e6, 1),        # £ -> £m
         "volume_gwh": round(abs(acc[m]["vol"]) / 1e3, 1)}    # |MWh| -> GWh (down-regulation magnitude)
        for m in sorted(acc)
    ]


def fetch_csv_texts(min_year: int) -> list[str]:
    """Download the Constraint Breakdown CSVs for financial years starting >= min_year,
    resolving current resource URLs via the CKAN package (resilient to re-publishing)."""
    pkg = requests.get(PKG_URL, timeout=60).json()
    if not pkg.get("success"):
        raise RuntimeError("CKAN package_show returned success=false")
    texts = []
    for r in pkg["result"]["resources"]:
        if (r.get("format") or "").upper() != "CSV":
            continue
        m = re.search(r"(20\d\d)-20\d\d", r.get("name", "") or "")
        if not m or int(m.group(1)) < min_year:
            continue
        logger.info("fetching %s", r.get("name"))
        texts.append(requests.get(r["url"], timeout=120).text)
    if not texts:
        raise RuntimeError("no Constraint Breakdown CSV resources found")
    return texts


def _payload(months: list[dict], generated_at: str) -> dict:
    if not months:
        return {
            "generated_at": generated_at, "currency": "GBP", "status": "unavailable",
            "source": SOURCE,
            "reason": "NESO Constraint Breakdown unavailable at build time.",
            "months": [],
        }
    total_cost = round(sum(m["cost_gbp_m"] for m in months), 1)
    total_vol = round(sum(m["volume_gwh"] for m in months), 1)
    peak = max(months, key=lambda m: m["cost_gbp_m"])
    return {
        "generated_at": generated_at, "currency": "GBP", "status": "ok",
        "unit_cost": "GBP million", "unit_volume": "GWh",
        "source": SOURCE,
        "note": ("Thermal-constraint cost and volume (NESO). The dominant thermal "
                 "constraint is the B6 Scotland-England boundary, whose cost is "
                 "overwhelmingly turning Scottish wind down and replacement up — a "
                 "managed grid-stability cost (the British equivalent of German "
                 "redispatch), not energy discarded by choice. Volume is the magnitude "
                 "of net thermal down-regulation (wind turned down), shown positive — "
                 "not pure metered curtailed-wind GWh."),
        "period_start": months[0]["month"], "period_end": months[-1]["month"],
        "totals": {"cost_gbp_m": total_cost, "volume_gwh": total_vol,
                   "peak_month": peak["month"], "peak_cost_gbp_m": peak["cost_gbp_m"]},
        "months": months,
    }


def build(months: list[dict]) -> None:
    payload = _payload(months, datetime.now(timezone.utc).isoformat(timespec="seconds"))
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "uk_constraints.json").write_text(json.dumps(payload, indent=2))
    if payload["status"] == "ok":
        t = payload["totals"]
        logger.info("wrote data/uk_constraints.json (%d months, %s..%s)",
                    len(months), payload["period_start"], payload["period_end"])
        logger.info("totals: thermal constraint cost £%.0fm, volume %.0f GWh; peak £%.1fm in %s",
                    t["cost_gbp_m"], t["volume_gwh"], t["peak_cost_gbp_m"], t["peak_month"])
        for m in months[-12:]:
            logger.info("    %s  £%6.1fm  %7.1f GWh", m["month"], m["cost_gbp_m"], m["volume_gwh"])
    else:
        logger.warning("wrote data/uk_constraints.json with status=unavailable")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the UK constraint-payments JSON artefact.")
    parser.add_argument("--use-cache", action="store_true", help="Re-use data/_raw_uk_constraints.json.")
    parser.add_argument("--since-year", type=int, default=2022, help="First financial-year start to include.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    logger.info("uk constraints build start (use_cache=%s, since=%d)", args.use_cache, args.since_year)

    if args.use_cache:
        if not CACHE.exists():
            logger.error("no cache at %s — run once without --use-cache first.", CACHE)
            sys.exit(1)
        texts = json.loads(CACHE.read_text())
    else:
        try:
            texts = fetch_csv_texts(args.since_year)
            CACHE.write_text(json.dumps(texts))
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            logger.error("NESO Constraint Breakdown fetch failed: %s — writing unavailable artefact", exc)
            build([])          # degrade gracefully, don't crash the refresh
            return

    build(aggregate_monthly(texts))
    logger.info("uk constraints build done")


if __name__ == "__main__":
    main()
