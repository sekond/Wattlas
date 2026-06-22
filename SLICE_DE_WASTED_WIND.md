# Vertical slice spec — "Why Germany throws away wind it can't ship south"

> **Status:** spec only. No code is written until each step below is approved under
> the `RUN.md` / `RUN_V2.md` protocol (one step per turn, confirmation-gated).
> Detailed per-step prompts will live in `prompts/v3_prompts.md`, mirroring
> `prompts/v2_prompts.md`. This is **phase one (Germany only)**; the France
> regional layer is deferred to phase two, after this ships and is validated.

This is the first **map-based** view in Wattlas and the first that goes *below* the
bidding-zone line. It reuses existing Spread and Curtailment data and adds two new,
isolated pipeline modules. It stays fully static — pre-computed JSON + a pre-simplified
TopoJSON basemap, no backend, no tiles, no browser storage.

---

## 1. The one question this slice answers

**"Germany built its wind in the north and its demand in the south — so how much
clean power does the grid throw away because it can't move it, and what does that
say about pricing the whole country as one zone?"**

The argument the data must make, in three beats:

1. Generation and demand sit in different places (a map).
2. That mismatch is structural and the grid is congested between them (north surplus,
   south deficit + redispatch).
3. The waste is real and paid for — yet one uniform price hides the scarcity, which is
   the heart of the bidding-zone-split debate.

---

## 2. The three panels

### Panel 1 — The mismatch map (capacity vs demand)

**Shows:** where wind and solar capacity actually sits vs where load is.

- Choropleth of **installed capacity (MW) by Landkreis** (~400 districts), with a
  **wind / solar toggle** (the two are rendered as separate metrics, never summed).
- **Top-20 largest plants** as individual points (utility-scale, ≥30 kW, so
  coordinates are public), hover = name · fuel · MW · Landkreis.
- **Demand layer:** control-area / Land-level load from SMARD (real, coarse). An
  optional population-weighted Landkreis proxy may be added **only if clearly
  labelled as a proxy** (see copy block C).

**Insight to land:** wind capacity clusters in the windy north/northeast; solar is
more distributed; demand concentrates in the industrial south and west. The map and
the load layer don't line up.

**Acceptance criteria:**
- All ~400 Landkreise render with no missing-geometry holes; the wind/solar toggle
  swaps the metric and the legend (MW).
- "No data" / zero renders visually distinct from a low-but-present value.
- Landkreis MW totals reconcile to within **±2%** of the national MaStR wind and
  solar totals (sanity check against the raw extract).
- Top-20 plants plot at correct coordinates with correct fuel colour (reuse the
  canonical palette in `frontend/fuels.js` / `pipeline/fuels.py`).
- Combined page payload (TopoJSON + panel JSON) **< 400 KB** gzipped.
- The map shows installed *capacity*, captioned as such (copy block D).

### Panel 2 — Surplus north, deficit south (the structural imbalance + congestion)

**Shows:** that the north routinely generates more than it consumes and the south
less — and that the grid can't always bridge the gap.

- Per **control area** (50Hertz, TenneT, Amprion, TransnetBW): **net balance =
  generation − load** over time, from SMARD (hourly → daily, tz-aware Europe/Berlin).
- **Redispatch / curtailment volume** (netztransparenz, regional) overlaid as the
  congestion evidence — *the* reason the surplus can't always reach the deficit.

**Insight to land:** the imbalance is physical and persistent; redispatch spikes when
the north is long and the corridor is full.

> **Data honesty note:** the DE–LU north–south bottleneck is *internal* to a single
> bidding zone, so it does **not** appear in ENTSO-E cross-border flows or in zonal
> prices. We evidence it with **net regional balance (SMARD) + redispatch volume
> (netztransparenz)**, not a clean intra-German MW flow series (which is not publicly
> published in a usable form). Do not fabricate an inter-TSO flow line.

**Acceptance criteria:**
- Net balance computed per control area, grouped in Europe/Berlin local time, 23/25-h
  DST days handled (no assumption of 24 values/day).
