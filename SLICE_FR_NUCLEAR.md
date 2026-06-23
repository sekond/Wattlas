# Vertical slice spec — "France's nuclear: where it sits, who it powers, when it dips"

> **Status:** spec only. No code until each step is approved under the
> `RUN.md` / `RUN_V2.md` protocol (one step per turn, confirmation-gated). Per-step
> prompts will live in `prompts/v4_prompts.md`; the runbook in `RUN_V4.md`. This is
> **phase two** — the France regional layer — and it deliberately **reuses the map
> machinery** (`frontend/geo.js`, D3-geo + committed TopoJSON) built for the Germany
> slice (`SLICE_DE_WASTED_WIND.md`). If France is built before Germany, Step 1 adds
> that machinery here instead.

Built as the matched twin of the Germany slice: same static architecture, same map
toolkit, same honesty discipline — a deliberate diptych. **Germany can't move its
wind to where the demand is; France can't always keep its nuclear running.** Each
country's low-carbon bet has a hidden weakness, and this slice tells France's half.

---

## 1. The one question this slice answers

**"France runs on a handful of big nuclear sites instead of scattered renewables —
so where is that power made, which régions lean on it, and what happens to the whole
country when the fleet dips?"**

Three beats:

1. The power is concentrated — a few large sites on rivers and coasts (a map).
2. A few nuclear-rich régions carry the country; big-demand régions import (regional
   coverage).
3. The fleet isn't "always on" — maintenance and heatwave river-cooling limits create
   real dips, and something has to fill the gap (availability / fragility).

---

## 2. The panels (three core + a cost section)

### Panel 1 — The nuclear map (where the power is made)

**Shows:** France's centralised generation geography vs Germany's distributed one.

- Choropleth of the 13 metropolitan régions by nuclear generation (or total
  generation), with **nuclear sites as points** sized by capacity (~18 sites / ~56
  reactors), hover = site · reactors · MW · river/coast.
- **Demand overlay:** régional consumption, so producer régions read differently from
  consumer régions (e.g. Île-de-France consumes far more than it makes).

**Insight:** a few big sites on the Loire, Rhône and the coast power the entire
country — the structural opposite of Germany's scattered wind and solar.

**Acceptance criteria:**
- All 13 régions render (metropolitan France; DROM excluded and noted); nuclear sites
  plot at correct coordinates with capacity-scaled markers.
- Régional generation/consumption totals reconcile to within ±3% of the national
  éCO2mix totals.
- Nuclear marker colour uses the canonical fuel palette (`Nuclear` grey).
- Combined payload (TopoJSON + JSON) < 350 KB gzipped.

### Panel 2 — Who exports, who imports (regional coverage)

**Shows:** the régional surplus/deficit balance — France's analog of Germany's
north-surplus/south-deficit panel.

- Per région: **net balance = generation − consumption** (the éCO2mix régional
  *solde*), as diverging bars and/or a choropleth; positive = net exporter, negative =
  net importer. Hour-of-day or daily profile.
- **Insight:** nuclear-dense régions (e.g. Centre-Val de Loire, Grand Est, Normandie,
  Auvergne-Rhône-Alpes) run large surpluses; demand-heavy or generation-poor régions
  (e.g. Île-de-France, PACA, Bretagne) lean on imports.

**Acceptance criteria:**
- Net balance computed per région, tz-aware Europe/Paris, DST-safe.
- Exporter/importer régions are directionally correct against known facts.
- Gaps render as gaps; régions with missing data show "no data", never zero.

> **Data honesty note:** France is one bidding zone, so a régional surplus/deficit is a
> **physical** balance, not a regional price. True inter-régional *flow matrices* are
> not cleanly published — use the régional net balance (the published *solde*), not a
> fabricated région-to-région flow line.

### Panel 3 — Availability & fragility (when the fleet dips)

**Shows:** that nuclear has its own seasonality and weather dependence.

- Nuclear **available capacity and output over time** (the year): spring/summer
  maintenance and refuelling dips, unplanned outages, and heatwave river-temperature
  derations — overlaid with **what fills the gap** (imports, gas, hydro).
- The diptych punchline tying to Germany: *Germany can't ship its wind south; France
  can't always keep its nuclear cool.*

**Insight:** the "stable baseload" still swings — France's hidden weather dependence,
the mirror of Germany's wind volatility.

**Acceptance criteria:**
- Output and available-capacity series render over the period; the gap-fillers stack
  reconciles (output + imports + gas + hydro ≈ demand on dip days).
- The summer-maintenance and any heatwave deration periods are visible and annotated.
- Copy block B (availability methodology) present; no alarmist framing.

---

### Panel 4 — What does the power really cost?

**Shows:** that the cost ranking depends on what you count — a toggle from plant-level
"sticker price" to "full system cost", applied symmetrically to every technology.

