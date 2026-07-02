"""Build the Dunkelflaute slice: detect low-renewable spells in DE-LU and extract the
worst event's hourly series + a frequency/duration summary. Writes data/dunkelflaute.json.

Run: python pipeline/build_dunkelflaute.py             (fetches ~12 months)
     python pipeline/build_dunkelflaute.py --use-cache (offline, parquet cache)

Reuses the existing ENTSO-E pipeline (generation-by-type via metrics.collapse_generation,
load, day-ahead price). No new external source.

Landmines this script is built around:
  * The low-renewable THRESHOLD is a stated, adjustable CHOICE, not a law of nature
    (wind+solar share of demand below THRESHOLD_PCT). Stated in the JSON + UI.
  * Detection uses a 24-hour rolling mean of the wind+solar share so a brief midday
    solar peak doesn't fragment a multi-day spell — "the daily-average renewable share
    stayed below the threshold".
  * Net imports matter most exactly during these hours: net_imports = load - generation
    (positive = importing). Don't double-count; it closes the demand balance.
  * Generation-by-type has gaps/"other" buckets (#9) — rendered honestly, never faked.
  * tz-aware (Europe/Berlin), DST-safe (group in local time).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import pandas as pd

from metrics import collapse_generation, to_hourly
from build_spread import DATA_DIR, LOCAL_TZ

logger = logging.getLogger("wattlas.build_dunkelflaute")

ZONE = "DE_LU"
THRESHOLD_PCT = 10        # wind+solar share of demand below which an hour is "low-renewable"
MIN_SPELL_HOURS = 24      # a spell must persist at least this long (a sustained day+ of low VRE)
ROLL_WINDOW = 24          # rolling mean window (hours) used to smooth day/night + midday solar
PAD_HOURS = 6            # context hours shown either side of the worst event
DF_CACHE = DATA_DIR / "_raw_dunkelflaute.parquet"   # the whole assembled hourly df (gitignored)

# collapse_generation canonical columns -> the simplified backup stack we display.
GROUPS = {
    "wind": ["Wind onshore", "Wind offshore"],
    "solar": ["Solar"],
    "gas": ["Gas"],
    "coal": ["Lignite", "Hard coal"],
    "nuclear": ["Nuclear"],
    "hydro": ["Hydro", "Pumped storage"],
    "biomass": ["Biomass"],
    "other": ["Oil", "Other fossil", "Waste", "Geothermal", "Other renewable", "Other"],
}
STACK = ["wind", "solar", "biomass", "hydro", "nuclear", "coal", "gas", "other"]


def fetch_inputs(start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Fetch DE-LU generation-by-type + load + day-ahead price, return one tz-aware hourly
    DataFrame with the grouped fuel columns + load + price."""
    from entsoe_client import make_entsoe_client  # retrying client (transient-5xx safe)

    token = os.environ.get("ENTSOE_API_TOKEN")
    if not token:
        sys.exit("ENTSOE_API_TOKEN not set. Copy .env.example to .env and fill it in.")
    client = make_entsoe_client(token)
    # generation in monthly chunks (the raw has tuple columns; collapse to canonical fuels)
    chunks = []
    cur = start
    while cur < end:
        nxt = min(cur + pd.DateOffset(months=1), end)
        logger.info("fetching generation %s..%s", cur.date(), nxt.date())
        chunks.append(client.query_generation(ZONE, start=cur, end=nxt, psr_type=None))
        cur = nxt
    fuel = collapse_generation(pd.concat(chunks), local_tz=LOCAL_TZ)   # hourly MW per canonical fuel

    logger.info("fetching load + day-ahead price")
    load = client.query_load(ZONE, start=start, end=end)
    load = (load["Actual Load"] if hasattr(load, "columns") else load)
    price = client.query_day_ahead_prices(ZONE, start=start, end=end)

    df = _assemble(fuel, to_hourly(load), to_hourly(price))
    return df


