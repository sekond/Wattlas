# RUN_V9.md — Execution protocol for the Storage slice

Same rules as `RUN.md` / `RUN_V2`–`V8`: **you never copy-paste prompts.** Claude Code
reads them from `prompts/v9_prompts.md` and works through `SLICE_STORAGE.md` in order.
Approve each step; verify before the next. **Stays static**; reuses the ENTSO-E pipeline,
`data/spread.json`, and (for capacity) MaStR.

## How to start

> **Follow RUN_V9.md.**

## Protocol

One step per turn: state → wait for approval → execute the step's prompt → regenerate
JSON + run tests → report → wait.

**Verification checkpoint (🧑):** at **Step 1**, the user sanity-checks the battery day —
charge in the cheap midday hours, discharge in the evening peak, plausible captured spread.

**Guardrail:** static; the arbitrage figure is an explicit **upper bound** (perfect
foresight, stated efficiency) — same discipline as the Spread view; state MW vs MWh.

## The steps (detail in `prompts/v9_prompts.md`; rationale in `SLICE_STORAGE.md`)

### Step 0 — Pre-flight
Execute **Prompt 0**: read `CLAUDE.md`, `SLICE_STORAGE.md`, `SOURCES.md`, `schema.md`;
<200-word summary. **Gate:** names the landmines — arbitrage is an upper bound;
MW (power) vs MWh (energy); more storage flattens the spread (cannibalisation).

### Step 1 — Battery model + capacity 🧑
Execute **Prompt 1**: `build_storage.py` runs a transparent battery-arbitrage model over
real day-ahead prices and assembles a storage-capacity series → `data/storage.json`;
schema; tests. **🧑 USER sanity-checks** the battery day.
**Gate:** charge/discharge align with price; capture plausible; user confirms.

### Step 2 — Panel 1 (a day in the life of a battery)
Execute **Prompt 2**: `storage.html` shell + the price curve with charge/discharge + copy
block A (upper-bound caveat).
**Gate:** buy-low/sell-high reads at a glance; assumptions + upper-bound stated.

### Step 3 — Panel 2 (where storage is being built)
Execute **Prompt 3**: installed capacity + growth (by country; DE by region from MaStR).
**Gate:** capacity + growth render; MW/MWh stated; gaps honest.

### Step 4 — Panel 3 (storage vs the spread)
Execute **Prompt 4**: tie to `spread.json` — widening spread improves the case; the honest
limits (losses, cycling, cannibalisation).
**Gate:** ties to spread; caveats explicit.

### Step 5 — Integrate, polish, lock in
Execute **Prompt 5**: rounding / caveat pass; optional dashboard callout; add the builder
to `refresh-data.yml`; offline tests; static.
**Gate:** definition of done in `SLICE_STORAGE.md` §11 met.
