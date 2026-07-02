#!/usr/bin/env python3
"""Regenerate frontend/geo/nordic_zones.topo.json — the 12 Nordic bidding zones.

ONE-OFF curated asset, NOT part of the daily refresh (like landkreise/regions_fr).
Re-run only if the NUTS vintage or a zone boundary changes.

What it does:
  1. Downloads Eurostat GISCO NUTS-3 2021 (1:3M) to the system temp dir (cached).
  2. Tags each Nordic NUTS-3 county with its bidding zone via the crosswalk below
     (whole-county approximation — zones are not administrative units), excluding
     off-grid Jan Mayen/Svalbard; Aland is grouped with Finland.
  3. Dissolves counties -> zones and simplifies with mapshaper (needs `npx`),
     writing the committed TopoJSON next to this script.

The crosswalk was cross-checked against Svenska kraftnat, Statnett, Nord Pool,
Energinet and Wikipedia "Elomraden i Sverige". Counties the zone border physically
cuts through are approximations — see frontend/geo/README.md for the disclosure.
"""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

NUTS3_URL = ("https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
             "NUTS_RG_03M_2021_4326_LEVL_3.geojson")

# NUTS-3 (GISCO 2021) -> Nordic bidding zone. Finland (all NUTS-3) -> FI handled below.
CROSS: dict[str, str] = {
    # Sweden (4 zones). SE2/SE3 splits Gavleborg (larger part SE2) & Dalarna
    # (larger part SE3); SE3/SE4 splits Halland/Jonkoping/Kalmar (dominant part).
    "SE332": "SE1",
    "SE331": "SE2", "SE322": "SE2", "SE321": "SE2", "SE313": "SE2",
    "SE312": "SE3", "SE311": "SE3", "SE125": "SE3", "SE124": "SE3", "SE123": "SE3",
    "SE122": "SE3", "SE121": "SE3", "SE110": "SE3", "SE232": "SE3", "SE231": "SE3",
    "SE214": "SE3", "SE211": "SE3",
    "SE212": "SE4", "SE213": "SE4", "SE221": "SE4", "SE224": "SE4",
    # Norway (5 zones). Viken/Vestfold-Telemark/Innlandet -> NO1; Rogaland -> NO2 (each straddles).
    "NO020": "NO1", "NO081": "NO1", "NO082": "NO1", "NO091": "NO1",
    "NO092": "NO2", "NO0A1": "NO2",
    "NO060": "NO3", "NO0A3": "NO3",
    "NO071": "NO4", "NO074": "NO4",
    "NO0A2": "NO5",
    # Denmark (2 zones): Great Belt splits west (Jutland+Funen) from east (Zealand+Bornholm).
    "DK031": "DK1", "DK032": "DK1", "DK041": "DK1", "DK042": "DK1", "DK050": "DK1",
    "DK011": "DK2", "DK012": "DK2", "DK013": "DK2", "DK014": "DK2", "DK021": "DK2", "DK022": "DK2",
}
NAMES = {
    "SE1": "North (SE1)", "SE2": "North-central (SE2)", "SE3": "Central (SE3)", "SE4": "South (SE4)",
    "NO1": "East (NO1)", "NO2": "South (NO2)", "NO3": "Central (NO3)", "NO4": "North (NO4)", "NO5": "West (NO5)",
    "DK1": "West Denmark (DK1)", "DK2": "East Denmark (DK2)", "FI": "Finland (FI)",
}
ZONE_ORDER = ["SE1", "SE2", "SE3", "SE4", "NO1", "NO2", "NO3", "NO4", "NO5", "DK1", "DK2", "FI"]


def zone_for(props: dict) -> str | None:
    """Bidding zone for a NUTS-3 feature, or None to drop it (non-Nordic / off-grid)."""
    if props.get("CNTR_CODE") == "FI":
        return "FI"
    return CROSS.get(props.get("NUTS_ID"))


def main() -> int:
    out_path = Path(__file__).resolve().parent / "nordic_zones.topo.json"
    tmp = Path(tempfile.gettempdir()) / "wattlas_nordic_geo"
    tmp.mkdir(exist_ok=True)
    raw = tmp / "nuts3_2021.geojson"
    zoned = tmp / "nordic_zoned.geojson"

    if not raw.exists():
        print(f"Downloading GISCO NUTS-3 2021 -> {raw} ...")
        urllib.request.urlretrieve(NUTS3_URL, raw)
    src = json.loads(raw.read_text(encoding="utf-8"))

    feats = []
    for f in src["features"]:
        zone = zone_for(f["properties"])
        if zone is None:
            continue
        f["properties"] = {"zone": zone, "code": zone, "country": zone[:2], "name": NAMES[zone]}
        feats.append(f)
    zoned.write_text(json.dumps({"type": "FeatureCollection", "features": feats}), encoding="utf-8")

    from collections import Counter
    c = Counter(f["properties"]["zone"] for f in feats)
    print(f"{len(feats)} counties -> {len(c)} zones: " + ", ".join(f"{z}:{c[z]}" for z in ZONE_ORDER))

    cmd = ["npx", "-y", "mapshaper", str(zoned),
           "-dissolve", "zone", "copy-fields=code,country,name",
           "-simplify", "12%", "keep-shapes",
           "-rename-layers", "zones",
           "-o", f"format=topojson", "quantization=10000", str(out_path)]
    print("Running:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True, shell=(sys.platform == "win32"))
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"\nmapshaper step failed ({e}). The zoned GeoJSON is at {zoned};\n"
              f"run the mapshaper command above manually (needs Node/npx).")
        return 1
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
