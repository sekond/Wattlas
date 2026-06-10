# Prompt for Claude Code

Copy everything below the line into Claude Code, run from the root of your
Wattlas repo checkout, with this handoff folder placed at `design_handoff_dashboard_v2/`.

---

Implement the Dashboard v2 redesign described in
`design_handoff_dashboard_v2/README.md`. Read that README fully first — it is
the spec. The HTML/CSS/JS files in `design_handoff_dashboard_v2/frontend/` are
high-fidelity working prototypes of the target design; treat them as the source
of truth for visuals and behavior.

Context: this repo is a static, no-build-step site (vanilla JS + Chart.js,
GitHub Pages) that reads pre-computed JSON from `/data`. Read `CLAUDE.md` and
`data/schema.md` and respect their rules: fuel colors only from `fuels.js`,
display names from `util.js`, missing data renders as gaps (never fabricated
zeros), zones are bidding zones, every chart cites units and source.

Tasks:
1. Replace `frontend/dashboard.html` with the v2 desktop design: sidebar nav
   with scroll-spy, sticky zone/window control card, 8 story-driven panels,
   multi-zone comparison (up to 6 zones), date-range brush + presets, linked
   hover crosshair, dynamic story headlines and stat chips computed from data.
   Port the prototype's `v2/dash-core.js`, `v2/dash-panels-a.js`,
   `v2/dash-panels-b.js`, `v2/dash-boot.js`, `v2/dash.css` into the repo's file
   layout and naming conventions (rename as you see fit; keep modules small).
2. Add the mobile experience from `Mobile.html` + `v2/mobile.css` +
   `v2/mobile-panels.js` + `v2/dash-mobile-boot.js`: at ≤900px the dashboard
   becomes a tab-navigated single-panel app (bottom tab bar, lazy rendering,
   ≥44px touch targets). Decide whether to ship it as a media-query mode of
   dashboard.html or a separate page — prefer one responsive page if it stays
   maintainable.
3. Do NOT port anything marked PROTOTYPE ONLY in the README (React tweaks
   panel, iPhone bezel, Babel script tags). For the tweak alternatives
   (compact density, spread calendar heatmap, carbon scatter), implement the
   defaults (airy, bars, timeline); optionally expose the heatmap and scatter
   as plain in-page segmented toggles in their panels.
4. Keep the existing drill-down pages working; panel "Full view ↗" links must
   keep pointing at them. Don't change the data pipeline or JSON shapes.
5. Verify with a local static server from repo root: all 8 panels render with
   real data, zone comparison works on every applicable panel, the brush
   filters everything except Pulse/Mismatch/History, no console errors, and
   the page works at 390px width.

Match the prototypes pixel-for-pixel: tokens, type scale, chart colors, copy
(story templates, explainers, captions, tooltip texts) are all final.
