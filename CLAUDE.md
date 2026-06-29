# Wattlas — Claude Code Instructions

This file is automatically loaded by Claude Code at the start of every session. It defines how Claude Code should operate within this repository.

## How to start (read this first)

This project is built **step by step** via a runbook, `RUN.md`. When the user
says "Follow RUN.md" (or asks you to build/set up/implement Wattlas), open
`RUN.md` and run its protocol: work through the steps **in order, one per turn**.

For each step: state what it will do, **wait for the user's explicit approval**,
then perform it by reading and executing the relevant prompt from
`prompts/implementation_prompts.md` **yourself** — never ask the user to paste a
prompt. Report the result, then wait for approval again before the next step.

Two steps belong to the user (adding the ENTSO-E token; sanity-checking the first
real-data numbers) — pause and hand control over at those; do not attempt them.
Never advance past a failed or wrong-looking result; stop and propose a fix.

Run `bootstrap.py` first to verify the project is correctly assembled.

**For the v2 expansion** (more data sources + a consolidated dashboard): the plan
is in `docs/roadmaps/ROADMAP_V2.md`, driven by `docs/runbooks/RUN_V2.md`, with prompts in
`prompts/v2_prompts.md`. When the user says "Follow RUN_V2.md", run those phases
one at a time with the same confirmation-gated protocol. Read the v2 landmines
below before starting any v2 phase.

**For the v10 "Value Layer" expansion** (price-formation and value layer: capture
price, negative-prices, flexibility, storage cannibalization, curtailment-in-€,
locational signal, retail wedge, capacity adequacy, marginal-fuel, industrial
proxy): the vetted plan is in `docs/roadmaps/ROADMAP_V10.md`, driven by `docs/runbooks/RUN_V10.md`, with
prompts in `prompts/v10_prompts.md`. When the user says "Follow RUN_V10.md", run
the slices one at a time with the same confirmation-gated protocol. Honour the two
acceptance gates (capture-price canonical-hourly weighting; the locational view's
no-simulated-price rule) and the three VERIFY-FIRST source checks before building.
(Note: `v3`–`v9` belong to earlier single slices — wasted-wind, France nuclear,
Nordic, UK, Dunkelflaute, Iberian, Storage — and are unrelated to v10.)

## Project Overview

Wattlas is a web application that explores the temporal and financial dimensions of European electricity markets, with a focus on the renewable-energy transition. It pulls open data from the ENTSO-E Transparency Platform, computes market metrics in a Python/pandas pipeline, writes small pre-aggregated JSON files, and renders them in a static JavaScript frontend.

This first version implements a single view — **The Spread** — which answers one question: *how wide is the gap each day between the cheapest and most expensive hour of electricity, and how often do prices go negative?* The architecture must support adding three further views later (Pulse, Divergence, Mismatch) without restructuring, but those are explicitly out of scope for v1.

The audience is intentionally undecided; this is a learning project that will surface a target audience through exploration. Do not optimise for a specific persona yet.

## Architecture (do not deviate without flagging)

- **Pipeline (`/pipeline`, Python/pandas):** fetches from ENTSO-E, computes metrics, writes JSON to `/data`. This is the only code that touches the ENTSO-E API. The frontend never calls ENTSO-E directly.
- **Data (`/data`):** small pre-aggregated JSON artefacts, committed to the repo so the frontend works without re-running the pipeline.
- **Frontend (`/frontend`, static JS):** reads the JSON files and renders charts. No backend, no database, no server-side rendering. Must run by opening a single HTML file or serving the folder statically.
- **No browser storage:** never use `localStorage` or `sessionStorage`. Hold state in JS variables only.

Rationale: a static, pre-computed app cannot drown in DevOps and cannot break from a live API outage. Preserve this property. If a future task seems to require a live backend, stop and flag the scope change rather than silently adding one.

## Domain knowledge and data landmines (critical — read before writing pipeline code)

These are non-obvious facts about the data. Getting them wrong produces code that looks correct but is silently wrong.

1. **Use the `entsoe-py` client, not raw HTTP.** `EntsoePandasClient` returns timezone-aware pandas objects. Day-ahead prices come from `query_day_ahead_prices(country_code, start, end)`.

2. **EIC codes / bidding zones are not countries.** Germany is the combined **DE-LU** zone (`DE_LU` in `entsoe-py`), shared with Luxembourg. Never assume "Germany == DE". For v1 use `DE_LU` only.

3. **Resolution break in October 2025 (this WILL look like a bug).** The German day-ahead market moved from **hourly to quarter-hourly** settlement in October 2025. A multi-month price series therefore changes resolution partway through. The pipeline must detect the native resolution and **resample everything to a single canonical resolution (hourly)** before computing daily metrics — average the sub-hourly values within each hour. Document this resampling choice in code comments.

4. **Timezones and DST.** Everything is UTC underneath; Germany trades in CET/CEST. Twice a year a day has 23 or 25 hours. Never assume "24 values per day". Group by calendar day in the **local (Europe/Berlin)** timezone, and let the count of hours per day vary. Keep timestamps tz-aware end to end; do not strip tzinfo.

5. **TB1 / TB2 are the core metrics.** TB1 = (max hourly price − min hourly price) within a calendar day. TB2 = (mean of the 2 most expensive hours − mean of the 2 cheapest hours) within a day. Compute per local calendar day.

