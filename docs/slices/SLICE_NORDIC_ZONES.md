# Vertical slice spec — "The Nordics: living with split price zones"

> **Status:** spec only. No code until each step is approved under the
> `RUN.md` protocol. Would be driven by `RUN_V5.md` + `prompts/v5_prompts.md`. Reuses
> the map machinery (`frontend/geo.js`, D3-geo + committed TopoJSON) from the earlier
> slices. **Stays static** — pre-computed JSON + committed boundaries, no backend, no
> tiles.

Third in the **"three ways to handle a congested grid"** set: Germany keeps one price
and curtails/redispatches (`SLICE_DE_WASTED_WIND.md`); the Nordics split into many
price zones (this slice); the UK pays wind to switch off (`SLICE_UK_REGIONAL.md`). The
set is the comparative through-line — same physics, different market designs.

## 1. The one question

**"Germany debates whether to split its single bidding zone; the Nordics already did.
What does living with SE1–SE4, NO1–NO5, DK1–DK2 and FI actually look like — and what
does it teach the German debate?"**

## 2. The panels

### Panel 1 — The map of zones
**Shows:** the Nordic countries split into ~13 bidding zones, shaded by average
day-ahead price — a hydro-rich, low-demand north that clears cheap vs a demand-heavy,
continent-connected south that clears dearer.
**Data:** ENTSO-E day-ahead price per zone (averaged); a committed Nordic price-zone
boundary GeoJSON.
**Acceptance:** all zones render and shade by price; legend in €/MWh; "no data" distinct.

### Panel 2 — How far prices diverge
**Shows:** within-country price gaps over time (e.g. SE1 vs SE4, NO2 vs NO4) — how often
and how much zones decouple. The evidence that zonal pricing produces real, localised
signals (the thing a single zone hides).
**Data:** ENTSO-E day-ahead prices per zone — **already the site's backbone via
`entsoe-py`**, so this panel is cheap.
**Acceptance:** within-country spread series renders, tz-aware (local time), DST-safe;
decoupling episodes visible; gaps honest.

### Panel 3 — The lesson for Germany
**Shows:** the structural hydro-north / demand-south split, tied explicitly to the DE
north–south slice — "Germany has the same physical split but one price; the Nordics
priced it." Evenhanded on the trade-offs (efficiency + investment signals vs solidarity,
complexity, and structurally higher southern prices).
**Acceptance:** the DE link is explicit; framing is non-advocacy; copy block A present.

## 3. Datasets & endpoints (from `SOURCES.md`)

| Dataset | Feeds | Granularity | Access | Static |
|---------|-------|-------------|--------|--------|
| [ENTSO-E day-ahead prices](https://transparency.entsoe.eu) per Nordic zone (SE1–4, NO1–5, DK1–2, FI) | Panels 1–2 | Bidding zone, hourly | Token (already held) | Y |
| [Energinet](https://www.energidataservice.dk/) / [Svenska kraftnät](https://data.svk.se/) / [Fingrid](https://data.fingrid.fi/en) *(optional generation/hydro context)* | Panel 3 context | Zone | Open / Key | Y |
| Nordic price-zone boundaries — **custom GeoJSON** (zones are groups of counties, not admin units) | Panel 1 basemap | ~13 zones | Build/curate | Y |

## 4. New pipeline modules (isolated)

- `pipeline/build_nordic_zones.py` — fetch ENTSO-E day-ahead prices for the Nordic
  zones, average + monthly series + within-country gaps → `data/nordic_prices.json`.
  Reuses the ENTSO-E client but stays a **separate builder**; add to the daily refresh.

## 5. Data contract (update `data/schema.md`)

```jsonc
// data/nordic_prices.json
{
  "generated_at": "ISO-8601", "unit": "EUR/MWh",
  "zones": [ { "code": "SE4", "country": "SE", "avg_price": 0, "months": [] } ],
  "within_country_gap": { "SE": { "months": [], "avg_gap": 0 } }
}
```

## 6. Frontend

- Reuses `frontend/geo.js` + D3.
- New asset `frontend/geo/nordic_zones.topo.json` (~13 zones, simplified, < 120 KB).
- New page `frontend/nordic_zones.html`.

## 7. Honest-framing copy blocks

**Block A — the zonal-pricing trade-off (Panel 3):**
> The Nordics are split into many price zones, so a windy, hydro-rich north can clear at
> a different (often lower) price than a demand-heavy south — the prices reflect where
> the grid is actually constrained. This is the live version of the split Germany debates
> for its single DE-LU zone. Supporters say zonal prices steer investment to where it's
> needed; critics say they push structurally higher prices onto some regions and add
> complexity. Wattlas takes no side — it shows what splitting looks like in a system that
> already did it.

**Block B — what a zone is:**
> A bidding zone is the area inside which electricity clears at one wholesale price. Nordic
> zones group regions by where the transmission grid constrains flows — they are not
> administrative regions, so the map boundaries are approximate.

## 8. Open risks & caveats

- **Zone-boundary geometry is the hard asset** — price zones aren't admin units and have
  no clean official TopoJSON. Build from county/elspot-area groupings or use a clearly
  schematic map; label as approximate.
- Nordic prices are heavily **hydro/reservoir- and weather-driven** — note this context so
  divergence isn't misread purely as congestion.
- ENTSO-E zone EIC codes; tz-aware, DST-safe; gaps render honestly.
- Stays static.

## 9. Out of scope

Full Nordic generation/hydro deep-dive; balancing/reserve markets; intraday.

## 10. Build sequence (gated)

0. Pre-flight (read this + `SOURCES.md` + schema; name the landmines: zones ≠ admin units; hydro-driven prices).
1. Zone map shell — commit `nordic_zones.topo.json`; render empty zone map via `geo.js`.
2. `build_nordic_zones.py` — ENTSO-E zone prices → `nordic_prices.json`; schema; tests. **🧑 USER sanity-checks prices** (north generally cheaper; plausible €/MWh).
3. Panel 1 — price-shaded zone map.
4. Panel 2 — within-country divergence over time.
5. Panel 3 — the lesson for Germany + copy blocks A/B; link to the DE slice.
6. Integrate & polish; add builder to `refresh-data.yml`; tests; static check.

## 11. Definition of done

Three panels render from committed JSON; numbers rounded + unit-labelled; copy blocks
present; schema updated; builder in the daily refresh; offline tests pass; reuses
`geo.js`; opens as a static file — no backend, no tiles.
