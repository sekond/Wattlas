# Wattlas slices — build bundle

Design and build artifacts for the two regional Wattlas slices, produced in Cowork.
Drop these into the Wattlas repo (preserving the `prompts/` and `frontend/`
subfolders), then build in **Claude Code**.

## Contents

| File | What it is | State |
|------|-----------|-------|
| `SOURCES.md` | European electricity data-source catalogue (ENTSO-E, MaStR, SMARD, netztransparenz, ODRÉ, RTE, Enedis, …) | Reference |
| **Germany — "wasted wind"** | | **Ready to build** |
| `WASTED_WIND_SLICE_README.md` | Germany package guide + which-tool note | — |
| `SLICE_DE_WASTED_WIND.md` | Spec: one question, 3 panels, datasets, modules, acceptance criteria, copy blocks | — |
| `RUN_V3.md` | Gated runbook — kick off with "Follow RUN_V3.md" | — |
| `prompts/v3_prompts.md` | The eight per-step prompts (0–7) | — |
| `frontend/wasted_wind.mockup.html` | Approved visual mockup (open in a browser) | — |
| **France — nuclear** | | **Ready to build** |
| `SLICE_FR_NUCLEAR.md` | Spec: 3 panels (fleet map, exporter/importer régions, availability/fragility) | — |
| `RUN_V4.md` | Gated runbook — kick off with "Follow RUN_V4.md" | — |
| `prompts/v4_prompts.md` | The eight per-step prompts (0–7) | — |
| `frontend/fr_nuclear.mockup.html` | Approved visual mockup (open in a browser) | — |
| `frontend/fr_true_cost.mockup.html` | Panel 4 — cost comparison mockup (sticker ↔ full-cost toggle) | — |

## How to use

These supplement the existing Wattlas repo (`CLAUDE.md`, `data/schema.md`,
`pipeline/build_curtailment.py`, `data/spread.json`, the fuel palette, the daily
`refresh-data.yml`). Open the repo in Claude Code and say **"Follow RUN_V3.md"**
(Germany) or **"Follow RUN_V4.md"** (France) to build a slice. France reuses the map
machinery (`geo.js` + D3) from the Germany slice.

## Notes

- **Which tool:** Claude Code builds these (iterative Python + D3 + tests + git + CI);
  this bundle was produced in Cowork (planning + design).
- **Mockups use illustrative placeholder data** except where noted real (Germany's
  547 negative-price hours; France's ~30 gCO₂/kWh, both from Wattlas). Mockup maps use
  stand-in geometry (DE Landkreise / FR départements); the live builds