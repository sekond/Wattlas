# Vertical slice spec — "Dunkelflaute: when the wind dies and the sun's gone"

> **Status:** spec only. No code until each step is approved under the `RUN.md`
> protocol. Driven by `RUN_V7.md` + `prompts/v7_prompts.md`. Reuses the existing
> ENTSO-E pipeline; **stays static** — pre-computed JSON, no backend.

The "grid stress" counterpart to the build-out stories: a renewable grid's scariest
hours are the cold, dark, windless spells ("Dunkelflaute") when wind and solar both
fall to near-zero and the system leans entirely on firm power and imports.

## 1. The one question

**"What actually happens during a Dunkelflaute — how far do wind and solar fall, how
long does it last, what fills the gap, and what does it cost?"**

## 2. The panels

### Panel 1 — Anatomy of a Dunkelflaute
**Shows:** hourly generation across a multi-day cold, still, dark spell — wind + solar
collapsing toward zero while gas, nuclear, hydro and imports surge to cover, with the
day-ahead price spiking.
**Data:** ENTSO-E generation-by-type + day-ahead price (already pulled). Identify the
worst low-renewable spell in the window.
**Acceptance:** the renewable collapse + backup surge + price spike render on one
aligned timeline; the event window is auto-selected from the data; gaps honest.

### Panel 2 — How often, how long, how deep
**Shows:** the frequency, duration and depth of low-renewable spells over the year — how
many hours wind+solar covered <X% of demand, and the worst runs.
**Data:** ENTSO-E generation + load (in hand).
**Acceptance:** a clear count/duration view; the threshold (e.g. renewables <10% of
demand) is stated and adjustable in code.

### Panel 3 — What fills the gap (and the honest takeaway)
**Shows:** the backup stack during Dunkelflaute hours — gas, imports, nuclear, hydro,
(storage) — and the plain point that a high-renewable grid still needs firm capacity or
storage for these hours.
**Acceptance:** the gap-filler mix renders; framing is non-ideological (the engineering
reality, not pro/anti-renewable); copy block A present.

## 3. Datasets

| Dataset | Feeds | Access | Static |
|---------|-------|--------|--------|
| [ENTSO-E](https://transparency.entsoe.eu) generation-by-type + day-ahead price + load (DE-LU; optionally neighbours) | All panels | Token (held) | Y |
| Weather context — [DWD](https://opendata.dwd.de/) / [renewables.ninja](https://www.renewables.ninja/) *(optional)* | Panel 1 annotation | Open | Y |

## 4. New pipeline module (isolated)

- `pipeline/build_dunkelflaute.py` — from existing generation/price/load, detect
  low-renewable spells (renewables share < threshold for ≥ N hours), extract the worst
  event's hourly series + a frequency/duration summary → `data/dunkelflaute.json`.
  Pure metric functions, offline-testable.

## 5. Data contract (update `data/schema.md`)

```jsonc
// data/dunkelflaute.json
{ "generated_at":"ISO-8601","zone":"DE_LU","threshold_pct":10,
  "worst_event": { "start":"", "end":"", "hours":[], "wind":[], "solar":[], "gas":[], "nuclear":[], "hydro":[], "imports":[], "price":[] },
  "spells": [ { "start":"", "hours":0, "min_renewable_pct":0 } ],
  "summary": { "spell_hours_year":0, "longest_spell_h":0 } }
```

## 6. Frontend

- Reuses Chart.js + the fuel palette. New page `frontend/dunkelflaute.html`. No map.

## 7. Honest-framing copy blocks

**Block A — what Dunkelflaute means:**
> A *Dunkelflaute* ("dark doldrums") is a stretch of cold, overcast, windless weather when
> wind and solar generate almost nothing — often for days. The grid doesn't fail; it
> leans on firm power (gas, nuclear, hydro) and imports. These hours are why a
> high-renewable system still needs firm capacity, storage or strong interconnection —
> not an argument against renewables, but the engineering reality they have to plan for.

## 8. Risks & caveats

- Define the threshold explicitly (renewables share of demand); it's a choice, not a law.
- Generation-by-type has gaps/"other" buckets (CLAUDE.md landmine 9) — render honestly.
- Imports/exports matter most exactly here — include net imports; don't double-count.
- tz-aware (Europe/Berlin), DST-safe; stays static.

## 9. Out of scope

Multi-country Dunkelflaute correlation (a later increment); sub-hourly; forecasting.

## 10. Build sequence (gated)

0. Pre-flight (read spec + SOURCES + schema; landmine: threshold is a defined choice).
1. `build_dunkelflaute.py` — detect spells + extract worst event → JSON; schema; tests. **🧑 USER sanity-checks** (a known winter spell shows up; renewables near-zero, price high).
2. `frontend/dunkelflaute.html` shell + Panel 1 (the event timeline).
3. Panel 2 (frequency/duration).
4. Panel 3 (gap-fillers) + copy block A.
5. Integrate & polish; add builder to `refresh-data.yml`; tests; static.

## 11. Definition of done

Panels render from committed JSON; numbers rounded + unit-labelled; threshold stated;
copy block A present; schema updated; builder in refresh; offline tests pass; static.
