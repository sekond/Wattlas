# RUN.md — Execution protocol for Claude Code

**You (the user) never copy-paste prompts.** Claude Code reads the prompts itself
from `prompts/implementation_prompts.md` and works through them in order. Your
only job is to approve each step before it runs, and to do the two steps that
require a human (your API token, and eyeballing the first real numbers).

## How to start

Open this project in Claude Code and say:

> **Follow RUN.md.**

That's the only thing you need to type to begin. From there, Claude Code runs the
protocol below.

---

## The protocol Claude Code follows

Claude Code: execute these steps **in order, one at a time**. This is a
turn-based loop — never run two steps in a single turn.

For each step:
1. State the step number and what it will do, in one or two sentences.
2. **Stop and wait for the user's explicit approval** ("go", "yes", "next", or
   similar) before doing anything. If the user says to skip, adjust, or stop,
   honour that.
3. On approval, perform the step by reading and executing the referenced prompt
   from `prompts/implementation_prompts.md` yourself — do not ask the user to
   paste it.
4. Report the result concisely (what changed, what the key output was, whether
   checks passed).
5. **Wait again** for the user before moving to the next step.

Two steps are the user's to perform — Step 2 and the verification inside Step 3.
At those, pause and clearly hand control to the user; do not attempt them.

If any step fails or a result looks wrong, stop the loop, report the problem,
and propose a fix. Do not auto-advance past a failure.

---

## The steps

### Step 0 — Pre-flight + orientation
Run `python bootstrap.py`, then execute **Prompt 0** (read CLAUDE.md, schema.md,
and all pipeline/ and frontend/ files; produce the <200-word summary; change
nothing). 
**Gate:** the summary must name the four landmines (resolution break, DST,
EIC/bidding-zone, arbitrage upper-bound). If not, re-read CLAUDE.md before
proceeding.

### Step 1 — Show the frontend on sample data
Tell the user to run `python -m http.server 8000` and open
`http://localhost:8000/frontend/index.html`, and confirm they see KPIs, the bar
chart, and the arbitrage caveat. (Claude Code: you can start the server, but the
user must confirm the visual.)
**Gate:** user confirms the page renders.

### Step 2 — 🧑 USER STEP: ENTSO-E token
Hand control to the user. They will: get a free token from
https://transparency.entsoe.eu, run `cp .env.example .env`, paste the token into
`.env`, and re-run `python bootstrap.py` until the token check passes.
**Do not attempt this step.** Wait until the user says it's done.

### Step 3 — Fetch real data, then USER verifies
Execute **Prompt 1** (install requirements; test `fetch_prices` on a 7-day
window first; then the full 12-month build; report days written, missing days,
widest day, total negative hours).
Then **🧑 hand control to the user to sanity-check the numbers**: avg daily TB1
in the tens-to-low-hundreds of €/MWh, a few hundred negative hours/year, widest
day in summer or a cold snap. 
**Gate:** the user confirms the numbers are plausible. If a number looks absurd,
stop — it is almost certainly the timezone or resolution-resampling landmine;
re-check metrics.py against CLAUDE.md before continuing.

### Step 4 — Harden the pipeline
Execute **Prompt 2** (logging; parquet cache + `--use-cache` flag; keep
incomplete days as `complete:false`).
**Gate:** `python pipeline/build_spread.py --use-cache` runs offline and
`python pipeline/test_metrics.py` still passes.

### Step 5 — Polish the frontend
Execute **Prompt 3** (annotate the widest day; blue/red legend; graceful
degradation if JSON missing; no overflow at 360px). Ask the user to reload and
confirm.
**Gate:** annotation visible, legend clear, arbitrage caveat still present.

### Step 6 — Lock in tests
Execute **Prompt 4** (tests for a 23-hour spring DST day, a data-gap day, TB2
fallback under 4 hours; add `pipeline/test_build.py`).
**Gate:** both `test_metrics.py` and `test_build.py` pass offline.

### Step 7 — Stop and review
Execute **Prompt 5** (no new code: checklist against the v1 success criteria in
CLAUDE.md; smallest fix for any gap; three reasons an expert might distrust the
numbers and how to fix each).
**Gate:** honest checklist produced. **Do not start a second view.**

---

## After v1
Do not build Pulse, Divergence, or Mismatch yet. They reuse this exact pattern
and are worthless until this view is trusted. The next real move is to put the
working Spread view in front of one actual person and watch their reaction —
that reaction is the audience signal the whole project exists to find.
