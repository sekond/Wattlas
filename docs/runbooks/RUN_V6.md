# RUN_V6.md — Execution protocol for the UK regional slice

Same rules as `RUN.md` / `RUN_V2`–`V5`: **you never copy-paste prompts.** Claude Code
reads them itself from `prompts/v6_prompts.md` and works through the steps in
`SLICE_UK_REGIONAL.md` in order. You approve each step before it runs and verify the
result before the next.

This builds **one slice** — the UK story (regional carbon map + Scottish wind constraint
payments + the three-fixes comparison), the British member of the "three ways to handle a
congested grid" set. It **reuses the map machinery** (`frontend/geo.js`, D3-geo +
committed TopoJSON) and adds **two new external sources**.

## How to start

> **Follow RUN_V6.md.**

## The protocol Claude Code follows

One step at a time — never more than one per turn. For each step:

1. State the step number and what it builds (note when it touches a new source).
2. **Stop and wait for the user's explicit approval.** Honour skip/stop/adjust.
3. On approval, execute that step's prompt from `prompts/v6_prompts.md` yourself.
4. Regenerate any affected JSON and run the tests.
5. Report concisely: what was added, key output (regions, intensity range, £ cost), criteria met.
6. **Wait again** before the next step.

**Verification checkpoint (🧑):** at **Step 2**, hand control to the user to sanity-check
regional carbon — clean, windy Scotland low; gas-heavy regions high; plausible gCO₂/kWh.

**Architectural guardrail (CLAUDE.md):** static — pre-computed JSON + committed TopoJSON,
**no backend, no tiles**. Reuse `geo.js`.

**New-source isolation (landmines 11–12):** the NESO Carbon Intensity API and the
constraint-payment feed each get their **own** module, never entangled with the ENTSO-E or
German/French pipelines. State units and methodology in writing.

## The steps (full detail in `prompts/v6_prompts.md`; rationale in `SLICE_UK_REGIONAL.md`)

### Step 0 — Pre-flight + orientation
Execute **Prompt 0**: read `CLAUDE.md`, `SLICE_UK_REGIONAL.md`, `SOURCES.md`, `data/schema.md`;
<200-word summary; change nothing.
**Gate:** names the three landmines — GB ≠ UK (no Northern Ireland); regional carbon here is
**consumption-based** (don't mix with the site's production-based view); a constraint payment
is a managed grid-stability cost, not energy discarded by choice.

### Step 1 — Region map shell
Execute **Prompt 1**: commit `frontend/geo/uk_dno.topo.json` (14 GB regions, < 120 KB); render
an empty 14-region map via `geo.js`. (Add D3 only if not already present.)
**Gate:** the 14 regions render, no data yet.

### Step 2 — Regional carbon 🧑
Execute **Prompt 2**: `pipeline/build_uk_regional_carbon.py` pulls the NESO Carbon Intensity
API → `data/uk_regional_carbon.json` (per-region intensity + mix); update `schema.md`; tests.
**🧑 USER sanity-checks** (Scotland clean, gas regions high).
**Gate:** the user confirms the intensities are plausible.

### Step 3 — Panel 1 (how clean each region is)
Execute **Prompt 3**: shade the 14 regions by gCO₂/kWh; legend; methodology stated (copy A).
**Gate:** regions render and shade; methodology + GB-not-UK noted.

### Step 4 — Constraint payments
Execute **Prompt 4**: `pipeline/build_uk_constraints.py` pulls constraint-payment & curtailed-
wind data (NESO / Elexon) → `data/uk_constraints.json` (monthly GWh + £); update `schema.md`;
tests.
**Gate:** the series builds; verify the dataset/columns; degrade gracefully if unavailable.

### Step 5 — Panel 2 (Scottish wind, paid to stop)
Execute **Prompt 5**: curtailed GWh and £ cost over time; spikes line up with high-wind, low-
demand periods; copy block B (what a constraint payment is).
**Gate:** the cost/volume series renders; copy block B present; gaps honest.

### Step 6 — Panel 3 (same problem, different fix)
Execute **Prompt 6**: compare GB constraint payments vs Germany's redispatch/curtailment vs the
Nordic zonal split; copy block C; explicit links to `wasted_wind.html` and `nordic_zones.html`.
**Gate:** both links present; evenhanded.

### Step 7 — Integrate, polish, lock in
Execute **Prompt 7**: rounding / caveat pass; optional dashboard callout; add both builders to
`refresh-data.yml` (degrade if a source is missing); confirm offline tests and static open.
**Gate:** definition of done in `SLICE_UK_REGIONAL.md` §11 met.

## Between steps
Each panel is a stopping point and a chance to show the DE↔Nordics↔UK comparison to a field
person. Build → show → re-prioritise.
