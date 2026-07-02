# v8 prompts — the Iberian blackout slice

Execute via `RUN_V8.md`, one step at a time. Full detail in `SLICE_IBERIAN_BLACKOUT.md`;
`CLAUDE.md` loaded automatically. Stay static; sober tone; **never assert a cause** — cite
the official investigation. Round every number.

---

## Prompt 0 — Pre-flight
> **Goal:** load the slice into memory. **Inputs:** `CLAUDE.md`,
> `SLICE_IBERIAN_BLACKOUT.md`, `SOURCES.md`, `schema.md`. **Build:** <200-word summary.
> **Success:** names the landmines — never assert a cause (cite the official report); sober
> tone; figures around the outage are provisional/revised.

## Prompt 1 — Assemble the window 🧑 (USER verifies)
> **Goal:** the dated collapse + restoration series. **Inputs:** ENTSO-E load/generation for
> ES & PT around 28 Apr 2025; REE/REN + the official report for milestones.
> **Build:** `pipeline/build_iberian_blackout.py` — pull the fixed historical window,
> assemble the timeline + restoration milestones → `data/iberian_blackout.json` (shape in
> §5); update `schema.md`; test on a fixture. **Landmines:** provisional/revised figures
> (label); UTC + local timestamps; gaps honest; no inferred cause.
> **Output:** module, JSON, schema, test; console note of the window + sources.
> **🧑 Then hand to the user** to check against the public record + official report.
> **Success:** timeline matches the record; sourced; tested; user confirms; static.

## Prompt 2 — Panel 1: the collapse, hour by hour
> **Goal:** the collapse timeline. **Build:** `frontend/iberian_blackout.html` + a dated,
> sourced chart of ES/PT load/generation through the morning, collapse and trough; copy
> block A (frames the page, assigns no cause). **Success:** collapse renders as recorded;
> sober; no inferred cause.

## Prompt 3 — Panel 2: the restoration
> **Goal:** the recovery. **Build:** the staged restoration curve + sourced milestones
> (hydro black-start, interconnection with France/Morocco). **Success:** recovery renders;
> milestones sourced; no overclaiming.

## Prompt 4 — Panel 3: what it raised
> **Goal:** the stability question, carefully. **Build:** the inertia/stability questions
> investigators examined; copy block B; link the official report. **Landmines:** evenhanded;
> no single-technology blame; cause sourced, not asserted. **Success:** balanced; sourced.

## Prompt 5 — Integrate, polish, lock in
> **Build:** rounding / caveat pass; sober styling; offline tests; static (no daily
> refresh — historical). **Success:** §11 done.
