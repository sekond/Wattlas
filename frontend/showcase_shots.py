#!/usr/bin/env python3
"""Capture the real app screens for frontend/showcase.html.

ON-DEMAND — Playwright is not a committed dependency:
    pip install playwright && python -m playwright install chromium
    python frontend/showcase_shots.py

Serves the repo root on a local port, renders each page at ~display resolution
(1440px desktop / 780px mobile, deviceScaleFactor 1 / 2 — a gentle downscale into
the deck's frames, so thin lines and small text stay crisp), waits for the charts to
draw, and writes stable PNGs to frontend/public/showcase/. The deck frames already
reference these filenames and fall back to a styled placeholder if one is missing.
"""
from __future__ import annotations

import functools
import http.server
import socketserver
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent          # repo root
OUT = ROOT / "frontend" / "public" / "showcase"
PORT = 8099

# (page path, output filename, viewport width, device_scale_factor, viewport height)
SHOTS = [
    ("frontend/dashboard.html",        "dashboard.png",    1440, 1, 900),
    ("frontend/dashboard.html",        "dashboard-m.png",   780, 2, 1500),
    ("frontend/index.html",            "spread.png",       1440, 1, 900),
    ("frontend/index.html",            "spread-m.png",      780, 2, 1500),
    ("frontend/nordic_zones.html",     "nordic.png",       1440, 1, 900),
    ("frontend/dunkelflaute.html",     "dunkelflaute.png", 1440, 1, 900),
    ("frontend/storage.html",          "storage.png",      1440, 1, 900),
    ("frontend/iberian_blackout.html", "iberian.png",      1440, 1, 900),
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
        for path, fname, w, dsf, h in SHOTS:
            ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=dsf)
            page = ctx.new_page()
            page.goto(f"http://127.0.0.1:{PORT}/{path}", wait_until="networkidle")
            page.wait_for_timeout(1800)            # let Chart.js / D3 finish drawing
            page.screenshot(path=str(OUT / fname), full_page=False)   # the top fold, crisp
            ctx.close()
            print("captured", fname)
        browser.close()
    httpd.shutdown()
    print("done ->", OUT)


if __name__ == "__main__":
    main()
