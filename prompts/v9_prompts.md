# v9 prompts — the Storage slice

Execute via `RUN_V9.md`, one step at a time. Full detail in `SLICE_STORAGE.md`;
`CLAUDE.md` loaded automatically. Stay static; reuse the ENTSO-E pipeline, `spread.json`,
Chart.js and the fuel palette. Round every number; arbitrage is an explicit upper bound.

---

## Prompt 0 — Pre-flight
> **Goal:** load the slice into memory. **Inputs:** `CLAUDE.md`, `SLICE_STORAGE.md`,
> `SOURCES.md`, `schema.md`. **Build:** <200-word summary.
> **Success:** names the landmines — arbitrage is an upper bound; MW (power) vs MWh
> (energy); more storage flattens the spread (cannibalisation).

## Prompt 1 — Battery model + capacity 🧑 (USER verifies)
> **Goal:** the battery-day model + a capacity series. **Inputs:** ENTSO-E day-ahead price
> (held), `data/spread.json`; MaStR storage units for capacity.
> **Build:** `pipeline/build_storage.py` — a transparent toy battery (power, duration,
> round-trip efficiency stated) charging in the cheapest hours and discharging in the
> dearest over a representative day; compute captured €; assemble a committed capacity
> series (by country; DE by region) → `data/storage.json` (shape in §5); update `schema.md`;
> unit-test the model. **Landmines:** upper bound (perfect foresight); MW vs MWh; aggregates
> only; tz-aware.
> **Output:** module, JSON, schema, test; console note of captured spread + capacity.
> **🧑 Then hand to the user** to confirm charge-cheap/discharge-dear and plausible capture.
> **Success:** JSON + schema; plausible; tested; user confirms; static.

## Prompt 2 — Panel 1: a day in the life of a battery
> **Goal:** the arbitrage made visible. **Build:** `frontend/storage.html` + the day-ahead
> price curve with charge (cheap hours) / discharge (peak hours) marked; copy block A
> (upper-bound caveat + stated assumptions). **Success:** buy-low/sell-high obvious; static.

## Prompt 3 — Panel 2: where storage is being built
> **Goal:** the build-out. **Build:** installed capacity + growth (by country; DE by region
> from MaStR); state MW power / MWh energy. **Success:** capacity + growth render; units
> stated; gaps honest.

## Prompt 4 — Panel 3: storage vs the spread
> **Goal:** the economics, honestly. **Build:** tie to `spread.json` — a widening spread
> improves the arbitrage case; spell out the limits (round-trip losses, cycling wear,
> cannibalisation as more storage enters). **Success:** ties to spread; caveats explicit.

## Prompt 5 — Integrate, polish, lock in
> **Build:** rounding / caveat pass; optional dashboard callout; add `build_storage.py` to
> `refresh-data.yml`; offline tests; static. **Success:** §11 done.
