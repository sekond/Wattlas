# Wasted-wind slice — build package

Everything needed to build the first regional Wattlas slice: the German north–south
**"Why Germany throws away wind it can't ship south"** view. Drop these into the
Wattlas repo (preserving the `prompts/` and `frontend/` subfolders), open the repo in
**Claude Code**, and say **"Follow RUN_V3.md."**

## Contents

| File | What it is |
|------|-----------|
| `SLICE_DE_WASTED_WIND.md` | The spec — one question, three panels, datasets/endpoints, pipeline modules, acceptance criteria, honest-framing copy blocks, risks, out-of-scope. |
| `RUN_V3.md` | The gated runbook — turn-by-turn protocol; kick off with "Follow RUN_V3.md". |
| `prompts/v3_prompts.md` | The eight per-step prompts (0–7) Claude Code reads and executes itself. |
| `SOURCES.md` | The European data-source catalogue (MaStR, SMARD, netztransparenz, …) the slice draws on. |
| `frontend/wasted_wind.mockup.html` | The approved visual mockup — open in a browser. Illustrative placeholder data (real negative-price hours); the live build uses ~400 Landkreise. |

## Assumes the existing Wattlas repo

These supplement, not replace, what's already there: `CLAUDE.md` (the data landmines),
`data/schema.md` (the data contract), `pipeline/build_curtailment.py` +
`data/curtailment.json` and `data/spread.json` (reused by Panel 3), the canonical fuel
palette (`pipeline/fuels.py` / `frontend/fuels.js`), and the daily
`.github/workflows/refresh-data.yml`.

## Which tool builds it

**Claude Code**, in the repo. The slice is iterative multi-file coding — Python
pipeline modules (`open-mastr` download, SMARD fetch, pandas aggregation), TopoJSON
simplification, D3 frontend, unit tests, git, CI — and the whole `RUN_*` / `prompts/`
scaffold is a Claude Code workflow. This package (spec, runbook, prompts, catalogue,
mockup) was produced in **Cowork** — the planning and design layer — for Claude Code
to execute.

## Two steps stay human (either tool)

- Add/confirm `netztransparenz` credentials in `.env` (may already exist from the v2
  Curtailment phase).
- Sanity-check the first real MaStR capacity numbers at **Step 3**.

Pre-req: `open-mastr` installed and the ENTSO-E token present in `.env`.
