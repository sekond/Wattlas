# Wattlas — state vs roadmap review (June 2026)

A review of the live site (https://sekond.github.io/Wattlas/) against `ROADMAP_V2.md`
and the v3 slice specs (`SLICE_DE_WASTED_WIND.md`, `SLICE_FR_NUCLEAR.md`).

## Verdict

The roadmap is essentially fully delivered — every v1/v2 phase, one complete regional
slice, and three of the four panels of the second. Build quality is strong, and the
honesty discipline is the standout. Two gaps remain: the unbuilt cost panel, and the
fact that the most distinctive material is hidden behind nav links.

## Live vs roadmap

| Roadmap item | Status |
|---|---|
| v1 Spread + v2 Phases 1–6 — Pulse, Spread, Mix, Mismatch, Divergence (+flows), Carbon, Curtailment, History, consolidated dashboard (zone + window) | ✅ Live |
| v3 Slice 1 — DE "north–south / wasted wind" (3 panels) | ✅ Live, matches the spec closely |
| v3 Slice 2 — FR nuclear, panels 1–3 (fleet map, export/import, availability) | ✅ Live |
| v3 Slice 2 — FR Panel 4 (true-cost sticker↔full toggle) | ⏳ Spec'd + committed locally (`687fc19`); not pushed/built |
| Slices surfaced on the dashboard | ⚠️ Standalone pages only, reached via two `↗` nav links |

## What's strong

- Both slices shipped faithfully to spec, with real pipeline data (MaStR, SMARD,
  éCO2mix, netztransparenz).
- **Honesty discipline is excellent and consistent** — capacity-vs-output captioned;
  demand layer labelled a population proxy; curtailment defined as a managed
  grid-stability measure ("not energy discarded by choice"); the bidding-zone split
  given both sides with an explicit "Wattlas takes no side"; the diptych softened from
  "hidden weaknesses" to "two structural characteristics." This is the signal a
  credibility piece needs.
- Sources cited on every view; static architecture held (no backend, no tiles).
- The DE↔FR pairing is the distinctive thing the worldwide incumbents (Electricity
  Maps, Ember) don't do.

## Gaps & risks

1. **Panel 4 (cost) is stranded.** The most differentiated and most credibility-sensitive
   addition is fully spec'd and committed, but the commit never reached GitHub (no push
   auth in the authoring environment), so it's neither live nor visible to the build
   clone. Highest-leverage next step.
2. **The best stories are buried.** A first-time visitor lands on the dashboard and sees
   eight competent-but-generic panels starting with "Pulse." The two thesis-grade
   narratives (north–south, France nuclear) are one easily-missed `↗` away. For a piece
   whose job is to impress, the strongest material shouldn't be the hardest to find.
3. **No top-level "what this is and why."** The landing reads as a tool, not a thesis.
   The slices are the stories; they should lead.
4. **Feedback loop still open.** The roadmap's own refrain — "build → show →
   re-prioritise; you've shown it to one person" — still applies. A lot has been built
   on spec; little evidence of external reaction shaping it.

## Recommendations (priority order)

1. **Ship Panel 4** — push `687fc19`, then build it via `RUN_V4.md` Step 7 (see below).
2. **Surface both slices on the dashboard** — a "Deep dives" callout with a one-line hook
   each, or lead with them, instead of two `↗` links.
3. **Add a one-paragraph framing** to the landing so it reads as a thesis, not a tool.
4. **Sanity-check the live slice numbers** against known values (≈56 reactors / ≈61 GW
   for France; the FR Panel 3 availability series; DE Landkreis capacity totals).
5. **Close the loop** — show it to 5–10 energy people and let their reaction reprioritise.

## Ship Panel 4 (next actions)

The cost panel is committed locally on `develop` (`687fc19`) but not pushed. From
`C:\Users\Sebastian\Documents\Antigravity\Wattlas`:

```sh
git pull origin develop      # reconcile — this clone is behind origin
git push origin develop      # publish the slice docs incl. SLICE_FR_NUCLEAR.md, RUN_V4.md, prompts/v4_prompts.md
```

Then, in Claude Code (in the clone that builds the live site):

```
Follow RUN_V4.md
```

It will pick up at **Step 7** (panels 1–3 already shipped): `build_fr_costs.py` writes a
curated, sourced `data/fr_costs.json`, and the sticker↔full-cost toggle section is
appended to `fr_nuclear.html`. Step 8 polishes. Keep the credibility guardrails baked
into the prompt: symmetric adders on every technology, waste framed as *provisioned*
(critique adequacy, not "ignored"), every figure with a visible source + range, and the
section labelled curated estimates — not a live feed.
