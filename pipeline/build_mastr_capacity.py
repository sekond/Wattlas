"""Build the MaStR capacity aggregates for the "Wasted wind" Panel 1:
installed wind/solar capacity per Landkreis + the top-20 largest plants.

    python pipeline/build_mastr_capacity.py            (download via open-mastr, then aggregate)
    python pipeline/build_mastr_capacity.py --use-cache (skip download; use the local MaStR DB)

Writes data/de_capacity_by_landkreis.json and data/de_top_plants.json.

ISOLATION (CLAUDE.md landmine #11): this is its OWN pipeline module. It shares
nothing with the ENTSO-E builders — its own source (MaStR / Bundesnetzagentur),
its own units, its own German field names (translated via de_fields.py). A failure
here must not touch the other views.

UNITS (landmine #12): MaStR `Nettonennleistung` is in **kW**; we convert to **MW**
(÷1000) once, at load, and everything downstream is MW. Validated on the real
extract in Step 3 (a 3 MW turbine reads 3000).

SCALE (landmine: MaStR is millions of units): the registry holds ~4 million units
(mostly rooftop solar). We commit only the AGGREGATES below, never raw points.

GEOGRAPHY: units carry an 8-digit municipality key (Gemeindeschlüssel / AGS);
Kreis = AGS[:5]. The committed crosswalk pipeline/de_kreis_nuts.json maps each Kreis
to its NUTS-3 code so the AGS-keyed capacity joins the NUTS-keyed basemap
(frontend/geo/landkreise.topo.json). Landkreis display names come from the basemap.

OFFSHORE: offshore wind sits in the Exclusive Economic Zone and has no Landkreis
(no AGS). Such units are excluded from the per-Landkreis roll-up (they belong to no
Kreis) but kept in the national total and eligible for the top-20 plant points.

Attribution: data © Bundesnetzagentur (Marktstammdatenregister), open licence.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import de_fields

log = logging.getLogger("build_mastr_capacity")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PIPELINE_DIR = Path(__file__).resolve().parent
CROSSWALK_PATH = PIPELINE_DIR / "de_kreis_nuts.json"
BASEMAP_PATH = ROOT / "frontend" / "geo" / "landkreise.topo.json"

SOURCE = "MaStR (Bundesnetzagentur)"
TOP_N_PLANTS = 12   # per fuel (wind, solar)

# Columns we read from the open-mastr *_extended tables (shared schema).
_UNIT_COLS = [
    "NameStromerzeugungseinheit", "Energietraeger", "Lage", "EinheitBetriebsstatus",
    "Nettonennleistung", "Gemeindeschluessel", "Landkreis", "Bundesland",
    "Kuestenentfernung", "Breitengrad", "Laengengrad",
]


# --------------------------------------------------------------------------- #
# Pure, offline-testable aggregation (DataFrame in -> JSON-ready structures out)
# --------------------------------------------------------------------------- #

def normalise_units(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise a raw *_extended frame to the columns the aggregation needs.

    Output columns: name, fuel (canonical), mw, kreis5 (or None), landkreis, lat, lon.
    Filters to OPERATING units only (de_fields.mastr_is_operating). kW -> MW. Wind is
    split onshore/offshore via de_fields (EEZ Bundesland / coast distance / Lage)."""
    if df.empty:
        return pd.DataFrame(columns=["name", "fuel", "mw", "kreis5", "landkreis", "lat", "lon"])

    op = df[df["EinheitBetriebsstatus"].map(de_fields.mastr_is_operating)].copy()

    op["fuel"] = [
        de_fields.mastr_fuel(et, lage=lg, bundesland=bl, kuestenentfernung=ke)
        for et, lg, bl, ke in zip(
            op["Energietraeger"], op.get("Lage"), op.get("Bundesland"), op.get("Kuestenentfernung")
        )
    ]
    op["mw"] = pd.to_numeric(op["Nettonennleistung"], errors="coerce") / 1000.0  # kW -> MW

    ags = op["Gemeindeschluessel"].astype("string").str.strip()
    # Kreis = first 5 digits of a valid 8-digit AGS; offshore/at-sea units have none.
    op["kreis5"] = ags.where(ags.str.len() >= 5).str[:5]

    out = pd.DataFrame({
        "name": op["NameStromerzeugungseinheit"],
        "fuel": op["fuel"],
        "mw": op["mw"],
        "kreis5": op["kreis5"],
        "landkreis": op.get("Landkreis"),
        "lat": pd.to_numeric(op.get("Breitengrad"), errors="coerce"),
        "lon": pd.to_numeric(op.get("Laengengrad"), errors="coerce"),
    })
    return out[out["mw"].notna() & (out["mw"] > 0)]


