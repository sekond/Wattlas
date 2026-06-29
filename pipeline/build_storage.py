"""Build the Storage slice: a transparent battery-arbitrage model over real day-ahead
prices plus a curated storage-capacity series. Writes data/storage.json.

PURE / no network — reads the committed pulse.json (average 24h price profile) and
spread.json (per-day TB2, the 2-dearest-minus-2-cheapest spread a 2-hour battery
arbitrages). Run: python pipeline/build_storage.py

Landmines this script is built around:
  * UPPER BOUND (CLAUDE.md #7): the captured-arbitrage figure assumes PERFECT FORESIGHT
    and a stated round-trip efficiency — the same discipline as the Spread view's
    arbitrage number. Real revenue is lower (losses, cycling wear, cannibalisation).
  * MW (power) vs MWh (energy) are different — stated throughout.
  * Cannibalisation: more storage flattens the very spread it feeds on — noted, never
    implied as linear scaling.
  * The capacity series is CURATED from published market reports (aggregates only,
    approximate) — not a live registry pull. Stated in the JSON + UI.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("wattlas.build_storage")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Toy battery: 1 MW / 2 MWh (2-hour), 85% round-trip. Perfect foresight => upper bound.
BATTERY = {"power_mw": 1, "duration_h": 2, "round_trip": 0.85, "foresight": "perfect (upper bound)"}

# Curated operational grid-scale battery POWER (GW) by country/year — approximate,
# from published market reports (SolarPower Europe, Wood Mackenzie, Modo Energy, LCP
# Delta, national figures). Aggregates only. Energy (GWh) differs by duration.
CAPACITY = [
    {"country": "GB", "year": 2021, "power_gw": 1.6}, {"country": "GB", "year": 2022, "power_gw": 2.4},
    {"country": "GB", "year": 2023, "power_gw": 3.5}, {"country": "GB", "year": 2024, "power_gw": 4.5},
    {"country": "GB", "year": 2025, "power_gw": 5.9}, {"country": "GB", "year": 2026, "power_gw": 6.9},
    {"country": "DE", "year": 2021, "power_gw": 0.6}, {"country": "DE", "year": 2022, "power_gw": 0.8},
    {"country": "DE", "year": 2023, "power_gw": 1.1}, {"country": "DE", "year": 2024, "power_gw": 1.8},
    {"country": "DE", "year": 2025, "power_gw": 2.8}, {"country": "DE", "year": 2026, "power_gw": 4.5},
    {"country": "IT", "year": 2021, "power_gw": 0.2}, {"country": "IT", "year": 2022, "power_gw": 0.5},
    {"country": "IT", "year": 2023, "power_gw": 0.8}, {"country": "IT", "year": 2024, "power_gw": 1.3},
    {"country": "IT", "year": 2025, "power_gw": 2.0}, {"country": "IT", "year": 2026, "power_gw": 3.5},
    {"country": "Rest of Europe", "year": 2021, "power_gw": 1.5}, {"country": "Rest of Europe", "year": 2022, "power_gw": 2.3},
    {"country": "Rest of Europe", "year": 2023, "power_gw": 3.6}, {"country": "Rest of Europe", "year": 2024, "power_gw": 5.4},
    {"country": "Rest of Europe", "year": 2025, "power_gw": 8.3}, {"country": "Rest of Europe", "year": 2026, "power_gw": 10.1},
]
# Cumulative EU battery ENERGY (GWh) — sourced (SolarPower Europe market outlooks).
EU_ENERGY_GWH = [
    {"year": 2021, "gwh": 8}, {"year": 2022, "gwh": 15}, {"year": 2023, "gwh": 30},
    {"year": 2024, "gwh": 49}, {"year": 2025, "gwh": 77},
]


def battery_day(price_profile: list[float], power_mw: float, duration_h: int,
                round_trip: float) -> dict:
    """Charge in the `duration_h` cheapest hours, discharge in the dearest, over one
    representative day. Energy out is reduced by round_trip. Pure; unit-tested."""
    n = len(price_profile)
    order = sorted(range(n), key=lambda h: price_profile[h])
    charge_h = set(order[:duration_h])
    discharge_h = set(order[-duration_h:])
    charge_mw = [(-power_mw if h in charge_h else 0) for h in range(n)]
    discharge_mw = [(round(power_mw * round_trip, 2) if h in discharge_h else 0) for h in range(n)]
    cost = sum(price_profile[h] * power_mw for h in charge_h)               # buy at full power
    revenue = sum(price_profile[h] * power_mw * round_trip for h in discharge_h)  # sell the recoverable energy
    return {
        "hours": list(range(n)),
        "price": [round(p, 1) for p in price_profile],
        "charge_mw": charge_mw,
        "discharge_mw": discharge_mw,
        "charge_hours": sorted(charge_h),
        "discharge_hours": sorted(discharge_h),
        "captured_eur": round(revenue - cost, 1),     # € per cycle (this battery), UPPER BOUND
    }


def monthly_tb2(spread_days: list[dict]) -> list[dict]:
    """Mean daily TB2 per calendar month (the 2-hour spread the battery arbitrages)."""
    from collections import defaultdict
    acc = defaultdict(list)
    for d in spread_days:
        if d.get("tb2") is not None and d.get("date"):
            acc[d["date"][:7]].append(d["tb2"])
    return [{"month": m, "mean_tb2": round(sum(v) / len(v), 1)} for m, v in sorted(acc.items())]


def cannibalization_curve(base_spread: float, base_per_mw_eur_yr: float, base_gw: float,
                          scenarios: list[float], compression_per_gw: float = 0.03) -> list[dict]:
    """ILLUSTRATIVE parametric model (NOT a forecast): how the arbitrageable daily
    spread — and the per-MW revenue that rides on it — compresses as more battery
    capacity competes for the same spread.

    modelled_spread(gw) = base_spread * exp(-compression_per_gw * max(0, gw - base_gw)).
    per-MW arbitrage scales linearly with the spread. Monotonically non-increasing as
    gw grows from base_gw. The constants are illustrative — this is the cannibalisation
    direction made visible, not a prediction. Pure; unit-tested.
    """
    import math
    out = []
    for gw in scenarios:
        factor = math.exp(-compression_per_gw * max(0.0, float(gw) - base_gw))
        out.append({
            "assumed_gw": gw,
            "modelled_spread": round(base_spread * factor, 1),
            "per_mw_arbitrage_eur_yr": round(base_per_mw_eur_yr * factor),
        })
    return out


def compute(pulse: dict, spread: dict, generated_at: str) -> dict:
    profile = pulse["all_mean"]
    day = battery_day(profile, BATTERY["power_mw"], BATTERY["duration_h"], BATTERY["round_trip"])
    tb2 = [d["tb2"] for d in spread.get("days", []) if d.get("tb2") is not None]
    mean_tb2 = round(sum(tb2) / len(tb2), 1) if tb2 else None
    return {
        "generated_at": generated_at,
        "zone": pulse.get("zone", "DE_LU"),
        "currency": "EUR", "unit_power": "MW (power)", "unit_energy": "MWh (energy)",
        "battery": BATTERY,
        "note": ("Captured-arbitrage figures assume perfect foresight and an 85% round-trip "
                 "efficiency — an UPPER BOUND, like the Spread view. Real revenue is lower "
                 "(round-trip losses, cycling wear, and cannibalisation as more storage "
                 "flattens the very spread it feeds on)."),
        "day": day,
        "spread": {
            "mean_tb2_eur_mwh": mean_tb2,        # mean daily 2-hour spread (perfect foresight)
            "period_start": pulse.get("period_start"), "period_end": pulse.get("period_end"),
            "monthly_tb2": monthly_tb2(spread.get("days", [])),
        },
        "cannibalization": {
            "note": ("ILLUSTRATIVE parametric model, not a forecast: how the arbitrageable "
                     "daily spread (and the per-MW revenue on it) compresses as more battery "
                     "capacity competes for it. The decline is modelled, not measured."),
            "base_gw": 4.5, "base_spread_eur_mwh": mean_tb2,
            "compression_per_gw": 0.03,
            "scenarios": cannibalization_curve(
                base_spread=mean_tb2 or 0.0,
                base_per_mw_eur_yr=round((day["captured_eur"] or 0.0) * 365),
                base_gw=4.5, scenarios=[5, 10, 15, 20, 30, 40, 50]),
            "remuneration_note": ("As arbitrage erodes, storage revenue shifts toward "
                                  "capacity/availability payments (capacity market, ancillary "
                                  "services) — a structural shift this toy model does not capture."),
        },
        "capacity": CAPACITY,
        "capacity_note": ("Curated from published market reports (SolarPower Europe, Wood "
                          "Mackenzie, Modo Energy, LCP Delta); approximate operational "
                          "grid-scale battery POWER (GW). Energy (GWh) differs by duration "
                          "(~1.5–2h typical, rising). Pumped hydro not included."),
        "eu_energy_gwh": EU_ENERGY_GWH,
    }


def build() -> None:
    pulse = json.loads((DATA_DIR / "pulse.json").read_text())
    spread = json.loads((DATA_DIR / "spread.json").read_text())
    payload = compute(pulse, spread, datetime.now(timezone.utc).isoformat(timespec="seconds"))
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "storage.json").write_text(json.dumps(payload, indent=2))
    d = payload["day"]
    logger.info("wrote data/storage.json")
    logger.info("battery %d MW / %d MWh, %.0f%% round-trip; captured EUR %.1f/cycle (upper bound)",
                BATTERY["power_mw"], BATTERY["power_mw"] * BATTERY["duration_h"],
                BATTERY["round_trip"] * 100, d["captured_eur"])
    logger.info("charge hours %s (cheap), discharge hours %s (dear); mean daily TB2 %.1f EUR/MWh",
                d["charge_hours"], d["discharge_hours"], payload["spread"]["mean_tb2_eur_mwh"])


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    build()


if __name__ == "__main__":
    main()
