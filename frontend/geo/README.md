# `frontend/geo/` — committed map assets

## `landkreise.topo.json`

Pre-simplified TopoJSON basemap of the **~400 German Landkreise** (Kreise and
kreisfreie Städte), used by `wasted_wind.html` via `geo.js`. Committed as a static
asset so the page renders with **no map tiles and no runtime map service** — it
opens as a file (CLAUDE.md: stay static).

- **Source:** Eurostat **GISCO** NUTS 2021, level 3, EPSG:4326, 1:3M resolution.
  German NUTS-3 regions correspond 1:1 to the Kreise/Landkreise.
  `https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_03M_2021_4326_LEVL_3.geojson`
- **Licence:** © EuroGeographics for the administrative boundaries (GISCO open
  terms — attribution required wherever the map is shown).
- **Coverage:** 401 features (the 2021 NUTS-3 count for Germany).
- **Size:** ~88 KB (target < 150 KB).
- **Properties kept:** `NUTS_ID` (e.g. `DEF07`), `NAME_LATN` (e.g. `Nordfriesland`).

### How it was built (one-off; not part of the daily refresh)

```bash
# raw source downloaded to a temp dir, then:
mapshaper NUTS_RG_03M_2021_4326_LEVL_3.geojson \
  -filter 'CNTR_CODE === "DE"' \
  -filter-fields NUTS_ID,NAME_LATN \
  -simplify 15% keep-shapes \
  -rename-layers landkreise \
  -o format=topojson quantization=10000 frontend/geo/landkreise.topo.json
```

`keep-shapes` guarantees no district collapses during simplification; `quantization`
keeps coordinates compact. Regenerate only if the NUTS vintage changes — the basemap
is static and is **not** rebuilt by `refresh-data.yml`.

### Join key — NUTS-3 vs AGS (read before Step 3/4)

This basemap is keyed by **NUTS-3 code** (`DEF07`). MaStR aggregation (Step 3) keys
on the German **AGS / Kreisschlüssel** (`01054`). These are different coding systems
with a stable 1:1 crosswalk for Germany. The capacity JSON and the choropleth must be
joined through that crosswalk (built/applied in Step 3–4); do not assume `NUTS_ID == ags`.

---

## `regions_fr.topo.json` (France slice — v4)

Pre-simplified TopoJSON of the **13 metropolitan French régions**, used by
`fr_nuclear.html` via `geo.js`. Committed static asset; no tiles.

- **Source:** Eurostat **GISCO** NUTS 2021, **level 1** (EPSG:4326, 1:3M). Note: after
  the 2016 French reform the 13 régions sit at **NUTS-1** (`FR1`…`FRM`); NUTS-2 still
  holds the *old* 22 régions, so level 1 is correct here. Overseas (`FRY`) excluded —
  metropolitan France only.
- **Licence:** © EuroGeographics (GISCO open terms — attribution required).
- **Coverage:** 13 régions. **Size:** ~8 KB (target < 100 KB).
- **Properties kept:** `NUTS_ID` (e.g. `FRB`), `NAME_LATN` (e.g. `Centre — Val de Loire`).

```bash
mapshaper NUTS_RG_03M_2021_4326_LEVL_1.geojson \
  -filter 'CNTR_CODE === "FR" && NUTS_ID !== "FRY"' \
  -filter-fields NUTS_ID,NAME_LATN \
  -simplify 14% keep-shapes \
  -rename-layers regions \
  -o format=topojson quantization=10000 frontend/geo/regions_fr.topo.json
```

### Join key (read before Step 5)

Keyed by **NUTS-1 code** (`FRB`). éCO2mix régional data identifies régions by **name**
or **INSEE région code** — build a crosswalk to `NUTS_ID` when wiring `fr_regional.json`
(Step 5); do not assume the codes match.

---

## `nordic_zones.topo.json` (Nordic price-zones slice — v5)

Pre-simplified TopoJSON of the **12 Nordic electricity bidding zones** (Sweden SE1–SE4,
Norway NO1–NO5, Denmark DK1–DK2, Finland FI), used by `nordic_zones.html` via `geo.js`.
Committed static asset; no tiles.

- **Source:** Eurostat **GISCO** NUTS 2021, **level 3** (EPSG:4326, 1:3M) for SE, NO, DK,
  FI — the same family as the basemaps above. The NUTS-3 counties are **dissolved into
  bidding zones** via a county→zone crosswalk (below).
- **Licence:** © EuroGeographics (GISCO open terms — attribution required).
- **Coverage:** 12 zones dissolved from 62 NUTS-3 counties. **Size:** ~21 KB (target < 120 KB).
- **Object name:** `zones`. **Properties kept:** `code` (the join key, e.g. `SE4`),
  `country` (`SE`/`NO`/`DK`/`FI`), `name` (e.g. `South (SE4)`).

