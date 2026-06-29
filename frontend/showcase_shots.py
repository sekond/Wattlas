#!/usr/bin/env python3
"""Capture the real app screens for frontend/showcase.html.

ON-DEMAND — Playwright is not a committed dependency:
    pip install playwright && python -m playwright install chromium
    python frontend/showcase_shots.py

Serves the repo root locally, renders each page at ~display resolution (1440px,
deviceScaleFactor 1 — a gentle downscale into the deck's frames so thin lines and
small text stay crisp), waits for the charts to draw, and writes stable PNGs to
frontend/public/showcase/. One capture per view across the five sections of the
live information architecture (frontend/ia.js); the deck (showcase.html) frames them.
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

# One capture per view, grouped by the live five-section information architecture
# (see frontend/ia.js). The deck (showcase.html) frames each of these. Filenames
# are stable so the deck's <img src> need not change when this list is re-ordered.
SHOTS = [
    # the zone-compare dashboard (now panels.html — dashboard.html is the editorial
    # landing). Keep the nav chrome here; it's the "compare bidding zones" hero.
    {"path": "frontend/panels.html", "out": "dashboard-multi.png", "h": 950,
     "clicks": ["FR", "NL", "AT"], "scrollto": ".ctrl", "clip": False},

    # 01 · The Daily Rhythm
    {"path": "frontend/pulse.html", "out": "pulse.png", "h": 900},
    {"path": "frontend/index.html", "out": "spread.png", "h": 900},
    {"path": "frontend/negative_prices.html", "out": "negative_prices.png", "h": 900},
    {"path": "frontend/capture_price.html", "out": "capture_price.png", "h": 900},
    {"path": "frontend/history.html", "out": "history.png", "h": 900},

    # 02 · What's on the Grid
    {"path": "frontend/mix.html", "out": "mix.png", "h": 900},
    {"path": "frontend/carbon.html", "out": "carbon.png", "h": 900},
    {"path": "frontend/mismatch.html", "out": "mismatch.png", "h": 900},
    {"path": "frontend/marginal_fuel.html", "out": "marginal_fuel.png", "h": 900},

    # 03 · Geography of Price
    {"path": "frontend/divergence.html", "out": "divergence.png", "h": 900},
    {"path": "frontend/wasted_wind.html", "out": "wasted_wind.png", "h": 900},
    {"path": "frontend/fr_nuclear.html", "out": "fr_nuclear.png", "h": 900},
    {"path": "frontend/nordic_zones.html", "out": "nordic.png", "h": 900},
    {"path": "frontend/uk_regional.html", "out": "uk_regional.png", "h": 900},
    {"path": "frontend/curtailment.html", "out": "curtailment.png", "h": 900},
    {"path": "frontend/locational_signal.html", "out": "locational_signal.png", "h": 900},

    # 04 · When the Grid is Tested
    {"path": "frontend/dunkelflaute.html", "out": "dunkelflaute.png", "h": 900},
    {"path": "frontend/storage.html", "out": "storage.png", "h": 900},
    {"path": "frontend/capacity_adequacy.html", "out": "capacity_adequacy.png", "h": 900},
    {"path": "frontend/iberian_blackout.html", "out": "iberian.png", "h": 900},

    # 05 · The Bill
    {"path": "frontend/flexibility.html", "out": "flexibility.png", "h": 900},
    {"path": "frontend/retail_wedge.html", "out": "retail_wedge.png", "h": 900},
    {"path": "frontend/industrial.html", "out": "industrial.png", "h": 900},
    # "Curtailment in €" reuses curtailment.png (same page, #cost section).
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
            page.wait_for_timeout(1800)
            for z in s.get("clicks", []):
                page.click(f'.zchip[data-z="{z}"]', timeout=4000)
                page.wait_for_timeout(350)
            if s.get("scrollto"):
                page.evaluate("sel => { const el = document.querySelector(sel); if (el) el.scrollIntoView({block:'start'}); }", s["scrollto"])
                page.wait_for_timeout(1400)
            if s.get("scrollby"):
                page.evaluate("n => window.scrollBy(0, n)", s["scrollby"])
                page.wait_for_timeout(700)
            clip = None
            if s.get("clip", True):  # crop the nav sidebar — frame just the .main content
                box = page.evaluate("() => { const m = document.querySelector('main.main, .main'); if (!m) return null; const r = m.getBoundingClientRect(); return {x: Math.max(0, r.x), width: r.width}; }")
                if box:
                    clip = {"x": box["x"], "y": 0, "width": min(box["width"], 1440 - box["x"]), "height": s["h"]}
            page.screenshot(path=str(OUT / s["out"]), full_page=False, clip=clip)
            ctx.close()
            print("captured", s["out"])
        browser.close()
    httpd.shutdown()
    print("done ->", OUT)


if __name__ == "__main__":
    main()