# Per-Landkreis output fields, by canonical fuel.
_FUEL_FIELD = {
    "Wind onshore": "wind_onshore_mw",
    "Wind offshore": "wind_offshore_mw",
    "Solar": "solar_mw",
}


def aggregate_by_landkreis(
    units: pd.DataFrame, kreis_to_nuts: dict[str, str], nuts_to_name: dict[str, str]
) -> list[dict]:
    """Sum installed MW per Landkreis per fuel. Only units with a Kreis that maps to
    a basemap NUTS-3 are placed (offshore-at-sea and unmapped AGS are dropped here —
    the caller reports them). Returns one rounded record per Landkreis, sorted by AGS."""
    placed = units[units["kreis5"].notna() & units["kreis5"].isin(kreis_to_nuts)]
    rows: dict[str, dict] = {}
    grouped = placed.groupby(["kreis5", "fuel"])["mw"].sum()
    for (kreis5, fuel), mw in grouped.items():
        field = _FUEL_FIELD.get(fuel)
        if field is None:
            continue  # only wind/solar feed Panel 1
        nuts = kreis_to_nuts[kreis5]
        rec = rows.setdefault(kreis5, {
            "ags": kreis5, "nuts_id": nuts,
            "name": nuts_to_name.get(nuts, nuts),
            "wind_onshore_mw": 0, "wind_offshore_mw": 0, "solar_mw": 0,
        })
        rec[field] = round(rec[field] + float(mw))
    return [rows[k] for k in sorted(rows)]


def national_totals(units: pd.DataFrame) -> dict:
    """National installed MW per Panel-1 fuel (rounded). Includes offshore wind,
    which has no Landkreis (it sits in the EEZ), so the frontend can show it without
    it appearing on the choropleth."""
    g = units.groupby("fuel")["mw"].sum() if not units.empty else {}
    return {field: round(float(g.get(fuel, 0.0))) for fuel, field in _FUEL_FIELD.items()}


# Plant points are clustered PER FUEL so the wind/solar toggle can swap them. MaStR
# registers wind per turbine, so the largest individual units are offshore turbines
# packed into one farm — plotting them is a blob. Aggregating on a coarse grid turns
# each farm/park into one sized point.
_PLANT_GROUPS = {"wind": ("Wind onshore", "Wind offshore"), "solar": ("Solar",)}
_CLUSTER_GRID = 0.15   # ~10–17 km cells


def top_clusters_by_fuel(units: pd.DataFrame, n: int = TOP_N_PLANTS,
                         grid: float = _CLUSTER_GRID) -> dict[str, list[dict]]:
    """Largest wind and solar installations as map points, per fuel. Units are grouped
    into ~grid° cells (so an offshore farm's turbines collapse to one point), summed,
    and the top n cells per fuel returned — sized by total MW, coloured by canonical
    fuel, labelled by Landkreis (or 'Offshore' at sea) with the unit count."""
    cand = units[units["lat"].notna() & units["lon"].notna()].copy()
    out: dict[str, list[dict]] = {}
    for metric, fuels in _PLANT_GROUPS.items():
        sub = cand[cand["fuel"].isin(fuels)]
        if sub.empty:
            out[metric] = []
            continue
        cells = sub.assign(clat=(sub["lat"] / grid).round(), clon=(sub["lon"] / grid).round()) \
                   .groupby(["clat", "clon"])
        rows = []
        for _, c in cells:
            offshore = bool(c["kreis5"].isna().all())
            lk = c["landkreis"].dropna()
            rows.append({
                "name": (str(lk.mode().iat[0]).strip() if not lk.empty else "Offshore"),
                "fuel": ("Wind offshore" if offshore else "Wind onshore") if metric == "wind" else "Solar",
                "mw": round(float(c["mw"].sum())),
                "units": int(len(c)),
                "lat": round(float(c["lat"].mean()), 3),
                "lon": round(float(c["lon"].mean()), 3),
            })
        rows.sort(key=lambda r: -r["mw"])
        out[metric] = rows[:n]
    return out


