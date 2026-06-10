# Wattlas

**Explore when — and how much — the price of electricity moves in Europe.**

🔗 **Live site: https://sekond.github.io/Wattlas/**

## About

Wattlas turns open European electricity-market data into a set of explorable views
of how — and when — the price of power moves across Europe, centred on Germany (the
DE-LU bidding zone) and its neighbours. It runs on live data from the ENTSO-E
Transparency Platform, pre-computed into a static site with no backend.

It started as a way to learn the data terrain of European power markets, and grew
into a small tool that surfaces a few genuinely interesting things about them.

### The views

#### Pulse — the daily rhythm

Average day-ahead price by hour of day, weekday vs weekend. Shows the classic
"duck curve": prices crater around midday when solar floods the grid, then spike
in the evening as the sun drops and demand peaks.

![Pulse view](docs/screenshots/pulse.png)

#### Spread — the financial core

The daily gap between the cheapest and most expensive hour (the Top-Bottom
spread), with negative-price days highlighted. This is the signal that matters
most to battery storage and arbitrage.

![Spread view](docs/screenshots/spread.png)

#### Divergence — geography

How far neighbouring bidding zones drift apart, and where Germany sits against
France, the Netherlands, Belgium, Poland and Austria. Reveals structural facts
like France's nuclear fleet keeping its prices consistently below its neighbours'.

![Divergence view](docs/screenshots/divergence.png)

#### Mismatch — residual load

Total demand minus wind and solar, by hour of day: the demand that conventional
plants and batteries must still cover. It dips midday when renewables are
abundant and peaks in the evening — which is exactly why prices peak then too.

![Mismatch view](docs/screenshots/mismatch.png)

#### Mix — the generation breakdown

Full generation by fuel type, hour by hour, for any zone — with a two-zone
side-by-side comparison. The headline contrast: France's flat nuclear baseload
against Germany's volatile wind + solar with gas and coal filling the gaps. An
optional **carbon-intensity overlay** (production-based, IPCC AR5 lifecycle
factors) ties "how renewable" to "how clean": it falls when wind/solar rise, and
sits low for nuclear-heavy France (~30 gCO₂/kWh) vs coal-heavy Poland (~550).

#### Divergence + flows — geography, explained

Beyond *how far* neighbouring zones drift, the upgraded Divergence view shows the
*physical flow* across each German border and flags congested months where the
interconnector runs at its transmission limit — the mechanism behind a price gap.
(Western borders use flow-based market coupling and publish no explicit capacity,
so congestion is shown only where capacity data exists — never faked.)

#### Dashboard — everything at once

The landing page. A sidebar-navigated, story-driven layout with all eight views as
panels: pick a zone (compare up to six), choose a time window — or drag the
date-range brush — and every panel that supports it snaps to your choice, with a
linked hover crosshair across charts and a plain-language headline computed live
from the data. Collapses to a phone-native app with bottom-tab navigation on mobile.

#### History — the long view

Several years of daily spread, free to roam: drag to zoom into any stretch, jump
to a window, fold every year onto one seasonal curve, and read the year-on-year
trend. This is where the multi-year "YoY change" finally has real data behind it.

#### Curtailment — wasted clean power

Renewable energy thrown away when the grid can't absorb or move it — the cost of
Germany's north–south bottleneck, spiking on stormy, negative-price days. Sourced
from the German TSOs' netztransparenz.de redispatch API through an **isolated**
pipeline module (SMARD's public JSON API doesn't expose this). If the source's
credentials are absent the view degrades to an honest "awaiting source" state
rather than fabricating numbers.

### How it works

```
ENTSO-E API  →  pipeline/ (Python/pandas)  →  data/*.json  →  frontend/ (static JS)  →  GitHub Pages
```

The pipeline is the only thing that touches the ENTSO-E API. It fetches roughly a
year of data, computes the metrics, and writes small JSON files that the frontend
reads directly. No database, no server, nothing to break.

A scheduled GitHub Action re-runs the pipeline daily (05:17 UTC) and commits the
refreshed JSON to `main`; GitHub Pages redeploys automatically.

### A note on honesty

Energy data is easy to get subtly wrong, so a few correctness choices are made
explicit in the app rather than hidden:

