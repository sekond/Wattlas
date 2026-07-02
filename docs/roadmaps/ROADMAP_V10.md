# ROADMAP v10 — The "Value Layer": from what the grid did to what it was worth

Vetted plan produced under `../runbooks/RUN_V10.md` from `wattlas-consolidated-roadmap.md`
(synthesis of three energy podcasts) reviewed against the live codebase. Wattlas
already owns the *physical* half of the 2025–26 energy story (duck curve,
residual load, congestion, Dunkelflaute, curtailment, zone decoupling, a
transparent storage model). This layer adds the **economic, locational and
consumer** half: *what was it worth, where, and who paid for it.*

Every slice below stays **static** (pre-computed JSON, frontend slices
client-side — landmine 13). Each is one vertical slice: fetch/cache-read →
metric → JSON → `schema.md` → frontend → offline test.

## Why this order (the one thing to understand)

Data-feasibility re-ranks the roadmap's stages. Slices **1–6 need no new external
source** (they read existing per-zone price/generation caches, extend existing
modules, or assemble curated tables) — so they come first and ship fast. The
genuinely new sources (Eurostat for the retail wedge; a gas/CO₂ feed for the
marginal-fuel overlay) are back-loaded behind **three VERIFY-FIRST gates**. The
two highest silent-error risks — **capture-price** (resolution-break weighting)
and **locational signal** (an internal DE-LU bottleneck that must never be shown
as a simulated price) — are called out in every relevant slice.

Lane tags: **B2C** = consumer-facing · **B2B** = professional/industrial.

---

## Slice 1 — Capture-price / value-factor view  · B2B · READY
**Goal:** for solar and wind, per bidding zone, show the generation-weighted
capture price ÷ baseload (the value factor), trended over time, plus the share of
each tech's generation falling in negative-price hours. The roadmap's #1 gap.
**Source:** none new — reads `_raw_generation_{zone}.parquet` (build_mix) and
`_raw_zone_prices.parquet` (build_divergence) for the six shared zones (DE_LU, FR,
NL, BE, PL, AT). Must run after both (cache dependency, like `build_carbon`).
**JSON output:** `data/capture_price.json` —
`{zones:{DE_LU:{solar:[{month,capture,baseload,value_factor,neg_gen_share}],wind:[…]}…}, summary, note}`.
**Schema delta:** add `capture_price.json`.
**Metric + test:** `metrics.capture_metrics(gen_fuel_hourly_mw, price_hourly)` →
generation-weighted capture, time-weighted baseload, value factor, neg-price
generation share. Fixture: a few inline hours where solar generates into low/negative
prices → assert capture<baseload, value_factor∈(0,1], neg_gen_share correct.
**Frontend:** new "Capture" view (+ dashboard panel) — value-factor trend per zone,
tech toggle, neg-price-share annotation.
**Honesty caveats:** anchor figures (DE solar capture ~50–60% of baseload; ~16% of
solar at negative prices; 573 negative hours, 2025) are **cited context, not
computed truth** — compute from actual series. **Acceptance gate:** generation and
price MUST be resampled to one canonical hourly resolution (`metrics.to_hourly`)
before weighting, or the Oct-2025 break silently corrupts the capture price
(landmine 3). Negative prices never clipped (landmine 6).
**Ship test:** solar value factor is visibly below 1 and trends down where negative
hours rise; numbers reconcile in order of magnitude with the cited 2025 anchors.

## Slice 2 — Negative prices, first-class  · B2C-lean · READY
**Goal:** promote negative prices from a secondary line to a first-class metric —
hours/year per zone, a calendar heatmap, and **episode duration** (the part experts
now emphasise).
**Source:** none new — `_raw_zone_prices.parquet` (build_divergence) + DE_LU spread.
**JSON output:** `data/negative_prices.json` — per zone
`{by_month:[{month,neg_hours}], calendar:[{date,neg_hours}], episodes:[{length_hours,count}], total_neg_hours_12m}`.
**Schema delta:** add `negative_prices.json`.
**Metric + test:** `metrics.negative_price_episodes(prices)` → run-length encoding of
consecutive negative hours + per-day counts. Fixture: a series with episodes of
length 2 and 3 → asserts episode table + calendar.
**Frontend:** a calendar-heatmap panel + episode-duration histogram; consumer
explainer ("negative prices mean you could be paid to use power").
**Honesty caveats:** count on the **canonical hourly grid** (resample first, else
15-min periods inflate the hour count — landmine 3); local-tz calendar days
(landmine 4); never clip (landmine 6).
**Ship test:** total negative hours per zone reconciles with the Spread view's
negative-day count; episodes show plausible multi-hour midday solar runs.

