# v6 prompts — the UK regional slice

Detailed prompts for each step of the UK slice. Execute via `RUN_V6.md`, one step at a
time, with confirmation between steps. Full rationale, panels, JSON shapes, acceptance
criteria, and copy blocks live in `SLICE_UK_REGIONAL.md` — trust it. `CLAUDE.md` is loaded
automatically.

Prime directive: **stay static** (pre-computed JSON + committed TopoJSON, no backend, no
tiles). Reuse `frontend/geo.js` + D3. Each new source is its **own isolated module**. Round
every number; state units and methodology.

---

## Prompt 0 — Pre-flight + orientation

> **Goal:** load the slice into memory before touching code.
> **Inputs:** `CLAUDE.md`, `SLICE_UK_REGIONAL.md`, `SOURCES.md`, `data/schema.md`.
> **Build:** read them; produce a <200-word summary of the one question, three panels,
> datasets, and the two new modules. Change nothing.
> **Success criteria:** names the three landmines — GB ≠ UK (no Northern Ireland); regional
> carbon here is consumption-based (don't mix with the production-based site view); a
> constraint payment is a managed grid-stability cost, not energy discarded by choice.

---

## Prompt 1 — Region map shell

> **Goal:** stand up the 14-region GB map with no data.
> **Inputs:** GB DNO region boundaries (open GeoJSON), `mapshaper`; `geo.js` + D3.
> **Build:** simplify + commit `frontend/geo/uk_dno.topo.json` (< 120 KB); add
> `frontend/uk_regional.html`; render an empty 14-region map via `geo.js` + the page shell.
> Add D3 only if not already present.
> **Domain landmines:** Great Britain only (no Northern Ireland) — note it. No tiles.
> **Output:** the boundary asset, `uk_regional.html`; a note on file size.
> **Success criteria:** 14 regions render; no data yet; opens static; reuses `geo.js`.

---

## Prompt 2 — Regional carbon (NESO API) 🧑 (USER verifies)

> **Goal:** the per-region carbon data for Panel 1.
> **Inputs:** NEW source — NESO Carbon Intensity API (regional, 14 DNO-boundary regions,
> free, no key).
> **Build:** add `pipeline/build_uk_regional_carbon.py` (its **own** isolated module): pull
> per-region intensity (gCO₂/kWh) + generation mix → `data/uk_regional_carbon.json` (shape in
> §5); update `schema.md`; unit-test on a fixture.
> **Domain landmines:** state the methodology (NESO regional is **consumption-based**) and
> units; GB not UK; gaps honest.
> **Output:** the module, the JSON, schema update, test; a console note of the intensity range.
> **🧑 Then hand to the user** to sanity-check: Scotland clean/low, gas-heavy regions high.
> **Success criteria:** JSON produced + schema-documented; intensities plausible; tested;
> user confirms; static.

---

## Prompt 3 — Panel 1: how clean each region is

> **Goal:** the carbon-shaded region map.
> **Inputs:** `uk_regional_carbon.json`, the DNO asset, `geo.js`.
> **Build:** shade the 14 regions by gCO₂/kWh; legend; methodology stated (copy block A).
> **Success criteria:** regions shade by intensity; methodology + GB-not-UK noted; payload
> within budget.

---

## Prompt 4 — Constraint payments (NESO / Elexon)

> **Goal:** the curtailed-wind and £-cost data for Panel 2.
> **Inputs:** NEW source — NESO / Elexon constraint-payment & curtailment data (BMRS Insights).
> **Build:** add `pipeline/build_uk_constraints.py` (its **own** isolated module): curtailed
> GWh + £ cost over time → `data/uk_constraints.json` (shape in §5); update `schema.md`; tests.
> **Domain landmines:** confirm the exact dataset/columns (revised over time); state currency
> (GBP); degrade gracefully if the source is unavailable.
> **Output:** the module, the JSON, schema update, test; a console note of coverage + totals.
> **Success criteria:** monthly GWh + £ build; figures plausible; isolated module; static.

---

## Prompt 5 — Panel 2: Scottish wind, paid to stop

> **Goal:** the British "wasted wind" with a price tag.
> **Inputs:** `uk_constraints.json`.
> **Build:** plot curtailed GWh and £ cost over time; spikes line up with high-wind, low-
> demand periods; copy block B (what a constraint payment is — managed, paid, not waste-by-
> choice; the British equivalent of German redispatch).
> **Success criteria:** cost/volume series renders; copy block B present; gaps honest; static.

---

## Prompt 6 — Panel 3: same problem, different fix

> **Goal:** the three-fixes comparison.
> **Inputs:** the DE slice (`wasted_wind.html`) and the Nordic slice (`nordic_zones.html`).
> **Build:** Britain's constraint-payment design vs Germany's redispatch/curtailment vs the
> Nordic zonal split; copy block C; explicit links to both slices.
> **Domain landmines:** evenhanded — mechanism, not verdict.
> **Success criteria:** both links present; copy block C present; non-advocacy; static.

---

## Prompt 7 — Integrate, polish, lock in

> **Goal:** production-clean and auto-refreshed.
> **Inputs:** the three panels; `refresh-data.yml`; tests.
> **Build:** rounding / English-only / caveat pass; optional dashboard "Deep dives" callout +
> nav link; add both UK builders to the daily refresh (degrade if a source is missing);
> confirm offline tests and static open.
> **Success criteria:** definition of done in `SLICE_UK_REGIONAL.md` §11 met.