### Join key

Keyed by **bidding-zone code** `code` (`SE1`…`FI`) — *not* a NUTS code. The price JSON
(`data/nordic_prices.json`, built by `pipeline/build_nordic_zones.py`) keys on the same
zone codes, so the choropleth joins directly on `props.code`.

### ⚠️ Boundaries are APPROXIMATE (read before trusting the map)

Bidding zones are **not** administrative regions — they group areas by where the
transmission grid constrains flows, and have no official TopoJSON. This asset is built
by assigning each whole NUTS-3 county to the zone that covers most of it, so counties the
zone border physically cuts through are approximations (label the map "schematic"):

- **SE2/SE3 line:** Gävleborg → SE2 (larger part), Dalarna → SE3 (larger part).
- **SE3/SE4 line:** Halland, Jönköping, Kalmar, Gotland assigned by dominant population/area.
- **NO1/NO2/NO5 lines:** Viken, Vestfold og Telemark, Innlandet → NO1; Rogaland → NO2 — each
  straddles a zone border.
- **Excluded:** Jan Mayen (`NO0B1`) and Svalbard (`NO0B2`) — off the synchronous grid.
  **Åland** (`FI200`) is grouped with Finland (FI).

The crosswalk was cross-checked against Svenska kraftnät, Statnett, Nord Pool, Energinet
and Wikipedia "Elområden i Sverige".

### How it was built (one-off; not part of the daily refresh)

```bash
# 1) tag each Nordic NUTS-3 feature with its bidding zone (Python crosswalk),
#    excluding Jan Mayen/Svalbard, writing _tmp_geo/nordic_zoned.geojson
# 2) dissolve counties -> zones, simplify, emit TopoJSON:
mapshaper _tmp_geo/nordic_zoned.geojson \
  -dissolve zone copy-fields=code,country,name \
  -simplify 12% keep-shapes \
  -rename-layers zones \
  -o format=topojson quantization=10000 frontend/geo/nordic_zones.topo.json
```

`keep-shapes` prevents any zone collapsing during simplification. Static — **not** rebuilt
by `refresh-data.yml` (regenerate only if the NUTS vintage or a zone boundary changes).

---

## `uk_dno.topo.json` (UK regional slice — v6)

Pre-simplified TopoJSON of the **14 GB DNO licence-area regions** — the same regions
the NESO Carbon Intensity API uses — used by `uk_regional.html` via `geo.js`.
Committed static asset; no tiles.

- **Source:** NESO data portal, **"GIS Boundaries for GB DNO Licence Areas"** (2024-05-03).
  Published in **EPSG:27700** (OSGB / British National Grid); **reprojected to WGS84**
  in the build (mapshaper can't read 27700 from the GeoJSON crs member, so it is named
  explicitly via `-proj from=EPSG:27700`).
- **Licence:** NESO open data (attribution required).
- **Coverage:** 14 regions. **Size:** ~34 KB (target < 120 KB). **Object name:** `regions`.
- **Properties kept:** `regionid` (the join key, 1–14), `name` (e.g. `North Scotland`),
  `short` (map label, e.g. `N Scotland`), `dno` (the operator).

### Join key

Keyed by the Carbon Intensity API **`regionid` (1–14)** — *not* a postcode or GSP letter.
`pipeline/build_uk_regional_carbon.py` writes `data/uk_regional_carbon.json` keyed by the
same `regionid`, so the choropleth joins directly on `props.regionid`. The crosswalk from
the source's GSP-group letter (`Name` = `_A`…`_P`) to `regionid` lives in
`frontend/geo/uk_dno.build.py`.

### ⚠️ Great Britain only; boundaries approximate

These are **GB** licence areas — **Northern Ireland is excluded** (it is on the all-island
SEM). NESO notes the boundaries are *approximate*: they run through rural areas and shift
as connections are added. North Scotland (SSEN) includes the Highlands and islands
(Orkney, Shetland, Western Isles), so the map extends well north of the mainland.

### How it was built (one-off; not part of the daily refresh)

```bash
python frontend/geo/uk_dno.build.py   # downloads NESO GeoJSON, tags regionid, runs:
# mapshaper dno_tagged.geojson -proj from=EPSG:27700 wgs84 \
#   -simplify 8% keep-shapes -rename-layers regions \
#   -o format=topojson quantization=10000 frontend/geo/uk_dno.topo.json
```

Static — **not** rebuilt by `refresh-data.yml` (regenerate only if NESO republishes the
boundaries).
