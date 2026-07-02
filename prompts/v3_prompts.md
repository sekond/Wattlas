# v3 prompts — the "wasted wind" slice

Detailed prompts for each step of the Germany north–south slice. Execute via
`../docs/runbooks/RUN_V3.md`, one step at a time, with confirmation between steps. Full rationale,
panel definitions, JSON shapes, acceptance criteria, and verbatim copy blocks live
in `../docs/slices/SLICE_DE_WASTED_WIND.md` — trust it; don't re-derive. `CLAUDE.md` (with the v2
data landmines) is loaded automatically.

Prime directive: **stay static** (pre-computed JSON + committed TopoJSON, no backend,
no tiles). Each new source is its **own isolated module**; all German field names are
translated once in `de_fields.py`; no German label reaches the frontend; every
displayed number is rounded.

---

## Prompt 0 — Pre-flight + orientation

> **Goal:** load the slice into working memory before touching code.
> **Inputs:** `CLAUDE.md`, `../docs/slices/SLICE_DE_WASTED_WIND.md`, `../docs/SOURCES.md`, `data/schema.md`.
> **Build:** read those files; produce a single <200-word summary of the slice's one
> question, its three panels, the datasets feeding each, and the new pipeline
> modules. Change nothing.
> **Output:** the summary only.
> **Success criteria:** the summary names the two slice-specific landmines — (1) the
> north–south bottleneck is *internal* to the DE-LU bidding zone, so it appears in
> neither ENTSO-E cross-border flows nor zonal prices (evidence it with SMARD net
> balance + netztransparenz redispatch); (2) MaStR is millions of units, so only
> aggregates are committed. If either is missing, re-read before proceeding.

---

## Prompt 1 — Map shell (adds the D3 dependency)

> **Goal:** stand up the first map-capable page with no real data, proving the
> static, tile-free rendering path.
> **Inputs:** a public Landkreis boundary source (Eurostat GISCO NUTS-3, or BKG
> VG250); `mapshaper` for simplification; the existing frontend conventions
> (`styles.css`, `util.js`, data-loading separated from render).
> **Build:**
> 1. Obtain German Landkreis boundaries (~400 features), simplify with mapshaper
>    (quantize + ~5–10% of vertices), and commit as `frontend/geo/landkreise.topo.json`
>    — target **< 150 KB**.
> 2. Add D3 (`d3-geo`, `d3-selection`, `d3-scale`, `topojson-client`) from the same
>    CDN pattern Chart.js uses. This is a **new dependency** alongside Chart.js; note
>    it in the page and keep time-series panels on Chart.js.
> 3. Add `frontend/geo.js` (projection + choropleth + point helpers, render-only) and
>    `frontend/wasted_wind.html`; render an empty Germany choropleth from a tiny
>    inline fixture, plus the page shell (nav, mockup/honest banner, the three panel
>    placeholders).
> **Domain landmines:** never hand-draw geometry — use the committed TopoJSON. No
> tiles, no external map service (keeps the page openable as a file). Pick a
> projection suited to Germany (conic/Mercator) and verify no Landkreis collapses.
> **Output:** `frontend/geo/landkreise.topo.json`, `frontend/geo.js`,
> `frontend/wasted_wind.html`; console/notes on the basemap file size.
> **Success criteria:** (1) the map of Germany draws from the committed TopoJSON;
> (2) no real data yet; (3) basemap < 150 KB; (4) page opens statically; (5) existing
> pages unaffected.

---

## Prompt 2 — German→English translation module