## Slice 3 — Flexibility / dynamic-tariff savings calculator  · B2C · READY
**Goal:** "a shiftable load (EV / heat pump / battery) charging in the cheapest N
hours saves €X/year vs. a flat tariff," per zone. The B2C flagship; operationalises
the dynamic-tariff theme all three shows raise. *(Pulled ahead of the roadmap's
Stage 2 because it needs no new source.)*
**Source:** none new — `_raw_zone_prices.parquet` (build_divergence).
**JSON output:** `data/flex_savings.json` — per zone `presets:[{name,kwh_per_day,
window_h,annual_saving_eur,flat_cost_eur,optimized_cost_eur}]` + a compact
cheapest-N-vs-daily-mean table for a couple of client-side-interpolated presets.
**Schema delta:** add `flex_savings.json`.
**Metric + test:** `metrics.cheapest_n_hours_savings(prices, kwh_per_day, n)` →
annual saving vs flat (flat = annual mean price). Fixture: inline prices → known saving.
**Frontend:** a small calculator panel — pick a load preset and zone, read €/yr saved.
**Honesty caveats:** **perfect-foresight** (the cheapest N hours are known in
advance) — carry the **same upper-bound caveat as the battery model** verbatim
(landmine 7). Cheapest hours may be negative, kept (landmine 6).
**Ship test:** savings are positive and larger in high-spread zones; the caveat is
on-screen next to the number.

## Slice 4 — Storage revenue-stack / cannibalization upgrade  · B2B · READY (extend)
**Goal:** keep the honest arbitrage toy, but add spread compression as assumed
battery volume grows, and note the shift toward capacity/availability remuneration —
mirroring the solar-cannibalization logic on the storage side.
**Source:** none new — extends `build_storage.py` (reads pulse.json + spread.json).
**JSON output:** extend `data/storage.json` with
`cannibalization:[{assumed_gw, modelled_spread, per_mw_arbitrage}]` + a curated
capacity-remuneration note.
**Schema delta:** extend the `storage.json` entry.
**Metric + test:** parametric `spread_compression(installed_gw)` (illustrative).
Fixture: asserts monotonic arbitrage decline as GW rises; output labelled illustrative.
**Frontend:** add a cannibalization curve to the Storage deep-dive.
**Honesty caveats:** **double caveat** — the existing perfect-foresight upper bound
**and** the compression curve is illustrative/parametric, not measured (landmine 7).
**Ship test:** the curve declines monotonically and is labelled illustrative; the
base arbitrage number is unchanged.

## Slice 5 — Curtailment in €  · B2B · NEEDS-NEW-DATA (same source) · ⚠ VERIFY-FIRST
**Goal:** add a € axis and a running annual total to the Curtailment view.
**Source:** extend `build_curtailment.py` to pull netztransparenz **compensation
cost (€)**. **VERIFY-FIRST:** confirm the endpoint exists; if not, € = MWh ×
reference price labelled `method:"estimate"`.
**JSON output:** extend `data/curtailment.json` with `cost_eur` / `cost_by_month`,
`running_annual_total`, and a `method` field.
**Schema delta:** extend the `curtailment.json` entry.
**Metric + test:** trivial sum. Fixture: MWh × price → € with method label.
**Frontend:** € axis + running-total KPI on the Curtailment view.
**Honesty caveats:** currency stated; MWh→€ **method labelled**; the €7.2bn EU 2024
figure is **different-scope context** (7 countries), not conflated with DE (landmine 12).
Fails open if cost absent (landmine 8). Sequenced before Slice 6 so its € can feed it.
**Ship test:** the € total tracks MWh; method label is visible.

