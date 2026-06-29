# v2 prompts — the expansion phases

Detailed prompts for each phase in `../docs/roadmaps/ROADMAP_V2.md`. Execute via `../docs/runbooks/RUN_V2.md`, one
phase at a time, with confirmation between phases. Each follows the repo's rule:
explicit goal, inputs, output format, success criteria. `CLAUDE.md` (with the v2
data landmines) is loaded automatically — trust it; don't re-derive the quirks.

A reminder of the prime directive from CLAUDE.md: **stay static** (pre-computed
JSON, no backend) unless a phase explicitly says otherwise — and none of these
do. Pre-compute new data at build time into JSON the frontend reads.

---

## Phase 1 — Full generation mix

> **Goal:** add a "Mix" view showing the full generation breakdown by fuel type,
> and a two-zone side-by-side comparison (the France-nuclear vs Germany-renewables
> story).
> **Inputs:** ENTSO-E generation-per-type (already partially fetched for
> Mismatch); the existing pipeline and fuel-colour palette.
> **Build:**
> 1. Extend the pipeline to fetch and store *all* generation types for DE-LU and
>    the neighbour zones, aggregated by local hour of day and by day, written to
>    new JSON (update `data/schema.md`).
> 2. Add `frontend/mix.html`: a stacked-area chart of generation by fuel type for
>    a selected zone, plus a mode that shows two zones side by side for direct
>    comparison.
> 3. Reuse a single consistent fuel-colour palette across this and all other
>    views (lignite brown, solar yellow, nuclear grey, etc.). Define it once.
> **Domain landmines (see CLAUDE.md):** generation-by-type has more gaps and
> quirks than price data — some categories underreported, "other" buckets,
> missing hours. Handle gaps gracefully; never fabricate a clean stack. Keep
> hourly resampling + Europe/Berlin grouping. Zones are EIC/bidding zones, not
> countries.
> **Output:** `frontend/mix.html`, pipeline + schema changes, regenerated JSON, a
> console note of which zones/fuel types have usable data.
> **Success criteria:** (1) full fuel breakdown renders as a stacked area;
> (2) DE-LU vs FR side-by-side makes the nuclear-baseload vs renewables-volatility
> contrast obvious; (3) fuel colours consistent app-wide; (4) data gaps render
> cleanly; (5) still static.

---

## Phase 2 — Cross-border physical flows

