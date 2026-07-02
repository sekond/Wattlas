#!/usr/bin/env python3
"""Regenerate frontend/geo/uk_dno.topo.json — the 14 GB DNO licence-area regions.

ONE-OFF curated asset, NOT part of the daily refresh (like the other geo assets).
Re-run only if NESO republishes the boundaries.

What it does:
  1. Downloads the NESO "GB DNO Licence Areas" GeoJSON (EPSG:27700) to the system
     temp dir (cached).
  2. Tags each licence area with its NESO Carbon Intensity API `regionid` (1-14) via
     the GSP-group-letter crosswalk below — this is the join key to the regional
     carbon data (data/uk_regional_carbon.json, Step 2).
  3. Reprojects 27700 -> WGS84, simplifies, and writes the committed TopoJSON
     (object "regions") next to this script. Needs `npx` (mapshaper).

Source: NESO data portal, "GIS Boundaries for GB DNO Licence Areas" (2024-05-03).
The boundaries are GB only (no Northern Ireland) and approximate (they run through
rural areas and shift as connections are added) — see frontend/geo/README.md.
"""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

GEOJSON_URL = ("https://api.neso.energy/dataset/0e377f16-95e9-4c15-a1fc-49e06a39cfa0/"
               "resource/1c6a7dc0-1b6c-443a-bc67-5f7125649434/download/"
               "gb-dno-license-areas-20240503-as-geojson.geojson")

# GSP-group letter (GeoJSON `Name`) -> (Carbon Intensity API regionid, display name, short label).
# regionid 1-14 is the join key to NESO regional carbon. Names match the API shortnames.
CROSS = {
    "_P": (1,  "North Scotland",      "N Scotland"),
    "_N": (2,  "South Scotland",      "S Scotland"),
    "_G": (3,  "North West England",  "N West"),
    "_F": (4,  "North East England",  "N East"),
    "_M": (5,  "Yorkshire",           "Yorks"),
    "_D": (6,  "North Wales & Merseyside", "N Wales"),
    "_K": (7,  "South Wales",         "S Wales"),
    "_E": (8,  "West Midlands",       "W Mids"),
    "_B": (9,  "East Midlands",       "E Mids"),
    "_A": (10, "East England",        "E England"),
    "_L": (11, "South West England",  "S West"),
    "_H": (12, "South England",       "S England"),
    "_C": (13, "London",              "London"),
    "_J": (14, "South East England",  "S East"),
}


def main() -> int:
    out_path = Path(__file__).resolve().parent / "uk_dno.topo.json"
    tmp = Path(tempfile.gettempdir()) / "wattlas_uk_geo"
    tmp.mkdir(exist_ok=True)
    raw = tmp / "dno_2024.geojson"
    tagged = tmp / "dno_tagged.geojson"

    if not raw.exists():
        print(f"Downloading NESO DNO licence areas -> {raw} ...")
        urllib.request.urlretrieve(GEOJSON_URL, raw)
    src = json.loads(raw.read_text(encoding="utf-8"))

    feats = []
    for f in src["features"]:
        nm = f["properties"]["Name"]
        if nm not in CROSS:
            raise SystemExit(f"unmapped GSP group {nm!r}")
        rid, name, short = CROSS[nm]
        f["properties"] = {"regionid": rid, "name": name, "short": short,
                           "dno": f["properties"].get("DNO_Full")}
        feats.append(f)
    if len(feats) != 14:
        raise SystemExit(f"expected 14 regions, got {len(feats)}")
    # Keep the crs member so the explicit -proj from=EPSG:27700 below is well-founded.
    tagged.write_text(json.dumps({"type": "FeatureCollection", "crs": src.get("crs"),
                                  "features": feats}), encoding="utf-8")
    print(f"tagged 14 regions; regionids {sorted(p['properties']['regionid'] for p in feats)}")

    # mapshaper can't read EPSG:27700 from the GeoJSON crs member, so name it explicitly.
    cmd = ["npx", "-y", "mapshaper", str(tagged),
           "-proj", "from=EPSG:27700", "wgs84",
           "-simplify", "8%", "keep-shapes",
           "-rename-layers", "regions",
           "-o", "format=topojson", "quantization=10000", str(out_path)]
    print("Running:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True, shell=(sys.platform == "win32"))
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"\nmapshaper step failed ({e}). Tagged GeoJSON is at {tagged};\n"
              f"run the mapshaper command above manually (needs Node/npx).")
        return 1
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