> **Goal:** one isolated place that maps MaStR/SMARD German field and category names
> to English, so no German leaks into the frontend or the ENTSO-E pipeline.
> **Inputs:** the MaStR field/category names (fuel/technology, status, location keys)
> and SMARD's generation-type and control-area labels.
> **Build:** add `pipeline/de_fields.py` with explicit dictionaries (fuel/technology,
> unit status, control-area names) and small pure helpers to translate a record.
> Keep it dependency-free and pure.
> **Domain landmines:** be exhaustive about the categories the slice actually uses
> (wind onshore/offshore, solar; the four control areas); map unknowns to a labelled
> "Other" rather than passing German through.
> **Output:** `pipeline/de_fields.py` + `pipeline/test_de_fields.py` (offline).
> **Success criteria:** (1) every category used downstream resolves to an English
> label; (2) tests pass offline; (3) no other module hardcodes a German string.

---

## Prompt 3 — MaStR capacity aggregation 🧑 (USER verifies)

> **Goal:** turn the raw MaStR registry into the two small, committed aggregates that
> feed Panel 1.
> **Inputs:** MaStR via `open-mastr` (bulk download); `de_fields.py`; the canonical
> fuel palette (`pipeline/fuels.py`).
> **Build:**
> 1. Add `pipeline/build_mastr_capacity.py` (its **own** isolated module): download
>    MaStR bulk, filter to **operating** wind (onshore/offshore) and solar units, map
>    each unit's municipality key (AGS) → Landkreis, and sum **net nominal capacity
>    (MW)** per Landkreis per technology.
> 2. Extract the **top-20 plants by MW** (utility-scale, ≥30 kW, so coordinates are
>    public) with name, fuel, MW, lat/lon, Landkreis.
> 3. Write `data/de_capacity_by_landkreis.json` and `data/de_top_plants.json` (shapes
>    in `../docs/slices/SLICE_DE_WASTED_WIND.md` §5); **update `data/schema.md` in the same change.**
> 4. Unit-test the aggregation on a small inline fixture (no network).
> **Domain landmines:** millions of units (mostly rooftop solar) — commit **only the
> aggregates**, never raw points. Watch kW vs MW. Drop decommissioned units. Carry the
> Bundesnetzagentur attribution. Coordinates are restricted <30 kW — irrelevant after
> aggregation, but relevant for the top-20 (all ≥30 kW).
> **Output:** the module, the two JSON files, the schema update, the test; a console
> note of national wind/solar totals and any unmapped AGS codes.
> **🧑 Then stop and hand to the user** to sanity-check: national wind/solar totals in
> the tens-of-GW range, north wind-heavy, Bayern solar-heavy, Landkreis sums within
> ~2% of national totals.
> **Success criteria:** (1) both JSON files produced and schema-documented; (2) totals
> reconcile within ~2%; (3) aggregation unit-tested; (4) user confirms plausibility;
> (5) still static.

---

## Prompt 4 — Panel 1: the mismatch map

> **Goal:** the headline visual — where capacity sits vs where demand is.
> **Inputs:** `de_capacity_by_landkreis.json`, `de_top_plants.json`, the basemap and
> `geo.js`, the fuel palette; control-area or Land-level load (from SMARD, Step 5) or
> a clearly-labelled population proxy for the demand layer.
> **Build:**
> 1. Colour the Landkreis choropleth by installed MW with a **wind / solar toggle**
>    (separate metrics, never summed); legend in MW; "no data" distinct from low.
> 2. Plot the **top-20 plants** as points in canonical fuel colours, hover = name ·
>    fuel · MW · Landkreis.
> 3. Add the demand layer (labelled honestly if a proxy) and the capacity-vs-output
>    caption — **copy block D** verbatim.
> **Domain landmines:** capacity ≠ output (block D). If using the population proxy,
> label it (block C). Keep render logic in `geo.js`, data-loading separate.
> **Output:** Panel 1 in `frontend/wasted_wind.html`.
> **Success criteria:** (1) all ~400 Landkreise render, toggle swaps metric + legend;
> (2) Landkreis totals reconcile to national MaStR totals within ~2%; (3) top-20 plot
> correctly; (4) combined payload < 400 KB gzipped; (5) caption present.

---

## Prompt 5 — Panel 2: surplus north, deficit south (NEW SOURCE: SMARD)

