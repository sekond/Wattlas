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

Powers the **Mismatch** view: the hour-of-day profile of wind+solar share of
generation vs demand, for DE-LU. Arrays are length 24 (local hour 0–23); a slot
is `null` if no data fell in that hour.

```json
{
  "zone": "DE_LU",
  "generated_at": "2026-06-03T10:00:00Z",
  "period_start": "2025-06-03",
  "period_end": "2026-06-03",
  "hours": [0, 1, "…", 23],
  "renewable_share_pct": [38.6, "…"],   // wind + solar as % of total generation
  "demand_gw": [49.4, "…"]              // actual load, GW
}
```

Both are computed on hourly-resampled data (landmine #3) grouped in local time
(landmine #4).

### Frontend obligations
- Render `perfect_arbitrage_eur_per_mw` only alongside a visible caveat that it is an unachievable upper bound (see CLAUDE.md landmine #7).
- Treat `complete: false` days distinctly (e.g. muted) and never break if `days` has gaps.
- Round every number before display.