## Slice 6 — Locational / market-design signal  · B2B · READY (scope-narrowed)
**Goal:** make the internal DE north–south congestion legible and frame the
market-design debate — *without* fabricating a split price.
**Source:** none new — assembles `de_regional_balance.json` (SMARD),
`curtailment.json` (redispatch, + € from Slice 5), `de_capacity_by_landkreis.json`
(MaStR), and the existing Divergence view. A new thin `build_locational_signal.py`.
**JSON output:** `data/locational_signal.json` — `{monthly:[{month,north_surplus_gwh,
south_deficit_gwh,redispatch_gwh,congestion_index}], context:{decision, de5, academic_dissent}}`.
**Schema delta:** add `locational_signal.json`.
**Metric + test:** a small pure north–south imbalance/congestion index. Fixture:
inline regional balance → expected index.
**Frontend:** a locational-signal panel — congestion evidence + an annotated policy
block; links to the DE north–south deep-dive and Divergence.
**Honesty caveats — highest framing risk:** the north–south bottleneck is **internal
to the DE-LU zone**, so it appears in **neither cross-border flows nor zonal prices**
(landmine 2) — evidence comes only from SMARD balance + netztransparenz redispatch.
**No simulated clearing price is produced.** The DE5 benchmark (−€613m redispatch /
+€339m welfare, **2019-vintage**) and the academic dissent (**<€3/MWh spreads**) are
shown as a **contested range** with both poles cited; the decided reality (single
zone *retained*, Aktionsplan Gebotszone, 15 Dec 2025) is annotated (landmine 7).
**Ship test:** redispatch volume rises with high-wind/low-price periods; the panel
contains no computed split price and shows the DE5/academic figures as a range.

## Slice 7 — Wholesale→retail wedge  · B2C · NEEDS-NEW-DATA · ⚠ VERIFY-FIRST
**Goal:** decompose the consumer price into wholesale | grid fees | levies/taxes —
the primary B2C build. *(Held to here, not dropped: it is the first slice needing a
brand-new external source + unit reconciliation, so it follows the existing-data wins.)*
**Source:** NEW isolated module `build_retail_wedge.py` → **Eurostat `nrg_pc_204`**
(household electricity price components; open API, no key). **VERIFY-FIRST:** dataset
code + component breakdown.
**JSON output:** `data/retail_wedge.json` —
`{countries:{DE:[{period,wholesale,network,taxes_levies,total,currency:"EUR/kWh"}]…}}`,
`wholesale` cross-referenced from our own price mean.
**Schema delta:** add `retail_wedge.json`.
**Metric + test:** assembly + wholesale-share calc. Fixture: inline components → total + shares.
**Frontend:** a stacked decomposition (wholesale / network / taxes-levies) over time,
with a north–south grid-fee annotation linking to Slice 6.
**Honesty caveats:** **EUR/kWh ≠ our €/MWh** — conversion documented; Eurostat is
**biannual averages, not hourly**, so the "dynamic" framing is bounded and stated
(landmine 12); Eurostat **"DE" = country, not the DE_LU zone** — stated where
wholesale (zone) meets retail (country) (landmine 2). The 2026 ~€6.5bn grid-fee
subsidy is curated/cited policy. Isolated module (landmine 11).
**Ship test:** the three components sum to the published total; the wholesale share
is a minority of the consumer price, as expected.

## Slice 8 — Capacity-cost / adequacy panel  · B2B · NEEDS-DATA (curated) + READY (stress)
**Goal:** surface the forward consumer-cost of capacity policy alongside a
Dunkelflaute residual-load stress indicator.
**Source:** stress indicator reuses `mismatch.json` + `dunkelflaute.json` (READY); the
€-cost line is a **curated/cited** table modelled on `fr_costs.json`.
**JSON output:** `data/capacity_adequacy.json` — `{stress:{…from existing…},
cost:{tender_gw:12, target_year:2031, levy:[{year,eur_bn,range}], source, status:"pending"}}`.
**Schema delta:** add `capacity_adequacy.json`.
**Metric + test:** a minimal residual-load stress summary. Fixture: inline residual
load → expected stress flags.
**Frontend:** a forward consumer-cost line + a stress indicator panel.
**Honesty caveats:** the 12 GW / 10-hour gas tender, 2031 target, and up-to-€3bn
(2031) / up-to-€2.3bn-a-year (2032–45) levy come from a **May-2026 cabinet bill
pending Bundestag** — carry "**not yet law**" + a range + citation (landmine 7/12).
**Ship test:** the cost line is labelled provisional with a citation; the stress
indicator lights up on known Dunkelflaute spells.

