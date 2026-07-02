# Wattlas — instructions bundle

All planning, spec, and instruction artifacts for the Wattlas regional "stories",
produced in Cowork. Drop into the Wattlas repo (preserving `prompts/` and `frontend/`),
and build in **Claude Code** with `Follow RUN_Vx.md`.

## The set — "three ways to handle a congested grid" (+ extensions)

Germany keeps one price and curtails/redispatches · the Nordics split into price zones ·
the UK pays wind to switch off. Plus the France nuclear story and its true-cost panel.

## Contents & status

| File | What it is | Status |
|------|-----------|--------|
| `README.md` (this) | Bundle index | — |
| `SOURCES.md` | European electricity data-source catalogue | Reference |
| `REVIEW.md` | Live-site vs roadmap gap analysis + recommendations | Reference |
| **Germany — north–south / wasted wind** | | **✅ Live** |
| `SLICE_DE_WASTED_WIND.md` | Spec (3 panels) | built |
| `RUN_V3.md` + `prompts/v3_prompts.md` | Runbook + prompts | built |
| `WASTED_WIND_SLICE_README.md` | Slice guide | — |
| `frontend/wasted_wind.mockup.html` | Mockup | — |
| **France — nuclear (incl. Panel 4 true cost)** | | **✅ Live** |
| `SLICE_FR_NUCLEAR.md` | Spec (4 panels) | built |
| `RUN_V4.md` + `prompts/v4_prompts.md` | Runbook + prompts (Step/Prompt 7 = cost) | built |
| `frontend/fr_nuclear.mockup.html` | Mockup (panels 1–3) | — |
| `frontend/fr_true_cost.mockup.html` | Mockup (Panel 4 cost toggle) | — |
| **Nordics — split price zones** | | **◐ Ready to build (`RUN_V5`)** |
| `SLICE_NORDIC_ZONES.md` | Spec (3 panels) | ready |
| `RUN_V5.md` + `prompts/v5_prompts.md` | Runbook + prompts (0–6) | ready |
| `frontend/nordic_zones.mockup.html` | Mockup | — |
| **UK — regional carbon + constraints** | | **◐ Ready to build (`RUN_V6`)** |
| `SLICE_UK_REGIONAL.md` | Spec (3 panels) | ready |
| `RUN_V6.md` + `prompts/v6_prompts.md` | Runbook + prompts (0–7) | ready |
| `frontend/uk_regional.mockup.html` | Mockup | — |
| **Dunkelflaute — wind-and-solar drought** | | **◐ Ready to build (`RUN_V7`)** |
| `SLICE_DUNKELFLAUTE.md` | Spec (3 panels) | ready |
| `RUN_V7.md` + `prompts/v7_prompts.md` | Runbook + prompts (0–5) | ready |
| `frontend/dunkelflaute.mockup.html` | Mockup | — |
| **Iberian blackout — 28 Apr 2025** | | **◐ Ready to build (`RUN_V8`)** |
| `SLICE_IBERIAN_BLACKOUT.md` | Spec (3 panels) | ready |
| `RUN_V8.md` + `prompts/v8_prompts.md` | Runbook + prompts (0–5) | ready |
| `frontend/iberian_blackout.mockup.html` | Mockup | — |
| **Storage — batteries & pumped hydro** | | **◐ Ready to build (`RUN_V9`)** |
| `SLICE_STORAGE.md` | Spec (3 panels) | ready |
| `RUN_V9.md` + `prompts/v9_prompts.md` | Runbook + prompts (0–5) | ready |
| `frontend/storage.mockup.html` | Mockup | — |

## How to use

These supplement the existing repo (`CLAUDE.md`, `data/schema.md`,
`pipeline/build_*.py`, the fuel palette, `refresh-data.yml`). In Claude Code:
`Follow RUN_V3.md` (Germany) or `Follow RUN_V4.md` (France) — both already built and
live. Nordics and UK are now build-ready too: `Follow RUN_V5.md` (Nordics) /
`Follow RUN_V6.md` (UK). The grid-stress trio adds `Follow RUN_V7.md` (Dunkelflaute),
`RUN_V8.md` (Iberian blackout) and `RUN_V9.md` (Storage). All seven non-live stories are
build-ready, each with spec + runbook + prompts + mockup.

## Notes

- **Which tool:** Claude Code builds (Python + D3 + tests + git + CI); this bundle was
  produced in Cowork (planning + design).
- **Mockups use illustrative placeholder data** unless noted real (Germany's 547
  negative-price hours; France's ~30 gCO₂/kWh). Mockup maps use stand-in/schematic
  geometry (DE Landkreise, FR départements, Nordic schematic zones); live builds use the
  boundaries each spec names. The cost panel is curated published estimates, not a feed.
- **Static discipline throughout:** pre-computed JSON + committed TopoJSON, no backend,
  no tiles.
- **Credibility guardrails** are written into every spec: symmetric framing, sources +
  ranges, honest "no live feed" / "schematic" / "provisioned not ignored" labelling.