- Northern areas (50Hertz, TenneT) show structural surplus on high-wind days; southern
  (TransnetBW, Amprion) show deficit — directionally correct against known facts.
- Redispatch/curtailment series renders; gaps render as gaps; if netztransparenz
  credentials are absent the panel degrades to the existing **"awaiting source"**
  state (reuse `build_curtailment.py` behaviour) rather than erroring or faking zeros.

### Panel 3 — The waste, and the price that hides it

**Shows:** the wasted clean energy against the negative-price hours it coincides
with, then the punchline.

- **Curtailment volume (MWh/day)** — reuse existing `data/curtailment.json` /
  `build_curtailment.py` — plotted against **negative-price hours/day** from existing
  Spread data (`data/spread.json`).
- **Punchline sub-panel "one price, split grid":** a single DE-LU day-ahead price
  line spanning the physically split grid, with the evenhanded bidding-zone-split
  copy (block A).

**Insight to land:** stormy, high-wind days produce both curtailment *and* negative
prices — yet every region pays the same wholesale price, so the price signal never
tells the south it's short or the north it's long.

**Acceptance criteria:**
- Curtailment MWh/day and negative-price hours/day share a linked time axis;
  correlation is visible on stormy weeks.
- Panel 3 **reuses** existing curtailment and spread JSON — totals cross-check against
  those views (no recomputation drift).
- The split punchline panel renders copy block A verbatim; no advocacy language.

---

## 3. Datasets & endpoints

All sourced from `SOURCES.md`. Secrets (where needed) live in `.env` (gitignored);
read via environment variables. Each row that is new gets its **own isolated pipeline
module** — never entangled with the ENTSO-E pipeline (landmine 11).

