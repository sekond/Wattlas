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
