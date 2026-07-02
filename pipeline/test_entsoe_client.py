"""Offline tests for the retrying ENTSO-E client factory.

No external network: the retry-behaviour test spins up a localhost HTTP server
that returns 504 twice, then 200, and proves the session rides through it — the
exact failure that crashed the daily job (a transient `504 Gateway Time-out`).
"""
from __future__ import annotations

import http.server
import socketserver
import threading

from entsoe_client import RETRY_STATUSES, make_entsoe_client, retrying_session


def test_retry_config_covers_gateway_5xx():
    client = make_entsoe_client("dummy-token")
    retry = client.session.get_adapter("https://web-api.tp.entsoe.eu/").max_retries
    assert 504 in retry.status_forcelist
    assert set(RETRY_STATUSES) <= set(retry.status_forcelist)
    assert retry.total >= 3
    assert "GET" in retry.allowed_methods
    assert retry.raise_on_status is False  # let entsoe-py raise on the final response
    assert client.timeout and client.timeout >= 60


def test_transient_504_is_retried_then_succeeds():
    fail_first = {"n": 2}  # 504 for the first two hits, then 200

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if fail_first["n"] > 0:
                fail_first["n"] -= 1
                self.send_response(504)
                self.end_headers()
                self.wfile.write(b"gateway timeout")
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")

        def log_message(self, *args):  # keep test output quiet
            pass

    with socketserver.TCPServer(("127.0.0.1", 0), Handler) as httpd:
        port = httpd.server_address[1]
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        # backoff=0 so the test doesn't sleep between retries
        session = retrying_session(retries=3, backoff=0)
        resp = session.get(f"http://127.0.0.1:{port}/api")
        httpd.shutdown()

    assert resp.status_code == 200
    assert resp.text == "ok"
    assert fail_first["n"] == 0  # both 504s were consumed, i.e. it actually retried
