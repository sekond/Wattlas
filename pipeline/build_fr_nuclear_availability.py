"""Build the French nuclear availability/output data for the France-nuclear Panel 3:
monthly nuclear output over the year (the maintenance dip), what moves alongside it,
and — when RTE credentials are present — the nuclear **available capacity** ceiling.

    python pipeline/build_fr_nuclear_availability.py

Writes data/fr_nuclear_availability.json.

ISOLATION (CLAUDE.md landmine #11): its OWN module. Two sources, kept separate:
  • Output + mix + exchanges: RTE **éCO2mix national** via ODRÉ (open, no key). MW → GW.
  • Available capacity: RTE **Data Portal "Unavailability Additional Information" v6**
    (OAuth2 client-credentials). MW → GW.

AVAILABLE CAPACITY vs OUTPUT (block-B distinction). "Output" (`nuclear_gw`) is how much
the fleet DID generate (éCO2mix). "Available capacity" (`available_gw`) is how much it
COULD have generated — installed capacity minus declared unavailabilities (planned
refuelling/maintenance + forced outages). It is a **declared upper bound** on producible
power, never actual generation — labelled as such in the UI (project upper-bound rule).

We compute it the robust way: the unavailability feed lists only units that HAVE an
outage (fully-available units are simply absent), so summing per-record available_capacity
would badly understate the fleet. Instead:
    fleet_available(t) = installed_total − Σ_units unavailable_capacity(t)
time-weighted to a monthly mean in Europe/Paris. `installed_total` is the committed fleet
(data/fr_nuclear_sites.json). See memory `rte-oauth-pending`.

DEGRADES CLEANLY (project credibility rule): if RTE_CLIENT_ID / RTE_CLIENT_SECRET are
absent, or the token/resource call is unauthorized (not subscribed / invalid), we log a
warning and leave `available_gw` null — we never fabricate it. Output still ships.

HONEST FRAMING (not the mockup): the real data shows nuclear output dips in spring/summer
(refuelling + maintenance, concentrated in the lower-demand months **by design**), but
France remains a **net exporter every month** (`ech_physiques` < 0) because summer demand
also falls and solar rises — so imports do NOT "fill the gap" at monthly resolution. We
therefore show the seasonal output dip and the net-export line, and reserve the heatwave
river-cooling story (event-scale, not monthly) for the annotated copy — never fabricated.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

log = logging.getLogger("build_fr_nuclear_availability")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ODRE = ("https://odre.opendatasoft.com/api/explore/v2.1/catalog/"
        "datasets/eco2mix-national-cons-def/records")
SOURCE_OUTPUT = "RTE éCO2mix national via ODRÉ (Opendatasoft)"
SOURCE_BOTH = ("RTE éCO2mix national via ODRÉ (output) + RTE Data Portal "
               "Unavailability Additional Information v6 (available capacity, OAuth2)")
WINDOW_MONTHS = 24

# RTE Data Portal (OAuth2 client-credentials). Token: POST with an HTTP Basic header and
# an EMPTY body (grant_type is implied by the app type — do NOT put it in the body).
RTE_TOKEN_URL = "https://digital.iservices.rte-france.com/token/oauth/"
RTE_UNAVAIL_URL = ("https://digital.iservices.rte-france.com/open_api/"
                   "unavailability_additional_information/v6/generation_unavailabilities")
PARIS = ZoneInfo("Europe/Paris")   # bucket months by France local-calendar boundaries
_CHUNK_DAYS = 150                   # stay under RTE's (undocumented, ~155-day) window cap


# --------------------------------------------------------------------------- #
# Pure, offline-testable assembly
# --------------------------------------------------------------------------- #

def assemble_months(rows: list[dict], available_by_month: dict[str, float] | None = None) -> list[dict]:
    """Monthly rows (MW averages) -> the JSON months (GW, rounded), chronological.

    `net_export_gw` = −ech_physiques (+ = France exporting). `available_gw` is filled from
    `available_by_month` (RTE OAuth) when supplied, else null (degraded to output)."""
    avail = available_by_month or {}
    out = []
    for x in sorted(rows, key=lambda r: r["month"]):
        g = lambda k: (x.get(k) or 0) / 1000.0
        out.append({
            "month": x["month"],
            "nuclear_gw": round(g("nuc"), 2),
            "hydro_gw": round(g("hyd"), 2),
            "gas_gw": round(g("gas"), 2),
            "wind_gw": round(g("eo"), 2),
            "solar_gw": round(g("sol"), 2),
            "other_gw": round(g("bio") + g("coal") + g("oil"), 2),
            "demand_gw": round(g("dem"), 2),
            "net_export_gw": round(-g("ech"), 2),   # + = net exporter
            "available_gw": avail.get(x["month"]),  # RTE OAuth, else None
        })
    return out


def _parse_dt(s: str | None) -> datetime | None:
    """RTE ISO-8601 ('...Z' or '+02:00') -> tz-aware UTC datetime; None if unparseable."""
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_intervals(records: list[dict]) -> list[tuple[datetime, datetime, float]]:
    """RTE generation_unavailabilities records -> flat list of (start, end, unavailable_MW).

    Pure. De-duplicates by `identifier`, keeping the highest `version` (belt-and-braces
    even with last_version=true). Each record's `values[]` is a piecewise-constant step
    function of variable-length intervals; we keep each interval as-is (time-weighting is
    done later, so no resampling needed). `unavailable_capacity` is used directly; if a
    value omits it, it's derived as unit_installed − available_capacity. available==0 is a
    real full outage, not missing data."""
    best: dict[object, tuple[int, dict]] = {}
    for i, r in enumerate(records):
        ident = r.get("identifier", i)            # fall back to position if no id
        ver = r.get("version") or 0
        if ident not in best or ver > best[ident][0]:
            best[ident] = (ver, r)

    intervals: list[tuple[datetime, datetime, float]] = []
    for _ver, r in best.values():
        unit_installed = r.get("affected_asset_or_unit_installed_capacity")
        for v in r.get("values") or []:
            s, e = _parse_dt(v.get("start_date")), _parse_dt(v.get("end_date"))
            if s is None or e is None or e <= s:
                continue
            u = v.get("unavailable_capacity")
            if u is None:
                ac = v.get("available_capacity")
                if ac is not None and unit_installed is not None:
                    u = unit_installed - ac
            if u is None:
                continue
            intervals.append((s, e, float(u)))
    return intervals


def monthly_available_gw(intervals: list[tuple[datetime, datetime, float]],
                         installed_mw: float, months: list[str]) -> dict[str, float]:
    """Time-weighted monthly mean of fleet AVAILABLE capacity (GW), per "YYYY-MM".

    Pure. For each calendar month (boundaries in Europe/Paris, so DST 23h/25h days are
    handled — never assume 24h/day): mean_unavailable_MW = Σ(interval_MW × hours overlapping
    the month) / hours_in_month; available = installed_mw − mean_unavailable; → GW."""
    out: dict[str, float] = {}
    for ym in months:
        y, mo = int(ym[:4]), int(ym[5:7])
        m_start = datetime(y, mo, 1, tzinfo=PARIS).astimezone(timezone.utc)
        ny, nmo = (y + 1, 1) if mo == 12 else (y, mo + 1)
        m_end = datetime(ny, nmo, 1, tzinfo=PARIS).astimezone(timezone.utc)
        hours = (m_end - m_start).total_seconds() / 3600.0
        if hours <= 0:
            continue
        unavailable_mwh = 0.0
        for (s, e, u) in intervals:
            ov_start, ov_end = max(s, m_start), min(e, m_end)
            if ov_end > ov_start:
                unavailable_mwh += u * (ov_end - ov_start).total_seconds() / 3600.0
        available_mw = installed_mw - unavailable_mwh / hours
        out[ym] = round(available_mw / 1000.0, 2)
    return out


def installed_nuclear_mw() -> float:
    """National installed nuclear capacity (MW) from the committed fleet (precise)."""
    p = DATA_DIR / "fr_nuclear_sites.json"
    if p.exists():
        return float(json.loads(p.read_text(encoding="utf-8"))["fleet_total"]["capacity_mw"])
    return 0.0


def installed_nuclear_gw() -> float:
    """National installed nuclear capacity (GW) from the committed fleet, for context."""
    return round(installed_nuclear_mw() / 1000, 1)


# --------------------------------------------------------------------------- #
# ODRÉ I/O (output, mix, exchanges — open, no key)
# --------------------------------------------------------------------------- #

def _get(params: dict) -> dict:
    url = ODRE + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Wattlas pipeline)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def fetch_months() -> list[dict]:
    """Monthly national averages of the generation mix + exchanges + demand (MW)."""
    select = ("avg(nucleaire) as nuc, avg(hydraulique) as hyd, avg(gaz) as gas, "
              "avg(eolien) as eo, avg(solaire) as sol, avg(bioenergies) as bio, "
              "avg(charbon) as coal, avg(fioul) as oil, avg(ech_physiques) as ech, "
              "avg(consommation) as dem")
    return _get({
        "select": select,
        "group_by": "date_format(date_heure, 'yyyy-MM') as month",
        "order_by": "month desc", "limit": str(WINDOW_MONTHS),
    })["results"]


# --------------------------------------------------------------------------- #
# RTE Data Portal I/O (available capacity — OAuth2 client-credentials)
# --------------------------------------------------------------------------- #

def _rte_token(client_id: str, client_secret: str) -> str:
    """Exchange client credentials for an OAuth2 bearer token (RTE Data Portal).

    HTTP Basic header (base64 of "id:secret"), EMPTY body — grant_type is implied by the
    registered 'Web/Server' app type and must NOT be sent in the body."""
    key = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    req = urllib.request.Request(
        RTE_TOKEN_URL, data=b"",  # empty bytes -> POST
        headers={"Authorization": "Basic " + key,
                 "Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["access_token"]


def _rte_fetch_window(token: str, start: datetime, end: datetime) -> list[dict]:
    """All NUCLEAR unavailability records active in [start, end), following pagination."""
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    records: list[dict] = []
    cont: str | None = None
    for _page in range(50):  # safety cap; continuation_token expires fast, fetch back-to-back
        params = {
            "start_date": start.strftime(fmt), "end_date": end.strftime(fmt),
            "fuel_type": "NUCLEAR", "last_version": "true",
            "event_status": "ACTIVE", "date_type": "EVENT_DATE",
        }
        if cont:
            params["continuation_token"] = cont
        url = RTE_UNAVAIL_URL + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
        with urllib.request.urlopen(req, timeout=120) as r:
            body = json.load(r)
        records += body.get("generation_unavailabilities") or []
        cont = body.get("continuation_token")
        if not cont:
            break
    return records


def _chunks(start: datetime, end: datetime, days: int):
    cur = start
    step = timedelta(days=days)
    while cur < end:
        nxt = min(cur + step, end)
        yield cur, nxt
        cur = nxt


def build_available_by_month(months: list[str]) -> dict[str, float] | None:
    """Fetch RTE nuclear unavailability and reduce to {month: available_gw}, or None.

    Returns None (cleanly degrading to output) when credentials are absent or the API is
    unauthorized/unreachable — never fabricates a series."""
    cid = os.environ.get("RTE_CLIENT_ID")
    secret = os.environ.get("RTE_CLIENT_SECRET")
    if not cid or not secret:
        log.warning("RTE_CLIENT_ID / RTE_CLIENT_SECRET not set — available capacity "
                    "unavailable; degrading to output. Register at https://data.rte-france.com "
                    "and subscribe the app to 'Unavailability Additional Information'.")
        return None
    if not months:
        return None
    try:
        token = _rte_token(cid, secret)
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError, TimeoutError) as exc:
        code = getattr(exc, "code", None)
        log.warning("RTE OAuth token request failed (%s) — check RTE_CLIENT_ID / RTE_CLIENT_SECRET. "
                    "Degrading to output.", f"HTTP {code}" if code else type(exc).__name__)
        return None

    earliest = min(months)
    y, mo = int(earliest[:4]), int(earliest[5:7])
    start = datetime(y, mo, 1, tzinfo=PARIS).astimezone(timezone.utc) - timedelta(days=2)
    end = datetime.now(timezone.utc)
    raw: list[dict] = []
    try:
        for cs, ce in _chunks(start, end, _CHUNK_DAYS):
            raw += _rte_fetch_window(token, cs, ce)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            log.warning("RTE unavailability call denied (HTTP %s): the app authenticated OK but is not "
                        "authorized for this API. Subscribe your RTE application to 'Unavailability "
                        "Additional Information' (Generation) at https://data.rte-france.com, then re-run. "
                        "Degrading to output.", exc.code)
        else:
            log.warning("RTE unavailability fetch failed (HTTP %s) — degrading to output.", exc.code)
        return None
    except (urllib.error.URLError, TimeoutError) as exc:
        log.warning("RTE unavailability fetch failed (%s) — degrading to output.", type(exc).__name__)
        return None

    intervals = parse_intervals(raw)
    installed = installed_nuclear_mw()
    avail = monthly_available_gw(intervals, installed, months)
    log.info("RTE availability: %d outage records over %s..%s, installed %.0f MW",
             len(raw), months[0], months[-1], installed)
    return avail


def build() -> dict:
    rows = fetch_months()
    month_keys = sorted(r["month"] for r in rows)
    available = build_available_by_month(month_keys)
    months = assemble_months(rows, available)

    have_avail = available is not None and any(m["available_gw"] is not None for m in months)
    installed_gw = installed_nuclear_gw()

    # Sanity (do not skip): availability is an upper bound on output and <= installed.
    if have_avail:
        for m in months:
            a = m["available_gw"]
            if a is None:
                continue
            if a < m["nuclear_gw"] - 0.5 or a > installed_gw + 0.5:
                log.warning("available_gw out of range for %s: available %.2f, output %.2f, "
                            "installed %.1f — check the RTE join.", m["month"], a, m["nuclear_gw"], installed_gw)

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": SOURCE_BOTH if have_avail else SOURCE_OUTPUT,
        "unit": "GW",
        "installed_nuclear_gw": installed_gw,
        "available_note": (
            "available_gw = installed nuclear − mean declared unavailability (RTE OAuth "
            "Unavailability Additional Information feed); a declared upper-bound on producible "
            "power, not actual generation."
            if have_avail else
            "available_gw is null: 'available capacity' needs the RTE OAuth unavailability "
            "feed (RTE_CLIENT_ID/_SECRET); degraded to output (éCO2mix)."
        ),
        "period_start": months[0]["month"] if months else None,
        "period_end": months[-1]["month"] if months else None,
        "months": months,
    }
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "fr_nuclear_availability.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")

    if months:
        lo = min(months, key=lambda m: m["nuclear_gw"]); hi = max(months, key=lambda m: m["nuclear_gw"])
        exporting = sum(1 for m in months if m["net_export_gw"] > 0)
        log.info("Months: %d (%s..%s), installed nuclear %.1f GW",
                 len(months), out["period_start"], out["period_end"], installed_gw)
        log.info("Nuclear output: low %.1f GW (%s), high %.1f GW (%s)",
                 lo["nuclear_gw"], lo["month"], hi["nuclear_gw"], hi["month"])
        log.info("Net exporter in %d/%d months (France exports even during the summer dip)",
                 exporting, len(months))
        if have_avail:
            with_a = [m for m in months if m["available_gw"] is not None]
            log.info("Available capacity wired (RTE OAuth): %d/%d months, e.g. %s = %.1f GW available "
                     "vs %.1f GW output", len(with_a), len(months),
                     with_a[-1]["month"], with_a[-1]["available_gw"], with_a[-1]["nuclear_gw"])
        else:
            log.info("Available capacity: null (no RTE credentials) — view shows output only.")
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    build()
