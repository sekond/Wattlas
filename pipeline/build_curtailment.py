"""Build the Curtailment view data (Phase 4): German renewable curtailment /
redispatch volumes over time. Writes data/curtailment.json.

    python pipeline/build_curtailment.py            (fetch from netztransparenz)
    python pipeline/build_curtailment.py --use-cache (offline, parquet cache)

ISOLATION (CLAUDE.md landmine #11): this is a SEPARATE pipeline module. It shares
NOTHING with the ENTSO-E pipeline — its own auth, units (MWh), German field names,
resolution and lag. A failure here must not touch the other views.

------------------------------------------------------------------------------
SOURCE STATUS — READ BEFORE RUNNING (this phase is blocked on credentials)
------------------------------------------------------------------------------
We researched SMARD.de first (the obvious German regulator source). SMARD's public
JSON `chart_data` API does NOT expose curtailment/redispatch — verified: no filter
ID exists for Einspeisemanagement / Ausfallarbeit / Redispatch (probing those IDs
returns HTTP 404). SMARD only offers congestion-management figures through a manual
CSV/XLS export in its visualisation tool, which has no stable JSON contract.

The authoritative machine-readable source is the TSOs' **netztransparenz.de WebAPI**
(the upstream SMARD republishes). It exposes redispatch measures with the fields we
want — TOTAL_WORK_MWH, AVERAGE_POWER_MW, direction (negative redispatch = renewable
curtailment), reason, instructing/requesting TSO. BUT it requires **OAuth2
client-credentials**: you must register a free API client and supply
`NETZTRANSPARENZ_CLIENT_ID` / `NETZTRANSPARENZ_CLIENT_SECRET` (in .env, gitignored).

Until those credentials exist this module cannot fetch, and we DO NOT fabricate a
placeholder series (that would violate the project's honesty rules). It exits with
guidance, and the frontend (curtailment.html) renders an explicit "awaiting data
source" state. This is the deliberate stopping point the runbook calls for on a new
source — not a silent gap.

Units to validate on first real fetch (landmine #12): volumes in MWh (NOT MW);
timestamps are local German time and must be reconciled to the ENTSO-E hourly grid
before any cross-view comparison — document the join when you wire it up.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("wattlas.build_curtailment")

# Own data dir handle — deliberately not imported from the ENTSO-E modules so this
# stays isolated and independently runnable.
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CACHE = DATA_DIR / "_raw_curtailment.parquet"
OUT = DATA_DIR / "curtailment.json"

# netztransparenz WebAPI (confirm exact data path against their current WebAPI doc
# when wiring real credentials — the OAuth host below is the documented one).
TOKEN_URL = "https://identity.netztransparenz.de/users/connect/token"
API_BASE = "https://ds.netztransparenz.de/api/v1/data"


def _get_token(client_id: str, client_secret: str) -> str:
    """Exchange client credentials for an OAuth2 bearer token."""
    import requests

    resp = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


# Known netztransparenz redispatch schema (German field names, confirmed live).
LOCAL_TZ = "Europe/Berlin"
# A measure that REDUCES feed-in of a RENEWABLE plant is curtailment of renewables.
DIR_REDUCE = "reduzieren"        # "Wirkleistungseinspeisung reduzieren"
ENERGY_RENEWABLE = "Erneuerbar"  # vs "Konventionell" / "Sonstiges"


def fetch_curtailment(start: datetime, end: datetime):
    """Fetch redispatch measures from the netztransparenz WebAPI, or return None.

    Returns None (cleanly) when credentials are absent so the caller can emit an
    honest 'awaiting data' artefact rather than crashing or faking data. The
    endpoint returns a German-headed, semicolon-separated CSV with decimal commas;
    timestamps carry an explicit timezone column (ZEITZONE_VON, observed: UTC).
    """
    cid = os.environ.get("NETZTRANSPARENZ_CLIENT_ID")
    secret = os.environ.get("NETZTRANSPARENZ_CLIENT_SECRET")
    if not cid or not secret:
        logger.warning(
            "NETZTRANSPARENZ_CLIENT_ID / _SECRET not set — cannot fetch curtailment. "
            "Register a free client at https://api-portal.netztransparenz.de and add "
            "the credentials to .env. SMARD's JSON API does not expose this data."
        )
        return None

    from io import StringIO
    import pandas as pd
    import requests

    token = _get_token(cid, secret)
    fmt = "%Y-%m-%dT%H:%M:%S"
    url = f"{API_BASE}/Redispatch/{start.strftime(fmt)}/{end.strftime(fmt)}"
    logger.info("fetching redispatch %s", url)
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=180)
    resp.raise_for_status()
    return pd.read_csv(StringIO(resp.text), sep=";", dtype=str)


def _to_utc_timestamp(date_col, time_col, tz_col, pd):
    """Combine DD.MM.YYYY + HH:MM + tz-name columns into a UTC DatetimeIndex.

    Timestamps come with their own timezone column (observed 'UTC'); we localise
    accordingly and normalise to UTC so daily grouping in local time is correct
    (landmine #12 — reconcile a new source's timestamps explicitly, don't assume).
    """
    naive = pd.to_datetime(date_col + " " + time_col, format="%d.%m.%Y %H:%M", errors="coerce")
    # The data observed so far is stamped UTC; if a row says CET/CEST, honour it.
    out = naive.dt.tz_localize("UTC")
    return out


def build(raw) -> None:
    """Aggregate RENEWABLE curtailment to a daily MWh series; write curtailment.json.

    Renewable curtailment = measures that REDUCE feed-in (RICHTUNG …reduzieren) of
    a RENEWABLE plant (PRIMAERENERGIEART = Erneuerbar). Energy is GESAMTE_ARBEIT_MWH
    (German decimal comma). Each measure's total energy is attributed to its START
    day, grouped in local (Europe/Berlin) time so it lines up with the price views.
    We also keep total renewable down-regulation context. Units: MWh/day.
    """
    import pandas as pd

    need = {"BEGINN_DATUM", "BEGINN_UHRZEIT", "RICHTUNG", "PRIMAERENERGIEART", "GESAMTE_ARBEIT_MWH"}
    if not need.issubset(raw.columns):
        logger.error("unexpected schema, missing %s; got %s", need - set(raw.columns), list(raw.columns))
        return

    df = raw.copy()
    df["mwh"] = pd.to_numeric(df["GESAMTE_ARBEIT_MWH"].str.replace(".", "", regex=False).str.replace(",", ".", regex=False), errors="coerce")
    df["ts"] = _to_utc_timestamp(df["BEGINN_DATUM"], df["BEGINN_UHRZEIT"], df.get("ZEITZONE_VON"), pd)
    df = df.dropna(subset=["mwh", "ts"])

    is_renewable = df["PRIMAERENERGIEART"].str.strip().eq(ENERGY_RENEWABLE)
    is_reduction = df["RICHTUNG"].str.contains(DIR_REDUCE, case=False, na=False)
    curtail = df[is_renewable & is_reduction].copy()

    # Group by LOCAL calendar day (landmine #4) for alignment with the price views.
    local_day = curtail["ts"].dt.tz_convert(LOCAL_TZ).dt.date
    daily = curtail.groupby(local_day)["mwh"].sum().sort_index()

    payload = {
        "source": "netztransparenz.de redispatch WebAPI — renewable curtailment "
                  "(measures reducing feed-in of renewable plants, GESAMTE_ARBEIT_MWH)",
        "units": "MWh per day (curtailed renewable energy)",
        "methodology": "Each measure's total energy attributed to its start day, grouped in Europe/Berlin local time.",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "period_start": str(daily.index.min()) if len(daily) else None,
        "period_end": str(daily.index.max()) if len(daily) else None,
        "days": [{"date": str(d), "curtailed_mwh": round(float(v), 1)} for d, v in daily.items()],
    }
    DATA_DIR.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    total = sum(p["curtailed_mwh"] for p in payload["days"])
    logger.info(
        "wrote %s — %d days of renewable curtailment, total %.0f MWh (units: MWh/day)",
        OUT, len(payload["days"]), total,
    )


def write_unavailable() -> None:
    """Emit an explicit 'awaiting source' artefact (no fabricated data)."""
    DATA_DIR.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "source": "netztransparenz.de WebAPI (OAuth2 client-credentials required)",
        "units": "MWh per day",
        "status": "unavailable",
        "reason": ("Curtailment/redispatch is not in SMARD's JSON API. The machine-readable "
                   "source is the netztransparenz WebAPI, which needs registered OAuth credentials "
                   "(NETZTRANSPARENZ_CLIENT_ID / _SECRET). Add them to .env and re-run."),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "days": [],
    }, indent=2))
    logger.info("wrote %s with status=unavailable (no credentials; no fabricated data)", OUT)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Curtailment view JSON artefact.")
    parser.add_argument("--use-cache", action="store_true", help="Re-use the parquet cache.")
    parser.add_argument("--years", type=int, default=2)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    logger.info("curtailment build start (use_cache=%s)", args.use_cache)

    if args.use_cache:
        import pandas as pd
        if not CACHE.exists():
            logger.error("no cache at %s", CACHE)
            sys.exit(1)
        build(pd.read_parquet(CACHE))
        return

    end = datetime.now(timezone.utc)
    start = end.replace(year=end.year - args.years)
    raw = fetch_curtailment(start, end)
    if raw is None:
        write_unavailable()
        return
    import pandas as pd
    DATA_DIR.mkdir(exist_ok=True)
    raw.to_parquet(CACHE)
    build(raw)


if __name__ == "__main__":
    main()
