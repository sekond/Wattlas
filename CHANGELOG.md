# Changelog

All notable changes to Wattlas. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); dates are UTC.

## [1.0.0] — 2026-06-10

First tagged release. A static, pre-computed site (Python/pandas pipeline →
`data/*.json` → vanilla-JS + Chart.js frontend → GitHub Pages) exploring the
temporal and financial dimensions of European electricity markets, centred on the
DE-LU bidding zone and its neighbours (FR, NL, BE, PL, AT). No backend, no
database, no browser storage.

### Views
- **Pulse** — average day-ahead price by hour of day (weekday vs weekend).
- **Spread** — daily cheapest↔priciest gap (TB1), negative-price days, and an
  explicitly-labelled upper-bound battery-arbitrage figure.
- **Divergence** — monthly price by bidding zone, the DE-FR gap, **plus physical
  cross-border flows and congestion** (flagged where flow nears transmission
  capacity; "no data" shown for flow-based borders that publish no NTC).
- **Mismatch** — residual load (demand − wind − solar) by hour of day, **per zone**.
- **Mix** — full generation breakdown by fuel for each zone, with two-zone
  comparison and a single canonical fuel-colour palette.
- **Carbon** — production-based grid carbon intensity (IPCC AR5 lifecycle factors)
  computed from the generation mix; falls as renewable share rises.
- **Curtailment** — wasted renewable energy from the German TSOs'
  netztransparenz.de redispatch API, via an isolated pipeline module; degrades to
  an honest "awaiting source" state if its credentials are absent.
- **History** — multi-year daily spread with drag-to-zoom, a seasonal
  (month-of-year) fold, and a real year-on-year trend.
- **Dashboard** (landing page) — sidebar-navigated, story-driven layout unifying
  all eight views: multi-zone comparison (up to six), a date-range brush with
  presets, linked hover crosshair, data-computed headlines, and a phone-native
  bottom-tab layout on mobile.

### Pipeline
- One `build_*.py` per view writing pre-aggregated JSON to `data/` (committed, so
  the site works before the pipeline is ever run). Pure, offline-testable metric
  functions in `pipeline/metrics.py`.
- Per-zone generation, carbon, flows, multi-year history, per-zone Spread/Pulse,
  and per-zone Mismatch builders added in the v2 expansion.
- A daily GitHub Action (`refresh-data.yml`, 05:17 UTC) re-runs every builder and
  commits refreshed JSON; GitHub Pages redeploys automatically.

### Correctness & honesty
- Mixed hourly/quarter-hourly data (Germany's Oct-2025 settlement change) resampled
  to a single hourly grid; spreads are labelled a **conservative lower bound**.
- All grouping in local time (Europe/Berlin), including 23- and 25-hour DST days.
- Negative prices and negative residual load kept, never clipped; data gaps render
  as gaps, never fabricated zeros.
- The arbitrage figure is always labelled an unachievable **upper bound**; carbon
  intensity states its production-based, lifecycle methodology.

### Release housekeeping
- `.gitignore` hardened (secrets, Python caches, raw-data parquet, OS/editor cruft).
- The design-handoff bundle moved to `design-archive/` (reference only).
- README reconciled with the shipped views, scripts, and structure; this changelog added.
