# v4 prompts — the France nuclear slice

Detailed prompts for each step of the France nuclear slice. Execute via `../docs/runbooks/RUN_V4.md`,
one step at a time, with confirmation between steps. Full rationale, panel definitions,
JSON shapes, acceptance criteria, and verbatim copy blocks live in `../docs/slices/SLICE_FR_NUCLEAR.md`
— trust it; don't re-derive. `CLAUDE.md` (with the v2 data landmines) is loaded
automatically.

Prime directive: **stay static** (pre-computed JSON + committed TopoJSON, no backend,
no tiles). Reuse `frontend/geo.js` + D3 from the Germany slice. Each new source is its
**own isolated module**; all French field names are translated once in `fr_fields.py`;
no French label reaches the frontend; every displayed number is rounded.

---

## Prompt 0 — Pre-flight + orientation

> **Goal:** load the slice into working memory before touching code.
> **Inputs:** `CLAUDE.md`, `../docs/slices/SLICE_FR_NUCLEAR.md`, `../docs/SOURCES.md`, `data/schema.md`.
> **Build:** read those files; produce a single <200-word summary of the slice's one
> question, its three panels (fleet map, exporter/importer régions, availability/
> fragility), the datasets feeding each, and the new pipeline modules. Change nothing.
> **Output:** the summary only.
> **Success criteria:** the summary names the two landmines — (1) France is a single
> bidding zone, so a région's surplus/deficit is a *physical* balance (the éCO2mix
> *solde*), not a regional price, and inter-régional flow matrices aren't cleanly
> published; (2) Panel 3 distinguishes "available capacity" from "output". If either is
> missing, re-read before proceeding.

---

## Prompt 1 — Map shell (régions)

> **Goal:** stand up the France map with no real data, reusing the Germany slice's
> static, tile-free rendering path.
> **Inputs:** a public région boundary source (Eurostat GISCO NUTS-2 for FR), `mapshaper`;
> the existing `frontend/geo.js` and D3 dependency from the Germany slice.
> **Build:**
> 1. Obtain the 13 metropolitan régions, simplify with mapshaper (quantize + few
>    vertices), commit as `frontend/geo/regions_fr.topo.json` — target **< 100 KB**.
> 2. Add `frontend/fr_nuclear.html` and render an empty région choropleth via `geo.js`,
>    plus the page shell (nav, honest banner, three panel placeholders). Add D3 here
>    **only if** the Germany slice hasn't already.
> **Domain landmines:** never hand-draw geometry — use the committed TopoJSON. No
> tiles, no external map service. Metropolitan France only (DROM excluded; note it).
> **Output:** `frontend/geo/regions_fr.topo.json`, `frontend/fr_nuclear.html`; a note on
> the basemap file size.
> **Success criteria:** (1) the map of France draws from the committed TopoJSON;
> (2) no real data yet; (3) basemap < 100 KB; (4) opens statically; (5) reuses `geo.js`.

---

## Prompt 2 — French→English translation module

> **Goal:** one isolated place mapping éCO2mix/RTE French field and category names to
> English, so no French leaks into the frontend or the other pipelines.
> **Inputs:** éCO2mix/RTE field names (fuel/technology, région names, consumption and
> *solde*/balance labels).
> **Build:** add `pipeline/fr_fields.py` with explicit dictionaries and small pure
> helpers to translate a record. Dependency-free and pure.
> **Domain landmines:** be exhaustive about the categories used downstream (nuclear,
> hydro, gas, solar, wind, imports; the 13 régions); map unknowns to a labelled "Other".
> **Output:** `pipeline/fr_fields.py` + `pipeline/test_fr_fields.py` (offline).
> **Success criteria:** (1) every category used downstream resolves to English; (2) tests
> pass offline; (3) no other module hardcodes a French string.

---

## Prompt 3 — Nuclear fleet 🧑 (USER verifies)