> **Goal:** upgrade Divergence so it shows *physical* flows and congestion, not
> just price differences — explaining *why* zones decouple.
> **Inputs:** ENTSO-E cross-border physical flows and day-ahead NTC (net transfer
> capacity); the existing Divergence view.
> **Build:**
> 1. Pipeline: fetch physical flows (MW, directional) between DE-LU and each
>    neighbour, plus the available transmission capacity, aggregated to a sensible
>    resolution; write to JSON (update schema).
> 2. Frontend: add to Divergence a flow indicator per border (direction +
>    magnitude) and a congestion flag for hours/periods where flow is at/near
>    capacity. Visually connect a congested border to the price gap on that border.
> **Domain landmines:** flows are directional (DE→FR ≠ FR→DE); capacity values may
> be reported per-direction and may be missing for some borders/periods (this is
> normal — show "no data", don't error). Keep tz-aware, hourly handling.
> **Output:** updated Divergence frontend, pipeline + schema changes, regenerated
> JSON, console note of which borders have flow + capacity data.
> **Success criteria:** (1) physical flow shown per DE border with direction;
> (2) congested hours flagged where flow ≈ capacity; (3) a congested border
> visibly coincides with a price gap; (4) missing-border data handled gracefully;
> (5) still static.

---

## Phase 3 — Consolidated dense dashboard

> **Goal:** one dense dashboard where all approaches are reactive panels driven by
> shared controls, replacing the need to navigate between separate pages.
> **Inputs:** all existing views plus Phase 1 (Mix) and Phase 2 (flows). No new
> data source.
> **Build `frontend/dashboard.html`:**
> 1. A persistent global control bar: zone selector (DE-LU + neighbours) and
>    time-window selector (offer only windows the data supports).
> 2. Panels in a responsive grid (multi-column desktop, stacked mobile): Pulse,
>    Spread, Divergence (+flows), Mix, Mismatch.
> 3. Shared state — changing zone or window re-renders all panels together from
>    pre-computed JSON. No navigation between approaches.
> **Density requirements:** one inline headline KPI per panel (not four cards);
> secondary numbers in tooltips; consistent fonts, axes, and the shared
> zone/fuel colour palette across all panels; fits a desktop screen with minimal
> scroll; stacks on mobile.
> **Resolution honesty:** when a window is finer than a panel's native resolution
> (e.g. "last week" on monthly Divergence), show the nearest sensible resolution
> with a small note; never break or blank.
> **Keep the standalone pages** (don't delete pulse/spread/etc.html); dashboard is
> additive until proven. Link to it from the nav.
> **Output:** `frontend/dashboard.html`, any aggregation/schema changes,
> regenerated JSON, console note of supported zones + windows.
> **Success criteria:** (1) all approaches as panels on one page; (2) changing
> zone/window updates all panels together; (3) denser than today yet readable,
> consistent styling; (4) graceful resolution degradation; (5) still static;
> (6) existing pages still work.

---

## Phase 4 — Curtailment / "wasted" renewables (NEW SOURCE: SMARD)

> **Goal:** add a "Curtailment" view showing when/where/how much renewable
> generation was throttled because the grid couldn't absorb or transmit it.
> **Inputs:** NEW source — SMARD.de (German regulator) redispatch & curtailment
> data. Research its download API/format first.
> **Build:**
> 1. A new, *separate* pipeline module for SMARD (isolate it — different source,
>    different failure modes; do not entangle with the ENTSO-E pipeline). Fetch
>    curtailment/redispatch volumes (and cost if available), write to JSON.
> 2. `frontend/curtailment.html`: curtailed energy over time, ideally split by
>    cause/region; relate it to high-wind and negative-price periods.
> **Domain landmines:** this is a new source with its own auth, units, language
> (German field names), and resolution. Validate units explicitly. Don't assume it
> aligns 1:1 with ENTSO-E timestamps — reconcile carefully and document the join.
> Handle gaps; this dataset can lag.
> **Output:** new pipeline module, `frontend/curtailment.html`, schema entry,
> generated JSON, console note on data coverage and units.
> **Success criteria:** (1) curtailment over time renders with correct, stated
> units; (2) curtailment events line up sensibly with high-wind/negative-price
> periods from Spread; (3) the new pipeline is isolated and independently runnable;
> (4) still static.

---

## Phase 5 — Carbon intensity (NEW SOURCE)

> **Goal:** tie "renewable share" to "how clean is this hour" via grid carbon
> intensity (gCO2/kWh).
> **Inputs:** NEW source — a grid carbon-intensity dataset/API by zone and hour.
> Research a free/open option and its terms first; report the choice before
> building.
> **Build:**
> 1. A separate pipeline module to fetch carbon intensity by zone/hour → JSON.
> 2. Overlay carbon intensity on Mix and/or Pulse; optionally a "cleanest vs
>    dirtiest hours" mini-view.
> **Domain landmines:** carbon-intensity methodologies differ (production-based vs
> consumption-based, which factors). State which the source uses; don't mix
> methodologies across zones. Validate units (gCO2/kWh). Isolate the source.
> **Output:** new pipeline module, frontend overlay/view, schema entry, generated
> JSON, console note on source + methodology + coverage.
> **Success criteria:** (1) carbon intensity falls as renewable share rises
> (sanity check); (2) France (nuclear) reads low, coal-heavy hours read high;
> (3) methodology stated in the UI; (4) source isolated; (5) still static.

---

## Phase 6 — Time investigation layer

> **Goal:** let users investigate freely across time — custom ranges, zoom,
> multi-year, seasonal overlays.
> **Inputs:** existing data; extend history depth where available.
> **Build:**
> 1. Pipeline: pre-compute a longer history (target 3–5y where ENTSO-E provides
>    it) into JSON sized for client-side slicing.
> 2. Frontend (dashboard + relevant panels): a custom date-range picker and
>    click-drag zoom on time-series charts; a multi-year window option; a
>    month-of-year / seasonal overlay mode. Populate the "YoY change" KPI with a
>    real multi-year trend now that the history exists.
> **Domain landmines:** longer history spans more DST transitions and crosses the
> Oct-2025 resolution break — keep the resampling discipline. Watch JSON size; if
> a file gets large, split by year and load on demand (still static).
> **Output:** pipeline/history changes, updated frontend with range/zoom/overlays,
> regenerated JSON, console note on history depth per zone.
> **Success criteria:** (1) custom range + zoom work on time-series panels;
> (2) multi-year view shows a real trend (spreads/negative-hours over years);
> (3) seasonal overlay reveals summer-vs-winter structure; (4) YoY KPI populated;
> (5) still static; (6) load stays responsive.

---

## After v2
Don't treat all six as a checklist to grind through. After each phase, show the
sharpened app to a field person and let their reaction re-order what's left. The
ceiling note in CLAUDE.md still holds: stay static until real usage forces a
backend, and make crossing that line a deliberate decision, not a drift.
