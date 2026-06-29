# v10 prompts — the "Value Layer" expansion

One self-contained implementation prompt per slice, in build order. Execute via
`../docs/runbooks/RUN_V10.md`, one slice per turn, with confirmation between slices. Full rationale,
JSON shapes, schema deltas, metric signatures, honesty caveats and lane tags live in
`../docs/roadmaps/ROADMAP_V10.md` — trust it; don't re-derive. `CLAUDE.md` (with the v2 data landmines)
is loaded automatically.

Prime directive: **stay static** (pre-computed JSON, no backend). Each new source is
its **own isolated, non-fatal module**. Every metric function is **pure and
offline-unit-tested**. Every displayed number is rounded. Resample to canonical hourly
(`metrics.to_hourly`) before any per-hour metric; keep timestamps tz-aware; never clip
negative prices; carry every caveat into the UI text, not just code comments.

Three slices are **VERIFY-FIRST** (5, 7, 9): before building, confirm the named source
exists and is licence-clean; if not, take the documented fallback and report it.

---

## Prompt 1 — Capture-price / value-factor view  (B2B · READY)

> **Goal:** generation-weighted capture price ÷ baseload (the value factor) for solar
> and wind, per bidding zone, trended monthly, plus each tech's share of generation in
> negative-price hours.
> **Inputs:** `../docs/roadmaps/ROADMAP_V10.md` Slice 1; `_raw_generation_{zone}.parquet` (build_mix),
> `_raw_zone_prices.parquet` (build_divergence) for DE_LU, FR, NL, BE, PL, AT;
> `metrics.py`, `fuels.py`, `data/schema.md`.
> **Build:** new `pipeline/build_capture_price.py` that reads both caches (run after
> build_mix + build_divergence), **resamples generation AND price to canonical hourly
> via `metrics.to_hourly` BEFORE weighting**, and a new pure
> `metrics.capture_metrics(gen_fuel_hourly_mw, price_hourly)`. Write
> `data/capture_price.json` per the roadmap shape. Add an offline test fixture
> (inline hours, solar generating into negative prices). New "Capture" frontend view +
> dashboard panel. Update `data/schema.md`.
> **Output format:** `data/capture_price.json`
> `{generated, source, zones:{DE_LU:{solar:[{month,capture,baseload,value_factor,neg_gen_share}],wind:[…]}…}, summary, note}`.
> **Success criteria:** gen+price proven to share one canonical hourly resolution before
> weighting; value_factor∈(0,1] in the fixture; negatives never clipped; the 50–60% /
> 16% / 573h anchors appear as cited 2025 context, not computed truth; test passes offline;
> all displayed numbers rounded.

---

## Prompt 2 — Negative prices, first-class  (B2C-lean · READY)

> **Goal:** per zone — negative hours/month, a date→count calendar, and episode (run-length)
> duration.
> **Inputs:** `../docs/roadmaps/ROADMAP_V10.md` Slice 2; `_raw_zone_prices.parquet`; `metrics.py`.
> **Build:** new `pipeline/build_negative_prices.py` (after build_divergence); new pure
> `metrics.negative_price_episodes(prices)` (run-length encoding of consecutive negative
> hours + per-day counts) **on the canonical hourly grid**. Write
> `data/negative_prices.json`. Fixture: a series with episodes of length 2 and 3. Frontend:
> calendar-heatmap + episode-duration histogram + a consumer explainer. Update `schema.md`.
> **Output format:** per zone `{by_month:[{month,neg_hours}], calendar:[{date,neg_hours}],
> episodes:[{length_hours,count}], total_neg_hours_12m}`.
> **Success criteria:** total negative hours reconcile with the Spread view's negative-day
> count; counting is on hourly (not 15-min) periods; local-tz days; test passes; rounded.

---

## Prompt 3 — Flexibility / dynamic-tariff savings calculator  (B2C · READY)

> **Goal:** "a shiftable load charging in the cheapest N hours saves €X/year vs. a flat
> tariff," per zone.
> **Inputs:** `../docs/roadmaps/ROADMAP_V10.md` Slice 3; `_raw_zone_prices.parquet`; `metrics.py`.
> **Build:** new `pipeline/build_flex_savings.py`; new pure
> `metrics.cheapest_n_hours_savings(prices, kwh_per_day, n)` (flat = annual mean price).
> Write `data/flex_savings.json` with a few presets (EV / heat pump / home battery) + a
> compact cheapest-N-vs-mean table for client-side interpolation. Fixture: inline prices →
> known saving. Frontend: a small calculator panel. Update `schema.md`.
> **Output format:** per zone `presets:[{name,kwh_per_day,window_h,annual_saving_eur,
> flat_cost_eur,optimized_cost_eur}]` + interpolation table.
> **Success criteria:** savings positive and larger in high-spread zones; the
> **perfect-foresight caveat is on-screen** beside the number (same as the battery model);
> negatives kept; test passes; rounded.

