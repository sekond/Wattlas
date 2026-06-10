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

## The views

The **Dashboard** is the home page; the eight topic views below are the panels it
unifies, and each also has a focused standalone page (linked from the dashboard).

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

## How it works

```
Open-data APIs  →  pipeline/ (Python/pandas)  →  data/*.json  →  frontend/ (static JS)  →  GitHub Pages
```

The pipeline is the only thing that touches the upstream APIs (ENTSO-E for prices,
generation, load and flows; netztransparenz.de for curtailment). It fetches up to
~12 months for most views and ~3 years for History, computes the metrics, and
writes small JSON files the frontend reads directly. No database, no server,
nothing to break.

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
  kept, never clipped.

## Status

Released as **v1.0.0** — see [Releases](https://github.com/sekond/Wattlas/releases).
A working, deployed learning project: the data engineering is complete and the
numbers reproduce known structural features of the German and European markets. It
is not a commercial product and makes no investment recommendations.

## Run it locally

1. Get a free ENTSO-E API token: https://transparency.entsoe.eu (Account
   Settings → Web API Security Token).
2. `cp .env.example .env` and paste your token in. *(Curtailment additionally needs
   `NETZTRANSPARENZ_CLIENT_ID` / `NETZTRANSPARENZ_CLIENT_SECRET`; without them that
   one view shows its "awaiting source" state.)*
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
   ```
   > `build_carbon.py` and `build_mismatch_zones.py` read the per-zone generation
   > cache, so run them **after** `build_mix.py` (the daily Action orders them this way).
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
- `pipeline/build_*.py` — fetch + compute + write scripts (ENTSO-E modules; `build_curtailment.py` is isolated)
- `pipeline/test_metrics.py`, `pipeline/test_build.py` — offline unit tests
- `data/*.json` — pre-aggregated, committed view data; `data/schema.md` — the pipeline↔frontend contract
- `frontend/dashboard.html` — the landing dashboard; `frontend/{pulse,index(Spread),divergence,mix,mismatch,curtailment,history}.html` — standalone views
- `frontend/dash/` — dashboard modules (`dash-core/panels-a/panels-b/boot.js`, `mobile-panels.js`, `dash.css`, `mobile.css`)
- `frontend/fuels.js` — fuel palette mirror; `frontend/util.js`, `frontend/styles.css` — shared helpers and styles
- `ROADMAP_V2.md`, `RUN_V2.md`, `prompts/` — the v2 expansion plan, runner and prompts
- `design-archive/` — frozen design-handoff bundle (reference only; the live dashboard lives in `frontend/dash/`)
- `.github/workflows/refresh-data.yml` — daily data refresh

## Tests

```
python pipeline/test_metrics.py
python pipeline/test_build.py
```

Metric functions are pure and tested offline (DST days — both the 23-hour spring
and 25-hour autumn switch — the Oct-2025 resolution break, negative prices,
data-gap days, TB2 fallback, hour-of-day and monthly aggregations, the
generation/carbon/flow metrics, and the flows empty-NTC edge case). `test_build.py`
runs the full `build()` against a fixture into a temp directory and asserts the
JSON is written with schema-correct keys — all without network.

## Data sources

- [ENTSO-E Transparency Platform](https://transparency.entsoe.eu) — prices,
  generation, load and cross-border flows for every view except Curtailment. A
  free API token is required to re-run the pipeline; see the setup above.
- [netztransparenz.de](https://www.netztransparenz.de) — the German TSOs'
  redispatch/curtailment API, used only by the Curtailment view (separate OAuth
  credentials; the view degrades gracefully without them).