| Dataset | Feeds | Granularity | Access / auth | Lag | Static |
|---------|-------|-------------|---------------|-----|--------|
| [MaStR](https://www.marktstammdatenregister.de/MaStR) via [`open-mastr`](https://open-mastr.readthedocs.io/) bulk download | Panel 1 capacity + top-20 plants | Unit → rolled to Landkreis (AGS) | Open (attribution; coords restricted <30 kW — irrelevant after aggregation) | Registry, periodic | Y* (commit **aggregates only**) |
| [SMARD `chart_data`](https://github.com/bundesAPI/smard-api) — `https://www.smard.de/app/chart_data/{filter}/{region}/...json` | Panel 2 generation & load per control area | 4 control areas + national; 15-min / hourly | Open (no key); **German labels** | ~hours | Y |
| netztransparenz redispatch/curtailment (via existing `build_curtailment.py`; [stromfee.club](https://stromfee.club/redispatch/) wrapper as fallback) | Panel 2 congestion + Panel 3 curtailment | Regional / per-TSO | **Credentials in `.env`**; degrades to "awaiting source" if absent | 1–3 days | Y |
| Existing `data/spread.json` (+ `spread_summary.json`) | Panel 3 negative-price hours | DE-LU daily | Already in repo | — | Y |
| Landkreis boundaries — [Eurostat GISCO NUTS](https://ec.europa.eu/eurostat/web/gisco) or BKG VG250, simplified with [mapshaper](https://mapshaper.org/) | Panel 1 basemap | ~400 Landkreise | Open | Static | Y |

---

## 4. New pipeline modules (isolation preserved)

New code, each pure and offline-testable on small fixtures (per coding conventions),
writing pre-aggregated JSON to `data/`:

- **`pipeline/de_fields.py`** *(new — the translation layer)*. Single source of truth
  mapping German MaStR/SMARD field names and category labels → English. **No German
  string is allowed to reach the frontend or the ENTSO-E pipeline.** Unit-tested with a
  small dictionary fixture.
- **`pipeline/build_mastr_capacity.py`** *(new, isolated)*. Downloads MaStR (bulk via
  `open-mastr`), filters to **operating** wind (onshore/offshore) and solar units,
  maps each unit's municipality key (AGS) → Landkreis, sums **net nominal capacity
  (MW)**, and extracts the **top-20 plants by MW**. Writes
  `data/de_capacity_by_landkreis.json` + `data/de_top_plants.json`. Uses `de_fields`.
- **`pipeline/build_regional_balance.py`** *(new, isolated from ENTSO-E — SMARD is a
  separate source with its own quirks, landmine 11)*. Fetches per-control-area
  generation and load from SMARD, resamples to the canonical hourly grid (mind the
  Oct-2025 resolution break, landmine 3), computes net balance, writes
  `data/de_regional_balance.json`. Uses `de_fields`.
- **Reuse** `pipeline/build_curtailment.py` (already isolated, already handles the
  netztransparenz credential-absent degrade) for Panels 2–3. Extend only if a
  per-region split is needed.

All new builders are added to the daily `refresh-data.yml` GitHub Action, and must
not crash the workflow if their source is unavailable (degrade, log, continue —
landmine 8).

---

## 5. Data contract (update `data/schema.md` in the same change)

New JSON shapes (rounded numbers only; units stated):

```jsonc
// data/de_capacity_by_landkreis.json
{
  "generated_at": "ISO-8601",
  "source": "MaStR (Bundesnetzagentur)",
  "unit": "MW",
  "metric": "installed net nominal capacity",
  "landkreise": [
    { "ags": "09162", "name": "München", "wind_onshore_mw": 12, "wind_offshore_mw": 0, "solar_mw": 845 }
    // ~400 entries
  ]
}

// data/de_top_plants.json
{
  "generated_at": "ISO-8601",
  "source": "MaStR (Bundesnetzagentur)",
  "unit": "MW",
  "plants": [
    { "name": "...", "fuel": "Wind offshore", "mw": 0, "lat": 0.0, "lon": 0.0, "landkreis": "..." }
    // 20 entries
  ]
}

// data/de_regional_balance.json
{
  "generated_at": "ISO-8601",
  "source": "SMARD (Bundesnetzagentur)",
  "unit": "GW",
  "areas": ["50Hertz", "TenneT", "Amprion", "TransnetBW"],
  "days": [
    { "date": "YYYY-MM-DD", "generation_gw": {}, "load_gw": {}, "balance_gw": {} }
  ]
}
```

Reused unchanged: `data/curtailment.json`, `data/spread.json`.

---

## 6. New frontend dependencies & assets

- **D3-geo** (`d3-geo`, `d3-selection`, `d3-scale`, `topojson-client`) loaded from CDN.
  **This is a new dependency** — Wattlas is currently Chart.js-only. D3 is added
  *alongside* Chart.js for geographic rendering; time-series panels stay on Chart.js.
  Rationale for D3 over Leaflet/MapLibre: **no tile server, no runtime network
  dependency** → the page still opens as a static file, preserving the architecture.
- **`frontend/geo/landkreise.topo.json`** — pre-simplified TopoJSON of German
  Landkreise. Raw GeoJSON is ~5–15 MB; after mapshaper simplification (~5–10% of
  vertices, quantized) target **< 150 KB**. Committed as a static asset.
- **`frontend/geo.js`** — a small map helper (projection, choropleth, points),
  keeping render logic separate from data-loading (per conventions).
- **`frontend/wasted_wind.html`** — standalone page (consistent with the existing
  per-view pages), later linkable as a dashboard panel. Keep standalone until it
  proves better integrated.

---

## 7. Honest-framing copy blocks (use verbatim; credibility-sensitive)

**Block A — the bidding-zone-split debate (Panel 3 punchline):**
> Germany and Luxembourg are a single bidding zone: one wholesale electricity price
> for the whole area, even when the grid physically can't move power from the windy
> north to the industrial south. When the link is full, cheap northern wind can't
> reach southern demand, so the operator pays some plants to turn down and others to
> turn up — *redispatch* — and the cost lands on consumers' grid fees.
> Some economists argue this is the case for splitting Germany into smaller bidding
> zones, so prices would signal scarcity where the grid is constrained and pull
> investment to where it's needed. Others argue a single zone preserves price
> solidarity between regions, avoids structurally higher prices in the south, and
> keeps the market simpler and more liquid. *Wattlas takes no side — it shows the
> physical mismatch the debate is about.*
> *(Verify the current status of the EU bidding-zone review before publishing.)*

**Block B — curtailment definition (Panels 2–3):**
> "Wasted" here means renewable energy the grid couldn't absorb or transmit and was
> instructed to reduce. These are regional volumes reported by the German TSOs
> (netztransparenz) with a 1–3 day lag — a real, paid-for quantity, not an estimate,
> and not attributed to individual turbines.

**Block C — demand proxy (only if the population-weighted layer is used):**
> Demand shown here is distributed using population as a proxy; Germany doesn't
> publish electricity consumption at Landkreis resolution at this cadence. Read it as
> *where people and activity are*, not metered load.

**Block D — capacity vs output (Panel 1 caption):**
> This map shows installed *capacity* (MW), not energy produced. A high-capacity
> Landkreis still generates little on a calm or dark day. Capacity shows where the
> build-out happened; the time-series panels show what it does.

---

## 8. Open risks & data-quality caveats

- **MaStR volume & freshness.** Millions of units (mostly rooftop solar); only the
  **aggregated** outputs are committed. Confirm Landkreis (AGS) coverage and dedupe
  decommissioned units during step 3. Bulk extract is large — runs in the pipeline,
  never shipped raw.
- **Demand granularity.** True Landkreis-level load isn't published; the honest
  baseline is control-area/Land load (SMARD). The population proxy is optional and
  must be labelled (block C).
- **Intra-zone flows.** No clean public MW series for north→south flow; we use net
  regional balance + redispatch as the evidence (see Panel 2 note). Don't overclaim.
- **Redispatch lag & credentials.** 1–3 day lag; needs netztransparenz credentials;
  must degrade gracefully.
- **Boundary/projection accuracy.** Simplified TopoJSON trades fidelity for size;
  pick a projection suited to Germany (e.g., conic) and verify no Landkreis collapses.
- **MaStR attribution.** Display the Bundesnetzagentur attribution required by the
  open licence.

---

## 9. Out of scope for this slice

- **France** (nuclear-vs-demand regional layer) — phase two, after this validates.
- **Unit-level rendering** of all wind/solar — aggregation + top-20 only.
- **Per-turbine curtailment attribution** — volumes by region only.
- **Live / real-time / forecasting** — stays static, historical.
- **Consumption-based carbon**, pan-zoom map tiles, and any backend or database.

---

## 10. Build sequence (gated steps — one per turn, per RUN protocol)

1. **Map shell.** Add D3 + `topojson-client`; commit simplified
   `landkreise.topo.json`; render an empty choropleth from a tiny inline fixture.
   *Ship test:* the map of Germany draws, no data yet.
2. **Translation module.** `pipeline/de_fields.py` + unit tests.
3. **MaStR aggregation.** `build_mastr_capacity.py` → the two JSON files; update
   `schema.md`; unit-test aggregation on a fixture. **← USER sanity-checks the first
   real capacity numbers (gated, per RUN.md).**
4. **Panel 1.** Wire choropleth + wind/solar toggle + top-20 points + caption (block D).
5. **Regional balance.** `build_regional_balance.py` from SMARD → Panel 2 (net balance
   + redispatch overlay, reusing curtailment's degrade behaviour).
6. **Panel 3.** Curtailment vs negative-price reuse + "one price, split grid" punchline
   + copy blocks A/B.
7. **Integrate & polish.** Standalone page → optional dashboard panel; rounding /
   English-only / caveat pass; add new builders to `refresh-data.yml`.

---

## 11. Definition of done

- `python pipeline/build_mastr_capacity.py` and `build_regional_balance.py` produce the
  three JSON artefacts; the page renders all three panels from committed JSON with no
  network calls.
- Every displayed number is rounded and unit-labelled; **no German labels** surface in
  the UI; the curtailment and split copy carry their honest-framing caveats.
- New JSON shapes documented in `schema.md` in the same change; new builders in the
  daily refresh action; all degrade gracefully if a source is missing.
- Aggregation/metric functions have offline unit tests that pass.
- The page opens as a static file — no backend, no tiles, no browser storage.
