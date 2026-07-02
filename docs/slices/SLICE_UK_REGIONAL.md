# Vertical slice spec — "The UK: regional carbon, and wind paid to stop"

> **Status:** spec only. No code until each step is approved under the `RUN.md`
> protocol. Would be driven by `RUN_V6.md` + `prompts/v6_prompts.md`. Reuses the map
> machinery (`frontend/geo.js`, D3-geo + committed TopoJSON). **Stays static** —
> pre-computed JSON + committed boundaries, no backend, no tiles.

The British member of the **"three ways to handle a congested grid"** set: Germany keeps
one price and curtails/redispatches (`SLICE_DE_WASTED_WIND.md`); the Nordics split into
price zones (`SLICE_NORDIC_ZONES.md`); Britain pays wind to switch off — the same
physical problem, a third market design.

## 1. The one question

**"Britain's wind is in the north (Scotland), its demand in the south; when the grid
between can't carry it, wind farms are paid to switch off. How clean is each region, and
what does the bottleneck cost?"**

## 2. The panels

### Panel 1 — How clean each region is
**Shows:** the 14 GB regions shaded by grid carbon intensity — clean, windy Scotland and
the hydro/nuclear north vs gas-heavy regions — with the day/period swing.
**Data:** NESO Carbon Intensity API (regional, 14 DNO-boundary regions, forecast +
actual).
**Acceptance:** 14 regions render and shade by gCO₂/kWh; legend; methodology stated.

### Panel 2 — Scottish wind, paid to stop
**Shows:** wind constraint volumes and the **£ cost** over time — wind curtailed because
the grid (the B6 boundary between Scotland and England) can't move it south. The British
"wasted wind", with a transparent price tag consumers pay.
**Data:** NESO / Elexon constraint-payment & curtailment data (BMRS Insights).
**Acceptance:** curtailed GWh and £ render over time; spikes line up with high-wind, low-
demand periods; gaps honest; "paid to reduce" defined (copy block B).

### Panel 3 — Same problem, different fix
**Shows:** Britain's constraint-payment market design side by side with Germany's
redispatch/curtailment and the Nordics' zonal split — three answers to one bottleneck.
**Acceptance:** explicit links to the DE and Nordic slices; evenhanded; copy block C.

## 3. Datasets & endpoints (from `SOURCES.md`)

| Dataset | Feeds | Granularity | Access | Static |
|---------|-------|-------------|--------|--------|
| [Carbon Intensity API (NESO)](https://carbonintensity.org.uk/) | Panel 1 | 14 GB regions, 30-min, forecast + actual | Open (no key) | Y |
| [Elexon BMRS Insights](https://bmrs.elexon.co.uk/) / [NESO data portal](https://www.neso.energy/data-portal) — constraint costs & curtailed wind | Panel 2 | GB / boundary, daily–monthly | Open | Y |
| GB DNO region boundaries — open GeoJSON, simplified with mapshaper | Panel 1 basemap | 14 regions | Open | Y |

## 4. New pipeline modules (isolated)

- `pipeline/build_uk_regional_carbon.py` — Carbon Intensity API → `data/uk_regional_carbon.json`
  (per-region intensity + generation mix).
- `pipeline/build_uk_constraints.py` — constraint payments & curtailed wind →
  `data/uk_constraints.json` (monthly GWh + £). Separate, isolated module.

## 5. Data contract (update `data/schema.md`)

```jsonc
// data/uk_regional_carbon.json
{ "generated_at": "ISO-8601", "unit": "gCO2/kWh", "methodology": "NESO regional, consumption-based",
  "regions": [ { "id": "Scotland-North", "intensity": 0, "renewable_pct": 0 } ] }

// data/uk_constraints.json
{ "generated_at": "ISO-8601", "currency": "GBP",
  "months": [ { "month": "YYYY-MM", "curtailed_gwh": 0, "cost_gbp_m": 0 } ] }
```

## 6. Frontend

- Reuses `frontend/geo.js` + D3.
- New asset `frontend/geo/uk_dno.topo.json` (14 regions, simplified, < 120 KB).
- New page `frontend/uk_regional.html`.

## 7. Honest-framing copy blocks

**Block A — carbon methodology (Panel 1):**
> Regional carbon intensity from NESO — state whether it is production- or consumption-
> based (NESO's regional figures are consumption-based) and that it covers Great Britain,
> not Northern Ireland. gCO₂/kWh.

**Block B — what a constraint payment is (Panel 2):**
> When the grid can't carry Scottish wind south, the system operator pays wind farms to
> turn down (and other plants elsewhere to turn up) to keep the system stable. These
> "constraint payments" are a real, published cost that consumers ultimately pay — the
> British equivalent of Germany's redispatch — not energy discarded by choice.

**Block C — three fixes, one problem (Panel 3):**
> Germany, the Nordics and Britain all face renewable-rich regions a congested grid can't
> fully serve. Germany keeps one price and curtails + redispatches; the Nordics split into
> price zones; Britain pays constraints. Each has trade-offs; Wattlas shows the mechanism,
> not a verdict.

## 8. Open risks & caveats

- **Great Britain, not UK** — NESO/GB excludes Northern Ireland (all-island SEM); say so.
- **Constraint-payment data** — confirm the NESO/Elexon dataset and columns during the
  build; figures and methods are revised.
- Carbon API is **consumption-based** regionally — don't mix with the site's
  production-based carbon view without labelling.
- DNO boundary geometry simplified; tz-aware; gaps honest; stays static.

## 9. Out of scope

All-island / Northern Ireland; balancing-market depth; postcode-level carbon (the API
supports it, but region-level is the v1 scope).

## 10. Build sequence (gated)

0. Pre-flight (read this + `SOURCES.md` + schema; name the landmines: GB ≠ UK; regional carbon is consumption-based; constraint payment ≠ waste-by-choice).
1. Region map shell — commit `uk_dno.topo.json`; render empty 14-region map via `geo.js`.
2. `build_uk_regional_carbon.py` → `uk_regional_carbon.json`; schema; tests. **🧑 USER sanity-checks** (Scotland clean, gas regions high).
3. Panel 1 — carbon-shaded region map + copy block A.
4. `build_uk_constraints.py` → `uk_constraints.json`; schema; tests.
5. Panel 2 — Scottish constraint payments over time + copy block B.
6. Panel 3 — three-fixes comparison + copy block C; link to DE + Nordic slices.
7. Integrate & polish; add builders to `refresh-data.yml`; tests; static check.

## 11. Definition of done

Three panels render from committed JSON; numbers rounded + unit-labelled; copy blocks
present; GB-not-UK and consumption-based-carbon stated; schema updated; builders in the
daily refresh; offline tests pass; reuses `geo.js`; opens as a static file — no backend,
no tiles.
