# Data contract — `/data` JSON shapes

The pipeline writes these files; the frontend reads them. If you change a shape, change it here in the same commit.

All prices are in EUR/MWh. All dates are ISO `YYYY-MM-DD` in the Europe/Berlin calendar.

---

## `spread.json`

One row per calendar day.

```json
{
  "zone": "DE_LU",
  "generated_at": "2026-05-29T10:00:00Z",
  "days": [
    {
      "date": "2025-07-02",
      "tb1": 487.0,            // max hourly price - min hourly price, that day
      "tb2": 421.5,            // mean(top 2 hours) - mean(bottom 2 hours)
      "min_price": -38.0,
      "max_price": 449.0,
      "mean_price": 64.2,
      "negative_hours": 6,     // count of hours with price < 0
      "hours_observed": 24,    // 23/24/25 depending on DST; <24 if data gaps
      "complete": true         // false if the day had missing hours
    }
  ]
}
```

## `spread_summary.json`

Pre-computed headline figures so the frontend does no aggregation.

```json
{
  "zone": "DE_LU",
  "period_start": "2025-06-01",
  "period_end": "2026-05-31",
  "avg_daily_tb1": 96.0,
  "widest_day": { "date": "2025-07-02", "tb1": 487.0 },
  "total_negative_hours": 412,
  "negative_hours_by_month": [
    { "month": "2025-06", "hours": 58 }
  ],
  "yoy_tb1_change_pct": 38.0,        // null if <2 years of data available
  "perfect_arbitrage_eur_per_mw": 118400.0,
  "perfect_arbitrage_is_upper_bound": true,   // ALWAYS true; frontend must surface the caveat
  "battery_assumptions": { "power_mw": 1, "duration_h": 2, "round_trip_efficiency": 1.0, "foresight": "perfect" },
  "missing_days": ["2025-09-14"]
}
```

## `pulse.json`

Powers the **Pulse** view: the average price shape across the hours of a local
day, split weekday vs weekend. Arrays are length 24, indexed by local hour 0–23
(Europe/Berlin). A slot is `null` if no data fell in that hour.

```json
{
  "zone": "DE_LU",
  "generated_at": "2026-06-03T10:00:00Z",
  "period_start": "2025-06-03",
  "period_end": "2026-06-03",
  "hours": [0, 1, 2, "…", 23],
  "all_mean":     [62.1, "…"],   // mean price across all days, per hour
  "weekday_mean": [58.4, "…"],   // Mon–Fri only
  "weekend_mean": [48.9, "…"]    // Sat–Sun only
}
```

