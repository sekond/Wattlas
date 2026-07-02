# RUN_V7.md — Execution protocol for the Dunkelflaute slice

Same rules as `RUN.md` / `RUN_V2`–`V6`: **you never copy-paste prompts.** Claude Code
reads them from `prompts/v7_prompts.md` and works through `SLICE_DUNKELFLAUTE.md` in
order. Approve each step; verify before the next. **Stays static**, reuses the ENTSO-E
pipeline; no new external source (weather is optional context).

## How to start

> **Follow RUN_V7.md.**

## Protocol

One step per turn: state → wait for approval → execute the step's prompt from
`prompts/v7_prompts.md` → regenerate JSON + run tests → report → wait.

**Verification checkpoint (🧑):** at **Step 1**, the user sanity-checks the detected worst
spell — a known cold, still winter period, renewables near-zero, price elevated.

**Guardrail:** static; reuse Chart.js + the fuel palette; the low-renewable threshold is a
**stated, adjustable choice**, not a law. Non-ideological framing (engineering reality).

## The steps (detail in `prompts/v7_prompts.md`; rationale in `SLICE_DUNKELFLAUTE.md`)

### Step 0 — Pre-flight
Execute **Prompt 0**: read `CLAUDE.md`, `SLICE_DUNKELFLAUTE.md`, `SOURCES.md`, `schema.md`;
<200-word summary. **Gate:** names the landmine — the renewable-share threshold is a
defined choice, and net imports matter most during these hours.

### Step 1 — Detect spells 🧑
Execute **Prompt 1**: `build_dunkelflaute.py` detects low-renewable spells and extracts the
worst event's hourly series + a frequency/duration summary → `data/dunkelflaute.json`;
schema; tests. **🧑 USER sanity-checks** the detected event.
**Gate:** user confirms the spell is plausible.

### Step 2 — Panel 1 (anatomy of a Dunkelflaute)
Execute **Prompt 2**: `dunkelflaute.html` shell + the event timeline (wind/solar collapse,
backup surge, price spike on one axis).
**Gate:** renewable collapse + backup + price render aligned.

### Step 3 — Panel 2 (how often, how long, how deep)
Execute **Prompt 3**: frequency/duration of low-renewable spells; worst runs.
**Gate:** counts/durations render; threshold stated.

### Step 4 — Panel 3 (what fills the gap)
Execute **Prompt 4**: the backup stack during Dunkelflaute hours + copy block A.
**Gate:** gap-filler mix renders; non-ideological framing.

### Step 5 — Integrate, polish, lock in
Execute **Prompt 5**: rounding / caveat pass; optional dashboard callout; add the builder
to `refresh-data.yml`; offline tests; static.
**Gate:** definition of done in `SLICE_DUNKELFLAUTE.md` §11 met.
