# Handoff: Wattlas — Unified Navigation & Responsive Shell

## Overview
Wattlas is a static web app for exploring the temporal and financial side of European
electricity markets. It has **eight analytical views** plus **two long-form "map story"
pages**, all reading from pre-computed JSON (no live backend).

This handoff documents the work done in this round: a **single, unified site navigation**
that replaced the inconsistent per-page menus, plus the **responsive shell** (desktop
sidebar ↔ mobile scroll-nav) that makes the site usable on phones.

## About the Design Files
The files in this bundle are **design references created in HTML** — working prototypes
that show the intended look, structure, and behavior. They are not meant to be shipped
verbatim. The task is to **recreate this navigation system and responsive shell in the
target codebase's environment** (React/Vue/Svelte/etc.) using its established patterns,
or — if Wattlas continues as a static HTML site — to adopt `nav.js` + the shared CSS
directly as the single source of navigation truth.

The key architectural idea to preserve regardless of framework: **navigation is defined
in exactly one place and injected/rendered on every page.** Do not hand-author the menu
per page — that is the exact bug this round fixed.

## Fidelity
**High-fidelity.** Final colors, typography, spacing, grouping, active states, and
responsive breakpoints are all settled. Recreate pixel-accurately.

---

## The Navigation System (the core deliverable)

### Single source of truth
All links live in one ordered data structure (`GROUPS` in `nav.js`). Both the desktop
sidebar and the mobile menu are generated from it, and the current page is auto-marked
active by matching `location.pathname`. To add/rename/reorder a nav item you edit one
array — never the markup of N pages.

The link set (in order):

| Group | Label | Target | Marker | Notes |
|---|---|---|---|---|
| — | Dashboard | `dashboard.html` | ⌂ | Home |
| The eight views | Pulse | `pulse.html` | 1 | |
| | Spread | `index.html` | 2 | |
| | Mix | `mix.html` | 3 | |
| | Mismatch | `mismatch.html` | 4 | |
| | Divergence | `divergence.html` | 5 | |
| | Carbon | `dashboard.html#carbon` | 6 | section link — never marked active as a page |
| | Curtailment | `curtailment.html` | 7 | |
| | History | `history.html` | 8 | |
| Map stories | Germany North - South Grid | `wasted_wind.html` | DE | featured (amber accent) |
| | France Nuclear | `fr_nuclear.html` | FR | featured (amber accent) |

The two "Map stories" are visually featured (amber markers, grouped under their own
heading) because they were the new pages that the old navs couldn't even reach.

### Desktop — persistent left sidebar (`.shell` → `.side`)
- Layout: CSS grid `grid-template-columns: 244px minmax(0,1fr)`. Sidebar is the first
  column, page content (`.main`) the second.
- Sidebar is `position: sticky; top: 0; height: 100vh; overflow-y: auto` so it stays put
  while content scrolls.
- Structure: brand block → grouped `<nav class="sidenav">` with uppercase group labels
  (`.navgroup`) → footer credit (`.foot`, pinned to bottom with `margin-top:auto`).
- Each link: a numeric/letter marker (`.n`) + label, optional subtitle (`.sub`).
- **Active state:** `background: var(--surface-2)`, `font-weight: 600`, and a 2px
  `border-left` in `--amber`. `aria-current="page"` is set.
- Story links (`.story`): marker rendered in `--amber`, bold.

### Mobile (<900px) — horizontal scroll-nav (`.topbar` → `.topnav`)
- The sidebar (`.side`) is `display:none`; `.shell` becomes `display:block`.
- A sticky top bar appears with the brand and a horizontally-scrollable pill row
  carrying the same links (`overflow-x:auto`, `-webkit-overflow-scrolling:touch`).
- Pills are rounded (`border-radius:999px`); active pill gets `--surface-2` fill +
  border. Story pills use an amber tint, and the active story pill is a solid amber fill.
- A thin divider (`.div`) separates the eight views from the map stories.
- On load, the active pill is scrolled into view (`nav.scrollLeft = active.offsetLeft-16`)
  so users can see where they are.

### Critical interaction detail — sticky collision
Some pages (the dashboard, and any with a `.bar` zone/window control or a `.jumpnav`)
have **their own sticky bar**. Two competing sticky bars overlap and break the layout.
`nav.js` detects `document.querySelector(".bar, .jumpnav")` and, if present, adds
`.static` to the mobile `.topbar` so it sits in normal flow instead of sticking.
**Preserve this rule** — it is the difference between a clean and a broken dashboard on
mobile.

### Why CSS is injected by `nav.js` (not only in `styles.css`)
`index.html` (the validated "Spread" view) is self-contained and intentionally does NOT
load `styles.css`. So `nav.js` injects its own `<style id="wattlas-nav-css">` block at
runtime, with an `--amber` fallback (`#b8860b`) for that one page. This guarantees the
nav looks correct on **every** page regardless of which stylesheet it loads. In a
component framework this concern disappears — the nav component carries its own styles.

