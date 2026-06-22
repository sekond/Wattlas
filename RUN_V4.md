# RUN_V4.md — Execution protocol for the France nuclear slice

Same rules as `RUN.md` / `RUN_V2.md` / `RUN_V3.md`: **you never copy-paste prompts.**
Claude Code reads them itself from `prompts/v4_prompts.md` and works through the steps
defined in `SLICE_FR_NUCLEAR.md` in order. You approve each step before it runs and
verify the result before the next.

This builds **one vertical slice** — the France nuclear view (fleet map + exporter/
importer régions + availability/fragility) — the matched twin of the Germany slice. It
**reuses the map machinery** (`frontend/geo.js`, D3-geo + committed TopoJSON) built in
`RUN_V3.md`. If France is built first, Step 1 adds that machinery here instead.

## How to start

Open the project in Claude Code and say:

> **Follow RUN_V4.md.**

## The protocol Claude Code follows

Execute the steps below **one at a time** — never more than one step per turn. For
each step:

1. State the step number and what it builds, in one or two sentences. Note when a step
   touches a new source (éCO2mix régional, RTE).
2. **Stop and wait for the user's explicit approval** ("go", "next", etc.). Honour
   skip / stop / adjust.
3. On approval, execute that step's prompt from `prompts/v4_prompts.md` yourself — do
   not ask the user to paste it.
4. Regenerate any affected JSON and run the tests (`python pipeline/test_metrics.py`,
   plus any new slice tests) to confirm nothing broke.
5. Report concisely: what was added, key console output (sites, totals, coverage), and
   whether the step's success criteria are met.
6. **Wait again** for the user before the next step.

**Verification checkpoints — pause for the user (🧑):**
- **Step 3 (nuclear fleet):** hand control to the user to sanity-check the fleet —
  ~18 sites, ~56 reactors, ~61 GW total; the biggest sites (e.g. Gravelines, Paluel,
  Cattenom) in the 5+ GW range. If a number looks off, stop — it's almost certainly the
  source list, a kW/MW slip, or a decommissioned unit (Fessenheim) left in.
- **Before Step 6 (availability):** 🧑 if the RTE unavailability feed is used, the user
  adds **RTE OAuth credentials** to `.env`; otherwise the panel degrades to
  éCO2mix-derived output. Do not attempt to obtain credentials yourself.

If a step fails, a result looks wrong, or a source returns unexpected data, **stop** —
report it and propose a fix. Do not auto-advance past a problem. Prefer a small test
fetch before a full pipeline run.

**Architectural guardrail (from CLAUDE.md):** this slice stays **static** —
pre-computed JSON + committed TopoJSON, **no backend, no tiles** (D3-geo renders the
committed boundaries). If a step seems to need a live backend or tile service, stop and
flag it as a deliberate decision rather than adding one.

**New-source isolation (landmines 11–12):** éCO2mix régional and RTE each get their
**own** pipeline module, never entangled with the ENTSO-E or the German (SMARD/MaStR)
pipelines. All French field names are translated in one place (`fr_fields.py`); no
French label reaches the frontend.

## The steps (full detail in `prompts/v4_prompts.md`; rationale in `SLICE_FR_NUCLEAR.md`)

### Step 0 — Pre-flight + orientation
Execute **Prompt 0**: read `CLAUDE.md`, `SLICE_FR_NUCLEAR.md`, `SOURCES.md`, and
`data/schema.md`; produce a <200-word summary of the slice, its three panels, and the
data plan; change nothing.
**Gate:** the summary must name the slice's two landmines — France is one bidding zone
(so a régional surplus/deficit is physical, not a price), and "available capacity" ≠
"output" (Panel 3). If not, re-read before proceeding.

### Step 1 — Map shell (régions)
Execute **Prompt 1**: commit a pre-simplified `frontend/geo/regions_fr.topo.json` (13
metropolitan régions, target <100 KB) and render an empty choropleth via the existing
`frontend/geo.js`. (Add D3 here only if the Germany slice hasn't already.)
**Gate:** the map of France draws, no real data yet; payload within budget.

### Step 2 — Translation module
Execute **Prompt 2**: add `pipeline/fr_fields.py` — the single French→English mapping
for éCO2mix/RTE field and category names — with offline unit tests.
**Gate:** `python pipeline/test_metrics.py` (and new field tests) pass.

### Step 3 — Nuclear fleet 🧑
Execute **Prompt 3**: `pipeline/build_fr_nuclear_sites.py` → `data/fr_nuclear_sites.json`
(site, reactors, capacity, région, water, lat/lon); update `schema.md`; test.
**🧑 Then hand control to the user** to sanity-check the fleet totals (see checkpoint).
**Gate:** the user confirms the totals are plausible.

### Step 4 — Panel 1 (the fleet map)
Execute **Prompt 4**: régions choropleth + nuclear site points (canonical `Nuclear`
colour) + régional consumption overlay + copy block A.
**Gate:** 13 régions render, sites plot correctly, totals reconcile, payload < 350 KB.

### Step 5 — Panel 2 (who exports, who imports)
Execute **Prompt 5**: `pipeline/build_fr_regional.py` (éCO2mix régional) →
`data/fr_regional.json`; render the diverging net-balance panel + copy block C.
**Gate:** exporter/importer régions directionally correct; gaps render as "no data".

### Step 6 — Panel 3 (availability & fragility)
Execute **Prompt 6**: `pipeline/build_fr_nuclear_availability.py` →
`data/fr_nuclear_availability.json`; render availability/output + gap-fillers, the
diptych punchline, and copy block B. *(🧑 RTE OAuth credentials if the unavailability
feed is used.)*
**Gate:** summer dip visible; gap-fillers reconcile to demand; no alarmist framing.

### Step 7 — Panel 4: what does the power really cost?
Execute **Prompt 7**: `pipeline/build_fr_costs.py` writes a curated, sourced cost dataset
(plant + back-end + system + support, each with a range) → `data/fr_costs.json`; render
the stacked €/MWh bar with the **sticker price ↔ full system cost** toggle, a dynamic
takeaway, visible source citations, and copy block E. Symmetric — every technology gets
the hidden-cost adders — and study-based, not a live feed.
**Gate:** the toggle works; every figure shows a source and a range; framing is
symmetric/non-advocacy; stays static.

### Step 8 