> **Goal:** the geocoded fleet that feeds Panel 1's site points.
> **Inputs:** ODRÉ/RTE installations registry, or a committed source list of sites.
> **Build:**
> 1. Add `pipeline/build_fr_nuclear_sites.py` (its **own** isolated module): produce per
>    site — name, reactors, capacity (MW), région, river/coast, lat/lon — →
>    `data/fr_nuclear_sites.json` (shape in `../docs/slices/SLICE_FR_NUCLEAR.md` §5); **update
>    `schema.md` in the same change.**
> 2. Unit-test on a small fixture (no network).
> **Domain landmines:** confirm the live reactor count and capacity rather than
> hardcoding — Fessenheim closed (2020), Flamanville-3 commissioning. Carry source
> attribution. Coordinates for the fleet are public.
> **Output:** the module, the JSON, the schema update, the test; a console note of the
> fleet totals.
> **🧑 Then stop and hand to the user** to sanity-check: ~18 sites, ~56 reactors, ~61 GW;
> biggest sites (Gravelines, Paluel, Cattenom) around 5+ GW.
> **Success criteria:** (1) JSON produced and schema-documented; (2) totals plausible;
> (3) tested; (4) user confirms; (5) still static.

---

## Prompt 4 — Panel 1: the fleet map

> **Goal:** France's centralised generation geography vs Germany's distributed one.
> **Inputs:** `fr_nuclear_sites.json`, `regions_fr.topo.json`, `geo.js`, the fuel
> palette; régional consumption (from Step 5's éCO2mix build, or a labelled proxy until
> then).
> **Build:**
> 1. Choropleth of the 13 régions by generation (or nuclear output), with **nuclear
>    sites as points** sized by capacity (canonical `Nuclear` colour), hover = site ·
>    reactors · MW · river/coast.
> 2. Régional **consumption overlay** so producer régions read differently from consumer
>    régions (e.g. Île-de-France). Add copy block A.
> **Domain landmines:** capacity ≠ output. Keep render logic in `geo.js`, data-loading
> separate.
> **Output:** Panel 1 in `frontend/fr_nuclear.html`.
> **Success criteria:** (1) all 13 régions render; (2) sites plot at correct coordinates;
> (3) generation/consumption totals reconcile within ±3% of national éCO2mix; (4) payload
> < 350 KB; (5) copy block A present.

---

## Prompt 5 — Panel 2: who exports, who imports (NEW SOURCE: éCO2mix régional)

> **Goal:** the régional surplus/deficit balance — France's analog of Germany's
> north/south panel.
> **Inputs:** NEW source — RTE éCO2mix régional via ODRÉ (generation-by-type +
> consumption per région); `fr_fields.py`.
> **Build:**
> 1. Add `pipeline/build_fr_regional.py` (**own** module, isolated): fetch per-région
>    generation and consumption, resample to the canonical hourly grid (Europe/Paris),
>    compute **net balance = generation − consumption** (the *solde*) →
>    `data/fr_regional.json` (shape in §5); update schema.
> 2. Render Panel 2: diverging net balance by région (exporters +, importers −) + copy
>    block C.
> **Domain landmines:** French labels (→ `fr_fields`); validate units (GW); group in
> Europe/Paris, DST-safe. France is one bidding zone — **no inter-régional flow line**;
> use the published net balance. Gaps render as "no data".
> **Output:** the module, `data/fr_regional.json`, schema update, Panel 2; a console note
> of unit validation and coverage.
> **Success criteria:** (1) exporter/importer régions directionally correct (Centre-Val
> de Loire / Grand Est / Normandie + ; Île-de-France −); (2) gaps honest; (3) module
> isolated; (4) units stated; (5) still static.

---

## Prompt 6 — Panel 3: availability & fragility

