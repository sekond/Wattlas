"""Build the Iberian-blackout slice: assemble the ES/PT load curve around the fixed
historical window of 28 April 2025 + sourced restoration milestones. Writes
data/iberian_blackout.json.

A ONE-OFF historical pull (NOT a daily refresh). Run:
    python pipeline/build_iberian_blackout.py             (fetch the window)
    python pipeline/build_iberian_blackout.py --use-cache (offline, parquet cache)

SENSITIVITY (CLAUDE.md / spec): a real event that affected millions. Sober, factual.
  * NEVER assert a single cause. The `official` block CITES the ENTSO-E Expert Panel
    final report (multiple interacting factors; "the problem is voltage control, not
    renewable energy") — Wattlas reports what the data shows and what the report found.
  * Figures around an outage are provisional/revised — labelled. Gaps render honestly.
  * Times are CEST (Europe/Madrid). The milestones are sourced to the public record.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import pandas as pd

from build_spread import DATA_DIR

logger = logging.getLogger("wattlas.build_iberian_blackout")

EVENT_DATE = "2025-04-28"
TZ = "Europe/Madrid"          # CEST — the reference clock for the timeline + milestones
# Fixed window: the day of the event into the early hours of the 29th (restoration done ~04:00).
WIN_START = pd.Timestamp("2025-04-28 00:00", tz=TZ)
WIN_END = pd.Timestamp("2025-04-29 06:00", tz=TZ)
CACHE = DATA_DIR / "_raw_iberian_blackout.parquet"

# Sourced restoration milestones (CEST, Madrid). From ENTSO-E / REE / REN / public record.
MILESTONES = [
    {"t": "2025-04-28T12:33:00", "label": "Grid collapse — Spain loses ~60% of generation (~15 GW) in seconds; cascade to Portugal"},
    {"t": "2025-04-28T12:35:00", "label": "Black-start sequence begins"},
    {"t": "2025-04-28T12:44:00", "label": "First France–Spain 400 kV line (west) re-energised; Portugal black-start (Castelo do Bode hydro, Tapada do Outeiro)"},
    {"t": "2025-04-28T13:04:00", "label": "Spain–Morocco interconnection re-energised"},
    {"t": "2025-04-28T13:35:00", "label": "Eastern France–Spain interconnection re-energised"},
    {"t": "2025-04-28T18:36:00", "label": "First Spain–Portugal 220 kV tie-line re-energised"},
    {"t": "2025-04-28T21:35:00", "label": "Southern Spain–Portugal 400 kV tie-line re-energised"},
    {"t": "2025-04-29T00:22:00", "label": "Portugal transmission grid restored"},
    {"t": "2025-04-29T04:00:00", "label": "Spain restoration completed"},
]

# Cited, NOT asserted by Wattlas.
OFFICIAL = {
    "report": "ENTSO-E Expert Panel — Final Report on the Grid Incident in Spain and Portugal on 28 April 2025",
    "published": "2026-03-20",
    "conclusion": ("The final report attributes the blackout to a combination of many interacting "
                   "factors — gaps in voltage and reactive-power control, oscillations, differing "
                   "voltage-regulation practices, and rapid generator disconnections in Spain that "
                   "cascaded — rather than a single cause or a single technology."),
    "quote": "The problem is not renewable energy, but voltage control, regardless of the type of generation.",
    "quote_attrib": "Damián Cortinas, Chair, ENTSO-E Board of Directors (final-report briefing)",
    "report_url": "https://www.entsoe.eu/news/2026/03/20/entso-e-publishes-expert-panel-final-report-on-28-april-2025-blackout-in-spain-and-portugal/",
}

SOURCES = [
    {"label": "ENTSO-E — 28 April 2025 Iberian blackout (data + final report)",
     "url": "https://www.entsoe.eu/publications/blackout/28-april-2025-iberian-blackout/"},
    {"label": "Red Eléctrica de España (REE)", "url": "https://www.ree.es/en"},
    {"label": "REN (Portugal)", "url": "https://datahub.ren.pt/en/"},
]


def fetch_load(start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Actual total load for ES and PT over the window, on a common Madrid-tz index."""
    from entsoe import EntsoePandasClient

    token = os.environ.get("ENTSOE_API_TOKEN")
    if not token:
        sys.exit("ENTSOE_API_TOKEN not set. Copy .env.example to .env and fill it in.")
    client = EntsoePandasClient(api_key=token)

    cols = {}
    for zone in ("ES", "PT"):
        logger.info("fetching actual load for %s", zone)
        load = client.query_load(zone, start=start, end=end)
        s = (load["Actual Load"] if hasattr(load, "columns") else load)
        cols[zone] = s.tz_convert(TZ)
    df = pd.DataFrame(cols)
    return df