---

## Prompt 4 — Storage revenue-stack / cannibalization upgrade  (B2B · READY, extend)

> **Goal:** add spread compression vs. assumed battery GW to the Storage deep-dive, plus a
> capacity-remuneration note — keeping the honest arbitrage toy.
> **Inputs:** `../docs/roadmaps/ROADMAP_V10.md` Slice 4; `pipeline/build_storage.py`; `storage.json`.
> **Build:** extend `build_storage.py` with a parametric illustrative
> `spread_compression(installed_gw)`; add a `cannibalization` block to `storage.json`.
> Fixture: monotonic arbitrage decline as GW rises. Frontend: a cannibalization curve on
> the Storage deep-dive. Update the `storage.json` schema entry.
> **Output format:** `storage.json += {cannibalization:[{assumed_gw,modelled_spread,
> per_mw_arbitrage}], note}`.
> **Success criteria:** curve declines monotonically and is **labelled illustrative**; the
> existing perfect-foresight upper-bound caveat is retained (double caveat); base arbitrage
> number unchanged; test passes; rounded.

---

## Prompt 5 — Curtailment in €  (B2B · NEEDS-DATA same source · ⚠ VERIFY-FIRST)

> **Goal:** a € axis + running annual total on the Curtailment view.
> **Inputs:** `../docs/roadmaps/ROADMAP_V10.md` Slice 5; `pipeline/build_curtailment.py`; `curtailment.json`.
> **Build:** **VERIFY-FIRST** — does netztransparenz expose redispatch compensation cost
> (€)? If yes, extend `build_curtailment.py` to fetch it; if no, compute `MWh × reference
> price` and set `method:"estimate"`. Add `cost_eur`/`cost_by_month`,
> `running_annual_total`, `method` to `curtailment.json`. Fixture: MWh×price → € with
> method label. Frontend: € axis + running-total KPI. Update the schema entry.
> **Output format:** `curtailment.json += {cost_by_month:[{month,cost_eur}],
> running_annual_total, method}`.
> **Success criteria:** the verify result is reported; € tracks MWh; **method labelled**;
> the €7.2bn EU figure shown as different-scope context (7 countries), not as DE; fails
> open if cost absent; test passes; rounded.

---

## Prompt 6 — Locational / market-design signal  (B2B · READY, scope-narrowed · highest framing risk)

> **Goal:** make internal DE north–south congestion legible and frame the market-design
> debate — **without fabricating a split price**.
> **Inputs:** `../docs/roadmaps/ROADMAP_V10.md` Slice 6; `de_regional_balance.json`, `curtailment.json`
> (+ € from Slice 5), `de_capacity_by_landkreis.json`; the Divergence view; `../docs/slices/SLICE_DE_WASTED_WIND.md` for the north–south landmine.
> **Build:** new thin `pipeline/build_locational_signal.py` that assembles those JSONs +
> a curated `context` block; a small pure north–south imbalance/congestion index. Write
> `data/locational_signal.json`. Fixture: inline regional balance → expected index.
> Frontend: a congestion-evidence panel + an annotated policy block; link to the DE
> north–south deep-dive and Divergence. Update `schema.md`.
> **Output format:** `{monthly:[{month,north_surplus_gwh,south_deficit_gwh,redispatch_gwh,
> congestion_index}], context:{decision,de5:{redispatch_meur:-613,welfare_meur:339,vintage:"2019"},
> academic_dissent:"<€3/MWh (range)"}}`.
> **Success criteria:** **no computed clearing/split price anywhere**; the bottleneck is
> evidenced only from SMARD balance + netztransparenz redispatch (not flows/zonal prices);
> DE5 and academic figures shown as a **contested range** with both cited; the 15 Dec 2025
> single-zone decision annotated; test passes; rounded.

---

## Prompt 7 — Wholesale→retail wedge  (B2C · NEEDS-NEW-DATA · ⚠ VERIFY-FIRST)

