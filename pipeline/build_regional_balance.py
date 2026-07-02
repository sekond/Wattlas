"""Build the regional net-balance data for "Wasted wind" Panel 2: per-control-area
generation − load over time, evidencing Germany's structural north-surplus /
south-deficit imbalance.

    python pipeline/build_regional_balance.py

Writes data/de_regional_balance.json.

ISOLATION (CLAUDE.md landmine #11): its OWN pipeline module. Source is SMARD
(Bundesnetzagentur), separate from the ENTSO-E builders — its own endpoint, its own
chunking, its own German catalogue. A failure here must not touch the other views.

WHY net balance, not an inter-TSO flow line (SLICE §2, Panel 2 note): the DE-LU
north–south bottleneck is INTERNAL to one bidding zone, so it appears in neither
ENTSO-E cross-border flows nor zonal prices. There is no clean public intra-German
MW flow series. We evidence the imbalance with **net regional balance (this module)
+ redispatch volume (curtailment.json)** — never a fabricated flow line.

UNITS (landmine #12, validated on the real feed): SMARD day-resolution values are
**MWh per day**. We convert to **average GW** (÷24h ÷1000). At HOUR resolution a value
is MWh/h ≈ avg MW; we deliberately use SMARD's native DAY aggregation, which SMARD
computes in German local time — so 23/25-hour DST days and the sub-hourly→daily
aggregation are handled at source (landmines #3–4), consistently across the window.

COVERAGE: Germany shut its last reactors in 2023, so the Nuclear series 404s for the
control areas — that is expected and tolerated (the filter is simply absent; landmine
#8). Missing days/filters render as gaps, never fabricated zeros.

Net balance = total generation − grid load (Netzlast), per control area, per day.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

log = logging.getLogger("build_regional_balance")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
BERLIN = ZoneInfo("Europe/Berlin")

SMARD = "https://www.smard.de/app/chart_data"
SOURCE = "SMARD (Bundesnetzagentur) — Realisierte Erzeugung & Netzlast"
CONTROL_AREAS = ["50Hertz", "TenneT", "Amprion", "TransnetBW"]

# SMARD "Realisierte Erzeugung" filter IDs -> the English/canonical fuel they mean.
# We sum ALL of them for total generation; the mapping is documentation (no German
# label ever reaches the frontend). Nuclear is kept though it is now ~absent.
GENERATION_FILTERS = {
    1223: "Lignite", 1224: "Nuclear", 1225: "Wind offshore", 1226: "Hydro",
    1227: "Other fossil", 1228: "Other renewable", 4066: "Biomass", 4067: "Wind onshore",
    4068: "Solar", 4069: "Hard coal", 4070: "Pumped storage", 4071: "Gas",
}
LOAD_FILTER = 410       # Realisierter Stromverbrauch: Netzlast (grid load)
WINDOW_DAYS = 365       # rolling window kept in the output


# --------------------------------------------------------------------------- #
# Pure, offline-testable assembly (no network)
# --------------------------------------------------------------------------- #

def to_avg_gw(mwh_per_day: float) -> float:
    """MWh/day -> average GW over the day (÷24h ÷1000), rounded to 2 dp."""
    return round(mwh_per_day / 24.0 / 1000.0, 2)


def assemble_days(by_area: dict[str, dict[str, dict]], areas: list[str]) -> list[dict]:
    """Combine per-area {date: {"gen_mwh", "load_mwh"}} maps into the JSON `days`.

    One record per date that any area covers; an area missing that date is simply
    absent from that day's dicts (gaps stay gaps — never zero-filled). balance =
    generation − load. Values are average GW."""
    all_dates = sorted({d for area in areas for d in by_area.get(area, {})})
    days = []
    for date in all_dates:
        gen, load, bal = {}, {}, {}
        for area in areas:
            rec = by_area.get(area, {}).get(date)
            if not rec or rec.get("load_mwh") is None or rec.get("gen_mwh") is None:
                continue
            g, l = rec["gen_mwh"], rec["load_mwh"]
            gen[area] = to_avg_gw(g)
            load[area] = to_avg_gw(l)
            bal[area] = round(to_avg_gw(g) - to_avg_gw(l), 2)
        if gen:
            days.append({"date": date, "generation_gw": gen, "load_gw": load, "balance_gw": bal})
    return days


# --------------------------------------------------------------------------- #
# SMARD I/O (kept out of the pure functions)
# --------------------------------------------------------------------------- #

def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Wattlas research)"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def _epoch_to_berlin_date(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=BERLIN).date().isoformat()


def fetch_day_series(filter_id: int, region: str, n_chunks: int = 2) -> dict[int, float]:
    """{epoch_ms: MWh} from the latest n_chunks day-chunks for (filter, region).
    Each filter has its OWN index; a missing filter/region 404s and yields {}."""
    base = f"{SMARD}/{filter_id}/{region}"
    try:
        timestamps = _get(f"{base}/index_day.json")["timestamps"]
    except urllib.error.HTTPError:
        return {}
    out: dict[int, float] = {}
    for ts in timestamps[-n_chunks:]:
        try:
            series = _get(f"{base}/{filter_id}_{region}_day_{ts}.json")["series"]
        except urllib.error.HTTPError:
            continue
        for t, v in series:
            if v is not None:
                out[t] = v
    return out


def fetch_region(region: str) -> dict[str, dict]:
    """Per-day {date: {"gen_mwh", "load_mwh"}} for one control area."""
    load = fetch_day_series(LOAD_FILTER, region)
    gen_by_day: dict[int, float] = {}
    covered: dict[int, int] = {}
    missing = []
    for fid in GENERATION_FILTERS:
        s = fetch_day_series(fid, region)
        if not s:
            missing.append(GENERATION_FILTERS[fid])
            continue
        for t, v in s.items():
            gen_by_day[t] = gen_by_day.get(t, 0.0) + v
            covered[t] = covered.get(t, 0) + 1
    if missing:
        # Absent series are normal: Nuclear ended in 2023; inland areas have no
        # offshore wind; TransnetBW has no lignite. Tolerated as gaps (landmine #8).
        log.info("  %s: no series for %s (expected — fuel absent in this control area)",
                 region, ", ".join(missing))
    out: dict[str, dict] = {}
    for t, l in load.items():
        if t in gen_by_day and l is not None:
            out[_epoch_to_berlin_date(t)] = {"gen_mwh": gen_by_day[t], "load_mwh": l}
    return out


def build() -> dict:
    by_area = {}
    for region in CONTROL_AREAS:
        log.info("Fetching SMARD generation + load for %s …", region)
        by_area[region] = fetch_region(region)

    days = assemble_days(by_area, CONTROL_AREAS)
    days = days[-WINDOW_DAYS:]   # keep the most recent rolling window (days are sorted)

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": SOURCE,
        "unit": "GW",
        "note": "Average GW per day (SMARD MWh/day ÷24h). balance = generation − load. "
                "Net balance is the evidence for the intra-zone north–south bottleneck "
                "(no public inter-TSO flow series exists).",
        "areas": CONTROL_AREAS,
        "days": days,
    }
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "de_regional_balance.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")

    # validation: period-average net balance per area (north surplus / south deficit)
    import statistics
    for area in CONTROL_AREAS:
        bals = [d["balance_gw"][area] for d in days if area in d["balance_gw"]]
        if bals:
            log.info("  %-11s mean net balance %+.2f GW over %d days", area, statistics.mean(bals), len(bals))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    build()
