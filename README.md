# Wattlas

**Explore when — and how much — the price of electricity moves in Europe.**

🔗 **Live site: https://sekond.github.io/Wattlas/**

## About

Wattlas turns open European electricity-market data into four explorable views
of how — and when — the price of power moves in Germany (the DE-LU bidding zone).
It runs on live data from the ENTSO-E Transparency Platform, pre-computed into a
static site with no backend.

It started as a way to learn the data terrain of European power markets, and grew
into a small tool that surfaces a few genuinely interesting things about them.

### The four views

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
   python pipeline/build_spread.py        # The Spread  -> data/spread*.json
   python pipeline/build_pulse.py         # Pulse       -> data/pulse.json
   python pipeline/build_divergence.py    # Divergence  -> data/divergence.json
   python pipeline/build_mismatch.py      # Mismatch    -> data/mismatch.json
   ```
5. Serve the repo root and open the site:
   `python -m http.server 8000` then visit `http://localhost:8000/` (Pulse is the
   landing page).

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
- `pipeline/build_*.py` — one fetch+compute+write script per view
- `pipeline/test_metrics.py`, `pipeline/test_build.py` — offline unit tests
- `data/schema.md` — the JSON contract between pipeline and frontend
- `frontend/index.html` — Spread view; `frontend/{pulse,divergence,mismatch}.html` — the other views
- `frontend/util.js`, `frontend/styles.css` — shared frontend helpers and styles
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

## Data source

[ENTSO-E Transparency Platform](https://transparency.entsoe.eu) — the European
transmission operators' open data platform. A free API token is required to
re-run the pipeline; see the setup instructions above.