> **Goal:** show nuclear's seasonality and weather dependence, and what fills the gap.
> **Inputs:** RTE éCO2mix (nuclear output) and, where accessible, the RTE unavailability
> feed (OAuth); `fr_fields.py`.
> **Build:**
> 1. Add `pipeline/build_fr_nuclear_availability.py` (**own** module): nuclear available
>    capacity + output over time and the gap-fillers (imports, gas, hydro) →
>    `data/fr_nuclear_availability.json` (shape in §5); update schema.
> 2. Render Panel 3: availability/output over the year with the spring/summer
>    maintenance dip and any heatwave deration, the gap-fillers, the diptych punchline
>    (Germany can't move its wind; France can't always keep its nuclear cool), and copy
>    block B.
> **Domain landmines:** "available capacity" ≠ "output" (block B). Heatwave river-cooling
> limits aren't a clean per-reactor dataset — show the observable dip and annotate; don't
> fabricate. Non-alarmist framing. If RTE OAuth is absent, degrade to éCO2mix output.
> **Output:** the module, `data/fr_nuclear_availability.json`, schema update, Panel 3.
> **Success criteria:** (1) output + available-capacity render; (2) gap-fillers reconcile
> to demand on dip days; (3) maintenance/heatwave periods visible and annotated; (4) copy
> block B present; (5) still static.

---

## Prompt 7 — Panel 4: cost comparison (curated, study-based)

> **Goal:** the "what does the power really cost?" section — a symmetric, sourced cost
> stack with a sticker-price ↔ full-system-cost toggle.
> **Inputs:** published estimates — Lazard LCOE+ 2024, Cour des comptes (EPR/EPR2),
> ANDRA / Cigéo, OECD-NEA system costs, IRENA. No live feed.
> **Build:**
> 1. `pipeline/build_fr_costs.py` transcribes per-technology figures (utility solar,
>    onshore wind, existing FR fleet, new-build EPR2) into components — plant, back-end
>    (waste + decommissioning), system & integration, implicit support — each with a
>    **range and a source** → `data/fr_costs.json` (shape in §5); update `schema.md`.
> 2. Render Panel 4: a stacked €/MWh bar per technology with a **toggle** — "sticker
>    price" shows plant only; "full system cost" stacks all adders on every technology —
>    a takeaway that updates with the toggle, visible citations, and copy block E.
> **Domain landmines:** symmetric or it's advocacy — the hidden-cost lens applies to all
> technologies, never nuclear alone. Nuclear back-end is large in total but small per MWh
> and is *provisioned* (critique adequacy, don't say "ignored"). Renewables' system costs
> rise with share. Show ranges; note source lean (Lazard = US new-build; NEA = Nuclear
> Energy Agency). Curated estimates — never present as "the truth".
> **Output:** `pipeline/build_fr_costs.py`, `data/fr_costs.json`, schema update, Panel 4.
> **Success criteria:** (1) toggle switches plant-only ↔ full stack for all techs and the
> takeaway updates; (2) every figure shows a source + range; (3) existing vs new nuclear
> distinct; (4) framing symmetric/non-advocacy; (5) stays static (curated JSON).

---

## Prompt 8 — Integrate, polish, lock in

> **Goal:** make the slice production-clean and keep it fresh automatically.
> **Inputs:** the three panels; `.github/workflows/refresh-data.yml`; the test suite.
> **Build:**
> 1. Final pass: round every number, units labelled, **no French labels** in the UI, all
>    copy-block caveats present; optional dashboard panel/link (keep the standalone page).
> 2. Add `build_fr_nuclear_sites.py`, `build_fr_regional.py`,
>    `build_fr_nuclear_availability.py` to the daily refresh action; each degrades (log +
>    continue) if its source is unavailable.
> 3. Confirm offline tests pass and the page opens statically with no network calls.
> **Domain landmines:** stay static; don't let a missing RTE/éCO2mix run crash the action.
> **Output:** updated workflow, polished `frontend/fr_nuclear.html`, green tests.
> **Success criteria:** the definition of done in `../docs/slices/SLICE_FR_NUCLEAR.md` §11 is met —
> three panels render from committed JSON, English-only, rounded, caveated, static, tests
> passing, refresh wired.