- A stacked €/MWh bar per technology — utility solar, onshore wind, France's existing
  (amortised) fleet, and new-build nuclear (EPR2) — with components: plant LCOE, waste &
  decommissioning, system & integration, and implicit/historic support.
- A **toggle**: "sticker price" shows plant LCOE only; "full system cost" stacks the
  usually-omitted adders on *every* technology. A one-line takeaway updates with it.
- Every figure carries a **visible source and a range**; the section states it is curated
  published estimates, not a live feed.

**Insight:** on sticker price wind and solar beat new nuclear roughly two-to-one and
match the existing fleet; add full system + back-end costs and the order shifts — the
amortised fleet looks cheapest, renewables' system costs narrow their lead, new build
stays priciest. No single number settles it.

**Why symmetric (credibility requirement):** the hidden-cost lens applies to *all*
technologies, never nuclear alone. Nuclear's back-end (waste, decommissioning) is large
in total (Cigéo ≈ €33–37bn) but small per MWh because it is spread over decades — and it
is *provisioned* (EDF ≈ €26bn) and already inside the Cour des comptes LCOE, so the
defensible critique is provision *adequacy*, not "ignored" costs. Renewables carry
system-integration costs (firming, grid, balancing, storage) that rise with penetration,
plus historic feed-in-tariff support. Show both, with ranges; note source lean (Lazard =
US new-build; OECD-NEA = the Nuclear Energy Agency).

**Data:** curated from published studies — Lazard LCOE+ 2024, Cour des comptes (EPR/EPR2),
ANDRA / Cigéo, OECD-NEA system costs, IRENA — transcribed into a small committed JSON
(`data/fr_costs.json`) by `pipeline/build_fr_costs.py`, each figure with a source and a
range. **This is the one section not derived from a live feed.**

**Acceptance criteria:**
- The toggle switches plant-only ↔ full-stack for every technology; the takeaway updates.
- Every number has a visible citation; each technology shows a range, not just a point.
- Existing-fleet vs new-build nuclear are distinct bars (legacy is much cheaper than EPR2).
- Framing is symmetric and non-advocacy; the "depends what you count" caveat is present.
- Stays static (committed JSON); no live feed implied.

---

## 3. Datasets & endpoints

From `SOURCES.md`. Secrets (RTE OAuth) live in `.env`; read via env vars. Each new
source is its **own isolated module** — never entangled with the ENTSO-E or the
German (SMARD/MaStR) pipelines.

