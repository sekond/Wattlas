# RUN_V10.md — Review & Plan: the "Value Layer" expansion

This is a Claude Code runbook. It governs how you (Claude Code) turn the
consolidated podcast-synthesis conclusions into a vetted, sequenced
implementation plan for Wattlas. **Read this whole file before doing anything.**

> Namespace note: this is the **v10** expansion. The `v2`–`v9` band is already
> taken — `RUN_V2.md` (the dashboard expansion), `RUN_V3.md` (wasted-wind / DE
> north–south), `RUN_V4.md` (France nuclear), and the `v5`–`v9` slice runbooks
> (Nordic, UK regional, Dunkelflaute, Iberian blackout, Storage). Leave all of
> them untouched. The Value-Layer plan lives in `../roadmaps/ROADMAP_V10.md` +
> `../../prompts/v10_prompts.md`.

Companion input: `../roadmaps/wattlas-consolidated-roadmap.md` (the conclusions to review).
Sibling runbooks you must stay consistent with: `../../RUN.md`, `RUN_V2.md`,
`../roadmaps/ROADMAP_V2.md`. Domain rules live in `../../CLAUDE.md` — they override anything here
if they conflict.

---

## What this runbook is for

The roadmap was written from *outside* the codebase — from podcast and expert
discourse. Your job is **not** to implement it. Your job is to:

1. **Review** each proposed view critically against what the repo can actually
   support (data, schema, architecture, the static-site constraint), and
2. **Produce** a concrete, sequenced implementation plan (`../roadmaps/ROADMAP_V10.md` +
   `../../prompts/v10_prompts.md`) that a later build pass can execute one slice at a time.

You are acting as a critical reviewer first, planner second, builder **not at
all** in this runbook. Do not write pipeline or frontend code here. The output
of this runbook is *documents*, not features.

---

## Operating protocol (same discipline as ../../RUN.md / RUN_V2.md)

- **One step per turn.** State what the step will do, then **wait for the
  user's explicit approval** before doing it. Report the result, then wait again.
- **Never advance past a wrong-looking result.** Stop and propose a fix.
- **Do not invent data.** If a proposed view needs data the pipeline does not
  fetch and cannot fetch from ENTSO-E / netztransparenz, say so plainly and mark
  the view **blocked** or **context-only** — never scaffold a fake.
- **Stay static.** If any proposed view seems to need a live backend, database,
  or server-side compute, STOP and flag it as a deliberate scope decision (per
  ../../CLAUDE.md landmine 13). The default answer is "pre-compute to JSON at build
  time; the frontend slices client-side."
- **Honesty caveats are requirements, not nice-to-haves.** Any view carrying an
  upper-bound/perfect-foresight/contested-number caveat must record that caveat
  in the plan so it survives into implementation (per ../../CLAUDE.md landmine 7).
- **One focused question at a time** when something is ambiguous — but first
  check `../../CLAUDE.md`, `data/schema.md`, and the existing `build_*.py` scripts to
  see if they already answer it.

---

## The nine candidate items (from the consolidated roadmap)

Stage 1 — build now: **(1)** Capture-Price / Value-Factor view ·
**(2)** Market-Design / Locational-Signal view · **(3)** Curtailment-in-€ +
negative-prices-as-first-class-metric.
Stage 2 — next: **(4)** Wholesale→Retail wedge (decomposed, dynamic) ·
**(5)** Storage revenue-stack / cannibalization upgrade · **(6)** Flexibility /
dynamic-tariff savings calculator · **(7)** Capacity-cost / adequacy panel.
Stage 3 — context layers: **(8)** Marginal-fuel / gas-CO₂ overlay ·
**(9)** Thin industrial-competitiveness layer.

Treat the roadmap's stage numbering as a *hypothesis to test*, not a fixed order.
Your data-feasibility review may legitimately re-rank it.

---

## Step-by-step

### Step 0 — Orient (no approval needed to read; report findings, then pause)
Read `../../CLAUDE.md`, `../../README.md`, `data/schema.md`, every `pipeline/build_*.py`,
and `pipeline/metrics.py` / `pipeline/fuels.py`. Produce a short inventory:
what series the pipeline already fetches, what JSON already exists, what metric
functions already exist, and which frontend views consume them. **Pause for
approval before Step 1.**

### Step 1 — Data-feasibility audit
For each of the nine items, classify it as READY / NEEDS NEW PUBLIC DATA /
CONTEXT-ONLY (per the rules above), naming the exact source and isolation plan
for any new fetch. Output a table. **Pause for approval.**

### Step 2 — Schema & architecture impact
For every READY and NEEDS-NEW-DATA item, specify the new `data/*.json`
artefact(s) and shape, the `data/schema.md` delta, new-vs-extended `build_*.py`
module, and any new pure function in `metrics.py` (with its offline unit-test
fixture). Confirm the static property. Flag any JSON large enough to need
year-splitting (landmine 14). **Pause for approval.**

### Step 3 — Landmine pass
Walk every item against the ../../CLAUDE.md landmines explicitly: DE-LU coding (2),
Oct-2025 resolution break (3), DST/variable-hours (4), negative prices (6),
upper-bound labelling (7), missing-data grace (8), per-direction flows (10),
source isolation (11), units/methodology in writing (12). Capture-Price and
Locational get the most scrutiny. **Pause for approval.**

### Step 4 — Re-rank and sequence
Produce the final build order as a dependency-aware sequence of **vertical
slices** (fetch → metric → JSON → schema → frontend → test). Justify deviations
from the roadmap's stage order with data-feasibility reasons. Each slice must be
independently shippable and valuable. **Pause for approval.**

### Step 5 — Write the plan files
Write `../roadmaps/ROADMAP_V10.md` (mirror `../roadmaps/ROADMAP_V2.md`) and `../../prompts/v10_prompts.md`
(one self-contained prompt per slice, in build order). Update `../../CLAUDE.md`'s "How
to start" section to register the v10 runbook the way v2 is registered. **Pause
for approval before writing.**

### Step 6 — Self-review
Re-read the two new files against this runbook and ../../CLAUDE.md. Confirm every slice
is static, every caveat survived, every new source is isolated, every metric has
a planned offline test, nothing fabricates data, and the order is
dependency-correct. Report a short pass/fail checklist. **Done.**

---

## Definition of done for this runbook
- `../roadmaps/ROADMAP_V10.md` and `../../prompts/v10_prompts.md` exist and are internally
  consistent with `../../CLAUDE.md` and `data/schema.md`.
- Every one of the nine items is classified with a justification.
- The build order is a sequence of independently shippable vertical slices.
- No code was written. No data was fabricated. The static-site property is
  preserved across every planned slice.
- Each contested or upper-bound number from the roadmap is carried into the plan
  **with its caveat attached**.
