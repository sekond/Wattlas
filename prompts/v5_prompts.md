# v5 prompts — the Nordic price-zones slice

Detailed prompts for each step of the Nordic slice. Execute via `RUN_V5.md`, one step at
a time, with confirmation between steps. Full rationale, panels, JSON shapes, acceptance
criteria, and copy blocks live in `SLICE_NORDIC_ZONES.md` — trust it. `CLAUDE.md` is loaded
automatically.

Prime directive: **stay static** (pre-computed JSON + committed TopoJSON, no backend, no
tiles). Reuse `frontend/geo.js` + D3 and the existing ENTSO-E client. Round every number.

---

## Prompt 0 — Pre-flight + orientation

> **Goal:** load the slice into memory before touching code.
> **Inputs:** `CLAUDE.md`, `SLICE_NORDIC_ZONES.md`, `SOURCES.md`, `data/schema.md`.
> **Build:** read them; produce a <200-word summary of the one question, three panels,
> datasets, and the new module. Change nothing.
> **Success criteria:** names the two landmines — (1) Nordic price zones aren't admin
> regions, so boundary geometry is approximate/schematic; (2) Nordic prices are
> hydro/reservoir-driven, so divergence isn't purely congestion.

---

## Prompt 1 — Zone map shell

> **Goal:** stand up the Nordic zone map with no data, reusing the static rendering path.
> **Inputs:** a Nordic price-zone boundary source (custom — county groupings) or a
> schematic layout; `frontend/geo.js` + D3.
> **Build:** commit `frontend/geo/nordic_zones.topo.json` (or a schematic zone layout);
> add `frontend/nordic_zones.html`; render an empty zone map via `geo.js` plus the page
> shell (nav, honest banner, three panel placeholders). Add D3 only if not already present.
> **Domain landmines:** zones are not administrative units — never imply a precise map;
> label schematic/approximate. No tiles.
> **Output:** the boundary/schematic asset, `nordic_zones.html`; a note on file size.
> **Success criteria:** zones render from the committed asset; no data yet; opens static;
> reuses `geo.js`.

---

## Prompt 2 — Zone prices (ENTSO-E) 🧑 (USER verifies)

> **Goal:** the per-zone price data that feeds Panels 1–2.
> **Inputs:** ENTSO-E day-ahead prices via the existing `entsoe-py` client, for SE1–4,
> NO1–5, DK1–2, FI.
> **Build:** add `pipeline/build_nordic_zones.py` (its **own** builder, not entangled with
> `build_spread.py`): fetch day-ahead prices per zone, compute averages + monthly series +
> within-country gaps → `data/nordic_prices.json` (shape in §5); update `schema.md`; unit-
> test the aggregation on a fixture.
> **Domain landmines:** correct EIC zone codes; tz-aware (local), DST-safe; gaps render
> honestly; prices are hydro-driven (note in output).
> **Output:** the module, the JSON, schema update, test; a console note of per-zone averages.
> **🧑 Then hand to the user** to sanity-check: north cheaper than south, plausible €/MWh,
> winter within-country gaps.
> **Success criteria:** JSON produced + schema-documented; prices plausible; tested; user
> confirms; static.

---

## Prompt 3 — Panel 1: the map of zones

> **Goal:** the price-shaded zone map.
> **Inputs:** `nordic_prices.json`, the zone asset, `geo.js`.
> **Build:** shade each zone by average price (sequential scale); legend in €/MWh; "no
> data" distinct; the schematic caveat.
> **Success criteria:** all zones shade by price; north-cheap/south-dear gradient visible;
> caveat present; payload within budget.

---

## Prompt 4 — Panel 2: how far prices diverge

> **Goal:** show within-country price decoupling over time.
> **Inputs:** `nordic_prices.json` (per-zone monthly series).
> **Build:** plot a country's far-north vs far-south zone over time (e.g. SE1 vs SE4; NO4
> vs NO2), with the gap visible; note other countries show the same.
> **Domain landmines:** tz-aware/DST-safe; gaps honest; hydro-driven context.
> **Success criteria:** divergence renders; winter decoupling visible; gaps honest; static.

---

## Prompt 5 — Panel 3: the lesson for Germany

> **Goal:** tie the Nordic split to Germany's single-zone debate.
> **Inputs:** the DE north–south slice (`wasted_wind.html`) for the link/compare.
> **Build:** the structural hydro-north/demand-south split vs Germany's one-price-plus-
> curtailment; copy blocks A (zonal-pricing trade-off, evenhanded) and B (what a zone is);
> explicit link to the DE slice.
> **Domain landmines:** evenhanded — show trade-offs both ways; no advocacy.
> **Success criteria:** DE link explicit; copy blocks A/B present; non-advocacy; static.

---

## Prompt 6 — Integrate, polish, lock in

> **Goal:** production-clean and auto-refreshed.
> **Inputs:** the three panels; `refresh-data.yml`; tests.
> **Build:** rounding / English-only / caveat pass; optional dashboard "Deep dives"
> callout + nav link; add `build_nordic_zones.py` to the daily refresh (degrade if the
> source is unavailable); confirm offline tests and static open.
> **Success criteria:** definition of done in `SLICE_NORDIC_ZONES.md` §11 met.