| Dataset | Feeds | Granularity | Access / auth | Lag | Static |
|---------|-------|-------------|---------------|-----|--------|
| [ODRÉ — éCO2mix régional](https://opendata.reseaux-energies.fr/) ([API](https://odre.opendatasoft.com/api/v1/console)) | Panels 1–3: régional generation-by-type, consumption, net balance (*solde*) | 13 régions, 15-min / hourly | Open (Opendatasoft, ~50k calls/mo); **French labels** | ~15 min–hours | Y |
| [RTE Data Portal](https://data.rte-france.com/) | Panel 3: generation-unit **unavailability** (planned/unplanned) + national output | National / unit | **OAuth2 (`.env`)** | hours–days | Y |
| Nuclear fleet locations — ODRÉ "registre des installations" / RTE, or a committed geocoded list | Panel 1 site points | Per site (~18) / reactor (~56) | Open | Static | Y |
| [Enedis Open Data](https://data.enedis.fr/) *(optional, finer demand)* | Panel 1 demand at commune/IRIS | Commune / IRIS | Open | Daily | Y |
| Région boundaries — [Eurostat GISCO NUTS-2](https://ec.europa.eu/eurostat/web/gisco) (FR régions), simplified with [mapshaper](https://mapshaper.org/) | Panel 1–2 basemap | 13 régions | Open | Static | Y |

---

## 4. New pipeline modules (isolation preserved)

New, pure, offline-testable; write pre-aggregated JSON to `data/`:

- **`pipeline/fr_fields.py`** *(new — French translation layer)*. The single place
  mapping éCO2mix/RTE French field and category names → English (fuel/technology,
  région names, balance/solde labels). No French string reaches the frontend.
- **`pipeline/build_fr_nuclear_sites.py`** *(new, isolated)*. Produce the geocoded
  fleet — site name, reactors, capacity (MW), région, river/coast, lat/lon — from the
  ODRÉ/RTE registry or a committed source list → `data/fr_nuclear_sites.json`.
- **`pipeline/build_fr_regional.py`** *(new, isolated)*. Fetch éCO2mix régional
  generation-by-type + consumption per région, resample to the canonical hourly grid
  (Europe/Paris), compute net balance (*solde*) → `data/fr_regional.json`. Uses
  `fr_fields`.
- **`pipeline/build_fr_nuclear_availability.py`** *(new, isolated)*. Nuclear available
  capacity + output over time and the gap-fillers (imports, gas, hydro), from éCO2mix
  (+ RTE unavailability where accessible) → `data/fr_nuclear_availability.json`.
- **Reuse** `frontend/geo.js` and the D3 dependency from the Germany slice; the Carbon
  view's factors for any clean-power context.

All new builders join the daily `refresh-data.yml`, degrading (log + continue) if a
source is unavailable.

---

## 5. Data contract (update `data/schema.md` in the same change)

```jsonc
// data/fr_nuclear_sites.json
{
  "generated_at": "ISO-8601",
  "source": "ODRÉ / RTE",
  "unit": "MW",
  "sites": [
    { "name": "Gravelines", "region": "Hauts-de-France", "reactors": 6, "capacity_mw": 5460, "water": "coast", "lat": 51.01, "lon": 2.13 }
  ]
}

// data/fr_regional.json
{
  "generated_at": "ISO-8601",
  "source": "RTE éCO2mix régional via ODRÉ",
  "unit": "GW",
  "regions": [
    { "code": "CVL", "name": "Centre-Val de Loire", "nuclear_gw": 0, "generation_gw": 0, "consumption_gw": 0, "net_balance_gw": 0 }
  ],
  "hours": [0],
  "net_balance_profile": { "CVL": [] }
}

// data/fr_nuclear_availability.json
{
  "generated_at": "ISO-8601",
  "source": "RTE éCO2mix (+ RTE unavailability)",
  "unit": "GW",
  "installed_gw": 0,
  "days": [
    { "date": "YYYY-MM-DD", "available_gw": 0, "output_gw": 0, "imports_gw": 0, "gas_gw": 0, "hydro_gw": 0 }
  ]
}
```

---

Curated cost dataset (Panel 4 — **not a live feed**):

```jsonc
// data/fr_costs.json — curated published estimates, transcribed with sources + ranges
{
  "generated_at": "ISO-8601",
  "unit": "EUR/MWh",
  "note": "Illustrative central values with ranges; methodology-dependent and contested.",
  "components": ["plant", "back_end", "system", "support"],
  "technologies": [
    { "name": "Solar (utility)", "plant": 55, "back_end": 1, "system": 18, "support": 3,
      "range_full": [60, 100], "sources": ["Lazard LCOE+ 2024", "OECD-NEA", "IRENA"] },
    { "name": "Wind (onshore)", "plant": 50, "back_end": 1, "system": 16, "support": 3,
      "range_full": [55, 95], "sources": ["Lazard LCOE+ 2024", "OECD-NEA"] },
    { "name": "Nuclear — existing fleet", "plant": 50, "back_end": 5, "system": 1, "support": 3,
      "range_full": [50, 70], "sources": ["Cour des comptes", "ANDRA / Cigéo"] },
    { "name": "Nuclear — new build (EPR2)", "plant": 110, "back_end": 6, "system": 1, "support": 4,
      "range_full": [100, 190], "sources": ["Cour des comptes (EPR2)", "ANDRA / Cigéo", "Lazard LCOE+ 2024"] }
  ]
}
```

## 6. New frontend dependencies & assets

- **Reuses D3-geo + `frontend/geo.js`** from the Germany slice (no new library if that
  slice shipped first; otherwise add D3 here, same CDN pattern).
- **`frontend/geo/regions_fr.topo.json`** — pre-simplified TopoJSON of the 13
  metropolitan régions, target **< 100 KB**.
- **`frontend/fr_nuclear.html`** — the page (render logic via `geo.js`, data-loading
  separate). Standalone first; optional dashboard panel later.

---

## 7. Honest-framing copy blocks (use verbatim)

**Block A — the strategy framing (Panel 1):**
> France made a deliberate, state-led bet in the 1970s–80s: a large fleet of reactors
> supplying most of its electricity. The result is a highly centralised, low-carbon
> grid — a handful of big sites on rivers and the coast powering the whole country, the
> structural opposite of Germany's distributed wind and solar. This view shows where
> that power is made and which régions lean on it; it takes no position on nuclear
> policy.

**Block B — availability methodology (Panel 3):**
> "Available capacity" is how much of the fleet could run; "output" is how much
> actually did. Dips come from planned maintenance and refuelling (concentrated in the
> lower-demand months), unplanned outages, and — in heatwaves — environmental limits on
> how much warm water reactors may return to rivers, which forces output down. These
> are operational and environmental constraints, not safety failures. Values are
> illustrative placeholders pending the live RTE / éCO2mix feed; verify current figures.

**Block C — one bidding zone (Panel 2):**
> France is a single bidding zone: one wholesale price nationwide. A région's surplus
> or deficit here is a physical balance (generation − consumption), not a regional
> price — the same reason Germany's north–south split doesn't show up in prices.

**Block D — data vintage (footer):**
> Régional generation, consumption and balance come from RTE's éCO2mix via ODRÉ
> (production-based; French fields translated once in `fr_fields.py`). Nuclear site
> locations are public. Counts (reactors, capacity) and endpoints change — verify
> during the build.

---

**Block E — the cost comparison (Panel 4):**
> Plant-level cost is only the sticker price. This view adds the costs headline figures
> leave out — waste &amp; decommissioning, the system cost of running a grid on variable
> renewables, and implicit public support — applied to every technology, not just one.
> Nuclear's waste and decommissioning are large in total (the Cigéo repository ≈ €33–37bn)
> but small per MWh, and they are *provisioned* and already in France's official cost
> figures; the real question is whether the provisions are adequate. Renewables' system
> costs rise as their share grows. Figures are illustrative central values from published
> studies (Lazard, Cour des comptes, ANDRA, OECD-NEA, IRENA), each with a wide,
> assumption-dependent range — curated estimates, not a live feed. It takes no side; the
> point is that the ranking depends on what you count.

---

## 8. Open risks & data-quality caveats

- **French field names & language** — all translated once in `fr_fields.py`; never
  leaked to the UI.
- **Inter-régional flows are thin** — use the published régional net balance (*solde*),
  not a fabricated région-to-région flow.
- **RTE OAuth** — the unavailability feed needs registered credentials; degrade to
  éCO2mix-derived output if absent.
- **Fleet count drifts** — Fessenheim closed (2020), Flamanville-3 commissioning;
  confirm the live reactor count and capacity rather than hardcoding.
- **Heatwave constraints aren't a clean dataset** — show the observable output dip and
  annotate the cause; don't fabricate a per-reactor cooling series.
- **One bidding zone** — no sub-national price (block C).
- **Metropolitan France only** — DROM/overseas excluded for v1; state it.
- **Stay static** — pre-computed JSON + committed TopoJSON; no backend, no tiles.

---

## 9. Out of scope for this slice

- **Germany** (slice 1, `SLICE_DE_WASTED_WIND.md`).
- **Per-reactor real-time telemetry** and live outage tracking.
- **Forecasting**, consumption-based carbon, map tiles, any backend/database.
- **Commune/IRIS demand** beyond an optional Panel 1 overlay (Enedis) — deeper local
  demand is a later increment.
- **Overseas territories.**

---

## 10. Build sequence (gated steps — one per turn, per RUN protocol)

1. **Map shell (régions).** Add `frontend/geo/regions_fr.topo.json`; render an empty
   13-région choropleth via the existing `geo.js`. (Add D3 here only if the Germany
   slice hasn't already.) *Ship test:* the map of France draws, no data.
2. **Translation module.** `pipeline/fr_fields.py` + unit tests.
3. **Nuclear fleet.** `build_fr_nuclear_sites.py` → `fr_nuclear_sites.json`; update
   `schema.md`; test. **🧑 USER sanity-checks** the fleet totals (~18 sites, ~56
   reactors, ~61 GW; biggest sites e.g. Gravelines, Paluel, Cattenom).
4. **Panel 1.** Régions choropleth + nuclear site points + consumption overlay +
   copy block A.
5. **Regional coverage.** `build_fr_regional.py` (éCO2mix régional) → `fr_regional.json`;
   Panel 2 (exporter/importer régions) + copy block C.
6. **Availability & fragility.** `build_fr_nuclear_availability.py` →
   `fr_nuclear_availability.json`; Panel 3 (availability/output + gap-fillers) + the
   diptych punchline + copy block B. *(🧑 RTE OAuth credentials if the unavailability
   feed is used.)*
7. **Panel 4 — true cost.** `build_fr_costs.py` writes a curated, sourced cost dataset
   (plant + back-end + system + support, with ranges) → `fr_costs.json`; render the
   stacked €/MWh bar with the sticker ↔ full-cost toggle, dynamic takeaway, visible
   sources, and copy block E. Symmetric; study-based, not a feed.
8. **Integrate & polish.** English-only / rounding / caveat pass; optional dashboard
   panel; add builders to `refresh-data.yml`; confirm offline tests and static open.

---

## 11. Definition of done

- `build_fr_nuclear_sites.py`, `build_fr_regional.py`, `build_fr_nuclear_availability.py`
  produce their JSON; the page renders all three panels from committed JSON with no
  network calls.
- Every number rounded and unit-labelled; **no French labels** in the UI; copy blocks
  A–D present with their caveats.
- New JSON shapes documented in `schema.md` in the same change; new builders in the
  daily refresh; all degrade gracefully if a source is missing.
- Aggregation functions have offline unit tests that pass.
- Reuses `geo.js`; the page opens as a static file — no backend, no tiles, no browser
  storage.