- Prices are resampled to a consistent hourly resolution. Germany's day-ahead
  market switched from hourly to quarter-hourly settlement in October 2025, so
  spreads computed on hourly data are a **conservative lower bound** — true
  15-minute spreads are wider.
- All times are handled in local time (Europe/Berlin), including the 23- and
  25-hour days at daylight-saving transitions.
- Where the app shows a theoretical battery-arbitrage figure, it is labelled as
  an **upper bound** that assumes perfect foresight and no losses — not achievable
  revenue.

### Status

A working, deployed learning project. The data engineering is complete and the
numbers reproduce known structural features of the German and European markets.
It is not a commercial product and makes no investment recommendations.

## Run it locally

1. Get a free ENTSO-E API token: https://transparency.entsoe.eu (Account
   Settings → Web API Security Token).
2. `cp .env.example .env` and paste your token in.
3. Install deps: `pip install -r requirements.txt`
4. Build the data — one script per view (each supports `--use-cache` for offline
   re-runs once fetched):
   ```
   python pipeline/build_spread.py        # The Spread   -> data/spread*.json
   python pipeline/build_pulse.py         # Pulse        -> data/pulse.json
   python pipeline/build_divergence.py    # Divergence   -> data/divergence.json
   python pipeline/build_mismatch.py      # Mismatch     -> data/mismatch.json
   python pipeline/build_mix.py           # Mix (gen mix, all zones) -> data/mix.json
   python pipeline/build_carbon.py        # Carbon (from the mix cache) -> data/carbon.json
   python pipeline/build_mismatch_zones.py # Per-zone residual load (uses the mix cache + load) -> data/mismatch_by_zone.json
   python pipeline/build_flows.py         # Cross-border flows + congestion -> data/flows.json
   python pipeline/build_zone_views.py    # Per-zone Spread/Pulse for the dashboard (offline)
   python pipeline/build_history.py       # Multi-year history -> data/spread_history.json
   python pipeline/build_curtailment.py   # Curtailment (needs netztransparenz creds)
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
cache **without touching the ENTSO-E API** — useful for iterating on metrics or
recovering from an outage. In production this is automated by the daily GitHub
Action; locally it's a manual run.

## Project structure

- `pipeline/metrics.py` — pure, testable metric computations (shared across views)
- `pipeline/fuels.py` — canonical fuel taxonomy + CO₂ emission factors (single source of truth)
- `pipeline/build_*.py` — one fetch+compute+write script per view (ENTSO-E modules; `build_curtailment.py` is isolated)
- `pipeline/test_metrics.py`, `pipeline/test_build.py` — offline unit tests
- `data/schema.md` — the JSON contract between pipeline and frontend
- `frontend/dashboard.html` — the landing dashboard; `frontend/{pulse,index(Spread),divergence,mix,mismatch,curtailment,history}.html` — the standalone views
- `frontend/dash/` — dashboard v2 modules (`dash-core/panels-a/panels-b/boot.js`, `mobile-panels.js`, `dash.css`, `mobile.css`)
- `frontend/fuels.js` — fuel palette mirror; `frontend/util.js`, `frontend/styles.css` — shared helpers and styles
- `ROADMAP_V2.md`, `RUN_V2.md`, `prompts/v2_prompts.md` — the v2 expansion plan, runner and prompts
- `design-archive/` — frozen design-handoff bundle (reference only; the live dashboard lives in `frontend/dash/`)
- `.github/workflows/refresh-data.yml` — daily data refresh

## Tests

```
python pipeline/test_metrics.py
python pipeline/test_build.py
```

Metric functions are pure and tested offline (DST days — both the 23-hour spring
and 25-hour autumn switch, the Oct-2025 resolution break, negative prices,
data-gap days, TB2 fallback, hour-of-day and monthly aggregations). `test_build.py`
runs the full `build()` against a fixture into a temp directory and asserts the
JSON is written with schema-correct keys — all without network.

## Data sources

- [ENTSO-E Transparency Platform](https://transparency.entsoe.eu) — prices,
  generation, load and cross-border flows for every view except Curtailment. A
  free API token is required to re-run the pipeline; see the setup above.
- [netztransparenz.de](https://www.netztransparenz.de) — the German TSOs'
  redispatch/curtailment API, used only by the Curtailment view (separate OAuth
  credentials; the view degrades gracefully without them).
