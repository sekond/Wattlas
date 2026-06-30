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

# Frame each view from the top of .main down to the BOTTOM of its first chart panel
# — a clean "hero + first full chart" shot. Avoids the old fixed 900px clip that
# sliced charts in half (and missed History's chart, which sits below 900px).
CLIP_JS = r"""
() => {
  const main = document.querySelector('main.main, .main');
  if (!main) return null;
  const mr = main.getBoundingClientRect();
  const x = Math.max(0, mr.x);
  const width = Math.min(mr.width, 1440 - x);
  let chart = null;
  for (const el of main.querySelectorAll('canvas, svg')) {
    const r = el.getBoundingClientRect();
    if (r.width > 250 && r.height > 120) { chart = el; break; }  // first real chart, not a chevron/icon
  }
  let bottom = 760;
  if (chart) {
    const panel = chart.closest('.card, .panel, section, .block') || chart;
    bottom = panel.getBoundingClientRect().bottom;  // page is at scroll-top, so this is the document y
  }
  const height = Math.min(1300, Math.max(720, Math.round(bottom + 28)));
  return { x: Math.round(x), y: 0, width: Math.round(width), height };
}
"""


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
            clipped = s.get("clip", True)
            # clipped shots get a tall viewport so the first chart panel has room;
            # full-chrome shots (dashboard-multi) keep their requested height.
            vh = 1300 if clipped else s["h"]
            ctx = browser.new_context(viewport={"width": 1440, "height": vh}, device_scale_factor=1)
            page = ctx.new_page()
            page.goto(f"http://127.0.0.1:{PORT}/{s['path']}", wait_until="networkidle")
            page.wait_for_timeout(2500)  # let Chart.js / D3 draw after the data fetch
            for z in s.get("clicks", []):
                page.click(f'.zchip[data-z="{z}"]', timeout=4000)
                page.wait_for_timeout(350)
            # nudge the scroll to trigger any lazy / observer-driven chart draws, back to top
            page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(600)
            page.evaluate("() => window.scrollTo(0, 0)")
            page.wait_for_timeout(1200)
            if s.get("scrollto"):
                page.evaluate("sel => { const el = document.querySelector(sel); if (el) el.scrollIntoView({block:'start'}); }", s["scrollto"])
                page.wait_for_timeout(1400)
            if s.get("scrollby"):
                page.evaluate("n => window.scrollBy(0, n)", s["scrollby"])
                page.wait_for_timeout(700)
            clip = None
            if clipped:  # frame .main from the top to the first chart panel's bottom
                page.evaluate("() => window.scrollTo(0, 0)")
                clip = page.evaluate(CLIP_JS)
            page.screenshot(path=str(OUT / s["out"]), full_page=False, clip=clip)
            ctx.close()
            print("captured", s["out"], "->", (f"{clip['width']}x{clip['height']}" if clip else "full"))
        browser.close()
    httpd.shutdown()
    print("done ->", OUT)


if __name__ == "__main__":
    main()
