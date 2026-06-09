"""Build cross-border physical-flow data for the Divergence view: net physical
flow between DE-LU and each neighbour, and congestion where transmission capacity
is known. Writes data/flows.json.

Run: python pipeline/build_flows.py            (fetches 12 months)
     python pipeline/build_flows.py --use-cache (offline, parquet cache)

The insight (Phase 2): prices diverge *because* an interconnector is full, not
just *that* they diverge. Showing the physical flow — and flagging hours where it
sits at the transmission limit — turns a correlation into a mechanism.

Data realities (CLAUDE.md landmine #10):
- Flows are DIRECTIONAL. We fetch both directions and report NET flow, positive =
  DE-LU exporting to the neighbour, negative = importing.
- Net transfer capacity (NTC) is OFTEN MISSING. The western borders (FR, NL, BE)
  sit in the flow-based market-coupling region (CWE/Core), which does not publish
  an explicit day-ahead NTC, so capacity/congestion is genuinely unavailable
  there — we render "no capacity data" rather than faking it. We try day-ahead
  NTC, then fall back to year-ahead, then give up gracefully per direction.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import pandas as pd

from metrics import monthly_flow_stats
from build_spread import DATA_DIR, LOCAL_TZ

logger = logging.getLogger("wattlas.build_flows")

HOME = "DE_LU"
# DE-LU's coupled neighbours (same set as Divergence). BE connects via the
# ALEGrO HVDC link; the others are physical AC borders.
NEIGHBOURS = ["FR", "NL", "BE", "PL", "AT"]
CACHE = DATA_DIR / "_raw_flows.parquet"


def _to_utc(s: pd.Series) -> pd.Series:
    """Normalise a tz-aware Series to UTC. Flows and the various NTC horizons can
    come back in DIFFERENT timezones; combining them into one DataFrame on a mixed
    union index collapses it to a tz-less object Index. Converting everything to a
    single UTC DatetimeIndex first keeps the frame tz-aware (local-tz grouping
    still happens downstream in monthly_flow_stats)."""
    if s is None or s.empty:
        return pd.Series(dtype=float)
    if getattr(s.index, "tz", None) is not None:
        s = s.tz_convert("UTC")
    return s


def _safe_flow(client, frm: str, to: str, start, end) -> pd.Series:
    """One-directional physical flow, or an empty Series if the border has none."""
    try:
        return _to_utc(client.query_crossborder_flows(frm, to, start=start, end=end))
    except Exception as exc:  # missing border/period is normal (#8, #10)
        logger.warning("flow %s->%s unavailable: %s", frm, to, type(exc).__name__)
        return pd.Series(dtype=float)


def _safe_ntc(client, frm: str, to: str, start, end) -> pd.Series:
    """Day-ahead NTC with a year-ahead fallback; empty Series if none published.

    Flow-based borders publish no explicit NTC — that's expected, not an error.
    """
    for fn in ("query_net_transfer_capacity_dayahead", "query_net_transfer_capacity_yearahead"):
        try:
            cap = _to_utc(getattr(client, fn)(frm, to, start=start, end=end))
            if cap is not None and not cap.empty:
                logger.info("NTC %s->%s from %s (%d pts)", frm, to, fn.split("_")[-1], len(cap))
                return cap
        except Exception:
            continue
    logger.info("NTC %s->%s: none published (flow-based border or no data)", frm, to)
    return pd.Series(dtype=float)


def fetch_flows(start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Fetch net flow + per-direction capacity for every border into one frame.

    Columns per neighbour: '<nb>_net' (MW, +=export), '<nb>_cap_exp',
    '<nb>_cap_imp'. Flows are fetched in monthly chunks (the A11 query can time
    out over a full year), net is computed per chunk, then concatenated.
    """
    from entsoe import EntsoePandasClient

    token = os.environ.get("ENTSOE_API_TOKEN")
    if not token:
        sys.exit("ENTSOE_API_TOKEN not set. Copy .env.example to .env and fill it in.")
    client = EntsoePandasClient(api_key=token)

    cols: dict[str, pd.Series] = {}
    for nb in NEIGHBOURS:
        logger.info("[%s<->%s] fetching flows", HOME, nb)
        out_frames, in_frames = [], []
        a = start
        while a < end:
            b = min(a + pd.DateOffset(months=1), end)
            out_frames.append(_safe_flow(client, HOME, nb, a, b))
            in_frames.append(_safe_flow(client, nb, HOME, a, b))
            a = b
        flow_out = pd.concat([f for f in out_frames if not f.empty]) if any(not f.empty for f in out_frames) else pd.Series(dtype=float)
        flow_in = pd.concat([f for f in in_frames if not f.empty]) if any(not f.empty for f in in_frames) else pd.Series(dtype=float)
        if flow_out.empty and flow_in.empty:
            logger.warning("[%s<->%s] no flow data — skipping border", HOME, nb)
            continue
        net = flow_out.reindex(flow_out.index.union(flow_in.index)).fillna(0.0) - \
              flow_in.reindex(flow_out.index.union(flow_in.index)).fillna(0.0)
        net = net[~net.index.duplicated(keep="first")].sort_index()
        cols[f"{nb}_net"] = net
        # Capacity is fetched once over the full window (yearly NTC is constant-ish).
        cols[f"{nb}_cap_exp"] = _safe_ntc(client, HOME, nb, start, end)
        cols[f"{nb}_cap_imp"] = _safe_ntc(client, nb, HOME, start, end)

    return pd.DataFrame(cols)


