# Data contract — `/data` JSON shapes

The pipeline writes these files; the frontend reads them. If you change a shape, change it here in the same commit.

All prices are in EUR/MWh. All dates are ISO `YYYY-MM-DD` in the Europe/Berlin calendar.

---

## `last_updated.json`

A tiny meta file (not a view). Records the most recent `generated_at` across all
other `data/*.json`, written by `pipeline/build_last_updated.py` at the end of the
daily refresh (reads committed JSON only, no network). The frontend (`nav.js`)
fetches it to show a site-wide "Data updated &lt;date&gt;" footer stamp that tracks
the refresh automatically.

```json
{
  "generated_at": "2026-06-29T07:10:55+00:00",  // max generated_at across data/*.json
  "sources_counted": 33,                          // files that carried a generated_at
  "note": "…"
}
```

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

The largest wind and solar installations as map points, **per fuel** so the choropleth's
wind/solar toggle can swap them. MaStR registers wind per turbine, so units are grouped
into ~0.15° cells (an offshore farm's turbines collapse to one point) and the top 12 cells
per fuel are kept — sized by total MW, coloured by canonical fuel.

```json
{
  "generated_at": "2026-06-23T08:00:00Z",
  "source": "MaStR (Bundesnetzagentur)",
  "unit": "MW",
  "wind":  [ { "name": "Offshore", "fuel": "Wind offshore", "mw": 758, "units": 133, "lat": 54.456, "lon": 7.677 } ],
  "solar": [ { "name": "Leipzig",  "fuel": "Solar",         "mw": 519, "units": 140, "lat": 51.156, "lon": 12.469 } ]
  // 12 clusters per fuel, largest first
}
```

`fuel` is a canonical fuel (use `frontend/fuels.js` colours: offshore wind is darker than
onshore). `name` is the Landkreis (or `"Offshore"` at sea); `units` is how many MaStR
units the cluster aggregates. The frontend plots `wind` on the wind view and `solar` on
the solar view, re-drawing on toggle.

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

## `fr_nuclear_sites.json` (v4 — France-nuclear Panel 1)

The geocoded French nuclear fleet, from `pipeline/build_fr_nuclear_sites.py` (committed,
attributed source list — the fleet is small and stable). Net capacity in **MW**.
Operating sites only (Fessenheim excluded; **Flamanville-3 EPR included** → 18 sites /
57 reactors / ~63 GW; confirm against a live source — the count drifts).

```json
{
  "generated_at": "2026-06-22T13:00:00Z",
  "source": "Public site data / RTE / IAEA PRIS (compiled), net MW",
  "as_of": "2025",
  "unit": "MW",
  "fleet_total": { "sites": 18, "reactors": 57, "capacity_mw": 63010 },
  "sites": [
    { "name": "Gravelines", "region": "Hauts-de-France", "nuts_id": "FRE",
      "reactors": 6, "capacity_mw": 5460, "water": "coast", "lat": 51.015, "lon": 2.136 }
    // 18 entries, largest capacity first
  ]
}
```

`nuts_id` is the NUTS-1 région code (basemap join key, via `fr_fields`). `water` is one
of `river` / `coast` / `estuary`. Sites plot as points by `lat`/`lon` (canonical
`Nuclear` colour), sized by `capacity_mw`. All values rounded.

## `fr_regional.json` (v4 — France-nuclear Panel 2, NEW SOURCE: éCO2mix régional)

Per-région net balance (generation − consumption) from **RTE éCO2mix régional via ODRÉ**
(`pipeline/build_fr_regional.py`, isolated module). 12-month averages in **GW**.
`net_balance = −ech_physiques` (the published physical-exchange *solde*) — France is one
bidding zone, so this is a **physical** balance, not a regional price (no fabricated
inter-régional flow). **Corse** (non-interconnected zone) is absent from éCO2mix régional
→ it has no entry and renders as "no data".

```json
{
  "generated_at": "2026-06-22T13:00:00Z",
  "source": "RTE éCO2mix régional via ODRÉ (Opendatasoft)",
  "unit": "GW",
  "period_start": "2025-01-31", "period_end": "2026-01-31",
  "regions": [
    { "nuts_id": "FRB", "name": "Centre-Val de Loire", "insee": "24",
      "nuclear_gw": 7.8, "generation_gw": 8.5, "consumption_gw": 2.0, "net_balance_gw": 6.48 }
    // ~12 entries (Corse absent), sorted exporter → importer
  ]
}
```

`net_balance_gw[region] = generation_gw − consumption_gw`. Positive = net **exporter**
(nuclear-dense régions: Centre-Val de Loire, Auvergne-Rhône-Alpes, Normandie, Grand Est),
negative = net **importer** (Île-de-France most negative). Join to the basemap on
`nuts_id`; a région with no entry (Corse) is a gap, not zero.

## `fr_nuclear_availability.json` (v4 — France-nuclear Panel 3)

Monthly national generation mix + demand from **éCO2mix national via ODRÉ**
(`pipeline/build_fr_nuclear_availability.py`, isolated). `nuclear_gw` is **output** (how
much the fleet generated). `available_gw` is the nuclear **available capacity** (how much
it *could* generate) — a declared **upper bound** on producible power, never actual
generation. It is computed as installed nuclear capacity − mean declared unavailability
from the **RTE Data Portal "Unavailability Additional Information" v6** feed (OAuth2;
`RTE_CLIENT_ID`/`RTE_CLIENT_SECRET`), time-weighted per calendar month in Europe/Paris.
When those credentials are absent or the app isn't subscribed to that API, `available_gw`
is **null** and the view degrades to output only (see memory `rte-oauth-pending`). Values GW.

```json
{
  "generated_at": "2026-06-22T13:00:00Z",
  "source": "RTE éCO2mix national via ODRÉ (output) + RTE Data Portal Unavailability Additional Information v6 (available capacity, OAuth2)",
  "unit": "GW",
  "installed_nuclear_gw": 63.0,
  "available_note": "available_gw = installed nuclear − mean declared unavailability (RTE OAuth feed); a declared upper-bound, not actual generation. Null when credentials/subscription absent (degraded to output).",
  "period_start": "2024-02", "period_end": "2026-01",
  "months": [
    { "month": "2025-05", "nuclear_gw": 34.3, "hydro_gw": 7.5, "gas_gw": 0.4,
      "wind_gw": 4.6, "solar_gw": 4.9, "other_gw": 1.0, "demand_gw": 41.9,
      "net_export_gw": 10.0, "available_gw": 48.7 }
    // available_gw is null when the RTE OAuth feed is unavailable. ~24 months, chronological.
  ]
}
```

`net_export_gw` = −`ech_physiques` (**+ = France exporting**). Honest framing: nuclear
output dips spring/summer (maintenance, in low-demand months by design), yet
`net_export_gw` stays **positive every month** — France exports even during the dip;
imports do **not** fill the gap at monthly resolution. Heatwave river-cooling derations
are event-scale (not monthly) — annotate, never fabricate. No alarmist framing.

## `fr_costs.json` (v4 — France-nuclear Panel 4)

Curated €/MWh cost comparison from `pipeline/build_fr_costs.py`. **NOT a live feed** —
transcribed from published studies (Lazard, Cour des comptes, ANDRA/Cigéo, OECD-NEA,
IRENA), committed static. The hidden-cost lens is applied **symmetrically** to every
technology (waste & decommissioning, system & integration, implicit support) — never
nuclear alone; nuclear's back-end is provisioned, not ignored. Each technology carries a
**range** and **sources**; central values are illustrative.

```json
{
  "generated_at": "2026-06-23T08:00:00Z",
  "source": "Curated published estimates (not a live feed)",
  "unit": "EUR/MWh",
  "components": [ { "key": "plant", "label": "Plant (LCOE)", "color": "#4a78a6" }, … ],
  "technologies": [
    { "name": "Solar (utility)", "plant": 55, "waste": 1, "system": 18, "support": 3,
      "sticker_range": [40, 65], "full_range": [60, 100],
      "sources": ["Lazard LCOE+ 2024", "OECD-NEA system costs", "IRENA"] }
    // 4 technologies: utility solar, onshore wind, existing fleet, new-build EPR2
  ],
  "takeaways": { "sticker": "…", "full": "…" },
  "sources": ["Lazard LCOE+ 2024", "Cour des comptes (EPR/EPR2)", …]
}
```

The frontend stacks the four components per technology; the **"sticker price"** toggle
shows `plant` only, **"full system cost"** stacks all adders on every technology; the
matching `takeaways` string is shown. `full_range` ⊇ the sum of components (validated in
the builder). Copy block E and the per-technology sources/ranges are shown verbatim;
framing is symmetric and non-advocacy.

## `nordic_prices.json` (v5 — Nordic price-zones slice)

Day-ahead prices for the **12 Nordic bidding zones** (Sweden SE1–SE4, Norway
NO1–NO5, Denmark DK1–DK2, Finland FI), from `pipeline/build_nordic_zones.py` (its
own builder — landmine #11 — reusing the shared ENTSO-E client + `metrics.py`, not
entangled with `build_spread`/`build_divergence`). Powers `nordic_zones.html`
Panels 1–2. Zone EIC codes are from entsoe-py's `Area` enum; each zone is grouped
in its **own** local calendar (SE/NO/DK are CET, FI is EET/+1h — landmine #4).

```json
{
  "generated_at": "2026-06-24T08:00:00Z",
  "unit": "EUR/MWh",
  "note": "Day-ahead prices per bidding zone (ENTSO-E). Nordic prices are heavily hydro/reservoir- and weather-driven … within_country_gap is the spread between a country's dearest and cheapest zone per month (max - min).",
  "period_start": "2025-06-24",
  "period_end": "2026-06-23",
  "months": ["2025-06", "2025-07", "…", "2026-06"],
  "zones": [
    { "code": "SE4", "country": "SE", "name": "South (SE4)",
      "avg_price": 78.0,                 // mean over the period, EUR/MWh (1 dp); null if no data
      "months": [78.12, 80.4, "…"] }     // monthly mean aligned to top-level `months`; null where missing
    // 12 entries, one per zone
  ],
  "within_country_gap": {
    "SE": { "months": [12.3, "…"], "avg_gap": 14.0 },   // max - min across a country's zones, per month
    "NO": { "months": [], "avg_gap": 0 },
    "DK": { "months": [], "avg_gap": 0 }
    // FI omitted — single zone, no within-country gap
  }
}
```

`code` is the **join key** shared with `frontend/geo/nordic_zones.topo.json`
(`props.code`) and is a bidding-zone code, *not* a NUTS code. `avg_price` and the
`within_country_gap` series are rounded to 1 dp; per-zone `months` carry the 2-dp
`monthly_means` value. Gaps are **null**, never zero: a zone with no data, or a
month a zone didn't report, is `null`; `within_country_gap` is `null` for any month
fewer than two of a country's zones reported (landmine #8). `period_start/end`
reflect real coverage (complete local days only). **Hydro caveat:** Nordic
divergence reflects wet/dry reservoir years as well as grid congestion — the
frontend surfaces this so decoupling isn't misread as congestion alone.

## `uk_regional_carbon.json` (v6 — UK regional slice)

Per-region grid carbon intensity (gCO2/kWh) + generation mix for the 14 GB DNO
regions, from `pipeline/build_uk_regional_carbon.py` (isolated module — landmine #11;
NESO Carbon Intensity API, open/no key). Powers `uk_regional.html` Panel 1.

```json
{
  "generated_at": "2026-06-24T08:00:00Z",
  "unit": "gCO2/kWh",
  "methodology": "NESO regional Carbon Intensity API, consumption-based … Great Britain only — excludes Northern Ireland. Regional values are forecast-based; means over a recent ~2-week window. renewable_pct = wind + solar + hydro.",
  "basis": "forecast",
  "period_start": "2026-06-10", "period_end": "2026-06-23",
  "regions": [
    { "regionid": 1, "name": "North Scotland",
      "intensity": 8,                 // mean gCO2/kWh (integer); null if no data
      "renewable_pct": 78.0,          // wind + solar + hydro
      "low_carbon_pct": 80.0,         // + nuclear
      "mix": { "wind": 70.0, "hydro": 6.0, "gas": 4.0, "imports": 12.0, "…": 0 } }  // mean % per fuel
    // 14 entries, one per region (regionid 1-14)
  ]
}
```

`regionid` (1–14) is the **join key** to `frontend/geo/uk_dno.topo.json`
(`props.regionid`). **Consumption-based** (the carbon of electricity *used* in a region,
imports included) — do **not** mix with the site's production-based `carbon.json` view;
the methodology is stated (landmine #12). **GB only** — Northern Ireland excluded
(all-island SEM). Regional intensity is **forecast** (wind-dominated northern regions can
read near zero). Gaps are `null`, never zero.

## `uk_constraints.json` (v6 — UK regional slice, Panel 2)

Monthly **thermal-constraint cost (£m) and volume (GWh)** for Great Britain, from
`pipeline/build_uk_constraints.py` (isolated module — landmine #11; NESO "Constraint
Breakdown" open data). Powers `uk_regional.html` Panel 2.

```json
{
  "generated_at": "2026-06-24T08:00:00Z",
  "currency": "GBP", "status": "ok",
  "unit_cost": "GBP million", "unit_volume": "GWh",
  "source": "NESO Constraint Breakdown — Thermal constraints (open data portal)",
  "note": "Thermal-constraint cost and volume … the dominant thermal constraint is the B6 Scotland-England boundary … turning Scottish wind down and replacement up — a managed grid-stability cost, not energy discarded by choice. Volume is the thermal balancing-action volume, not pure curtailed-wind GWh.",
  "period_start": "2022-04", "period_end": "2026-06",
  "totals": { "cost_gbp_m": 0, "volume_gwh": 0, "peak_month": "YYYY-MM", "peak_cost_gbp_m": 0 },
  "months": [ { "month": "2025-01", "cost_gbp_m": 0, "volume_gwh": 0 } ]
}
```

**Methodology (landmine #12).** This is the **thermal**-constraint cost/volume (the
B6 Scotland–England boundary dominates it) — overwhelmingly the cost of turning Scottish
wind **down** and replacement generation **up**. It is a *managed grid-stability cost*,
the British equivalent of German redispatch — **not** energy discarded by choice, and the
volume is the **balancing-action volume**, not pure curtailed-wind GWh (so the frontend
labels it "constraint cost/volume", not "wasted wind"). Currency **GBP** (millions);
volume MWh→**GWh**; **Great Britain**. NESO revises these figures over time.

**Degraded state.** If the NESO source is unavailable at build time the file carries
`"status": "unavailable"` and an empty `months` array; the frontend renders an
"awaiting source" state and never fabricates data.

## `storage.json` (v9 — Storage slice)

A transparent battery-arbitrage model over real day-ahead prices + a curated storage-
capacity series, from `pipeline/build_storage.py` (**pure** — reads committed `pulse.json`
+ `spread.json`, no network). Powers `storage.html`.

```json
{
  "generated_at": "…", "zone": "DE_LU",
  "currency": "EUR", "unit_power": "MW (power)", "unit_energy": "MWh (energy)",
  "battery": { "power_mw": 1, "duration_h": 2, "round_trip": 0.85, "foresight": "perfect (upper bound)" },
  "note": "Captured-arbitrage figures are an UPPER BOUND (perfect foresight, 85% round-trip) …",
  "day": {
    "hours": [0, "…", 23], "price": [93.2, "…"],          // avg 24h price profile (pulse.json)
    "charge_mw": [0, "…", -1, "…"],                        // −power in the cheapest `duration_h` hours
    "discharge_mw": [0, "…", 0.85, "…"],                  // +power×round_trip in the dearest hours
    "charge_hours": [12, 13], "discharge_hours": [19, 20],
    "captured_eur": 134.0                                 // € per cycle for THIS battery, UPPER BOUND
  },
  "spread": {
    "mean_tb2_eur_mwh": 117.3,                            // mean daily 2-hour spread (spread.json TB2)
    "period_start": "2025-06-23", "period_end": "2026-06-22",
    "monthly_tb2": [ { "month": "2025-06", "mean_tb2": 0 } ]
  },
  "capacity": [ { "country": "GB", "year": 2025, "power_gw": 5.9 } ],   // curated, approximate, GW power
  "capacity_note": "Curated from published market reports … operational grid-scale POWER (GW) …",
  "eu_energy_gwh": [ { "year": 2025, "gwh": 77 } ]        // cumulative EU battery energy (sourced)
}
```

**Upper bound (landmine #7):** `captured_eur` and `mean_tb2_eur_mwh` assume perfect
foresight + a stated round-trip — never present them as achievable revenue (the frontend
carries copy block A). **MW vs MWh** are distinct and labelled (`unit_power`/`unit_energy`).
The **capacity** series is **curated/approximate** (aggregates only, GW power; energy
differs by duration) — not a live registry pull. Cannibalisation (more storage flattens
the spread) is noted, never implied linear.

## `dunkelflaute.json` (v7 — Dunkelflaute slice)

Low-renewable spell detection for DE-LU, from `pipeline/build_dunkelflaute.py` (reuses
the ENTSO-E generation/load/price pipeline). Powers `dunkelflaute.html`.

```json
{
  "generated_at": "…", "zone": "DE_LU",
  "threshold_pct": 10, "min_spell_hours": 24, "roll_window_h": 24,
  "unit": "GW (generation/imports), EUR/MWh (price)",
  "note": "Detected where the 24h rolling mean of the wind+solar share of demand stays below the threshold … threshold is a defined, adjustable choice … net imports = load − generation.",
  "period_start": "2025-06-23", "period_end": "2026-06-22",
  "worst_event": {
    "start": "…", "end": "…", "spell_start": "…", "spell_end": "…",
    "hours": ["ISO", "…"],
    "wind": [0.1, "…"], "solar": [], "gas": [], "coal": [], "nuclear": [], "hydro": [], "biomass": [],
    "imports": [2.1, "…"],            // net imports (GW); can be negative (exporting)
    "price": [178.5, "…"], "demand": [],
    "min_vre_pct": 1.5, "peak_price": 178.5
  },
  "spells": [ { "start": "…", "hours": 52, "min_vre_pct": 1.5 } ],
  "monthly": [ { "month": "2025-11", "low_hours": 73 } ],      // raw hours below threshold per month
  "summary": { "spell_count": 1, "spell_hours_year": 52, "longest_spell_h": 52,
               "low_vre_hours_year": 510, "threshold_pct": 10 },
  "mix": { "dunkelflaute": { "wind": 4.7, "coal": 41.0, "gas": 31.0, "net_import_pct": 17.1 },
           "normal": { "…": 0 } }                              // % of generation + net-import %
}
```

The **threshold is a stated, adjustable choice** (landmine in the spec), not a law —
surfaced in the UI. Generation values are **GW** (MW/1000); price **EUR/MWh**. Net
imports close the demand balance (`load − generation`, positive = importing), never
double-counted. Gaps stay `null`. Framing is the engineering reality, not anti-renewable
(copy block A).

## `iberian_blackout.json` (v8 — Iberian blackout slice, HISTORICAL — no daily refresh)

The fixed ES/PT load window around **28 April 2025** + sourced restoration milestones,
from `pipeline/build_iberian_blackout.py` (a one-off historical pull). Powers
`iberian_blackout.html`. **Sober, factual; no asserted cause.**

```json
{
  "generated_at": "…", "event_date": "2025-04-28", "zones": ["ES", "PT"],
  "tz": "Europe/Madrid (CEST)", "resolution": "hourly",
  "note": "… Spain's metered load is largely missing through the outage (reporting went down) — shown as a gap; Portugal's load fell to near zero … does not assert a cause.",
  "sources": [ { "label": "ENTSO-E …", "url": "https://www.entsoe.eu/…" } ],
  "timeline": [ { "t": "ISO (CEST)", "es_load_gw": 24.9, "pt_load_gw": 0.09 } ],   // gaps stay null
  "milestones": [ { "t": "2025-04-28T12:33:00", "label": "Grid collapse — …" } ],   // sourced, CEST
  "official": { "report": "ENTSO-E Expert Panel — Final Report …", "published": "2026-03-20",
                "conclusion": "… a combination of many interacting factors … not a single cause or technology",
                "quote": "The problem is not renewable energy, but voltage control …",
                "report_url": "https://www.entsoe.eu/news/2026/03/20/…" },
  "summary": { "pre_event_load_gw": { "ES": 27.5, "PT": 5.9 },
               "trough_load_gw": { "ES": null, "PT": 0.09 },
               "official_loss": "Spain lost ~60% of generation — a sudden ~15 GW drop", "restoration": "…" }
}
```

**Cause is CITED, never asserted** (landmine): the `official` block links the ENTSO-E
final report and carries the non-blame quote; there is **no** top-level Wattlas cause
field. Figures around the outage are **provisional/revised** — labelled. Times **CEST**
(Madrid). Spain's load gap renders as a gap, Portugal's collapse as recorded. Not in the
daily refresh — a fixed historical window.

## `capture_price.json` (v10 — Value Layer slice 1, no new source)

Per-zone, per-renewable-group generation-weighted **capture price**, time-weighted
**baseload**, **value factor** (capture/baseload) and **negative-price generation
share**, overall and by local month. Built offline from the generation cache
(build_mix) and the zone-price cache (build_divergence); generation and price are
resampled to one canonical hourly resolution **before weighting** (landmine #3).

```json
{
  "generated_at": "…", "zone_default": "DE_LU", "zones_available": ["DE_LU", "FR", …],
  "source": "ENTSO-E generation + day-ahead prices",
  "method": "generation-weighted capture price / time-weighted baseload (value factor)",
  "groups": { "solar": ["Solar"], "wind": ["Wind onshore", "Wind offshore"] },
  "context_note": "Anchor figures (…50-60%…16%…573h, 2025) are cited context, not computed here.",
  "zones": { "DE_LU": {
      "solar": { "capture": 48.3, "baseload": 87.6, "value_factor": 0.552, "neg_gen_share": 20.6,
                 "monthly": [ { "month": "2025-07", "capture": …, "baseload": …, "value_factor": …, "neg_gen_share": … } ] },
      "wind":  { "capture": …, "baseload": …, "value_factor": 0.885, "neg_gen_share": …, "monthly": [ … ] } } }
}
```

`value_factor` < 1.0 = the fuel earns less than baseload (cannibalization). capture/
baseload €/MWh, value_factor dimensionless, neg_gen_share percent. Negative prices kept
(landmine #6). Anchors are cited 2025 context, not these computed values.

## `negative_prices.json` (v10 — Value Layer slice 2, no new source)

Per-zone negative-price metrics from the zone-price cache: hours per month, a
date→count calendar, and episode (consecutive-negative-hour run-length) duration.
Counting is on the canonical hourly grid (landmine #3); days/months local-tz.

```json
{
  "generated_at": "…", "zone_default": "DE_LU", "zones_available": ["DE_LU", …],
  "source": "ENTSO-E day-ahead prices",
  "zones": { "DE_LU": {
      "period_start": "…", "period_end": "…",
      "total_neg_hours": 494, "longest_episode_h": 20, "max_in_one_day": 16,
      "by_month": [ { "month": "2025-07", "neg_hours": 64 } ],
      "calendar": [ { "date": "2025-07-06", "neg_hours": 7 } ],
      "episodes": [ { "length_hours": 1, "count": 142 }, { "length_hours": 2, "count": 96 } ] } }
}
```

## `flex_savings.json` (v10 — Value Layer slice 3, no new source)

Per-zone dynamic-tariff savings for shiftable-load presets, from the zone-price cache.
**UPPER BOUND** (landmine #7): assumes perfect foresight of the cheapest hours, like the
battery model — the frontend MUST label it so. Prices €/MWh; flat tariff = period mean.

```json
{
  "generated_at": "…", "zone_default": "DE_LU", "zones_available": ["DE_LU", …],
  "source": "ENTSO-E day-ahead prices", "flat_tariff": "period mean price",
  "perfect_foresight_is_upper_bound": true,
  "zones": { "DE_LU": {
      "period_start": "…", "period_end": "…",
      "presets": [ { "name": "EV", "window_h": 4, "kwh_per_day": 10.0,
                     "annual_saving_eur": 187.0, "flat_cost_eur": …, "optimized_cost_eur": …, "days": 360, "n": 4 } ] } }
}
```

## `locational_signal.json` (v10 — Value Layer slice 6, no new source)

Assembled from `de_regional_balance.json` (SMARD) + `curtailment.json` (netztransparenz):
per-month north-surplus / south-deficit (GW), redispatch volume (GWh), and a congestion
index = min(north surplus, |south deficit|). Plus a curated, cited `context` block.
**No simulated split-zone price** — the bottleneck is internal to DE-LU (landmine #2).

```json
{
  "generated_at": "…", "source": "SMARD control-area balance + netztransparenz redispatch",
  "north_areas": ["50Hertz", "TenneT"], "south_areas": ["Amprion", "TransnetBW"],
  "monthly": [ { "month": "2025-06", "north_surplus_gw": 6.83, "south_deficit_gw": -6.45,
                 "redispatch_gwh": 455.5, "congestion_index": 6.45 } ],
  "context": { "decision": "Single DE-LU zone retained (15 Dec 2025)…",
               "de5_redispatch_meur": -613, "de5_welfare_meur": 339, "de5_vintage": "2019 data",
               "academic_dissent": "<€3/MWh…", "stance": "no side, no split price" },
  "curtailment_available": true
}
```

DE5 (`-613` / `+339`, 2019 vintage) vs the academic `<€3/MWh` dissent are a **contested
range**, both cited; never resolved, never a computed split price.

## `capacity_adequacy.json` (v10 — Value Layer slice 8, curated cost + real stress)

Real stress (residual-load peak from `mismatch.json`, Dunkelflaute spell + spell-vs-normal
VRE share from `dunkelflaute.json`) alongside a **curated, provisional** capacity-cost table.

```json
{
  "generated_at": "…", "zone": "DE_LU",
  "stress": { "peak_residual_gw": 40.5, "peak_total_load_gw": 60.4, "longest_spell_h": 52,
              "spell_hours_year": 52, "low_vre_hours_year": 510,
              "vre_share_spell_pct": 8.9, "vre_share_normal_pct": 48.6 },
  "cost": { "tender_gw": 12, "tender_duration_h": 10, "target_year": 2031,
            "status": "provisional — May-2026 cabinet bill, pending Bundestag (NOT YET LAW)",
            "source": "…cabinet draft, May 2026", "levy_eur_bn": [ { "year": 2031, "eur_bn": 3.0 } ] }
}
```

Cost figures are **not yet law** — labelled provisional with a citation, like the France
cost stack. `storage.json` additionally gained a `cannibalization` block (v10 slice 4): an
**illustrative parametric** spread-compression curve (`scenarios:[{assumed_gw,modelled_spread,
per_mw_arbitrage_eur_yr}]`) — modelled, not measured, with a capacity-remuneration note.

## `retail_wedge.json` (v10 — Value Layer slice 7, NEW SOURCE: Eurostat)

Household electricity price decomposed into energy & supply | network | taxes/fees/levies,
per country and year, from Eurostat `nrg_pc_204_c` (band DC, EUR/kWh, ANNUAL). Isolated
module; non-fatal (writes `status:"unavailable"` on a Eurostat hiccup).

```json
{
  "generated_at": "…", "status": "ok", "currency": "EUR/kWh", "frequency": "annual",
  "components": { "energy": "Energy and supply (incl. wholesale + supplier margin)",
                  "network": "Network costs", "taxes_levies": "Taxes, fees, levies and charges" },
  "country_default": "DE", "geos_available": ["DE","ES","FR","NL","NO"],
  "countries": { "DE": [ { "period": "2024", "energy": 0.1654, "network": 0.1147,
                           "taxes_levies": 0.1147, "total": 0.3948, "currency": "EUR/kWh" } ] }
}
```

EUR/kWh ≠ our wholesale €/MWh (stated); annual, not hourly; "geo" is the COUNTRY, not the
DE-LU zone; "Energy and supply" includes wholesale + supplier margin (not pure wholesale).
`curtailment.json` additionally gained a `cost_estimate` block (v10 slice 5): an **estimate**
(curtailed MWh × a reference rate, `cost_estimate_eur` per day + `total_eur`) — not the
billed EinsMan compensation; the €7.2bn EU figure is different-scope context.

## `industrial_prices.json` (v10 — Value Layer slice 10, source: Eurostat)

Industrial electricity-price comparison from Eurostat `nrg_pc_205_c` (non-household, band
IC = 500-1 999 MWh/yr), energy|network|taxes_levies per country/year (EUR/kWh, annual).
Same isolated-fetch + JSON-stat pattern as `retail_wedge.json` (reuses its parser). Fails
open to `status:"unavailable"`.

```json
{
  "generated_at": "…", "status": "ok", "currency": "EUR/kWh", "frequency": "annual",
  "band": "IC (500-1 999 MWh/yr)", "country_default": "DE",
  "geos_available": ["DE","ES","FR","NL","NO"],
  "countries": { "DE": [ { "period": "2024", "energy": 0.129, "network": 0.0704,
                           "taxes_levies": 0.0823, "total": 0.2817, "currency": "EUR/kWh" } ] }
}
```

This is the PRICE layer of industrial competitiveness only; corporate strategy, M&A, PPAs
and capital-markets themes stay out of scope (the `industrial.html` view says so).

## `marginal_fuel.json` (v10 — Value Layer slice 9, MODEL overlay)

A MODELLED estimate (not a measurement): the CCGT short-run marginal cost
(gas/efficiency + EUA × carbon intensity) vs the actual day-ahead price, to infer when gas
sets the price. Gas = **Yahoo TTF=F** (front-month proxy, NOT licence-clean for
redistribution — labelled); CO2 = a **curated EUA** value from EEX auctions (slow-moving,
stated as-of); wholesale = our `spread.json`.

```json
{
  "generated_at": "…", "status": "ok", "is_model_not_measurement": true,
  "assumptions": { "ccgt_efficiency": 0.52, "ccgt_t_co2_per_mwh": 0.35, "eua_eur_t": 76.0, "eua_as_of": "2026-06" },
  "sources": { "gas": "Yahoo TTF=F proxy…", "co2": "curated EEX EUA…", "wholesale": "ENTSO-E spread.json" },
  "monthly": [ { "month": "2026-06", "gas_eur_mwh": 45.8, "gas_marginal_cost": 114.8, "wholesale_price": 120.6 } ],
  "inference": { "days_classified": 249, "gas_set_pct": 77, "renewable_set_pct": 2, "other_pct": 22 }
}
```

The marginal-fuel split is INFERRED from price vs modelled gas cost — change the assumptions
and it changes. The gas source is a Yahoo proxy (not licence-clean); the view must say so.

### Frontend obligations
- Render `perfect_arbitrage_eur_per_mw` only alongside a visible caveat that it is an unachievable upper bound (see CLAUDE.md landmine #7).
- For `retail_wedge`, state EUR/kWh vs €/MWh and country-vs-zone; for `curtailment.cost_estimate`, label it an estimate (not billed), with the EU figure as different-scope context.
- For `marginal_fuel`, label it a MODEL not a measurement, state the assumptions, and flag the gas source as a Yahoo TTF proxy (not licence-clean) + CO2 as a curated EEX value.
- For `flex_savings`, label `annual_saving_eur` as a perfect-foresight **upper bound** (same as the battery figure). For `capture_price`, present the roadmap anchors as cited context, not computed values; for `negative_prices`, never clip negatives and count hours, not 15-min slots.
- For `locational_signal`, never present a computed split-zone price; show DE5 vs academic figures as a contested range. For `capacity_adequacy`, label the cost figures provisional/"not yet law" with the citation. For `storage.cannibalization`, label the curve illustrative/modelled, not a forecast.
- Treat `complete: false` days distinctly (e.g. muted) and never break if `days` has gaps.
- Round every number before display.
- For `mix`/`carbon`, use the canonical fuel palette (`frontend/fuels.js`); render `null` fuel/hour slots as gaps, never zeros. Show the carbon methodology label.
- For `flows`, show flow direction explicitly and render "no capacity data" where `capacity_available` is false.
- For `de_capacity_by_landkreis`, join to the basemap on `nuts_id`; render Kreise with no entry as a distinct "no data" colour (not zero); caption the map as installed *capacity*, not output (copy block D). Wind and solar are separate toggled metrics.