## Slice 9 — Marginal-fuel / gas-CO₂ overlay  · B2B · NEEDS-NEW-DATA → maybe CONTEXT-ONLY · ⚠ VERIFY-FIRST
**Goal:** explain *why* the price is set (the geopolitics-as-price-driver theme) by
overlaying the marginal fuel / gas-CO₂ signal on Pulse/Mix.
**Source:** NEW — a free **TTF gas + CO₂** feed. **VERIFY-FIRST:** a genuinely free,
licence-clean source. **If none exists honestly → demote to a CONTEXT-ONLY explainer,
no data artefact.**
**JSON output (conditional):** `data/marginal_fuel.json`.
**Schema delta:** add `marginal_fuel.json` only if the data lands.
**Metric + test:** merit-order inference (heavily caveated). Fixture: inline fuel
prices + mix → inferred marginal fuel.
**Frontend:** an overlay toggle on Pulse/Mix.
**Honesty caveats:** marginal-fuel attribution is a **model, not a measurement** —
stated prominently (landmine 12). I disagree with the roadmap's implied readiness:
this is the **least feasible** of the candidate builds; treat as the last buildable
slice, ready to land as pure context.
**Ship test:** the inferred marginal fuel is gas in high-price hours and renewables
in negative-price hours; the model caveat is on-screen.

## Slice 10 — Industrial-competitiveness layer  · B2B · CONTEXT-ONLY
**Goal:** a *thin* DE vs. FR/ES/NO industrial-price comparison, with an explicit
scope boundary.
**Source:** optional thin **Eurostat `nrg_pc_205`** (industrial price proxy, reuses
Slice 7's module); corporate strategy, M&A, PPAs and capital-markets themes are
**out of Wattlas's data scope** (the roadmap says so itself).
**JSON output:** optional reuse of `retail_wedge` industrial variant; otherwise none.
**Schema delta:** none (or extend `retail_wedge.json`).
**Metric + test:** none beyond Slice 7's.
**Frontend:** a static annotated explainer with an explicit "out of data scope" note.
**Honesty caveats:** **deliberate boundary, not omission** — say plainly that the
financing/strategy themes sit above the day-ahead/physical layer Wattlas occupies.
**Ship test:** the page states the scope boundary explicitly; any price proxy is
labelled country-level Eurostat, not a Wattlas computation.

---

## The architectural line to hold (constructive guardrail)
Every slice above stays **static**: pre-computed JSON at build time, the frontend
slices client-side. No backend, no database, no server-side compute. Slice 6
explicitly avoids a live market model; Slice 3 pre-computes presets rather than
computing on demand. The honest ceiling ("any metric, any zone, any window, live")
still wants a real backend eventually — **do not cross that line until real usage
proves you need it** (landmine 13). When/if you do, that is its own planning
conversation; flag it, don't drift into it.

## VERIFY-FIRST gates (resolve before building the slice)
1. **Slice 5** — does netztransparenz expose redispatch **compensation cost (€)**?
   If not, fall back to a clearly-labelled `MWh × reference-price` estimate.
2. **Slice 7** — Eurostat `nrg_pc_204` dataset code + the energy/network/taxes-levies
   component breakdown, and the country coverage we need.
3. **Slice 9** — a genuinely free, licence-clean **TTF gas + CO₂** price feed. If
   none, Slice 9 becomes a context-only explainer.

## Contested / upper-bound numbers carried forward (with caveats)
- Solar capture **50–60%** of baseload; **~16%** of solar at negative prices; **573**
  negative hours (Slice 1) — 2025-vintage context.
- DE5 **−€613m** redispatch / **+€339m** welfare (2019 data) vs. academic **<€3/MWh**
  spreads (Slice 6) — a **contested range**.
- **€7.2bn** EU curtailment 2024 (Slice 5) — different scope (7 countries).
- **~€6.5bn** 2026 grid-fee subsidy (Slice 7) — curated policy.
- **12 GW** tender, up-to-**€3bn**(2031) / **€2.3bn**/yr (2032–45) levy (Slice 8) —
  pending-Bundestag, carry "not yet law".
- Battery captured-spread and the flexibility savings (Slices 3, 4) — **perfect-
  foresight upper bounds**.

## B2C vs. B2B lanes (to guide UX)
**B2C lane:** retail wedge (7) · flexibility calculator (3) · negative-prices
explainer (2). **B2B lane:** capture price (1) · storage cannibalization (4) ·
curtailment-€ (5) · locational signal (6) · capacity adequacy (8) · marginal-fuel
overlay (9) · industrial proxy (10).

## What would re-order these priorities
- EU forces a German bidding-zone split → Slice 6 jumps to #1 and needs *real*
  split-zone pricing, not the congestion-evidence framing.
- Capacity levy confirmed in final law → promote Slice 8 into the first wave.
- Solar value factor stops falling for four straight quarters → de-emphasise Slice 1.
- DE smart-meter / dynamic-tariff penetration above ~10% → Slice 3 gains a far
  larger audience; promote it.
