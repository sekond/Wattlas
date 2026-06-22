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
