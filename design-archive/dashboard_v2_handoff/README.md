# Handoff: Wattlas Dashboard v2 (desktop + mobile)

## Overview
A redesign of the Wattlas combined dashboard (`frontend/dashboard.html` in the
[sekond/Wattlas](https://github.com/sekond/Wattlas) repo). It replaces the long
stacked scroll with a sidebar-navigated, story-driven layout, adds cross-cutting
exploration (multi-zone comparison, a date-range brush, linked hover), and a
phone-native mobile variant with bottom-tab navigation.

The target codebase is plain HTML/CSS/JS + Chart.js with **no build step**, served
statically (GitHub Pages) and reading pre-computed JSON from `/data`. The design
files here follow the same conventions, so implementation is largely a port —
adopt the codebase's existing file/naming patterns and keep the no-backend contract.

## About the Design Files
The files in this bundle are **design references created in HTML** — working
prototypes showing intended look and behavior. The task is to recreate them inside
the Wattlas repo following its established patterns (`util.js`, `fuels.js`,
`styles.css` design-token conventions, schema rules in `data/schema.md`),
not to copy them in verbatim. In particular:

- `frontend/v2/dash-tweaks.jsx`, `frontend/v2/tweaks-panel.jsx` (React Tweaks
  panel) and `frontend/v2/ios-frame.jsx` + `Mobile Mockup.html` (iPhone bezel)
  are **prototyping chrome only — do not implement**. The tweak alternatives they
  toggle (density, calendar heatmap, carbon scatter) are documented below; pick
  defaults or expose them as plain in-page toggles if desired.
- React/Babel script tags exist only for that chrome. The production dashboard
  must remain dependency-free vanilla JS + Chart.js.

## Fidelity
**High-fidelity.** Colors, typography, spacing, copy, chart configurations and
interactions are final. Recreate pixel-perfectly. All charts run on the real
`/data` JSON (this bundle includes a snapshot so the prototypes work standalone:
serve the bundle root and open `frontend/Dashboard v2.html`).

## Screens / Views

### 1 · Desktop dashboard (`frontend/Dashboard v2.html`)
Replaces `dashboard.html`. Two-column grid shell:

- **Sidebar** (`232px`, sticky, full viewport height, right border
  `0.5px solid rgba(40,36,20,0.13)`): brand block ("Wattlas" 19px/600 +
  "European electricity, explained" 12px hint color), then 8 numbered nav links
  (13.5px, 7px 10px padding, 9px radius). Active link: `--surface-2` background,
  2px amber left border, scroll-spy driven (IntersectionObserver,
  rootMargin `-20% 0 -70% 0`). Footer pinned to bottom: data attribution, 11px.
- **Content column**: max-width `1060px`, centered, 36px side padding.

**Sticky control header** (z-30, fades into bg via gradient): a white card
(radius 14, border, shadow `0 1px 4px rgba(40,36,20,0.04)`) holding:
- *Zones row*: label "ZONES" (11px uppercase, letter-spacing .07em), then 6 zone
  chips (pill, 13px, colored 8px dot). One chip is **primary** (dark fill
  `#26251f`, light text); others tapped become **compare** (surface-2 fill,
  hint border). Up to all 6 zones selectable. Tapping the primary removes it and
  promotes the first comparison. Hint text explains state.
- *Window row*: segmented presets `30d / 90d / 6mo / All` + a **brush strip**
  (flex-1, min 220px, h 44px, surface-2 bg, radius 6): mini bar chart of DE-LU
  daily spread over the whole period drawn on canvas at devicePixelRatio.
  Drag selects a date range (live amber selection overlay:
  `rgba(184,134,11,0.16)` fill, 1.5px amber edges); selections < 3 days or
  double-click reset to All. Active range shown as "3 Jun 2025 – 2 Jun 2026"
  caption on the right (11.5px, tabular numerals).

**Eight panels**, each a white card (radius 14px, 24px padding, 28px gap, one
`<section class="panel" id="…">` per topic) with identical anatomy:
1. **Kicker** row: `N · NAME — tagline` (11.5px uppercase amber 600,
   letter-spacing .09em); optional "Full view ↗" link (12px hint) to the
   existing drill-down page on the right.
2. **Story headline** `h2` (21px/500, line-height 1.35, max 64ch): a sentence
   **computed from live data** with key numbers wrapped in colored `<strong>`
   (amber/red/green/blue). Templates per panel are in the JS (e.g. Pulse:
   "Power in {zone} is cheapest around {HH:00} and dearest around {HH:00} — a
   {€N} swing in an average day.").
3. **Explainer** paragraph (13px muted, max 76ch) ending in an ⓘ info button
   (16px circle) that opens a dark tooltip popover (max 300px, `#26251f` bg,
   12.5px) with methodology text. One tooltip open at a time; Escape/scroll/
   outside-click closes.
4. Optional **segmented toggles** (see per-panel notes).
5. **Chart** (`300px` tall desktop, `250px` mobile; Chart.js 4, `animation:false`,
   `interaction: index/intersect:false`, no legend plugin — custom HTML legends).
   Ticks 11px `#807e74`; y-grid `rgba(40,36,20,0.05)`; x-grid hidden; x-axis
   border `rgba(40,36,20,0.15)`.
6. **Stat chips** row: pills (surface-2 bg, 12.5px, label muted + value 600
   tabular; value colored `#3b6d11` positive / `#a32d2d` negative), some with
   their own ⓘ tooltip.
7. **Caption** (11.5px hint): units, methodology, source.

Per-panel specifics:
- **1 Pulse** — avg price by hour-of-day. Single zone: weekday (solid, zone
  color, 2.4px) vs weekend (amber dashed `[5,4]`, 1.8px) lines, tension .35.
  Comparing: one line per selected zone (primary 2.6px, others 1.8px).
  Stats: cheapest hour, priciest hour, daily swing.
- **2 Spread** — daily TB1 bars: blue `rgba(24,95,165,0.55)`; days with
  negative-price hours red `rgba(163,45,45,0.75)`; widest day solid amber;
  overlaid 14-day rolling mean line (`#26251f`, 1.6px). Comparing: switches to
  14-day rolling mean lines per zone. Alternative style (tweak): **calendar
  heatmap** — week columns × Mon–Sun rows, blue alpha `0.08+0.84·(v/max)^0.6`,
  red outline = negative-price day, month labels above, custom hover tooltip.
  Stats: avg spread, widest day, negative-price hours, arbitrage ceiling (ⓘ).
- **3 Mix** — stacked area by fuel using the canonical `fuels.js` palette/order
  (fuel color is identical in every view; gaps stay gaps, never zeros).
  Toggles: `Day by day / Average day` and `GW / % share`. Custom HTML legend.
  Stats: renewable share, top source, mean carbon intensity.
- **4 Mismatch** — residual load curve (blue 2.4px, teal fill
  `rgba(74,166,160,0.18)` to zero) + total demand (grey dashed 1.4px).
  Tooltip adds "covered by wind+solar" = demand − residual.
  Stats: trough, peak, midday→evening swing, hours wind+solar >50%.
- **5 Divergence** — toggle `Prices by zone / Flow vs price gap`. Prices: monthly
  mean per zone; selected zones colored, unselected greyed `rgba(120,118,110,0.28)`
  at 1.1px. Flows: bars = net flow on a German border (positive = exporting,
  darker blue) + red price-gap line on a right axis; amber dots flag congested
  months (≥20% hours at capacity). Border auto-picks the first selected
  non-DE zone with flow data, else FR.
- **6 Carbon** — daily intensity line (`#5a3a22`, fill `rgba(90,58,34,0.10)`);
  tooltip shows that day's renewable share. Alternative (tweak): scatter of
  renewable-share (x, 0–100%) vs intensity (y) per day, per selected zone.
  Stats: mean intensity (ⓘ methodology), cleanest hour, dirtiest hour.
- **7 Curtailment** — green bars `rgba(59,109,17,0.7)` curtailed MWh/day +
  red line of negative-price hours (right axis). Graceful empty state when the
  feed is unavailable ("Awaiting data source…" centered hint text).
- **8 History** — toggle `Multi-year / Seasonal / Year on year`. Multi-year:
  daily TB1 line with drag/wheel zoom (chartjs-plugin-zoom, amber drag fill).
  Seasonal: years folded onto 12 months. Yearly: bars (max thickness 64).
  **Exempt from the global window control** (note this in the explainer).
  Stats: YoY % (red if widening), years covered, widest year, total neg hours.

### 2 · Mobile app (`frontend/Mobile.html`, shown framed in `Mobile Mockup.html`)
Phone-native shell at 402px, reusing the same renderers:
- **Sticky header**: brand row (17px/650 + period caption 10.5px), horizontally
  scrollable zone-chip row (38px tall chips, hidden scrollbar), full-width
  window segmented control (38px buttons). 58px top padding clears the status bar.
- **One panel per screen** — same panel anatomy (story 17px, kicker stacked as
  its own block above the headline); only the active panel is rendered
  (lazy, on tab switch).
- **Bottom tab bar**: fixed, frosted (`backdrop-filter: blur(14px)`, translucent
  bg, top hairline), horizontally scrollable pills (≥44px tall) numbered 1–8;
  active pill dark-filled. 30px bottom padding clears the home indicator.
- All hit targets ≥38px; charts 250px tall; tools segments stretch full width.

## Interactions & Behavior
- **Global state** `{ zone, compare[], range }` — every panel re-renders on
  change (mobile: only the active panel).
- **Zone chips**: tap to add comparison; tap a comparison to remove; tap primary
  to promote next comparison; consistent zone colors everywhere:
  `DE_LU #185fa5 · FR #a3402d · NL #b8860b · BE #2f7d78 · PL #7d5ba6 · AT #3b6d11`.
- **Brush / presets**: filter all date-indexed panels (Pulse profiles, Mismatch,
  and History multi-year are period-wide and exempt). Live preview while
  dragging (selection overlay + period caption update), full re-render on release.
- **Linked hover**: charts register in two key-spaces — `date` (daily series)
  and `hour` (24h profiles). Hovering one chart draws a dashed amber guide
  (`rgba(184,134,11,0.55)`, dash [3,3]) at the same x-key in every sibling
  chart (implemented as a Chart.js plugin; registry pruned on chart destroy).
- **Scroll-spy** sidebar; anchor links scroll smoothly (`scroll-margin-top:132px`).
- **Tooltips**: Chart.js default tooltips, `itemSort` descending for stacks.
- No entrance animations; `animation:false` everywhere for instant re-renders.

## State Management
No framework — module-scope singletons:
- `D` loaded JSON (all fetched in parallel at boot; `loadJSON` tries
  `../data/`, `data/`, `/data/` so it works from repo root or `/frontend`).
- `S = { zone:"DE_LU", compare:[], range:null }` + chart-style flags.
- `charts` map (canvas id → Chart) — `draw()` destroys + recreates per render.
- `rerenders[]` — render fns invoked by `renderAll()`.
- Failure mode: if `spread_by_zone.json` missing, show a single status line;
  per-zone gaps show in-panel "No data for this zone" empty states.

## Design Tokens
```
--bg #faf9f5 · --surface #ffffff · --surface-2 #f1efe8 · --surface-3 #e9e6dc
--text #26251f · --muted #5b5a52 · --hint #807e74
--border rgba(40,36,20,0.13) · --border-soft rgba(40,36,20,0.07)
--blue #185fa5 · --red #a32d2d · --green #3b6d11 · --amber #b8860b
radius 14px (cards) / 9px (controls) / 999px (chips)
card padding 24px · section gap 28px · chart heights 300/230px
density "compact" tweak: 16px padding, 16px gap, 230/180px charts
type: system stack; story 21px/500 (17px mobile); explainer 13px;
kicker 11.5px uppercase amber; captions/stats 11–12.5px; ticks 11px
```
Fuel colors: keep `fuels.js` as the single source of truth.

## Assets
None — no images or icon fonts. ⓘ buttons are styled text. External libs:
Chart.js 4.4.1, chartjs-adapter-date-fns 3.0.0, chartjs-plugin-zoom 2.0.1 (CDN).

## Screenshots
`screenshots/desktop-overview.png` — sidebar, control card (zone chips + window
presets + brush strip) and the top of the Pulse panel. The HTML prototypes
themselves are the authoritative visual reference — open them in a browser for
every other view (capture tooling was unavailable when this bundle was built).

## Files
```
frontend/Dashboard v2.html      desktop dashboard (markup + script loading order)
frontend/Mobile.html            mobile app shell
frontend/Mobile Mockup.html     iPhone-framed presentation of Mobile.html (reference only)
frontend/v2/dash.css            all desktop tokens/components + responsive rules
frontend/v2/mobile.css          mobile shell overrides (header, tab bar, panels)
frontend/v2/dash-core.js        state, data loading, brush, linked hover, chart helpers
frontend/v2/dash-panels-a.js    Pulse, Spread (+heatmap), Mix renderers
frontend/v2/dash-panels-b.js    Mismatch, Divergence, Carbon, Curtailment, History
frontend/v2/dash-boot.js        desktop boot: chips, scroll-spy, tooltips, wiring
frontend/v2/mobile-panels.js    mobile panel markup builder
frontend/v2/dash-mobile-boot.js mobile boot: tabs, lazy render
frontend/v2/dash-tweaks.jsx     PROTOTYPE ONLY — tweaks chrome, do not port
frontend/v2/tweaks-panel.jsx    PROTOTYPE ONLY
frontend/v2/ios-frame.jsx       PROTOTYPE ONLY — device bezel
frontend/util.js, fuels.js      unchanged shared helpers from the repo
data/                           JSON snapshot so the prototypes run standalone
```
To preview: serve this folder (`python3 -m http.server`) and open
`frontend/Dashboard v2.html` and `frontend/Mobile Mockup.html`.
