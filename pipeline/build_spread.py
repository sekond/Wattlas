"""Build the Spread view data: fetch DE-LU day-ahead prices, compute metrics,
write data/spread.json and data/spread_summary.json.

Run: python pipeline/build_spread.py

Requires ENTSOE_API_TOKEN in the environment (see .env.example). Free token
from your ENTSO-E account: https://transparency.entsoe.eu

See CLAUDE.md for the data landmines this script is built around.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from metrics import (
    daily_spreads,
    negative_hours_by_month,
    perfect_arbitrage_revenue,
)

ZONE = "DE_LU"
LOCAL_TZ = "Europe/Berlin"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# v1 battery assumptions for the UPPER-BOUND arbitrage figure (CLAUDE.md #7)
BATTERY = {
    "power_mw": 1,
    "duration_h": 2,
    "round_trip_efficiency": 1.0,
    "foresight": "perfect",
}


def fetch_prices(start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """Fetch day-ahead prices for ZONE between start and end (tz-aware Series).

    Isolated so it can be swapped for a fixture in tests. Imported lazily so the
    rest of the module (and the unit tests) don't require the entsoe package.
    """
    from entsoe import EntsoePandasClient  # noqa: WPS433 (lazy import on purpose)

    token = os.environ.get("ENTSOE_API_TOKEN")
    if not token:
        sys.exit("ENTSOE_API_TOKEN not set. Copy .env.example to .env and fill it in.")

    client = EntsoePandasClient(api_key=token)
    return client.query_day_ahead_prices(ZONE, start=start, end=end)


def build(start: pd.Timestamp, end: pd.Timestamp, prices: pd.Series | None = None) -> None:
    """Compute metrics and write the JSON artefacts.

    `prices` may be injected (tests); otherwise fetched from ENTSO-E.
    """
    if prices is None:
        prices = fetch_prices(start, end)

    daily = daily_spreads(prices, local_tz=LOCAL_TZ)

    # Flag incomplete days: anything with fewer than 23 hours is suspect
    # (a normal short DST day has 23). We mark <23 as incomplete data gaps.
    days_payload = []
    missing_days = []
    for date, row in daily.iterrows():
        complete = int(row["hours_observed"]) >= 23
        if not complete:
            missing_days.append(str(date))
        days_payload.append(
            {
                "date": str(date),
                "tb1": row["tb1"],
                "tb2": row["tb2"],
                "min_price": row["min_price"],
                "max_price": row["max_price"],
                "mean_price": row["mean_price"],
                "negative_hours": int(row["negative_hours"]),
                "hours_observed": int(row["hours_observed"]),
                "complete": complete,
            }
        )

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    spread = {
        "zone": ZONE,
        "generated_at": generated_at,
        "days": days_payload,
    }

    # Summary
    if not daily.empty:
        widest_idx = daily["tb1"].idxmax()
        summary = {
            "zone": ZONE,
            "period_start": str(daily.index.min()),
            "period_end": str(daily.index.max()),
            "avg_daily_tb1": round(float(daily["tb1"].mean()), 1),
            "widest_day": {
                "date": str(widest_idx),
                "tb1": float(daily.loc[widest_idx, "tb1"]),
            },
            "total_negative_hours": int(daily["negative_hours"].sum()),
            "negative_hours_by_month": negative_hours_by_month(daily),
            "yoy_tb1_change_pct": None,  # populate when >2 years of data is fetched
            "perfect_arbitrage_eur_per_mw": perfect_arbitrage_revenue(
                prices,
                power_mw=BATTERY["power_mw"],
                duration_h=BATTERY["duration_h"],
                round_trip_efficiency=BATTERY["round_trip_efficiency"],
                local_tz=LOCAL_TZ,
            ),
            "perfect_arbitrage_is_upper_bound": True,
            "battery_assumptions": BATTERY,
            "missing_days": missing_days,
        }
    else:
        summary = {
            "zone": ZONE,
            "period_start": None,
            "period_end": None,
            "avg_daily_tb1": 0,
            "widest_day": None,
            "total_negative_hours": 0,
            "negative_hours_by_month": [],
            "yoy_tb1_change_pct": None,
            "perfect_arbitrage_eur_per_mw": 0,
            "perfect_arbitrage_is_upper_bound": True,
            "battery_assumptions": BATTERY,
            "missing_days": [],
        }

    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "spread.json").write_text(json.dumps(spread, indent=2))
    (DATA_DIR / "spread_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"Wrote {len(days_payload)} days to data/spread.json")
    print(f"Wrote summary to data/spread_summary.json (missing days: {len(missing_days)})")


def main() -> None:
    # Default: last ~12 months ending yesterday, in local tz.
    end = pd.Timestamp.now(tz=LOCAL_TZ).normalize()
    start = end - pd.DateOffset(months=12)
    build(start, end)


if __name__ == "__main__":
    main()