def assemble_timeline(df: pd.DataFrame) -> list[dict]:
    """Hourly ES/PT load (GW) on the Madrid clock. Gaps stay null (data around the outage
    is provisional/revised — never fabricated)."""
    hourly = df.resample("1h").mean()
    out = []
    for t, row in hourly.iterrows():
        out.append({
            "t": t.isoformat(),
            "es_load_gw": None if pd.isna(row.get("ES")) else round(float(row["ES"]) / 1000, 2),
            "pt_load_gw": None if pd.isna(row.get("PT")) else round(float(row["PT"]) / 1000, 2),
        })
    return out


def compute(df: pd.DataFrame, generated_at: str) -> dict:
    timeline = assemble_timeline(df)
    # Summary is EVENT-RELATIVE: the pre-event peak (before 12:33) and the trough during
    # the outage afternoon — not the unrelated overnight low.
    t0 = pd.Timestamp("2025-04-28 12:33", tz=TZ)
    before = df[df.index < t0]
    during = df[(df.index >= t0) & (df.index < pd.Timestamp("2025-04-28 20:00", tz=TZ))]
    gw = lambda v: None if pd.isna(v) else round(float(v) / 1000, 2)
    mx = lambda s: gw(s.dropna().max()) if s.dropna().size else None
    mn = lambda s: gw(s.dropna().min()) if s.dropna().size else None
    return {
        "generated_at": generated_at,
        "event_date": EVENT_DATE, "zones": ["ES", "PT"], "tz": TZ + " (CEST)",
        "resolution": "hourly",
        "note": ("Actual total load (ENTSO-E) for Spain and Portugal around the fixed window of "
                 "28 April 2025. Spain's metered load is largely missing through the outage — the "
                 "reporting itself went down — and is shown as a gap; Portugal's load fell to near "
                 "zero. Figures around an outage are provisional and revised. Times are CEST "
                 "(Madrid). This view shows what the data records and what the official report "
                 "found — it does not assert a cause."),
        "sources": SOURCES,
        "timeline": timeline,
        "milestones": MILESTONES,
        "official": OFFICIAL,
        "summary": {
            "pre_event_load_gw": {"ES": mx(before["ES"]), "PT": mx(before["PT"])},
            "trough_load_gw": {"ES": mn(during["ES"]), "PT": mn(during["PT"])},
            "official_loss": "Spain lost about 60% of its generation — a sudden ~15 GW drop — in seconds (official record).",
            "data_gap_note": "Spain's metered load is missing through the outage (reporting down); Portugal's load is recorded and collapses to near zero.",
            "restoration": "staged, completed ~04:00 CEST on 29 April 2025",
        },
    }


def build(df: pd.DataFrame) -> None:
    payload = compute(df, datetime.now(timezone.utc).isoformat(timespec="seconds"))
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "iberian_blackout.json").write_text(json.dumps(payload, indent=2))
    s = payload["summary"]
    logger.info("wrote data/iberian_blackout.json (%d hourly points, %d milestones)",
                len(payload["timeline"]), len(payload["milestones"]))
    logger.info("PT load pre-event ~%s GW -> trough ~%s GW (collapse); ES metered load missing during outage (gap)",
                s["pre_event_load_gw"]["PT"], s["trough_load_gw"]["PT"])
    logger.info("%d sources cited; cause sourced to official report (%s), not asserted",
                len(payload["sources"]), payload["official"]["published"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Iberian-blackout JSON artefact (one-off).")
    parser.add_argument("--use-cache", action="store_true", help="Re-use the parquet cache.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    logger.info("iberian blackout build start (use_cache=%s)", args.use_cache)

    if args.use_cache:
        if not CACHE.exists():
            logger.error("no cache at %s — run once without --use-cache.", CACHE)
            sys.exit(1)
        df = pd.read_parquet(CACHE)
    else:
        df = fetch_load(WIN_START, WIN_END)
        df.to_parquet(CACHE)
        logger.info("fetched + cached %d rows", len(df))

    build(df)
    logger.info("iberian blackout build done")


if __name__ == "__main__":
    main()
