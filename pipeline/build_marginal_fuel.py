"""Build the Marginal-fuel / gas-CO2 overlay (v10 slice 9). Writes data/marginal_fuel.json.

THIS IS A MODEL, NOT A MEASUREMENT (the headline caveat). It estimates the short-run
marginal cost of a gas (CCGT) plant — gas_price/efficiency + CO2_price x carbon_intensity —
and compares it to the actual day-ahead wholesale price, to show WHEN gas is likely setting
the price vs when cheaper renewables are. The hour-by-hour "marginal fuel" is inferred, not
observed.

SOURCES (both flagged, per the project's honesty/licence rules):
  * Gas: Yahoo Finance TTF=F (Dutch TTF front-month future, EUR/MWh). A convenience proxy —
    Yahoo's data is personal-use and NOT licence-clean for redistribution, and a front-month
    future is not day-ahead spot. Labelled as such in the JSON + UI.
  * CO2: a CURATED EUA price from EEX primary auctions (a slow-moving input, stated with its
    as-of date and source) — not a live feed.
  * Wholesale price: our own committed spread.json (real ENTSO-E day-ahead, DE-LU).

Isolated, non-fatal: a Yahoo hiccup writes status:"unavailable" and nothing else breaks.
"""
from __future__ import annotations

import json
import logging
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("wattlas.build_marginal_fuel")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Modelling assumptions (stated in the UI — change them and the picture changes).
GAS_EFF = 0.52              # CCGT electrical efficiency
CCGT_T_PER_MWH = 0.35      # CCGT carbon intensity, tCO2 per MWh electrical
EUA_EUR_T = 76.0           # curated EUA price (EEX primary auction)
EUA_AS_OF = "2026-06"

TTF_URL = "https://query1.finance.yahoo.com/v8/finance/chart/TTF=F?interval=1d&range=1y"


def gas_marginal_cost(gas_eur_mwh: float, eua_eur_t: float = EUA_EUR_T,
                      eff: float = GAS_EFF, carbon: float = CCGT_T_PER_MWH) -> float:
    """Short-run marginal cost of a CCGT, EUR/MWh electrical. Pure; unit-tested."""
    return gas_eur_mwh / eff + eua_eur_t * carbon


def classify(price: float, gmc: float) -> str:
    """Infer the likely marginal fuel from the wholesale price vs the gas marginal cost.
    A heuristic (NOT a measurement): near/above gas cost -> gas sets it; near zero or
    negative -> renewables; in between -> mixed/cheaper thermal. Pure; unit-tested."""
    if price <= 0 or price < 0.25 * gmc:
        return "renewable"
    if price >= 0.85 * gmc:
        return "gas"
    return "other"


def _fetch_gas_daily() -> dict:
    """{date_str: ttf_eur_mwh} from Yahoo TTF=F. Network; raises on failure."""
    req = urllib.request.Request(TTF_URL, headers={"User-Agent": "Mozilla/5.0"})
    d = json.loads(urllib.request.urlopen(req, timeout=40).read())
    r = d["chart"]["result"][0]
    ts = r["timestamp"]
    closes = r["indicators"]["quote"][0]["close"]
    out = {}
    for t, c in zip(ts, closes):
        if c is None:
            continue
        out[datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d")] = float(c)
    return out


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    base = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "is_model_not_measurement": True,
        "assumptions": {"ccgt_efficiency": GAS_EFF, "ccgt_t_co2_per_mwh": CCGT_T_PER_MWH,
                        "eua_eur_t": EUA_EUR_T, "eua_as_of": EUA_AS_OF},
        "sources": {
            "gas": "Yahoo Finance TTF=F (Dutch TTF front-month future, EUR/MWh) — convenience "
                   "PROXY, not licence-clean for redistribution, and a future not day-ahead spot.",
            "co2": "Curated EUA price from EEX primary auctions (slow-moving input, stated as-of).",
            "wholesale": "ENTSO-E day-ahead (our spread.json, DE-LU).",
        },
        "note": ("MODEL, not a measurement: the marginal fuel is INFERRED from the wholesale "
                 "price vs a modelled CCGT marginal cost (gas/efficiency + EUA x intensity). "
                 "Change the assumptions and the picture changes."),
    }
    try:
        gas = _fetch_gas_daily()
        if not gas:
            raise ValueError("no gas data")
    except Exception as e:  # isolated + non-fatal
        logger.warning("TTF=F fetch failed (%s) — status:unavailable", e)
        (DATA_DIR / "marginal_fuel.json").write_text(json.dumps({**base, "status": "unavailable"}, indent=2))
        return

    spread = json.loads((DATA_DIR / "spread.json").read_text())
    price_by_date = {d["date"]: d.get("mean_price") for d in spread.get("days", []) if d.get("mean_price") is not None}

    monthly = defaultdict(lambda: {"gas": [], "gmc": [], "price": []})
    counts = defaultdict(int)
    for date, g in gas.items():
        p = price_by_date.get(date)
        if p is None:
            continue
        gmc = gas_marginal_cost(g)
        m = date[:7]
        monthly[m]["gas"].append(g)
        monthly[m]["gmc"].append(gmc)
        monthly[m]["price"].append(p)
        counts[classify(p, gmc)] += 1

    months = [{
        "month": m,
        "gas_eur_mwh": round(sum(v["gas"]) / len(v["gas"]), 1),
        "gas_marginal_cost": round(sum(v["gmc"]) / len(v["gmc"]), 1),
        "wholesale_price": round(sum(v["price"]) / len(v["price"]), 1),
    } for m, v in sorted(monthly.items())]
    total = sum(counts.values()) or 1
    inference = {
        "days_classified": sum(counts.values()),
        "gas_set_pct": round(100 * counts["gas"] / total),
        "renewable_set_pct": round(100 * counts["renewable"] / total),
        "other_pct": round(100 * counts["other"] / total),
    }

    (DATA_DIR / "marginal_fuel.json").write_text(json.dumps(
        {**base, "status": "ok", "monthly": months, "inference": inference}, indent=2))
    logger.info("wrote marginal_fuel.json — %d months; gas-set %d%% / renewable-set %d%% of %d days",
                len(months), inference["gas_set_pct"], inference["renewable_set_pct"], inference["days_classified"])


if __name__ == "__main__":
    main()