def _assemble(fuel: pd.DataFrame, load: pd.Series, price: pd.Series) -> pd.DataFrame:
    """Group canonical fuels into the display stack and align with load + price (hourly)."""
    out = pd.DataFrame(index=fuel.index)
    for g, cols in GROUPS.items():
        present = [c for c in cols if c in fuel.columns]
        out[g] = fuel[present].sum(axis=1) if present else 0.0
    out["load"] = load.reindex(out.index)
    out["price"] = price.reindex(out.index)
    return out.dropna(subset=["load", "price"])


def detect_spells(vre_share: pd.Series, threshold: float, min_hours: int,
                  roll_window: int = ROLL_WINDOW) -> list[tuple[int, int]]:
    """Index runs [start, end) where the rolling-mean wind+solar share stays below
    `threshold` for at least `min_hours`. Pure; unit-tested with a small window."""
    roll = vre_share.rolling(roll_window, center=True, min_periods=max(1, roll_window // 2)).mean()
    below = (roll < threshold).to_numpy()
    runs: list[tuple[int, int]] = []
    i, n = 0, len(below)
    while i < n:
        if below[i]:
            j = i
            while j < n and below[j]:
                j += 1
            if j - i >= min_hours:
                runs.append((i, j))
            i = j
        else:
            i += 1
    return runs


def _round_list(s: pd.Series) -> list:
    return [None if pd.isna(v) else round(float(v) / 1000, 2) for v in s]   # MW -> GW


def compute(df: pd.DataFrame, threshold: float, min_hours: int, generated_at: str,
            roll_window: int = ROLL_WINDOW, pad: int = PAD_HOURS) -> dict:
    """Pure transform: hourly fuel/load/price DataFrame -> dunkelflaute.json payload."""
    gen_cols = list(GROUPS.keys())
    total_gen = df[gen_cols].sum(axis=1)
    vre = df["wind"] + df["solar"]
    net_imports = df["load"] - total_gen                  # closes the demand balance
    vre_share = (vre / df["load"] * 100).where(df["load"] > 0)

    runs = detect_spells(vre_share, threshold, min_hours, roll_window)
    spell_mask = pd.Series(False, index=df.index)
    spells = []
    for a, b in runs:
        idx = df.index[a:b]
        spell_mask.loc[idx] = True
        spells.append({"start": idx[0].isoformat(), "end": idx[-1].isoformat(),
                       "hours": int(b - a),
                       "min_vre_pct": round(float(vre_share.iloc[a:b].min()), 1)})

    # worst event = longest run (tie -> deepest), padded for context
    worst = {}
    if runs:
        a, b = max(runs, key=lambda r: (r[1] - r[0], -vre_share.iloc[r[0]:r[1]].mean()))
        lo, hi = max(0, a - pad), min(len(df), b + pad)
        ev = df.iloc[lo:hi]
        worst = {
            "start": ev.index[0].isoformat(), "end": ev.index[-1].isoformat(),
            "spell_start": df.index[a].isoformat(), "spell_end": df.index[b - 1].isoformat(),
            "hours": [t.isoformat() for t in ev.index],
            "wind": _round_list(ev["wind"]), "solar": _round_list(ev["solar"]),
            "gas": _round_list(ev["gas"]), "coal": _round_list(ev["coal"]),
            "nuclear": _round_list(ev["nuclear"]), "hydro": _round_list(ev["hydro"]),
            "biomass": _round_list(ev["biomass"]),
            "imports": [None if pd.isna(v) else round(float(v) / 1000, 2) for v in net_imports.iloc[lo:hi]],
            "price": [None if pd.isna(v) else round(float(v), 1) for v in ev["price"]],
            "demand": _round_list(ev["load"]),
            "min_vre_pct": round(float(vre_share.iloc[a:b].min()), 1),
            "peak_price": round(float(ev["price"].max()), 1),
        }

    # Panel 3: generation mix (% of generation) during spell vs normal hours, + net-import %.
    def shares(mask: pd.Series) -> dict:
        sub = df[mask]
        if sub.empty:
            return {}
        tg = sub[gen_cols].sum().sum()
        out = {g: round(float(sub[g].sum()) / tg * 100, 1) for g in gen_cols} if tg > 0 else {}
        out["net_import_pct"] = round(float((sub["load"] - sub[gen_cols].sum(axis=1)).sum()) / sub["load"].sum() * 100, 1)
        return out

    spell_hours = int(spell_mask.sum())
    # Panel 2 frequency: raw count of hours where wind+solar < threshold, by local month
    # (richer than sustained spells alone — winter nights pile up).
    low = vre_share < threshold
    local_months = low.index.tz_convert(LOCAL_TZ).tz_localize(None).to_period("M")
    low_by_month = low.groupby(local_months).sum()
    monthly = [{"month": str(p), "low_hours": int(v)} for p, v in low_by_month.items()]
    total_low_hours = int(low.sum())
    return {
        "generated_at": generated_at, "zone": ZONE,
        "threshold_pct": threshold, "min_spell_hours": min_hours, "roll_window_h": roll_window,
        "unit": "GW (generation/imports), EUR/MWh (price)",
        "note": ("A Dunkelflaute is detected where the 24-hour rolling mean of the wind+solar "
                 "share of demand stays below the stated threshold. The threshold is a defined, "
                 "adjustable choice, not a law. net imports = load - generation (positive = "
                 "importing) and close the demand balance."),
        "period_start": df.index[0].date().isoformat(), "period_end": df.index[-1].date().isoformat(),
        "worst_event": worst,
        "spells": sorted(spells, key=lambda s: -s["hours"]),
        "monthly": monthly,
        "summary": {
            "spell_count": len(spells),
            "spell_hours_year": spell_hours,
            "longest_spell_h": max((s["hours"] for s in spells), default=0),
            "low_vre_hours_year": total_low_hours,
            "threshold_pct": threshold,
        },
        "mix": {"dunkelflaute": shares(spell_mask), "normal": shares(~spell_mask)},
    }


def build(df: pd.DataFrame) -> None:
    payload = compute(df, THRESHOLD_PCT, MIN_SPELL_HOURS,
                      datetime.now(timezone.utc).isoformat(timespec="seconds"))
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "dunkelflaute.json").write_text(json.dumps(payload, indent=2))
    s = payload["summary"]
    logger.info("wrote data/dunkelflaute.json (threshold %d%%): %d spells, %d spell-hours, longest %dh",
                s["threshold_pct"], s["spell_count"], s["spell_hours_year"], s["longest_spell_h"])
    w = payload["worst_event"]
    if w:
        logger.info("worst event %s..%s: min wind+solar %.1f%% of demand, peak price EUR %.0f",
                    w["spell_start"][:13], w["spell_end"][:13], w["min_vre_pct"], w["peak_price"])
        logger.info("mix during spells: %s", payload["mix"]["dunkelflaute"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Dunkelflaute JSON artefact.")
    parser.add_argument("--use-cache", action="store_true", help="Re-use the parquet caches.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    logger.info("dunkelflaute build start (use_cache=%s)", args.use_cache)

    end = pd.Timestamp.now(tz=LOCAL_TZ).normalize()
    start = end - pd.DateOffset(months=12)

    if args.use_cache:
        if not DF_CACHE.exists():
            logger.error("no cache at %s — run once without --use-cache.", DF_CACHE)
            sys.exit(1)
        df = pd.read_parquet(DF_CACHE)
        logger.info("loaded %d hours from cache (no API call)", len(df))
    else:
        df = fetch_inputs(start, end)
        df.to_parquet(DF_CACHE)
        logger.info("fetched + cached %d hours", len(df))

    build(df)
    logger.info("dunkelflaute build done")


if __name__ == "__main__":
    main()
