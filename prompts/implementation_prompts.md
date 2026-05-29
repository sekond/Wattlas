# Implementation prompts for Claude Code

Hand these to Claude Code **in order**, one at a time. Each follows the repo's
Prompt Engineering Rules: explicit goal, inputs, output format, success criteria.
`CLAUDE.md` is loaded automatically and contains the domain landmines — the
prompts deliberately don't repeat them, so trust that file.

Most files in this repo are already scaffolded and working against synthetic
sample data. These prompts take it from "works on sample data" to "works on real
ENTSO-E data, tested, and polished."

---

## Prompt 0 — Orient (run first, no code)

> Read `CLAUDE.md` and `data/schema.md` in full, then read every file under
> `pipeline/` and `frontend/`. Summarise, in under 200 words: (1) what the v1
> scope is, (2) the data flow from ENTSO-E to the rendered chart, (3) the four
> data landmines you must respect, and (4) anything in the current code that
> looks inconsistent with `CLAUDE.md`. Do not change any files yet.

**Success:** an accurate summary that names the resolution break, DST handling,
EIC/bidding-zone rule, and the arbitrage upper-bound rule.

---

## Prompt 1 — Connect real data and run the pipeline end to end

> Goal: replace synthetic sample data with real ENTSO-E data.
> Inputs: a valid `ENTSOE_API_TOKEN` in `.env`; the existing
> `pipeline/build_spread.py` and `pipeline/metrics.py`.
> Steps: (1) install `requirements.txt`; (2) confirm `fetch_prices` works for a
> 7-day window before fetching the full year (fail fast on auth/zone errors);
> (3) run `python pipeline/build_spread.py` for the last 12 months; (4) sanity-
> check the output against `data/schema.md`.
> Output format: the regenerated `data/spread.json` and
> `data/spread_summary.json`, plus a short console summary (days written,
> missing days, widest day, total negative hours).
> Success criteria: both JSON files validate against the schema; the run does
> not crash on missing days or the Oct-2025 resolution change; numbers are
> plausible for Germany (expect avg daily TB1 in the tens-to-low-hundreds of
> €/MWh and a few hundred negative hours over the year).

---

## Prompt 2 — Harden the pipeline

> Goal: make the pipeline robust and observable.
> Inputs: the working pipeline from Prompt 1.
> Tasks: (1) add basic logging (start, fetch window, rows fetched, resampling
> applied, days written, missing days) instead of bare prints; (2) cache the raw
> fetched price series to `data/_raw_prices.parquet` and add a `--use-cache` flag
> so re-runs don't re-hit the API; (3) when a day is incomplete, keep it in
> `spread.json` with `complete: false` rather than dropping it.
> Output format: updated `pipeline/build_spread.py`; a one-paragraph note in
> `README.md` describing the cache flag.
> Success criteria: `python pipeline/build_spread.py --use-cache` runs with no
> network; existing unit tests still pass (`python pipeline/test_metrics.py`).

---

## Prompt 3 — Frontend polish

> Goal: tighten the Spread view without changing its scope.
> Inputs: `frontend/index.html`, the real `data/*.json`.
> Tasks: (1) add an annotation on the main chart marking the single widest day
> with a short label (date + TB1), since an annotated chart is the credibility
> differentiator; (2) add a one-line legend (blue = normal day, red = had
> negative-price hours); (3) ensure the page degrades gracefully if a JSON file
> is missing (show the existing status message, never a blank page);
> (4) verify on a 360px-wide mobile viewport that nothing overflows.
> Output format: updated `frontend/index.html`.
> Success criteria: opening the page (served statically from the repo root)
> shows KPIs, an annotated bar chart, the monthly negative-hours chart, and the
> arbitrage figure with its upper-bound caveat visible; all numbers rounded.

---

## Prompt 4 — Tests and a smoke check

> Goal: lock in correctness.
> Inputs: `pipeline/metrics.py`, `pipeline/test_metrics.py`.
> Tasks: (1) add tests for: a spring DST day (23 hours), a day with a data gap
> (e.g. 20 hours, `complete=false`), and TB2 falling back to TB1 when a day has
> fewer than 4 hours; (2) add a tiny `pipeline/test_build.py` that injects a
> fixture price Series into `build()` (no network) and asserts both JSON files
> are written with schema-correct keys.
> Output format: updated/added test files.
> Success criteria: `python pipeline/test_metrics.py` and
> `python pipeline/test_build.py` both pass offline.

---

## Prompt 5 — Stop here and review (no code)

> Do not start a second view. Review the v1 against the "Success Criteria for
> v1" in `CLAUDE.md` and list, as a checklist, which criteria are met and which
> are not. For any unmet criterion, propose the smallest change that would meet
> it. Then list the three most likely reasons a domain expert would distrust the
> current numbers, and what we'd need to fix each.

**Why stop:** the next views (Pulse, Divergence, Mismatch) reuse this exact
pattern. Prove this one is trustworthy before multiplying it.
