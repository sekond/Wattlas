# RUN_V5.md — Execution protocol for the Nordic price-zones slice

Same rules as `RUN.md` / `RUN_V2`–`V4`: **you never copy-paste prompts.** Claude Code
reads them itself from `prompts/v5_prompts.md` and works through the steps in
`SLICE_NORDIC_ZONES.md` in order. You approve each step before it runs and verify the
result before the next.

This builds **one slice** — the Nordic split-price-zones story (zone price map +
within-country divergence + the lesson for Germany), third in the "three ways to handle
a congested grid" set. It **reuses the map machinery** (`frontend/geo.js`, D3-geo +
committed TopoJSON) and the **existing ENTSO-E client**.

## How to start

> **Follow RUN_V5.md.**

## The protocol Claude Code follows

One step at a time — never more than one per turn. For each step:

1. State the step number and what it builds, in one or two sentences.
2. **Stop and wait for the user's explicit approval** ("go", "next"). Honour skip/stop/adjust.
3. On approval, execute that step's prompt from `prompts/v5_prompts.md` yourself.
4. Regenerate any affected JSON and run the tests (`python pipeline/test_metrics.py` plus
   any new ones).
5. Report concisely: what was added, key output (zones, price range, coverage), criteria met.
6. **Wait again** before the next step.

**Verification checkpoint (🧑):** at **Step 2**, hand control to the user to sanity-check
the zone prices — the north (NO4, SE1, SE2) generally cheaper than the south (SE4,
DK1/DK2), plausible €/MWh, and within-country gaps that widen in winter. If a zone reads
implausibly, stop — it's likely a wrong EIC zone code or a tz/resampling slip.

**Architectural guardrail (CLAUDE.md):** static — pre-computed JSON + committed TopoJSON,
**no backend, no tiles**. Reuse `geo.js`.

**Source note:** this slice reuses the **ENTSO-E client** the site already uses (same
source), via a *separate* builder `build_nordic_zones.py` — don't entangle it with
`build_spread.py`. The only genuinely new asset is the **zone-boundary geometry**, which
has no clean official TopoJSON (zones are county groupings) — build it or render a clearly
schematic map, labelled approximate (see the spec's risk note).

## The steps (full detail in `prompts/v5_prompts.md`; rationale in `SLICE_NORDIC_ZONES.md`)

### Step 0 — Pre-flight + orientation
Execute **Prompt 0**: read `CLAUDE.md`, `SLICE_NORDIC_ZONES.md`, `SOURCES.md`, `data/schema.md`;
produce a <200-word summary; change nothing.
**Gate:** the summary names the two landmines — Nordic price zones are not administrative
regions (boundary geometry is approximate), and Nordic prices are heavily hydro/reservoir-
and weather-driven (so divergence isn't purely congestion).

### Step 1 — Zone map shell
Execute **Prompt 1**: commit `frontend/geo/nordic_zones.topo.json` (or a clearly schematic
zone layout); render an empty zone map via `geo.js`. (Add D3 only if not already present.)
**Gate:** the Nordic zones render, no data yet; payload within budget.

### Step 2 — Zone prices 🧑
Execute **Prompt 2**: `pipeline/build_nordic_zones.py` fetches ENTSO-E day-ahead prices for
SE1–4, NO1–5, DK1–2, FI → `data/nordic_prices.json` (averages, monthly series, within-
country gaps); update `schema.md`; tests. **🧑 USER sanity-checks the prices.**
**Gate:** the user confirms the prices are plausible.

### Step 3 — Panel 1 (the map of zones)
Execute **Prompt 3**: shade each zone by average price; legend in €/MWh; "no data" distinct;
the schematic caveat.
**Gate:** all zones render and shade; north-cheap/south-dear gradient visible.

### Step 4 — Panel 2 (how far prices diverge)
Execute **Prompt 4**: within-country price series over time (e.g. SE1 vs SE4, NO4 vs NO2);
decoupling episodes visible.
**Gate:** divergence renders, tz-aware/DST-safe, gaps honest.

### Step 5 — Panel 3 (the lesson for Germany)
Execute **Prompt 5**: the structural split tied to the DE north–south slice; copy blocks
A/B; explicit link to `wasted_wind.html`.
**Gate:** DE link explicit; framing non-advocacy.

### Step 6 — Integrate, polish, lock in
Execute **Prompt 6**: rounding / caveat pass; optional dashboard "Deep dives" callout; add
the builder to `refresh-data.yml`; confirm offline tests and static open.
**Gate:** definition of done in `SLICE_NORDIC_ZONES.md` §11 met.

## Between steps
Each panel is a stopping point and a chance to show the slice — and the DE↔Nordics zone
comparison — to a field person. Build → show → re-prioritise.
