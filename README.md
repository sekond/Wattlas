# Wattlas

**Explore when — and how much — the price of electricity moves in Europe.**

🔗 **Live site: https://sekond.github.io/Wattlas/**

## About

Wattlas turns open European electricity-market data into a set of explorable views
of how — and when — the price of power moves across Europe, centred on Germany (the
DE-LU bidding zone) and its neighbours (France, the Netherlands, Belgium, Poland,
Austria). It runs on open data from the ENTSO-E Transparency Platform (and the
German TSOs for curtailment), pre-computed into a static site with no backend.

It started as a way to learn the data terrain of European power markets, and grew
into a small tool that surfaces a few genuinely interesting things about them.

More recently it went **below the bidding-zone line** and then **beyond price** — into
seven **deep dives**. Four are **map-based**, including a **trilogy on one problem**,
*three ways a congested grid is handled*: Germany keeps one price and curtails northern
wind it can't ship south (**North–south grid**, from **MaStR** + **SMARD**), the
**Nordics** already split into a dozen price zones (**Nordic price zones**, ENTSO-E), and
**Britain** keeps one price and pays Scottish wind to switch off (**UK regional**, from
**NESO**) — alongside **France nuclear**, the centralised mirror (**RTE's éCO2mix via
ODRÉ**). Three further stories are chart-based: **Dunkelflaute** (the cold, dark, windless
spells when wind and solar all but vanish), **Storage** (the batteries that live off the
daily price spread), and a sober, sourced replay of the **Iberian blackout** of 28 April
2025. The map views render with D3-geo from committed TopoJSON basemaps — still no map
tiles, no backend.

## The views

The **Dashboard** is the home page; the eight core topic views below are the panels it
unifies, and each also has a focused standalone page. Beyond them, seven **deep dives** —
standalone pages linked from the dashboard rather than dashboard panels — go further: four
**map stories** that drop below the bidding-zone line (**North–south grid**, **France
nuclear**, **Nordic price zones**, **UK regional**) and three chart-based stories on grid
stress, storage and a historical blackout (**Dunkelflaute**, **Storage**, **Iberian
blackout**).

### Dashboard — everything at once *(landing page)*

A sidebar-navigated, story-driven layout with all eight views as panels. Pick a
zone (compare up to six), choose a time window — or drag the date-range brush —
and every panel that supports it snaps to your choice, with a linked hover
crosshair across charts and a plain-language headline computed live from the data.
Collapses to a phone-native app with bottom-tab navigation on mobile.

### Pulse — the daily rhythm

Average day-ahead price by hour of day, weekday vs weekend: the classic "duck
curve" — prices crater around midday when solar floods the grid, then spike in the
evening as the sun drops and demand peaks.

### Spread — the daily gap

The gap each day between the cheapest and most expensive hour (the Top-Bottom
spread, TB1), with negative-price days highlighted and an explicitly upper-bound
battery-arbitrage figure — the signal that matters most to storage and arbitrage.

### Mix — the generation breakdown

Full generation by fuel type for any zone, with a two-zone side-by-side comparison
and one canonical fuel-colour palette. The headline contrast: France's flat
nuclear baseload against Germany's volatile wind + solar with gas and coal filling
the gaps.

### Mismatch — residual load

Demand minus wind and solar, by hour of day, **per zone**: the demand conventional
plants and batteries must still cover. It dips midday when renewables are abundant
and peaks in the evening — which is exactly why prices peak then too.

### Divergence — geography, explained

How far neighbouring bidding zones' prices drift apart, and *why*. Monthly mean
price per zone and the DE-FR gap, **plus the physical cross-border flow** on each
German border with congested months flagged where flow nears transmission capacity
— the mechanism behind a price gap. (Flow-based western borders publish no explicit
capacity, so congestion is shown only where the data exists — never faked.)

### Carbon — how clean each hour is