def build(raw: pd.DataFrame) -> None:
    """Compute monthly net flow + congestion per border; write data/flows.json."""
    borders_out: dict[str, dict] = {}
    all_months: set[str] = set()

    for nb in NEIGHBOURS:
        net_col = f"{nb}_net"
        if net_col not in raw.columns or raw[net_col].dropna().empty:
            continue
        net = raw[net_col].dropna()
        cap_exp = raw.get(f"{nb}_cap_exp", pd.Series(dtype=float)).dropna()
        cap_imp = raw.get(f"{nb}_cap_imp", pd.Series(dtype=float)).dropna()
        stats = monthly_flow_stats(net, cap_exp, cap_imp, local_tz=LOCAL_TZ)
        has_capacity = not cap_exp.empty or not cap_imp.empty
        by_month = {s["month"]: s for s in stats}
        all_months.update(by_month.keys())
        borders_out[nb] = {"_by_month": by_month, "capacity_available": has_capacity}
        logger.info(
            "[%s<->%s] %d months, capacity=%s, mean net %.0f MW",
            HOME, nb, len(stats), has_capacity,
            sum(s["net_flow_mw"] for s in stats) / len(stats) if stats else 0,
        )

    months = sorted(all_months)
    data: dict[str, dict] = {}
    for nb, info in borders_out.items():
        bm = info["_by_month"]
        data[nb] = {
            "net_flow_mw": [bm[m]["net_flow_mw"] if m in bm else None for m in months],
            "congestion_pct": [
                (bm[m]["congestion_pct"] if (m in bm and info["capacity_available"]) else None)
                for m in months
            ],
            "capacity_available": info["capacity_available"],
        }

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "home": HOME,
        "borders": list(data.keys()),
        "months": months,
        "flow_sign": "positive = DE-LU exporting to neighbour; negative = importing",
        "data": data,
    }
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "flows.json").write_text(json.dumps(payload, indent=2))
    cap_borders = [nb for nb, d in data.items() if d["capacity_available"]]
    logger.info(
        "wrote data/flows.json — borders: %s; capacity/congestion available for: %s",
        list(data.keys()), cap_borders or "none (flow-based borders publish no NTC)",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the cross-border flows JSON artefact.")
    parser.add_argument("--use-cache", action="store_true",
                        help="Re-use data/_raw_flows.parquet instead of the API.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    logger.info("flows build start (use_cache=%s)", args.use_cache)

    end = pd.Timestamp.now(tz=LOCAL_TZ).normalize()
    start = end - pd.DateOffset(months=12)

    if args.use_cache:
        if not CACHE.exists():
            logger.error("no cache at %s — run once without --use-cache first.", CACHE)
            sys.exit(1)
        raw = pd.read_parquet(CACHE)
        logger.info("loaded cache %s (%d rows x %d cols)", CACHE, *raw.shape)
    else:
        raw = fetch_flows(start, end)
        DATA_DIR.mkdir(exist_ok=True)
        raw.to_parquet(CACHE)
        logger.info("fetched + cached flows (%d rows x %d cols)", *raw.shape)

    build(raw)
    logger.info("flows build done")


if __name__ == "__main__":
    main()