6. **Negative prices are real, not errors.** Prices can be strongly negative (down to roughly −€300/MWh in extreme German solar peaks). Do not clip, floor, or treat negatives as missing. Count, per day, how many hours had a price < 0.

7. **The "perfect-arbitrage revenue" number is an UPPER BOUND, and must always be labelled as such** in both code comments and any text the frontend displays. It assumes perfect foresight, zero round-trip losses, and no price impact, so it materially overstates real battery revenue. Never present it as achievable revenue. This hedge is a credibility requirement, not a nicety.

8. **Missing data happens.** ENTSO-E has gaps. The pipeline must not crash on a missing day; it should record which days are missing and continue. The frontend must render gracefully when a day is absent.

## v2 expansion landmines (read before the v2 phases — see docs/roadmaps/ROADMAP_V2.md)

9. **Generation-by-type is messier than prices.** More categories, more gaps,
   underreported buckets, and an "other/unknown" category. Never fabricate a
   clean stacked area from incomplete data — show gaps honestly. Keep a single
   canonical fuel-colour palette defined in ONE place and reused across every
   view (a fuel is always the same colour everywhere).

10. **Flows are directional and capacity is per-direction.** DE→FR is not FR→DE;
    store and display direction explicitly. Net transfer capacity may be reported
    per direction and is often missing for some borders/periods — that's normal,
    render "no data", never error. "Congested" means physical flow is at/near
    available capacity in that direction.

11. **New external sources are isolated by default.** SMARD (Phase 4) and the
    carbon feed (Phase 5) each get their OWN pipeline module, separate from the
    ENTSO-E pipeline. Do not entangle them — different auth, units, languages
    (SMARD uses German field names), resolutions, and lag. A failure in one
    source must not break the others.

12. **Validate units and methodology on every new source, in writing.** State the
    units in code comments and in the UI (MWh vs GWh; gCO2/kWh). For carbon
    intensity, state whether it's production-based or consumption-based and don't
    mix methodologies across zones. Never assume a new source's timestamps align
    1:1 with ENTSO-E — reconcile explicitly and document the join.

13. **Stay static across all v2 phases.** Pre-compute everything (including new
    sources and longer history) into JSON at build time; the frontend slices
    client-side. No backend, no database. If a phase appears to need a live
    backend, STOP and flag it as a deliberate decision — do not drift across that
    line. The honest ceiling is "any metric/zone/window live on demand"; stay
    below it until real usage forces otherwise.

14. **Longer history (Phase 6) spans more DST transitions and crosses the
    Oct-2025 resolution break.** Keep the resampling discipline from landmines
    3–4 over the full range. If a JSON file grows large, split by year and load
    on demand — still static.

## Tone and Communication

- Use professional but conversational language
- Avoid unnecessary jargon
- Prioritize clarity and conciseness in every response
- Structure outputs with clear sections and numbered steps when applicable
- Keep explanations direct without unnecessary elaboration

## Prompt Engineering Rules

- Clarity and conciseness are paramount
- Structured outputs required for all tasks
- Each task must specify expected output format and success criteria

## Coding Conventions

- **Python:** target 3.10+. Use type hints on function signatures. Keep functions small and single-purpose. Prefer pure functions for all metric computation (input DataFrame → output DataFrame/dict) so they are unit-testable without network access. Use `pathlib` for file paths. No global state.
- **Data contract:** the pipeline and frontend agree on the JSON shape via `/data/schema.md`. If you change the shape of any JSON output, update `schema.md` in the same change.
- **Frontend:** vanilla JS modules or a single high-level chart library loaded from CDN. No build step for v1. No framework. Keep all DOM/render logic separate from data-loading logic.
- **Numbers on screen:** round every displayed number (`Math.round`, `toFixed`, or `Intl.NumberFormat`). Never show raw floats.
- **Comments:** comment the *why*, especially around any of the data landmines above. Do not comment the obvious.

## Workflow Expectations

1. Before implementing, restate the task as: goal, inputs, expected output format, success criteria. (This satisfies the Prompt Engineering Rules above.)
2. Work in the smallest shippable increment. Prefer one working vertical slice over broad scaffolding.
3. After writing pipeline code that computes a metric, write or update a unit test that runs on a small inline fixture (no network).
4. Never commit secrets. The ENTSO-E API token lives in `.env` (gitignored); read it via environment variable `ENTSOE_API_TOKEN`.
5. When a task is ambiguous, ask one focused question rather than guessing — but first check whether `CLAUDE.md`, `schema.md`, or the prompt files in `/prompts` already answer it.

## Success Criteria for v1 (definition of done)

- `python pipeline/build_spread.py` fetches ~12 months of DE-LU day-ahead prices, computes daily TB1, TB2, and negative-hour counts, and writes `data/spread.json` + `data/spread_summary.json`.
- The pipeline handles the Oct-2025 resolution break, DST days, and missing days without crashing.
- Opening `frontend/index.html` (served statically) renders the Spread view: KPI cards, the daily-spread bar chart with negative-price days highlighted, and the clearly-labelled upper-bound arbitrage figure.
- All displayed numbers are rounded; the arbitrage number carries its "upper bound" caveat in the UI.
- Metric functions have unit tests that pass offline.