# --------------------------------------------------------------------------- #
# I/O (kept out of the pure functions above so they test offline)
# --------------------------------------------------------------------------- #

def _load_crosswalk() -> dict[str, str]:
    return json.loads(CROSSWALK_PATH.read_text(encoding="utf-8"))["kreis_to_nuts"]


def _load_nuts_names() -> dict[str, str]:
    topo = json.loads(BASEMAP_PATH.read_text(encoding="utf-8"))
    geoms = topo["objects"]["landkreise"]["geometries"]
    return {g["properties"]["NUTS_ID"]: g["properties"]["NAME_LATN"] for g in geoms}


def _load_mastr_units(use_cache: bool) -> pd.DataFrame:
    """Download (unless --use-cache) and read operating wind+solar from the local
    open-mastr SQLite DB. Returns the concatenated normalised units."""
    from open_mastr import Mastr

    db = Mastr()
    if not use_cache:
        log.info("Downloading MaStR wind+solar (partial, cleansed) via open-mastr…")
        db.download(method="bulk", data=["wind", "solar"], bulk_cleansing=True)

    frames = []
    for table in ("wind_extended", "solar_extended"):
        # Wind- and solar-extended share most columns but not all (e.g. Lage and
        # Kuestenentfernung are wind-only). Select what each table actually has and
        # backfill the rest as null so normalise_units sees a consistent shape.
        have = set(pd.read_sql(f"SELECT * FROM {table} LIMIT 0", db.engine).columns)
        sel = [c for c in _UNIT_COLS if c in have]
        df = pd.read_sql(f"SELECT {', '.join(sel)} FROM {table}", db.engine)
        for c in _UNIT_COLS:
            if c not in df.columns:
                df[c] = None
        frames.append(normalise_units(df))
    return pd.concat(frames, ignore_index=True)


def build(use_cache: bool = False) -> dict:
    kreis_to_nuts = _load_crosswalk()
    nuts_to_name = _load_nuts_names()
    units = _load_mastr_units(use_cache)

    landkreise = aggregate_by_landkreis(units, kreis_to_nuts, nuts_to_name)
    clusters = top_clusters_by_fuel(units)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    cap = {
        "generated_at": now, "source": SOURCE,
        "unit": "MW", "metric": "installed net nominal capacity",
        "national_mw": national_totals(units),
        "landkreise": landkreise,
    }
    top = {"generated_at": now, "source": SOURCE, "unit": "MW",
           "wind": clusters["wind"], "solar": clusters["solar"]}

    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "de_capacity_by_landkreis.json").write_text(
        json.dumps(cap, ensure_ascii=False, indent=0), encoding="utf-8")
    (DATA_DIR / "de_top_plants.json").write_text(
        json.dumps(top, ensure_ascii=False, indent=0), encoding="utf-8")

    # ---- validation summary (the numbers the user sanity-checks) ----
    nat = units.groupby("fuel")["mw"].sum() / 1000.0  # GW
    placed = units[units["kreis5"].notna() & units["kreis5"].isin(kreis_to_nuts)]
    unmapped = units[units["kreis5"].notna() & ~units["kreis5"].isin(kreis_to_nuts)]
    no_ags = units[units["kreis5"].isna()]
    log.info("National operating capacity (GW): %s",
             {k: round(v, 1) for k, v in nat.items()})
    log.info("Landkreise with capacity: %d / 401", len(landkreise))
    log.info("Placed %.1f%% of MW; unmapped-AGS units: %d; offshore/at-sea (no AGS): %d",
             100 * placed["mw"].sum() / units["mw"].sum(), len(unmapped), len(no_ags))
    return cap


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser(description="Build MaStR capacity aggregates (Panel 1).")
    ap.add_argument("--use-cache", action="store_true",
                    help="Skip download; use the existing local open-mastr DB.")
    args = ap.parse_args()
    build(use_cache=args.use_cache)
