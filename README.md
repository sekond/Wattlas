# Wattlas

A small web app exploring the temporal and financial side of European electricity
markets — starting with **The Spread**: how wide the daily gap is between the
cheapest and most expensive hour of power in Germany, and how often prices go negative.

This is a learning project. It deliberately ships one view, end to end, before
adding more.

## How it works

```
ENTSO-E API  →  pipeline/ (Python/pandas)  →  data/*.json  →  frontend/ (static JS)
```

The pipeline is the only thing that touches ENTSO-E. It pre-computes everything
into small JSON files committed to the repo, so the frontend is a static site
with no backend and nothing to break.

## Quick start

**Building it with Claude Code?** Open the project in Claude Code and just say
**"Follow RUN.md"**. Claude Code reads the prompts itself and works through the
build step by step, pausing for your approval before each step — you never
copy-paste prompts. Run `python bootstrap.py` first to check everything is in place.

**Just want to run it yourself?** Follow the steps below.

1. Get a free ENTSO-E API token: https://transparency.entsoe.eu (Account
   Settings → Web API Security Token).
2. `cp .env.example .env` and paste your token in.
3. Install deps: `pip install -r requirements.txt`
4. Build the data: `python pipeline/build_spread.py`
   (re-run offline from cache once fetched: `python pipeline/build_spread.py --use-cache`)
5. Serve the site from the repo root and open the frontend:
   `python -m http.server 8000` then visit `http://localhost:8000/frontend/index.html`

> The repo ships with sample data already in `data/`, so step 5 works before you
> ever run the pipeline — handy for trying the frontend first.

### Offline re-runs: the raw-price cache

Every normal build caches the raw fetched price series to
`data/_raw_prices.parquet` (gitignored). Re-run with `--use-cache` to rebuild the
JSON from that cache **without touching the ENTSO-E API** — useful for iterating
on the metrics or recovering from an API outage. The cache holds the raw,
pre-resample prices, so a cached rebuild produces identical output to the live
one. If no cache exists yet, run once without the flag to populate it.

## Tests

```
python pipeline/test_metrics.py
python pipeline/test_build.py
```

> **On the spread numbers:** TB1/TB2 are computed on hourly-averaged prices. The
> German market switched to quarter-hourly settlement in Oct 2025, where true
> intraday spreads are wider — so post-Oct figures are a *conservative lower
> bound*, not an overstatement.

Metric functions are pure and tested offline (DST days — both the 23-hour spring
and 25-hour autumn switch, the Oct-2025 hourly→quarter-hourly resolution break,
negative prices, data-gap days, TB2 fallback, empty input). `test_build.py` runs
the full `build()` against a fixture into a temp directory and asserts both JSON
files are written with schema-correct keys — all without network.

## Layout

- `CLAUDE.md` — instructions + domain landmines for Claude Code (read this first)
- `pipeline/metrics.py` — pure, testable metric computations
- `pipeline/build_spread.py` — fetch + orchestrate + write JSON
- `pipeline/test_metrics.py` — offline unit tests
- `data/schema.md` — the JSON contract between pipeline and frontend
- `frontend/index.html` — the static Spread view (Chart.js via CDN)
- `prompts/implementation_prompts.md` — sequenced prompts to take v1 to "real, tested, polished"

## A note on the arbitrage number

The "perfect-arbitrage revenue" figure is an **upper bound**, not achievable
revenue: it assumes perfect foresight and no losses. It is always labelled as
such in the UI. Real battery revenue is materially lower. Don't quote it as a
target.
