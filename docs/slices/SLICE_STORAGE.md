# Vertical slice spec — "Storage: the batteries that live off the spread"

> **Status:** spec only. No code until each step is approved under the `RUN.md`
> protocol. Driven by `RUN_V9.md` + `prompts/v9_prompts.md`. **Stays static.** The
> optimistic counterpart to Dunkelflaute — the supply-side answer to volatility.

Grid-scale batteries and pumped hydro are arriving to soak up the daily price swing the
Spread view measures. This slice shows where they are and how they earn their keep.

## 1. The one question

**"Batteries and pumped hydro are arriving to soak up the volatility — where are they,
and how do they earn their keep off the daily price spread?"**

## 2. The panels

### Panel 1 — A day in the life of a battery
**Shows:** the day-ahead price over 24h with a simple battery charging in the cheap hours
(midday solar trough) and discharging in the expensive hours (evening peak) — the
arbitrage made visible.
**Data:** ENTSO-E day-ahead price (held) + a transparent toy battery model (power,
duration, round-trip efficiency stated).
**Acceptance:** charge/discharge align with cheap/expensive hours; the captured spread is
shown; the model's assumptions are stated; the figure is labelled an upper bound (no
perfect foresight in reality).

### Panel 2 — Where storage is being built
**Shows:** installed battery (and pumped-hydro) capacity and its growth — by country, and
for Germany by region from MaStR.
**Data:** MaStR (DE storage units); other registries / ENTSO-E where available.
**Acceptance:** capacity + growth render; units stated (MW power / MWh energy); gaps honest.

### Panel 3 — Storage vs the spread
**Shows:** how the widening daily spread (the Spread view) improves the arbitrage case —
and the honest limits: round-trip losses, cycling/degradation, falling spreads as more
storage enters (cannibalisation).
**Acceptance:** ties to the Spread data; the caveats are explicit; reuses the existing
"upper bound" discipline.

## 3. Datasets

| Dataset | Feeds | Access | Static |
|---------|-------|--------|--------|
| [ENTSO-E](https://transparency.entsoe.eu) day-ahead price + existing `data/spread.json` | Panels 1, 3 | Token (held) / in repo | Y |
| [MaStR](https://www.marktstammdatenregister.de/MaStR) storage units ([open-mastr](https://open-mastr.readthedocs.io/)); other registries | Panel 2 | Open | Y* |

## 4. New pipeline module (isolated)

- `pipeline/build_storage.py` — a transparent battery-arbitrage model over real prices +
  a committed storage-capacity series → `data/storage.json`. Pure, offline-testable; the
  arbitrage number is an explicit upper bound (perfect foresight, stated efficiency).

## 5. Data contract (update `data/schema.md`)

```jsonc
// data/storage.json
{ "generated_at":"ISO-8601","battery":{"power_mw":1,"duration_h":2,"round_trip":0.85,"foresight":"perfect (upper bound)"},
  "day": { "hours":[], "price":[], "charge_mw":[], "discharge_mw":[], "captured_eur":0 },
  "capacity": [ { "country":"DE","year":2024,"power_gw":0,"energy_gwh":0 } ] }
```

## 6. Frontend

- Reuses Chart.js + the fuel palette (storage = `Pumped storage` light blue). New page
  `frontend/storage.html`.

## 7. Honest-framing copy blocks

**Block A — the arbitrage is an upper bound:**
> A battery earns by charging when power is cheap and discharging when it's dear. The
> figure here assumes perfect foresight and a stated round-trip efficiency, so it's an
> *upper bound* on what a real battery captures — the same caveat as the Spread view's
> arbitrage number. Round-trip losses, cycling wear, and the fact that more storage
> flattens the very spread it feeds on all pull real revenue below this line.

## 8. Risks & caveats

- Keep the arbitrage figure an explicit upper bound (CLAUDE.md landmine 7).
- MaStR storage is large/varied — commit aggregates only; state MW vs MWh.
- Cannibalisation: more storage narrows spreads — note it, don't imply linear scaling.
- tz-aware/DST-safe; static.

## 9. Out of scope

Full revenue-stack modelling (balancing, capacity markets); per-asset economics.

## 10. Build sequence (gated)

0. Pre-flight (read spec + SOURCES + schema; landmine: arbitrage = upper bound; MW vs MWh).
1. `build_storage.py` — battery-day model over real prices + capacity series → JSON; schema; tests. **🧑 USER sanity-checks** (charge in cheap hours, discharge in peak; plausible capture).
2. `storage.html` shell + Panel 1 (a day in the life) + copy block A.
3. Panel 2 (where storage is built / growth).
4. Panel 3 (storage vs the spread) reusing `spread.json`.
5. Integrate & polish; add builder to `refresh-data.yml`; tests; static.

## 11. Definition of done

Panels render from committed JSON; numbers rounded + unit-labelled; arbitrage labelled an
upper bound; MW/MWh stated; copy block A present; schema updated; offline tests pass; static.