> **Goal:** show the structural north-surplus / south-deficit imbalance and the
> congestion that strands it.
> **Inputs:** NEW source — SMARD `chart_data` (per control area: generation by type +
> load); `de_fields.py`; the existing `build_curtailment.py` (netztransparenz) for the
> redispatch overlay.
> **Build:**
> 1. Add `pipeline/build_regional_balance.py` (**own** module, isolated from ENTSO-E):
>    fetch per-control-area (50Hertz, TenneT, Amprion, TransnetBW) generation and load,
>    resample to the canonical hourly grid (mind the Oct-2025 resolution break),
>    compute **net balance = generation − load**, write `data/de_regional_balance.json`
>    (shape in §5); update schema.
> 2. Render Panel 2: a diverging net-balance view per control area + the regional
>    redispatch/curtailment volume as the congestion overlay.
> **Domain landmines:** SMARD uses German labels (→ `de_fields`) and its own units —
> validate (GW) in writing. Group in Europe/Berlin local time; handle 23/25-h DST
> days. The bottleneck is intra-zone — do **not** invent an inter-TSO MW flow line;
> net balance + redispatch is the evidence. If netztransparenz credentials are absent,
> degrade to "awaiting source".
> **Output:** the module, `data/de_regional_balance.json`, schema update, Panel 2; a
> console note of unit validation and coverage.
> **Success criteria:** (1) north (50Hertz/TenneT) shows structural surplus, south
> (Amprion/TransnetBW) deficit — directionally correct; (2) redispatch overlay renders,
> gaps as gaps; (3) module isolated and independently runnable; (4) units stated;
> (5) still static.

---

## Prompt 6 — Panel 3: the waste, and the price that hides it

> **Goal:** tie wasted clean energy to negative prices, then deliver the
> bidding-zone-split punchline.
> **Inputs:** existing `data/curtailment.json` (`build_curtailment.py`) and
> `data/spread.json` (negative-price hours). No new source.
> **Build:**
> 1. Plot curtailment volume (MWh/day) against negative-price hours/day on a linked
>    time axis (reuse the existing views' data; no recomputation drift).
> 2. Add the "one price, split grid" sub-panel: a single DE-LU day-ahead price across
>    the split grid, with the evenhanded bidding-zone-split text — **copy block A**
>    verbatim — and the curtailment definition — **copy block B**.
> **Domain landmines:** curtailment is a regional volume with 1–3 day lag, not
> per-turbine (block B). Present the split debate evenhandedly — no advocacy (block A).
> Negative-price hours are real; cross-check totals against the Spread view.
> **Output:** Panel 3 in `frontend/wasted_wind.html`.
> **Success criteria:** (1) correlation visible on stormy weeks; (2) curtailment and
> negative-hour totals match the source views; (3) blocks A and B present verbatim;
> (4) no advocacy language; (5) still static.

---

## Prompt 7 — Integrate, polish, lock in

> **Goal:** make the slice production-clean and keep it fresh automatically.
> **Inputs:** the three panels; `.github/workflows/refresh-data.yml`; the test suite.
> **Build:**
> 1. Final pass: round every displayed number, units labelled, **no German labels** in
>    the UI, all four copy-block caveats present; optional link/panel from the
>    dashboard (keep the standalone page).
> 2. Add `build_mastr_capacity.py` and `build_regional_balance.py` to the daily refresh
>    action; ensure each degrades (logs + continues) if its source is unavailable so
>    the workflow never breaks.
> 3. Confirm offline tests pass and the page opens statically with no network calls.
> **Domain landmines:** stay static; a large basemap or multi-year growth gets split,
> not backended. Don't let a missing MaStR/SMARD run crash the action.
> **Output:** updated workflow, polished `frontend/wasted_wind.html`, green tests.
> **Success criteria:** the definition of done in `../docs/slices/SLICE_DE_WASTED_WIND.md` §11 is met
> — three panels render from committed JSON, English-only, rounded, caveated, static,
> tests passing, refresh wired.
