# v7 prompts — the Dunkelflaute slice

Execute via `RUN_V7.md`, one step at a time. Full detail in `SLICE_DUNKELFLAUTE.md`;
`CLAUDE.md` loaded automatically. Stay static; reuse the ENTSO-E pipeline, Chart.js and
the fuel palette; round every number.

---

## Prompt 0 — Pre-flight
> **Goal:** load the slice into memory. **Inputs:** `CLAUDE.md`, `SLICE_DUNKELFLAUTE.md`,
> `SOURCES.md`, `schema.md`. **Build:** <200-word summary; change nothing.
> **Success:** names the landmine — the renewable-share threshold is a defined, adjustable
> choice; net imports matter most during these hours.

## Prompt 1 — Detect spells 🧑 (USER verifies)
> **Goal:** find and extract Dunkelflaute events from data already pulled.
> **Inputs:** ENTSO-E generation-by-type, day-ahead price, load (DE-LU).
> **Build:** `pipeline/build_dunkelflaute.py` — compute hourly renewables share of demand;
> flag spells where it stays below a stated threshold (e.g. 10%) for ≥ N hours; extract the
> worst event's hourly series (wind, solar, gas, nuclear, hydro, net imports, price) and a
> frequency/duration summary → `data/dunkelflaute.json` (shape in §5); update `schema.md`;
> unit-test the detector on a fixture.
> **Landmines:** threshold is a choice — state it; generation has gaps/"other"; include net
> imports; tz-aware/DST-safe.
> **Output:** module, JSON, schema, test; console note of spell count + worst event.
> **🧑 Then hand to the user** to confirm a plausible winter spell (renewables near-zero,
> price elevated). **Success:** JSON + schema; plausible; tested; user confirms; static.

## Prompt 2 — Panel 1: anatomy of a Dunkelflaute
> **Goal:** the event timeline. **Inputs:** `dunkelflaute.json`.
> **Build:** `frontend/dunkelflaute.html` + a chart of the worst event — wind/solar
> collapsing, gas/nuclear/hydro/imports filling, price spiking, on an aligned timeline.
> **Success:** the collapse + backup + price spike read at a glance; gaps honest; static.

## Prompt 3 — Panel 2: how often, how long, how deep
> **Goal:** the frequency/duration view. **Build:** count of low-renewable hours and the
> worst runs over the window; threshold stated. **Success:** clear counts/durations; static.

## Prompt 4 — Panel 3: what fills the gap
> **Goal:** the backup stack + the honest takeaway. **Build:** the gap-filler mix during
> Dunkelflaute hours (gas, imports, nuclear, hydro); copy block A (engineering reality, not
> anti-renewable). **Success:** mix renders; non-ideological; copy block A present.

## Prompt 5 — Integrate, polish, lock in
> **Build:** rounding / caveat pass; optional dashboard callout; add `build_dunkelflaute.py`
> to `refresh-data.yml` (degrade gracefully); offline tests; static. **Success:** §11 done.
