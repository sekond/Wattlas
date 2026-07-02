"""Shared ENTSO-E client factory with transient-error retries.

Why this exists: the ENTSO-E Transparency gateway intermittently returns
429/500/502/503/504 (the daily job has failed on a `504 Gateway Time-out` from a
`query_load` call). entsoe-py's own ``retry_count`` only retries *connection*
errors, not HTTP 5xx — a 504 reaches ``response.raise_for_status()`` and raises,
crashing the (fatal) builder and failing the whole refresh.

This mounts a urllib3 ``Retry`` on the requests session so those statuses are
retried with exponential backoff *before* entsoe-py inspects the response. Every
ENTSO-E builder should create its client via :func:`make_entsoe_client` rather
than instantiating ``EntsoePandasClient`` directly, so the resilience is uniform.
"""
from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter

try:  # urllib3 >= 1.26
    from urllib3.util.retry import Retry
except ImportError:  # pragma: no cover - very old urllib3
    from requests.packages.urllib3.util.retry import Retry  # type: ignore

from entsoe import EntsoePandasClient

# Statuses that are worth retrying: rate-limit + gateway/proxy transients. A 400
# (bad request) or 401 (bad token) is a real error and is NOT retried.
RETRY_STATUSES = (429, 500, 502, 503, 504)


def retrying_session(retries: int = 5, backoff: float = 1.5) -> requests.Session:
    """A requests session that retries transient 5xx/429 on GET with backoff.

    backoff schedule (seconds, capped by urllib3): ~1.5, 3, 6, 12, 24 — roughly
    45s of retrying before giving up, which comfortably rides out a brief gateway
    hiccup without masking a genuine multi-minute outage.
    """
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        status_forcelist=RETRY_STATUSES,
        allowed_methods=frozenset({"GET", "POST"}),
        backoff_factor=backoff,
        respect_retry_after_header=True,
        raise_on_status=False,  # return the final response so entsoe-py raises cleanly
    )
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def make_entsoe_client(
    token: str, *, retries: int = 5, backoff: float = 1.5, timeout: int = 300
) -> EntsoePandasClient:
    """An ``EntsoePandasClient`` hardened against transient ENTSO-E errors.

    ``timeout`` bounds a single request (entsoe-py forwards it to requests); the
    gateway is slow, so it is generous. Retries handle the 5xx/429 gateway
    transients that entsoe-py's own retry_count does not.
    """
    return EntsoePandasClient(
        api_key=token, session=retrying_session(retries, backoff), timeout=timeout
    )