Means are computed on hourly-resampled prices (landmine #3) grouped in local
time (landmine #4); negative averages are kept (landmine #6).

## `divergence.json`

Powers the **Divergence** view: monthly mean day-ahead prices for DE-LU and its
coupled neighbours, plus the DE-LU − FR spread. Arrays are aligned to `months`.
A slot is `null` if a zone has no data that month.

```json
{
  "zone": "DE_LU",
  "generated_at": "2026-06-03T10:00:00Z",
  "period_start": "2025-06-03",
  "period_end": "2026-06-03",
  "zones": ["DE_LU", "FR", "NL", "BE", "PL", "AT"],
  "months": ["2025-06", "2025-07", "…"],
  "series": { "DE_LU": [64.0, "…"], "FR": [41.8, "…"], "…": [] },
  "de_fr_spread": [22.3, "…"]   // DE_LU mean − FR mean, per month
}
```

## `mismatch.json`

Powers the **Mismatch** view: the hour-of-day profile of **residual load** for
DE-LU. Arrays are length 24 (local hour 0–23); a slot is `null` if no data fell
in that hour.

```json
{
  "zone": "DE_LU",
  "generated_at": "2026-06-03T10:00:00Z",
  "period_start": "2025-06-03",
  "period_end": "2026-06-02",
  "hours": [0, 1, "…", 23],
  "residual_load_gw": [33.1, "…"],   // total load - (wind onshore+offshore+solar), GW; MAY BE NEGATIVE
  "total_load_gw": [49.4, "…"]       // total actual load, GW
}
```

Both are computed on hourly-resampled data (landmine #3) grouped in local time
(landmine #4). `residual_load_gw` is **not clipped**: a negative value (renewables
exceeding domestic load) is a real, interesting signal (landmine #6). The
renewable contribution per hour is `total_load_gw − residual_load_gw`.

## `mix.json` (v2 — Phase 1)

Powers the **Mix** view: full generation breakdown by canonical fuel, per zone,
both as an average hour-of-day profile (GW) and a daily series (GW). Fuels use the
single canonical taxonomy in `pipeline/fuels.py` / `frontend/fuels.js`; a fuel is
always the same colour everywhere (landmine #9). Gaps are `null`, never faked.

```json
{
  "generated_at": "2026-06-09T13:00:00Z",
  "zone_default": "DE_LU",
  "zones_available": ["DE_LU", "FR", "NL", "BE", "PL", "AT"],
  "fuels": ["Nuclear", "Lignite", "Hard coal", "Gas", "…", "Solar", "Other"],
  "period_start": "2025-06-09",
  "period_end": "2026-06-08",
  "zones": {
    "DE_LU": {
      "period_start": "2025-06-09",
      "period_end": "2026-06-08",
      "hours": [0, 1, "…", 23],
      "profile_gw": { "Lignite": [8.1, "…"], "Solar": [0.0, "…"] },  // mean GW per local hour, per fuel
      "days": ["2025-06-09", "…"],
      "daily_gw": { "Lignite": [7.9, "…"], "Solar": [4.2, "…"] }       // mean GW per local day, per fuel
    }
  }
}
```

Values are average GW (MW/1000). A fuel slot is `null` where no data fell in that
hour/day; `daily_gw` arrays align to `days`, `profile_gw` arrays are length 24.

## `carbon.json` (v2 — Phase 5)

Powers the **carbon-intensity** overlay. NOT a new external source — computed from
the same ENTSO-E generation mix as `mix.json`, using fixed per-fuel emission
factors (`pipeline/fuels.py`). Methodology: **production-based**, IPCC AR5
lifecycle median factors; pumped-storage discharge excluded (landmine #12). State
the methodology in the UI.

```json
{
  "generated_at": "2026-06-09T13:00:00Z",
  "methodology": "Production-based, IPCC AR5 lifecycle median factors. …",
  "factors_gco2_kwh": { "Nuclear": 12, "Lignite": 820, "Gas": 490, "Solar": 45, "…": 0 },
  "zone_default": "DE_LU",
  "zones_available": ["DE_LU", "FR", "…"],
  "period_start": "2025-06-09",
  "period_end": "2026-06-08",
  "zones": {
    "DE_LU": {
      "period_start": "2025-06-09",
      "period_end": "2026-06-08",
      "hours": [0, 1, "…", 23],
      "intensity_profile": [410, "…"],          // gCO2eq/kWh per local hour (integer)
      "renewable_share_profile": [38.2, "…"],   // % per local hour
      "days": ["2025-06-09", "…"],
      "intensity_daily": [395, "…"],            // gCO2eq/kWh per local day (integer)
      "renewable_share_daily": [41.0, "…"]      // % per local day
    }
  }
}
```

Sanity: intensity falls as renewable share rises; France (nuclear) reads low.

## `flows.json` (v2 — Phase 2)

Powers the **flow + congestion** layer of Divergence. Net physical flow between
DE-LU and each neighbour, plus congestion where transmission capacity is known.

```json
{
  "generated_at": "2026-06-09T13:00:00Z",
  "home": "DE_LU",
  "borders": ["FR", "NL", "BE", "PL", "AT"],
  "months": ["2025-06", "…", "2026-05"],
  "flow_sign": "positive = DE-LU exporting to neighbour; negative = importing",
  "data": {
    "FR": {
      "net_flow_mw": [820.0, "…"],        // monthly mean net flow, MW (+ = DE-LU exporting)
      "congestion_pct": [12.4, "…"],      // % of hours flow ≥ ~90% of capacity; null where capacity unknown
      "capacity_available": true           // false for flow-based borders with no published NTC
    }
  }
}
```

Direction matters (landmine #10): `net_flow_mw` is DE-LU export minus import.
`congestion_pct` is `null` (and `capacity_available: false`) for the flow-based
western borders (FR/NL/BE via CWE/Core), which publish no explicit day-ahead NTC —
render "no capacity data", never error. Arrays align to `months`.

## `spread_by_zone.json` / `pulse_by_zone.json` (v2 — Phase 3)

Per-zone Spread and Pulse for the dashboard's zone selector, computed offline from
the cached multi-zone prices (`build_zone_views.py`). Same metrics as the DE-LU
`spread.json` / `pulse.json`, keyed by zone.

```json
// spread_by_zone.json
{ "zone_default": "DE_LU", "zones_available": ["DE_LU","FR","…"],
  "period_start": "2025-06-09", "period_end": "2026-06-08",
  "zones": { "DE_LU": {
    "days": [{ "date": "2025-07-02", "tb1": 487.0, "tb2": 421.5, "negative_hours": 6, "complete": true }],
    "summary": { "avg_daily_tb1": 96.0, "total_negative_hours": 412,
                 "perfect_arbitrage_eur_per_mw": 118400.0, "perfect_arbitrage_is_upper_bound": true } } } }

// pulse_by_zone.json
{ "zones": { "DE_LU": { "hours": [0,"…",23], "all_mean": [...], "weekday_mean": [...], "weekend_mean": [...] } } }
```

## `mismatch_by_zone.json` (v2 — per-zone Mismatch for the dashboard)

Zone-keyed residual-load + total-demand hour-of-day profiles (GW), powering the
dashboard's zone-aware Mismatch panel. Built by `build_mismatch_zones.py`:
wind+solar from the per-zone generation cache (`_raw_generation_{zone}.parquet`)
minus per-zone `query_load`. The standalone Mismatch page keeps using the
DE-LU-only `mismatch.json`. Residual is NOT clipped (can be negative). All zones
grouped in Europe/Berlin local time (Central European).

```json
{ "zone_default": "DE_LU", "zones_available": ["DE_LU","FR","NL","BE","PL","AT"],
  "period_start": "2025-06-10", "period_end": "2026-06-09",
  "zones": { "DE_LU": {
    "hours": [0,"…",23],
    "residual_load_gw": [18.2,"…"],   // demand − wind − solar, GW; may be negative
    "total_load_gw": [49.4,"…"] } } }
```

## `spread_history.json` (v2 — Phase 6)

Multi-year DE-LU daily spread for the Time-investigation view, plus monthly,
yearly and seasonal (month-of-year) aggregates and the YoY TB1 change.

```json
{
  "zone": "DE_LU",
  "period_start": "2023-06-09", "period_end": "2026-06-08",
  "years_covered": [2023, 2024, 2025, 2026],
  "days":     [{ "date": "2023-06-09", "tb1": 88.0, "neg": 0 }],   // zoomable daily series
  "monthly":  [{ "month": "2023-06", "avg_tb1": 92.0 }],
  "yearly":   [{ "year": "2023", "avg_tb1": 110.0, "neg_hours": 240 }],
  "seasonal": [{ "month": 1, "avg_tb1": 70.0 }],                   // month-of-year 1-12, all years folded
  "negative_hours_by_month": [{ "month": "2023-06", "hours": 12 }],
  "yoy_tb1_change_pct": -5.2                                       // last 12mo vs prior 12mo; null if <24mo
}
```

## `curtailment.json` (v2 — Phase 4, NEW SOURCE — currently unavailable)

Curtailed/redispatched renewable energy per day (German grid). **Source blocked on
credentials** (see `pipeline/build_curtailment.py`): SMARD's JSON API does not
expose curtailment; the netztransparenz WebAPI needs OAuth credentials. Until then
this file carries `status: "unavailable"` and an empty `days` array — the frontend
renders an explicit "awaiting source" state rather than fabricating data.

```json
// unavailable state (no fabricated data)
{ "source": "netztransparenz.de WebAPI (OAuth2 client-credentials required)",
  "units": "MWh per day", "status": "unavailable", "reason": "…", "days": [] }

// populated state (once credentials are added)
{ "source": "netztransparenz.de redispatch …", "units": "MWh per day",
  "period_start": "2024-06-01", "period_end": "2026-06-01",
  "days": [{ "date": "2024-06-01", "curtailed_mwh": 12450.0 }] }
```

Units are **MWh/day** (validate on first real fetch, landmine #12). Isolated
pipeline module (landmine #11): no shared code with the ENTSO-E builders.

## `de_capacity_by_landkreis.json` (v3 — Wasted-wind Panel 1, NEW SOURCE: MaStR)

Installed wind/solar capacity per German Landkreis, from the
Marktstammdatenregister (`pipeline/build_mastr_capacity.py`, isolated module —
landmine #11). **Aggregates only** (MaStR is millions of units — never commit raw
points). Capacity is **installed MW, not energy** (frontend caption, copy block D).
`Nettonennleistung` is kW in the source; converted to **MW** here (landmine #12).

```json
{
  "generated_at": "2026-06-22T08:00:00Z",
  "source": "MaStR (Bundesnetzagentur)",
  "unit": "MW",
  "metric": "installed net nominal capacity",
  "national_mw": { "wind_onshore_mw": 70000, "wind_offshore_mw": 10400, "solar_mw": 110500 },
  "landkreise": [
    { "ags": "01060", "nuts_id": "DEF0E", "name": "Segeberg",
      "wind_onshore_mw": 412, "wind_offshore_mw": 0, "solar_mw": 388 }
    // ~400 entries, one per Kreis
  ]
}
```

`national_mw` is the country total per fuel (rounded MW), **including offshore wind**
— which has no Landkreis (EEZ) and so appears here but not in `landkreise`. Lets the
frontend show the offshore figure and avoid summing 400 rows.

`ags` is the 5-digit Kreisschlüssel (AGS first 5). `nuts_id` is the **join key to the
basemap** (`frontend/geo/landkreise.topo.json`, keyed by `NUTS_ID`); the mapping
lives in `pipeline/de_kreis_nuts.json` (Eurostat LAU↔NUTS, built once, static — see
its `overrides` for the Eisenach/Wartburgkreis NUTS-2021 case). Wind onshore/offshore
are **separate metrics, never summed with solar**. Offshore wind sits in the Exclusive
Economic Zone (no Landkreis), so `wind_offshore_mw` is ~0 for land Kreise — offshore
capacity shows in the national total and the top-20 points, not the choropleth. All
values rounded.

## `de_top_plants.json` (v3 — Wasted-wind Panel 1)

The 20 largest individual wind/solar units (by MW) with coordinates, plotted as map
points. Coordinates are public for utility-scale units (≥30 kW).

```json
{
  "generated_at": "2026-06-22T08:00:00Z",
  "source": "MaStR (Bundesnetzagentur)",
  "unit": "MW",
  "plants": [
    { "name": "…", "fuel": "Wind offshore", "mw": 0.0,
      "lat": 0.0, "lon": 0.0, "landkreis": "…" }
    // 20 entries, largest first
  ]
}
```

`fuel` is a canonical fuel (use `frontend/fuels.js` colours). `landkreis` may be
`null` for offshore units at sea.

## `de_regional_balance.json` (v3 — Wasted-wind Panel 2, NEW SOURCE: SMARD)

Per-control-area **net balance = generation − load** per day, from SMARD
(`pipeline/build_regional_balance.py`, isolated module). Evidence for the intra-zone
north–south bottleneck (which appears in **no** ENTSO-E flow or zonal price — there is
no public inter-TSO MW flow series; do not fabricate one). SMARD day-resolution values
are **MWh/day**; converted to **average GW** (÷24h ÷1000), aggregated by SMARD in
German local time (DST handled at source). Missing series (e.g. Nuclear post-2023, no
offshore in inland Amprion, no lignite in TransnetBW) render as gaps, never zeros.

```json
{
  "generated_at": "2026-06-22T09:00:00Z",
  "source": "SMARD (Bundesnetzagentur) — Realisierte Erzeugung & Netzlast",
  "unit": "GW",
  "areas": ["50Hertz", "TenneT", "Amprion", "TransnetBW"],
  "days": [
    { "date": "2026-06-21",
      "generation_gw": { "50Hertz": 11.9, "TenneT": 12.87, "Amprion": 11.14, "TransnetBW": 5.16 },
      "load_gw":       { "50Hertz": 9.66, "TenneT": 12.63, "Amprion": 15.77, "TransnetBW": 5.61 },
      "balance_gw":    { "50Hertz": 2.24, "TenneT": 0.24, "Amprion": -4.63, "TransnetBW": -0.45 } }
    // ~365 entries, one per day
  ]
}
```

`balance_gw[area]` = `generation_gw[area] − load_gw[area]`. North areas (50Hertz,
TenneT) run structurally **positive** (surplus), south/west (Amprion, TransnetBW)
**negative** (deficit). An area absent from a day's dicts is a gap. The Panel-2
redispatch overlay reuses `curtailment.json` (degrades to "awaiting source" if absent).

### Frontend obligations
- Render `perfect_arbitrage_eur_per_mw` only alongside a visible caveat that it is an unachievable upper bound (see CLAUDE.md landmine #7).
- Treat `complete: false` days distinctly (e.g. muted) and never break if `days` has gaps.
- Round every number before display.
- For `mix`/`carbon`, use the canonical fuel palette (`frontend/fuels.js`); render `null` fuel/hour slots as gaps, never zeros. Show the carbon methodology label.
- For `flows`, show flow direction explicitly and render "no capacity data" where `capacity_available` is false.
- For `de_capacity_by_landkreis`, join to the basemap on `nuts_id`; render Kreise with no entry as a distinct "no data" colour (not zero); caption the map as installed *capacity*, not output (copy block D). Wind and solar are separate toggled metrics.