Production-based grid carbon intensity (IPCC AR5 lifecycle factors) computed from
the generation mix. It falls as renewable share rises, reading low for
nuclear-heavy France (~30 gCO₂/kWh) and high for coal-heavy Poland (~550) — and it
can overlay the Mix view to tie "how renewable" to "how clean."

### Curtailment — wasted clean power

Renewable energy thrown away when the grid can't absorb or move it — the cost of
Germany's north–south bottleneck, spiking on stormy, negative-price days. Sourced
from the German TSOs' netztransparenz.de redispatch API through an **isolated**
pipeline module (SMARD's public JSON API doesn't expose this). If the source's
credentials are absent, the view degrades to an honest "awaiting source" state
rather than fabricating numbers.

### History — the long view

Several years of daily spread, free to roam: drag to zoom into any stretch, fold
every year onto one seasonal (month-of-year) curve, and read the year-on-year
trend — the multi-year "YoY change" with real data behind it.

### North–south grid — Germany below the zone *(map view)*

Why Germany's wind is in the north and its demand in the south. A map of all ~400
**Landkreise** shaded by installed wind/solar capacity (from **MaStR**) with the
top-20 plants; per-**control-area** net balance (from **SMARD**) showing 50Hertz and
TenneT running long while Amprion and TransnetBW run short, with a redispatch overlay;
and curtailment against negative-price hours, plus an even-handed explainer of the
single-bidding-zone debate. Curtailment is framed as a managed grid-stability measure —
not energy thrown away on purpose.

### France nuclear — the centralised mirror *(map view)*

