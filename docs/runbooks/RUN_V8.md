# RUN_V8.md — Execution protocol for the Iberian blackout slice

Same rules as `RUN.md` / `RUN_V2`–`V7`: **you never copy-paste prompts.** Claude Code
reads them from `prompts/v8_prompts.md` and works through `SLICE_IBERIAN_BLACKOUT.md` in
order. Approve each step; verify before the next. **Stays static** (a fixed historical
window, no daily refresh).

**Sensitivity:** a real event that affected millions. Sober, factual tone; **never assert
a single cause** — cite the official investigation; show what the data shows.

## How to start

> **Follow RUN_V8.md.**

## Protocol

One step per turn: state → wait for approval → execute the step's prompt → regenerate
JSON + run tests → report → wait.

**Verification checkpoint (🧑):** at **Step 1**, the user checks the assembled timeline
against the public record and the official report.

**Guardrail:** static; sober styling; cause attribution sourced to the official report,
not asserted; figures around the outage are provisional/revised — label them.

## The steps (detail in `prompts/v8_prompts.md`; rationale in `SLICE_IBERIAN_BLACKOUT.md`)

### Step 0 — Pre-flight
Execute **Prompt 0**: read `CLAUDE.md`, `SLICE_IBERIAN_BLACKOUT.md`, `SOURCES.md`, `schema.md`;
<200-word summary. **Gate:** names the landmines — never assert a cause (cite the official
report); keep tone sober; figures are provisional.

### Step 1 — Assemble the window 🧑
Execute **Prompt 1**: `build_iberian_blackout.py` pulls the fixed ES/PT window around
28 Apr 2025 (collapse + restoration) → `data/iberian_blackout.json`; schema; tests.
**🧑 USER checks** against the public record + official report.
**Gate:** the timeline matches the record; sources cited.

### Step 2 — Panel 1 (the collapse, hour by hour)
Execute **Prompt 2**: `iberian_blackout.html` shell + the dated, sourced collapse timeline
+ copy block A.
**Gate:** collapse renders as the data records it; no inferred cause.

### Step 3 — Panel 2 (the restoration)
Execute **Prompt 3**: the staged recovery + sourced milestones (hydro black-start,
interconnection).
**Gate:** recovery renders; milestones sourced; no overclaiming.

### Step 4 — Panel 3 (what it raised)
Execute **Prompt 4**: the stability/inertia questions investigators examined + copy block
B; link the official report.
**Gate:** evenhanded; no single-technology blame; cause sourced, not asserted.

### Step 5 — Integrate, polish, lock in
Execute **Prompt 5**: rounding / caveat pass; sober styling; offline tests; static. (No
daily refresh — historical.)
**Gate:** definition of done in `SLICE_IBERIAN_BLACKOUT.md` §11 met.
