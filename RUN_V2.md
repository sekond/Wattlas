# RUN_V2.md — Execution protocol for the v2 expansion

Same rules as `RUN.md`: **you never copy-paste prompts.** Claude Code reads them
itself from `prompts/v2_prompts.md` and works through the phases in
`ROADMAP_V2.md` in order. You approve each phase before it runs and verify the
result before the next.

## How to start

Open the project in Claude Code and say:

> **Follow RUN_V2.md.**

## The protocol Claude Code follows

Execute the phases in `ROADMAP_V2.md` **one at a time** — never more than one
phase per turn. For each phase:

1. State the phase number, what it builds, and (for Phases 4–5) that it adds a
   NEW external data source. One or two sentences.
2. **Stop and wait for the user's explicit approval** ("go", "next", etc.).
   Honour skip/stop/adjust.
3. On approval, execute that phase's prompt from `prompts/v2_prompts.md`
   yourself — do not ask the user to paste it.
4. Regenerate any affected JSON and run the existing tests
   (`python pipeline/test_metrics.py`) to confirm nothing broke.
5. Report concisely: what was added, the key console output (e.g. which zones /
   sources / windows now have data), and whether the phase's success criteria are
   met.
6. **Wait again** for the user before the next phase.

**Verification checkpoints — pause for the user:**
- After **Phase 1**: the user should eyeball the France-vs-Germany mix contrast.
- After **Phase 4** and **Phase 5**: these add new sources — the user should sanity-
  check units and that the new data aligns with existing views (e.g. curtailment
  vs negative-price periods; carbon down when renewables up). New sources are the
  most likely place for a units or timestamp-alignment bug.

If a phase fails, a result looks wrong, or a new source returns unexpected data,
**stop** — report it and propose a fix. Do not auto-advance past a problem. For
new sources especially, prefer a small test fetch before the full pipeline run.

**Architectural guardrail (from CLAUDE.md):** every phase here stays static —
pre-computed JSON, no backend, no database. If any phase seems to require a live
backend, stop and flag it as a deliberate decision rather than adding one.

## The phases (see ROADMAP_V2.md for full rationale)

1. **Generation mix** — full fuel breakdown + France/Germany comparison. (ENTSO-E)
2. **Cross-border flows** — physical flows + congestion in Divergence. (ENTSO-E)
3. **Dashboard** — consolidate all approaches into one dense reactive page. (no new data)
4. **Curtailment** — "wasted" renewables. (NEW SOURCE: SMARD)
5. **Carbon intensity** — clean-vs-dirty hours. (NEW SOURCE: carbon feed)
6. **Time investigation** — custom ranges, zoom, multi-year, seasonal. (no new data)

## Between phases — the move that matters
Each phase is a sensible stopping point and a chance to show the sharpened app to
a field person. Their reaction should re-order the remaining phases. Build → show
→ re-prioritise. Don't grind all six on spec.
