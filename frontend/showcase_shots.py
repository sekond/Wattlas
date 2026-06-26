#!/usr/bin/env python3
"""Capture the real app screens for frontend/showcase.html.

ON-DEMAND — Playwright is not a committed dependency:
    pip install playwright && python -m playwright install chromium
    python frontend/showcase_shots.py

Serves the repo root locally, renders each page at ~display resolution (1440px,
deviceScaleFactor 1 — a gentle downscale into the deck's frames, so thin lines and
small text stay crisp), waits for the charts to draw, and writes stable PNGs to
frontend/public/showcase/. The multi-zone shot selects extra bidding zones and
scrolls to the comparing panels so the deck can show the dashboard's headline
multi-country capability.
"""
from __future__ import annotations

import functools
import http.server
import socketserver
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "frontend" / "public" / "showcase"
PORT = 8099

SHOTS = [
    {"path": "frontend/dashboard.html", "out": "dashboard.png", "h": 950},
    # multi-country: add three zones to Germany, then frame the comparing control bar + panels
    {"path": "frontend/dashboard.html", "out": "dashboard-multi.png", "h": 950,
     "clicks": ["FR", "NL", "AT"], "scrollto": ".ctrl"},
    {"path": "frontend/index.html", "out": "spread.png", "h": 900},
    {"path": "frontend/nordic_zones.html", "out": "nordic.png", "h": 900},
    {"path": "frontend/dunkelflaute.html", "out": "dunkelflaute.png", "h": 900},
    {"path": "frontend/storage.html", "out": "storage.png", "h": 900},
    {"path": "frontend/iberian_blackout.html", "out": "iberian.png", "h": 900},
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    print(f"serving {ROOT} on :{PORT}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for s in SHOTS:
            ctx = browser.new_context(viewport={"width": 1440, "height": s["h"]}, device_scale_factor=1)
            page = ctx.new_page()
            page.goto(f"http://127.0.0.1:{PORT}/{s['path']}", wait_until="networkidle")
            page.wait_for_timeout(1800)                      # let Chart.js / D3 finish
            for z in s.get("clicks", []):
                page.click(f'.zchip[data-z="{z}"]', timeout=4000)
                page.wait_for_timeout(350)
            if s.get("scrollto"):
                page.eval_on_selector(s["scrollto"], "el => el.scrollIntoView({block:'start'})")
                page.wait_for_timeout(1400)                  # re-render the comparing panels
            page.screenshot(path=str(OUT / s["out"]), full_page=False)
            ctx.close()
            print("captured", s["out"])
        browser.close()
    httpd.shutdown()
    print("done ->", OUT)


if __name__ == "__main__":
    main()