### Integration contract for a static page
A page only needs this skeleton; `nav.js` does the rest:
```html
<body>
  <div class="shell"><main class="main">
    … page content …
  </main></div>
  <script src="nav.js"></script>
</body>
```
Map-story pages additionally wrap content in `<div class="main-inner">` (max-width 1080px,
centered) for comfortable long-form reading width.

---

## Design Tokens
From `styles.css` `:root` (light, warm-paper theme):

| Token | Value | Use |
|---|---|---|
| `--bg` | `#faf9f5` | page background |
| `--surface` | `#ffffff` | cards |
| `--surface-2` | `#f1efe8` | KPI tiles, active nav fill |
| `--text` | `#2b2a27` | primary text |
| `--muted` | `#5f5e5a` | secondary text / nav links |
| `--hint` | `#888780` | tertiary / markers / labels |
| `--border` | `rgba(0,0,0,0.12)` | hairlines (drawn at 0.5px) |
| `--blue` | `#185fa5` | data series |
| `--red` | `#a32d2d` | negative values |
| `--green` | `#3b6d11` | positive values |
| `--amber` | `#b8860b` | brand accent, active state, map-story highlight |
| `--radius` | `12px` | cards |
| `--radius-sm` | `8px` | tiles, controls, nav links |

**Typography:** system stack — `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
sans-serif`; body `line-height: 1.6`. Sidebar links 13.5px, group labels 10px uppercase
`letter-spacing:.08em`, brand 19px/600.

**Nav-specific measurements:** sidebar width 244px; sidebar padding `26px 16px 20px 22px`;
link padding `7px 10px`; marker column 16px; mobile breakpoint **900px**; mobile pill
padding `6px 12px`, `border-radius:999px`.

---

## Screens / Views
All views share the nav shell described above. Each is a single HTML page that fetches
its JSON from `../data/` and renders with Canvas/D3.

- **Dashboard** (`dashboard.html`) — home; KPIs + sticky zone/window control bar +
  jump-nav. (Has its own sticky bar → mobile nav goes static.)
- **Pulse** (`pulse.html`) — intraday price rhythm.
- **Spread** (`index.html`) — the validated reference view; self-contained styling.
- **Mix** (`mix.html`) — generation mix.
- **Mismatch** (`mismatch.html`) — supply/demand mismatch.
- **Divergence** (`divergence.html`) — cross-zone price divergence.
- **Curtailment** (`curtailment.html`) — curtailed renewable energy.
- **History** (`history.html`) — long-run price history.
- **Germany North - South Grid** (`wasted_wind.html`) — map story; D3 choropleth of
  Landkreis capacity, regional balance, top plants. Reads `de_*` + `geo/landkreise.topo.json`.
- **France Nuclear** (`fr_nuclear.html`) — map story; reactor sites, availability,
  regional output, costs. Reads `fr_*` + `geo/regions_fr.topo.json`.

## Responsive Behavior
- **≥900px:** two-column shell (244px sidebar + content).
- **<900px:** sidebar hidden, sticky/`static` top scroll-nav, `.main` padding reduced to
  `0 14px 64px`.
- **≤640px:** KPI grid drops to 2 columns, two-column rows stack to one.
- Charts use `max-width:100%`; chart wrappers shrink to ~220px tall on small screens.

## Scope of this bundle
This package contains **only the files required to evolve the navigation and responsive
shell** — the actual design work of this round. Runtime payloads and charting plumbing
(the `data/` JSON, `geo/` TopoJSON, `dash/` modules, `geo.js`/`fuels.js`/`util.js`
renderers, and the iPhone preview harness) are **intentionally omitted**: they are not part
of the design being evolved, and they live in the main Wattlas repo.

The pages here will render their nav and full layout correctly without data — the nav is
injected by `nav.js` independent of any fetch. Charts/maps will simply show their empty
state, which is irrelevant to evolving the navigation.

## Files in this bundle
```
README.md           ← this document
frontend/
  nav.js            ← single source of navigation (links + injected CSS + active state)
  styles.css        ← shared design tokens & components (nav CSS now lives in nav.js)
  dashboard.html  index.html  pulse.html  mix.html  mismatch.html
  divergence.html  curtailment.html  history.html
  wasted_wind.html  fr_nuclear.html           ← the two map stories
```

## Implementation checklist for the developer
1. Recreate the **one-source-of-truth nav** (the `GROUPS` array) — render it as a
   sidebar on desktop and a horizontal scroll-nav under 900px.
2. Mark the current route active (incl. `aria-current`); never hand-mark per page.
3. Feature the two map stories as a distinct group with the amber accent.
4. Reproduce the **sticky-collision rule**: pages with their own sticky toolbar must not
   double-stick the mobile nav.
5. Verify the active mobile pill scrolls into view on load.
6. Keep the design tokens and the 900 / 640px breakpoints.