The matched twin of North–south grid, in four panels. A map of the **13 metropolitan
régions** shaded by hosted nuclear capacity with the ~18 sites (57 reactors, ~63 GW) as
capacity-sized points; per-région net balance (RTE's éCO2mix *solde*) where nuclear-dense
régions export and Île-de-France imports; and the seasonal nuclear **output** dip
(spring/summer maintenance) against the generation mix. Honestly framed: France keeps
exporting through the dip; heatwave river-cooling limits are the event-scale risk.
*Germany can't ship its wind south; France can't always keep its nuclear cool.*

A fourth panel asks **"what does the power really cost?"** — a symmetric, sourced €/MWh
comparison of utility solar, onshore wind, France's amortised existing fleet, and
new-build EPR2, with a **"sticker price ↔ full system cost"** toggle. Flip it and the
hidden-cost adders (waste & decommissioning, system integration, implicit support) apply
to *every* technology, reshuffling the ranking — the point being that it depends on what
you count. Curated from published studies (not a live feed), each figure with a range and
a citation; it takes no side.

### Nordic price zones — living with the split *(map view)*

The Nordics already did what Germany debates: split into many bidding zones. A schematic
map of the **12 Nordic zones** (SE1–4, NO1–5, DK1–2, FI) shaded by average day-ahead price
— a cheap, hydro-rich north (NO4 ~€26/MWh) against a demand-heavy, continent-coupled south
(DK2 ~€90); within-country divergence over time, where Sweden's far-north SE1 and far-south
SE4 are one market with two prices that pull **widest in spring snowmelt**, not just winter;
and an even-handed lesson for the German single-zone question, linked to North–south grid.
Boundaries are **approximate** (zones aren't administrative regions, so they're built from
county groupings and labelled as such); zone prices are ENTSO-E — the source the site
already runs on.

### UK regional — wind paid to switch off *(map view)*

Britain's third answer to the same bottleneck. The **14 GB DNO regions** shaded by
**consumption-based** grid carbon intensity (clean wind/hydro Scotland near 0 gCO₂/kWh
against gas-heavy South Wales ~290) from the **NESO Carbon Intensity API**; the monthly
wind **constraint payments** — roughly **£2 bn a year** — Britain pays to turn Scottish
wind down (and replacement up) when the grid can't carry it south, from **NESO's Constraint
Breakdown**; and a three-fixes comparison linking back to the German and Nordic stories. A
constraint payment is framed as a managed grid-stability cost — the British equivalent of
German redispatch — not energy discarded by choice. **Great Britain only** (no Northern
Ireland), and the consumption-based methodology, are stated throughout.

### Dunkelflaute — when the wind dies and the sun's gone

A renewable grid's hardest hours. The view **auto-detects the worst low-renewable spell**
in the last year of German data — where the 24-hour rolling wind+solar share of demand
stays below a stated, adjustable **10%** — and plots it hour by hour: wind and solar
collapsing toward zero (to ~1.5% of demand in the detected November 2025 spell) while coal,
gas, biomass, hydro and **net imports** carry the load and the price climbs. Plus the
year's frequency of low-renewable hours and the normal-vs-spell generation mix. Framed as
the engineering reality a high-renewable grid plans for — firm capacity, storage or strong
interconnection — **not** an argument against renewables.

### Storage — the batteries that live off the spread

The optimistic counterpart to Dunkelflaute. A transparent toy battery (1 MW / 2 MWh, 85%
round-trip) arbitraged over the real average price profile — charging in the cheap midday
trough, discharging into the evening peak — with the captured spread labelled an explicit
**upper bound** (perfect foresight, the same caveat as Spread). Where grid-scale storage is
being built (Great Britain and Germany leading, roughly **6× since 2021**), in **GW power**
distinct from **GWh energy**; and how the widening daily spread improves the arbitrage case
while **cannibalisation** — more storage flattening the very spread it feeds on — pulls real
revenue back. Pure builder: it reads the committed Pulse and Spread data, no extra fetch.

### Iberian blackout — the day the grid went dark *(historical)*

A sober, data-led replay of the **28 April 2025** blackout across Spain and Portugal. The
ENTSO-E load curve records it honestly — Portugal's load **collapses to ~0.1 GW** and
rebuilds in stages overnight, while **Spain's metering goes dark** (a data gap, rendered as
a gap) — overlaid with sourced restoration milestones (hydro black-start, the France and
Morocco interconnectors, the Spain–Portugal tie-lines). It **does not assert a cause**:
that is cited to the **ENTSO-E Expert Panel final report** (20 March 2026 — *"a combination
of many interacting factors … not a single cause or technology"*; *"the problem is not
renewable energy, but voltage control"*). A fixed historical window, not a refreshing view.

## Value Layer (v10)

Wattlas already owned the *physical* half of the story — what the grid did. The **Value
Layer** adds the **economic, locational and consumer** half: *what was it worth, where, and
who paid for it.* Ten views, each leading with its caveat (the numbers here are easy to get
subtly wrong, so the honest framing is part of the view, not a footnote).

### Capture price / value factor

Generation-weighted capture price ÷ baseload — the **value factor** — for solar and wind per
zone, trended over time, with the share of each tech's output falling in negative-price
hours. (DE solar capture runs ~0.55 of baseload.) Resampled to canonical hourly first so the
Oct-2025 resolution break can't corrupt the weighting; the roadmap **anchor figures are
cited context, not computed truth** — the live numbers come from the actual series.

### Negative prices — first-class

Negative prices promoted from a secondary line to a metric in their own right: hours per
year per zone, a calendar heatmap, and **episode duration**. Counted on the canonical hourly
grid (so 15-minute periods can't inflate the count), in local-time calendar days, never
clipped.

### Flexibility / dynamic-tariff savings

What a shiftable load (EV, heat pump, battery) charging in the cheapest N hours saves per
year versus a flat tariff, per zone. The €/yr figure is a **perfect-foresight upper bound** —
the same caveat as the battery-arbitrage number, carried verbatim — because it assumes the
cheapest hours are known in advance.

### Storage cannibalization *(added to the Storage view)*

An illustrative parametric curve showing the daily spread compressing as assumed battery
volume grows, with per-MW arbitrage declining alongside it. **Doubly caveated:** the base
arbitrage is already a perfect-foresight upper bound, and the compression curve is
illustrative/parametric, **not measured or a forecast**.

### Curtailment in €

A € axis and a running annual total on the Curtailment view: curtailed MWh × a reference
rate. An **estimate**, explicitly labelled — *not* billed compensation — with the €7.2bn EU
2024 figure kept as different-scope (7-country) context, never conflated with the German
number.

### Locational / market-design signal

The internal north–south congestion made legible from SMARD balance + netztransparenz
redispatch, with the single-bidding-zone debate framed even-handedly. The bottleneck is
internal to the DE-LU zone, so **no simulated split price is produced**; the DE5 benchmark
and the academic dissent are shown as a **cited contested range**, with the decided reality
(single zone retained) annotated.

### Wholesale→retail wedge

The consumer price decomposed into wholesale | grid fees | levies & taxes over time
(EUR/kWh, annual). Stated plainly: **EUR/kWh ≠ our €/MWh** (conversion documented), the
source is biannual averages not hourly, and Eurostat **"DE" is the country, not the DE-LU
zone** — flagged where wholesale (zone) meets retail (country).

### Capacity & adequacy

A Dunkelflaute residual-load stress indicator alongside a forward consumer-cost line for
capacity policy. The 12 GW gas tender, 2031 target and levy figures come from a pending
cabinet bill — carried as **provisional, "not yet law"**, with a range and a citation.

### Marginal-fuel

A **model, not a measurement** — CCGT marginal cost (gas/efficiency + EUA × carbon
intensity) versus the day-ahead price, inferring when gas sets the price (~77% of days). The
model caveat is stated prominently; the gas input is a Yahoo TTF proxy and the CO₂ a curated
EEX value (see sources).

### Industrial prices

A thin DE vs FR/ES/NO industrial-price comparison from Eurostat, with an **explicit
out-of-scope boundary**: the financing, M&A, PPA and capital-markets themes sit above the
day-ahead/physical layer Wattlas occupies — a deliberate boundary, not an omission. Any price
shown is labelled country-level Eurostat, not a Wattlas computation.

## How it works

```
Open-data APIs  →  pipeline/ (Python/pandas)  →  data/*.json  →  frontend/ (static JS)  →  GitHub Pages
```

The pipeline is the only thing that touches the upstream APIs: **ENTSO-E** (prices,
generation, load, flows — for every zone, including the Nordic ones and the Iberian
window), **netztransparenz.de** (curtailment), **MaStR** and **SMARD** (German capacity
and regional balance), **ODRÉ — RTE éCO2mix** (French régional and national), and **NESO**
(the GB Carbon Intensity API and the Constraint Breakdown dataset, both open, no key). Each
new source is its **own isolated module**, so a failure in one can't break the others. It
fetches up to ~12 months for most views (~3 years for History; a fixed one-off window for
the Iberian blackout), computes the metrics, and writes small JSON files the frontend reads
directly. A couple of builders are deliberately **pure** — Storage reads the committed
Pulse and Spread data and needs no fetch at all. The four map views also draw committed,
pre-simplified **TopoJSON** basemaps with D3-geo — no map tiles, so the pages still open as
static files. No database, no server, nothing to break.

A scheduled GitHub Action re-runs the pipeline daily (05:17 UTC) and commits the
refreshed JSON to `main`; GitHub Pages redeploys automatically.

## A note on honesty

Energy data is easy to get subtly wrong, so a few correctness choices are made
explicit in the app rather than hidden:

- Prices are resampled to a consistent hourly resolution. Germany's day-ahead
  market switched from hourly to quarter-hourly settlement in October 2025, so
  spreads computed on hourly data are a **conservative lower bound** — true
  15-minute spreads are wider.
- All times are handled in local time (Europe/Berlin), including the 23- and
  25-hour days at daylight-saving transitions.
- The battery-arbitrage figure is labelled an unachievable **upper bound**
  (perfect foresight, no losses) — not achievable revenue.
- Carbon intensity is **production-based** (lifecycle factors), generation gaps
  render as gaps (never fabricated zeros), and negative prices / residual load are
  kept, never clipped. The Storage view extends the same upper-bound discipline to its
  battery-arbitrage figure.
- Where a metric needs a **threshold** (the Dunkelflaute low-renewable cutoff) or a
  methodology that differs from the rest of the site (NESO's **consumption-based** GB
  regional carbon, against the site's production-based view; UK regional is **Great
  Britain only**), the choice is stated in the view, not buried.
- The Iberian-blackout view is sober and **assigns no cause** of its own — it shows what
  the grid data recorded (Spain's missing load during the outage renders as a gap) and
  cites the conclusions to the official ENTSO-E investigation, which it links.

## Status

Released as **v1.0.0** — see [Releases](https://github.com/sekond/Wattlas/releases) — and
extended well beyond it since: **four map stories** (North–south grid, France nuclear,
Nordic price zones, UK regional) and **three chart-based deep dives** (Dunkelflaute,
Storage, Iberian blackout) added and deployed (see the [changelog](CHANGELOG.md)). A
working, deployed learning project: the data engineering is complete and the numbers
reproduce known structural features of the German, French, Nordic, British and wider
European markets — and replay a real historical event. It is not a commercial product and
makes no investment recommendations.

## Run it locally

1. Get a free ENTSO-E API token: https://transparency.entsoe.eu (Account
   Settings → Web API Security Token).
2. `cp .env.example .env` and paste your token in. *(Curtailment additionally needs
   `NETZTRANSPARENZ_CLIENT_ID` / `NETZTRANSPARENZ_CLIENT_SECRET`; without them that
   one view shows its "awaiting source" state. The deep-dive sources — SMARD, MaStR, ODRÉ
   éCO2mix, and **NESO** (GB Carbon Intensity + Constraint Breakdown) — are open and need
   no token; the Nordic, Dunkelflaute and Iberian-blackout views reuse the ENTSO-E token,
   and Storage needs no fetch at all. The France availability panel can optionally use RTE
   OAuth (`RTE_CLIENT_ID` / `RTE_CLIENT_SECRET`) and degrades to output without it.)*
3. Install deps: `pip install -r requirements.txt`
4. Build the data (each script supports `--use-cache` for offline re-runs once
   fetched):
   ```
   python pipeline/build_spread.py         # Spread        -> data/spread*.json
   python pipeline/build_pulse.py          # Pulse         -> data/pulse.json
   python pipeline/build_divergence.py     # Divergence    -> data/divergence.json
   python pipeline/build_mismatch.py       # Mismatch (DE-LU standalone) -> data/mismatch.json
   python pipeline/build_mix.py            # Mix (generation, all zones) -> data/mix.json
   python pipeline/build_carbon.py         # Carbon (from the mix cache) -> data/carbon.json
   python pipeline/build_mismatch_zones.py # Per-zone residual load (mix cache + load) -> data/mismatch_by_zone.json
   python pipeline/build_flows.py          # Cross-border flows + congestion -> data/flows.json
   python pipeline/build_zone_views.py     # Per-zone Spread/Pulse for the dashboard (offline)
   python pipeline/build_history.py        # Multi-year history -> data/spread_history.json
   python pipeline/build_curtailment.py    # Curtailment (needs netztransparenz creds)
   # Map views (below the bidding-zone line; sources are open / no ENTSO-E token):
   python pipeline/build_regional_balance.py        # North–south grid: SMARD per-control-area balance
   python pipeline/build_mastr_capacity.py          # North–south grid: MaStR capacity (needs `pip install open-mastr`; large download)
   python pipeline/build_fr_nuclear_sites.py        # France nuclear: committed fleet -> data/fr_nuclear_sites.json
   python pipeline/build_fr_costs.py                # France nuclear: curated €/MWh cost stack -> data/fr_costs.json
   python pipeline/build_fr_regional.py             # France nuclear: éCO2mix régional balance (ODRÉ)
   python pipeline/build_fr_nuclear_availability.py # France nuclear: monthly output mix (ODRÉ)
   # Further deep dives (sources open / reuse ENTSO-E — no extra token):
   python pipeline/build_nordic_zones.py            # Nordic price zones: ENTSO-E zone prices  -> data/nordic_prices.json
   python pipeline/build_uk_regional_carbon.py      # UK regional: NESO Carbon Intensity API   -> data/uk_regional_carbon.json
   python pipeline/build_uk_constraints.py          # UK regional: NESO Constraint Breakdown    -> data/uk_constraints.json
   python pipeline/build_dunkelflaute.py            # Dunkelflaute: ENTSO-E generation+load+price -> data/dunkelflaute.json
   python pipeline/build_storage.py                 # Storage: PURE (reads pulse.json + spread.json) -> data/storage.json
   python pipeline/build_iberian_blackout.py        # Iberian blackout: one-off ES/PT window    -> data/iberian_blackout.json
   ```
   > `build_carbon.py` and `build_mismatch_zones.py` read the per-zone generation
   > cache, so run them **after** `build_mix.py`; `build_storage.py` reads `pulse.json`
   > + `spread.json`, so run it **after** `build_pulse.py` (the daily Action orders them
   > this way). `build_iberian_blackout.py` is a **one-off historical** pull — not part of
   > the daily refresh. The map basemaps (`frontend/geo/*.topo.json`) are committed static
   > assets — not rebuilt by these scripts.
5. Serve the repo root and open the site:
   `python -m http.server 8000` then visit `http://localhost:8000/` (the dashboard
   is the landing page).

> The repo ships with real data already in `data/`, so step 5 works before you
> ever run the pipeline.

### Updating the data

Every normal build caches the raw fetched series to `data/_raw_*.parquet`
(gitignored). Re-run any script with `--use-cache` to rebuild the JSON from that
cache **without touching the APIs** — useful for iterating on metrics or recovering
from an outage. In production this is automated by the daily GitHub Action; locally
it's a manual run.

## Project structure

- `pipeline/metrics.py` — pure, testable metric computations (shared across views)
- `pipeline/fuels.py` — canonical fuel taxonomy + CO₂ emission factors (single source of truth)
- `pipeline/build_*.py` — fetch + compute + write scripts. ENTSO-E modules share `metrics.py`;
  each new source is **isolated**: `build_curtailment.py` (netztransparenz),
  `build_regional_balance.py` (SMARD), `build_mastr_capacity.py` (MaStR), the France
  `build_fr_nuclear_sites.py` / `build_fr_regional.py` / `build_fr_nuclear_availability.py` (ODRÉ),
  `build_fr_costs.py` (curated €/MWh cost stack, study-based), `build_nordic_zones.py` (ENTSO-E
  Nordic zone prices), `build_uk_regional_carbon.py` + `build_uk_constraints.py` (NESO),
  `build_dunkelflaute.py` (ENTSO-E low-renewable spell detection), `build_storage.py` (pure
  battery-arbitrage model over the committed Pulse/Spread data), and `build_iberian_blackout.py`
  (a one-off ES/PT historical pull)
- `pipeline/de_fields.py`, `pipeline/fr_fields.py` — German→English / French→English translation
  layers (no foreign label reaches the UI); `pipeline/de_kreis_nuts.json` — the NUTS-3↔AGS crosswalk
- `pipeline/test_*.py` — offline unit tests (`test_metrics`, `test_build`, `test_de_fields`,
  `test_mastr_capacity`, `test_regional_balance`, `test_fr_fields`, `test_fr_nuclear_sites`,
  `test_fr_regional`, `test_fr_nuclear_availability`, `test_fr_costs`, plus the deep dives:
  `test_nordic_zones`, `test_uk_regional_carbon`, `test_uk_constraints`, `test_dunkelflaute`,
  `test_storage`, `test_iberian_blackout`)
- `data/*.json` — pre-aggregated, committed view data; `data/schema.md` — the pipeline↔frontend contract
- `frontend/dashboard.html` — the landing dashboard; `frontend/{pulse,index(Spread),divergence,mix,mismatch,curtailment,history}.html` — standalone views
- `frontend/wasted_wind.html` (North–south grid), `frontend/fr_nuclear.html` (France nuclear),
  `frontend/nordic_zones.html` (Nordic price zones), `frontend/uk_regional.html` (UK regional) —
  the **map views**; `frontend/geo.js` — D3-geo render helpers (a reusable choropleth + rich hover);
  `frontend/geo/*.topo.json` — committed basemaps (with `*.build.py` regenerators for the curated ones)
- `frontend/dunkelflaute.html`, `frontend/storage.html`, `frontend/iberian_blackout.html` — the
  three chart-based **deep dives**
- `frontend/dash/` — dashboard modules (`dash-core/panels-a/panels-b/boot.js`, `mobile-panels.js`, `dash.css`, `mobile.css`)
- `frontend/fuels.js` — fuel palette mirror; `frontend/util.js`, `frontend/styles.css` — shared helpers and styles
- `ROADMAP_V2.md`, `RUN_V2.md` … `RUN_V9.md` (the staged slices: V3 North–south grid, V4 France
  nuclear, V5 Nordic zones, V6 UK regional, V7 Dunkelflaute, V8 Iberian blackout, V9 Storage),
  `SLICE_*.md`, `SOURCES.md`, `prompts/` — the staged expansion plans, runners and prompts
- `design-archive/` — frozen design-handoff bundle (reference only; the live dashboard lives in `frontend/dash/`)
- `.github/workflows/refresh-data.yml` — daily data refresh

## Tests

```
python -m pytest pipeline/ -q     # the whole suite
python pipeline/test_metrics.py    # or any single file directly
```

Metric functions are pure and tested offline (DST days — both the 23-hour spring
and 25-hour autumn switch — the Oct-2025 resolution break, negative prices,
data-gap days, TB2 fallback, hour-of-day and monthly aggregations, the
generation/carbon/flow metrics, and the flows empty-NTC edge case). `test_build.py`
runs the full `build()` against a fixture into a temp directory and asserts the
JSON is written with schema-correct keys. The map-view modules add their own offline
tests — the translation layers (with a drift-guard that every emitted fuel is
canonical and that the région crosswalk matches the committed basemap), the MaStR /
SMARD / éCO2mix aggregations, and the net-balance identities — all without network. The
deep dives test their pure functions the same way: the Nordic county→zone aggregation, the
UK carbon and constraint aggregations, the Dunkelflaute spell detector, the battery-arbitrage
model (charge-cheap / discharge-dear, and that efficiency keeps it below the lossless bound),
and the Iberian-blackout timeline (including its **"no asserted cause"** contract).

## Data sources

- [ENTSO-E Transparency Platform](https://transparency.entsoe.eu) — prices,
  generation, load and cross-border flows for every view except Curtailment, including the
  **Nordic bidding zones** (Nordic price zones), the German generation/load/price behind
  **Dunkelflaute**, and the fixed Spain/Portugal window for the **Iberian blackout**. A free
  API token is required to re-run the pipeline; see the setup above.
- [netztransparenz.de](https://www.netztransparenz.de) — the German TSOs'
  redispatch/curtailment API, used by Curtailment and the North–south grid view
  (separate OAuth credentials; degrades gracefully without them).
- [MaStR — Marktstammdatenregister](https://www.marktstammdatenregister.de) (via
  [`open-mastr`](https://open-mastr.readthedocs.io)) — Germany's per-installation
  registry; the North–south grid capacity map aggregates it to Landkreis level (open,
  attribution required; the bulk export is large, so it refreshes weekly in CI).
- [SMARD](https://www.smard.de/en) — per-control-area generation and load for the
  North–south grid net-balance panel (open, no key).
- [ODRÉ — RTE éCO2mix](https://opendata.reseaux-energies.fr) — French régional and
  national generation/consumption for the France nuclear view (open, no key). The
  optional available-capacity overlay would use the [RTE Data Portal](https://data.rte-france.com)
  (OAuth); without it Panel 3 shows output and degrades gracefully.
- [NESO Carbon Intensity API](https://carbonintensity.org.uk) — Great Britain's regional
  grid carbon intensity across the 14 DNO regions (**consumption-based**, forecast-led),
  for the UK regional carbon map (open, no key).
- [NESO Constraint Breakdown](https://www.neso.energy/data-portal/constraint-breakdown) —
  monthly thermal-constraint cost and volume (the B6 Scotland–England boundary, the bulk of
  Britain's wind constraint payments), resolved via the NESO data portal's CKAN API (open).
- Storage capacity (Storage, Panel 2) — a curated, committed series of operational
  grid-scale battery **power (GW)** by country and year, drawn from published market reports
  ([SolarPower Europe](https://www.solarpowereurope.org) market outlooks, Wood Mackenzie,
  Modo Energy, LCP Delta). Approximate aggregates, **not** a live registry pull; energy (GWh)
  differs by duration.
- [ENTSO-E Expert Panel — 28 April 2025 Iberian blackout (data + final report)](https://www.entsoe.eu/publications/blackout/28-april-2025-iberian-blackout/)
  — the official investigation the Iberian-blackout view cites for cause attribution and
  restoration milestones (alongside [REE](https://www.ree.es/en) and [REN](https://datahub.ren.pt/en/)).
  Wattlas asserts no cause of its own.
- Cost comparison (France nuclear, Panel 4) — a curated €/MWh cost stack drawn from
  published studies (Lazard *LCOE+* 2024, the Cour des comptes reports on the EPR/EPR2
  programme, ANDRA/Cigéo waste-disposal estimates, OECD-NEA system-cost work, and IRENA
  renewable-cost data). This is a hand-assembled, committed static table — **not a live
  feed** — where every figure carries a range and a citation; the view takes no side.
- [Eurostat — electricity price components](https://ec.europa.eu/eurostat) (`nrg_pc_204_c`
  household, `nrg_pc_205_c` industrial) — the wholesale/network/taxes split behind the
  Wholesale→retail wedge and the Industrial-prices comparison (open REST API, no key; annual
  averages in EUR/kWh, **country-level not bidding-zone**, isolated module, fails open).
- Yahoo Finance `TTF=F` — the Dutch TTF gas front-month (EUR/MWh) used **only** as the gas
  input to the marginal-fuel model. A **proxy, not licence-clean for redistribution** —
  labelled as such and never presented as an official price.
- EEX EUA — a curated carbon price drawn from EEX primary auctions for the marginal-fuel
  model (slow-moving, stated **as-of**, not a live feed).
- Region boundaries — pre-simplified, committed TopoJSON: German Landkreise and French
  régions from [Eurostat GISCO NUTS](https://ec.europa.eu/eurostat/web/gisco) (NUTS-3 /
  NUTS-1, © EuroGeographics); the **12 Nordic bidding zones** dissolved from GISCO NUTS-3
  counties via a verified county→zone crosswalk; and the **14 GB DNO licence areas** from the
  [NESO data portal](https://www.neso.energy/data-portal/gis-boundaries-gb-dno-license-areas),
  reprojected to WGS84. Bidding-zone boundaries are approximate (they aren't administrative
  regions) and labelled as such.
