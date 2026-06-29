# RUN_V3.md — Execution protocol for the "wasted wind" slice

Same rules as `../../RUN.md` / `RUN_V2.md`: **you never copy-paste prompts.** Claude Code
reads them itself from `../../prompts/v3_prompts.md` and works through the steps defined
in `../slices/SLICE_DE_WASTED_WIND.md` in order. You approve each step before it runs and
verify the result before the next.

This builds **one vertical slice** — the Germany north–south "Why Germany throws
away wind it can't ship south" view — and nothing else. France is a later slice.

## How to start

Open the project in Claude Code and say:

> **Follow RUN_V3.md.**

## The protocol Claude Code follows

Execute the steps below **one at a time** — never more than one step per turn. For
each step:

1. State the step number and what it builds, in one or two sentences. Note when a
   step adds the new map dependency (D3) or touches a new source (MaStR, SMARD).
2. **Stop and wait for the user's explicit approval** ("go", "next", etc.). Honour
   skip / stop / adjust.
3. On approval, execute that step's prompt from `../../prompts/v3_prompts.md` yourself —
   do not ask the user to paste it.
4. Regenerate any affected JSON and run the tests (`python pipeline/test_metrics.py`,
   plus any new slice tests) to confirm nothing broke.
5. Report concisely: what was added, key console output (rows written, totals,
   coverage), and whether the step's success criteria are met.
6. **Wait again** for the user before the next step.

**Verification checkpoints — pause for the user (🧑):**
- **Step 3 (MaStR aggregation):** hand control to the user to sanity-check the first
  real capacity numbers — national wind and solar totals in the tens-of-GW range,
  the north wind-heavy and the south (Bayern) solar-heavy, Landkreis totals
  reconciling to within ~2% of the national MaStR totals. If a number looks absurd,
  stop — it is almost certainly the AGS→Landkreis mapping or a unit (kW vs MW) slip.
- **Before Step 5–6 (curtailment / redispatch):** the curtailment data already
  exists from the v2 Curtailment phase. **🧑 If `netztransparenz` credentials are
  not already in `.env`**, the user adds them before these steps; otherwise the
  panels degrade to the existing "awaiting source" state. Do not attempt to obtain
  credentials yourself.

If a step fails, a result looks wrong, or a source returns unexpected data, **stop**
— report it and propose a fix. Do not auto-advance past a problem. Prefer a small
test fetch/aggregate before a full pipeline run.

**Architectural guardrail (from ../../CLAUDE.md):** this slice stays **static** —
pre-computed JSON + a committed, pre-simplified TopoJSON basemap, no backend, no
database, **no map tiles** (D3-geo renders the committed TopoJSON; no tile server,
so the page still opens as a file). If any step seems to need a live backend or a
tile service, stop and flag it as a deliberate decision rather than adding one.

**New-source isolation (landmines 11–12):** MaStR and SMARD each get their **own**
pipeline module, never entangled with the ENTSO-E pipeline. All German field names
are translated in one place (`de_fields.py`); no German label reaches the frontend.

## The steps (full detail in `../../prompts/v3_prompts.md`; rationale in `../slices/SLICE_DE_WASTED_WIND.md`)

### Step 0 — Pre-flight + orientation
Execute **Prompt 0**: read `../../CLAUDE.md`, `../slices/SLICE_DE_WASTED_WIND.md`, `../SOURCES.md`, and
`data/schema.md`; produce a <200-word summary of the slice, its three panels, and
the data plan; change nothing.
**Gate:** the summary must name the slice's two extra landmines — the north–south
bottleneck is *intra-zone* (not in ENTSO-E flows or zonal prices) and MaStR is
millions of units (aggregate only). If not, re-read before proceeding.

### Step 1 — Map shell (adds D3)
Execute **Prompt 1**: add D3 + `topojson-client` from CDN; commit a pre-simplified
`frontend/geo/landkreise.topo.json` (~400 Landkreise, target <150 KB); render an
empty choropleth of Germany from a tiny inline fixture in `frontend/wasted_wind.html`
via a new `frontend/geo.js`.
**Gate:** the map of Germany draws, no real data yet; payload within budget.

### Step 2 — Translation module
Execute **Prompt 2**: add `pipeline/de_fields.py` — the single German→English
mapping for MaStR/SMARD field and category names — with offline unit tests.
**Gate:** `python pipeline/test_metrics.py` (and new field tests) pass.

### Step 3 — MaStR capacity aggregation 🧑
Execute **Prompt 3**: `pipeline/build_mastr_capacity.py` downloads MaStR (bulk via
`open-mastr`), filters operating wind/solar, rolls up to Landkreis installed MW,
extracts the top-20 plants → `data/de_capacity_by_landkreis.json` +
`data/de_top_plants.json`; update `schema.md`; unit-test the aggregation on a
fixture.
**🧑 Then hand control to the user to sanity-check the numbers** (see checkpoint
above).
**Gate:** the user confirms the totals are plausible.

### Step 4 — Panel 1 (the mismatch map)
Execute **Prompt 4**: wire the choropleth to the real JSON, add the wind/solar
toggle, plot the top-20 plants as points (canonical fuel colours), and the
capacity-vs-output caption (copy block D).
**Gate:** toggle works, totals reconcile, top plants land correctly, payload < 400 KB.

### Step 5 — Panel 2 (surplus north, deficit south)
Execute **Prompt 5**: `pipeline/build_regional_balance.py` fetches per-control-area
generation and load from SMARD → `data/de_regional_balance.json`; render the
diverging net-balance panel with the redispatch overlay (reuse `build_curtailment.py`
degrade behaviour).
**Gate:** north shows structural surplus, south deficit; gaps render honestly.

### Step 6 — Panel 3 (waste vs price + the punchline)
Execute **Prompt 6**: plot curtailment volume (reuse `curtailment.json`) against
negative-price hours (reuse `spread.json`); add the "one price, split grid"
sub-panel with the evenhanded bidding-zone-split copy (block A) and the curtailment
caveat (block B).
**Gate:** correlation visible; totals match the source views; copy blocks present.

### Step 7 — Integrate, polish, lock in
Execute **Prompt 7**: final rounding / English-only / caveat pass; optional dashboard
panel link; add the new builders to `.github/workflows/refresh-data.yml` (degrade
gracefully if a source is missing); confirm offline tests pass and the page opens
statically.
**Gate:** definition of done in `../slices/SLICE_DE_WASTED_WIND.md` §11 met.

## Between steps — the move that matters
Each panel is a sensible stopping point and a chance to show the sharpened view to a
field person. Their reaction should re-order or trim what's left. Build → show →
re-prioritise. Don't grind all seven on spec.