> **Goal:** decompose the consumer price into wholesale | grid fees | levies/taxes over time.
> **Inputs:** `../docs/roadmaps/ROADMAP_V10.md` Slice 7; `../docs/SOURCES.md`; our own price mean (spread/divergence).
> **Build:** **VERIFY-FIRST** — confirm Eurostat `nrg_pc_204` dataset code + the
> energy/network/taxes-levies component breakdown + country coverage. New **isolated**
> `pipeline/build_retail_wedge.py` (own auth/units, non-fatal). Write `data/retail_wedge.json`;
> cross-reference `wholesale` from our price mean. Fixture: inline components → total+shares.
> Frontend: a stacked decomposition over time with a north–south grid-fee annotation linking
> to Slice 6. Update `schema.md`.
> **Output format:** `{countries:{DE:[{period,wholesale,network,taxes_levies,total,
> currency:"EUR/kWh"}]…}}`.
> **Success criteria:** components sum to the published total; **EUR/kWh↔€/MWh conversion
> documented**; "biannual, not hourly" stated; Eurostat "DE"=country≠DE_LU zone stated;
> the €6.5bn grid-fee subsidy cited as curated context; module isolated and non-fatal;
> test passes; rounded.

---

## Prompt 8 — Capacity-cost / adequacy panel  (B2B · curated + READY stress)

> **Goal:** a forward consumer-cost line for capacity policy + a Dunkelflaute residual-load
> stress indicator.
> **Inputs:** `../docs/roadmaps/ROADMAP_V10.md` Slice 8; `mismatch.json`, `dunkelflaute.json`; `fr_costs.json`
> as the curated-table pattern.
> **Build:** new `pipeline/build_capacity_adequacy.py` — a residual-load stress summary from
> the existing JSONs + a curated/cited `cost` table. Write `data/capacity_adequacy.json`.
> Fixture: inline residual load → stress flags. Frontend: a provisional cost line + a stress
> panel. Update `schema.md`.
> **Output format:** `{stress:{…}, cost:{tender_gw:12,target_year:2031,
> levy:[{year,eur_bn,range}],source,status:"pending"}}`.
> **Success criteria:** the cost figures are labelled **"not yet law"** with a range +
> citation (May-2026 cabinet bill); the stress indicator lights up on known Dunkelflaute
> spells; test passes; rounded.

---

## Prompt 9 — Marginal-fuel / gas-CO₂ overlay  (B2B · NEEDS-NEW-DATA → maybe CONTEXT · ⚠ VERIFY-FIRST)

> **Goal:** overlay the marginal fuel / gas-CO₂ signal on Pulse/Mix to explain *why* the
> price is set.
> **Inputs:** `../docs/roadmaps/ROADMAP_V10.md` Slice 9; `../docs/SOURCES.md`; `mix.json`, `pulse.json`.
> **Build:** **VERIFY-FIRST** — find a genuinely free, licence-clean **TTF gas + CO₂** feed.
> **If none exists honestly, STOP and build a CONTEXT-ONLY explainer instead (no data
> artefact), and report that decision.** If a feed exists: new isolated
> `pipeline/build_marginal_fuel.py` with a heavily-caveated merit-order inference; write
> `data/marginal_fuel.json`. Fixture: inline fuel prices + mix → inferred marginal fuel.
> Frontend: an overlay toggle on Pulse/Mix. Update `schema.md` only if data lands.
> **Output format:** `data/marginal_fuel.json` (conditional) or a static explainer page.
> **Success criteria:** if built, the marginal fuel is gas in high-price hours and
> renewables in negative-price hours, with the **"model, not measurement" caveat
> on-screen**; if no honest feed, a clean context-only explainer ships instead; test passes
> where applicable; rounded.

---

## Prompt 10 — Industrial-competitiveness layer  (B2B · CONTEXT-ONLY)

> **Goal:** a thin DE vs. FR/ES/NO industrial-price comparison with an explicit scope boundary.
> **Inputs:** `../docs/roadmaps/ROADMAP_V10.md` Slice 10; Slice 7's Eurostat module (if built).
> **Build:** a static annotated explainer. Optionally a thin Eurostat `nrg_pc_205`
> industrial-price proxy reusing Slice 7's module; otherwise pure context. State plainly
> that corporate strategy, M&A, PPAs and capital-markets themes are **out of Wattlas's data
> scope**. No new metric.
> **Output format:** a frontend explainer page (+ optional reuse of `retail_wedge` industrial
> variant).
> **Success criteria:** the page states the **scope boundary explicitly** (deliberate, not
> an omission); any price proxy is labelled country-level Eurostat, not a Wattlas
> computation; nothing fabricated.
