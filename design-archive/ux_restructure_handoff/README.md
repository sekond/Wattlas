# Handoff: Wattlas UX Restructure (information architecture, landing, footer, mobile)

## Overview

Wattlas had grown to **26 destinations in one flat sidebar**, grouped by how the data
pipeline produced them — *“The Eight Views” / “Deep dives” / “Value layer.”* Those are
build-history categories, not a visitor's questions, so the menu was an undifferentiated
wall of near-equal links with no hierarchy, no path through it, and no editorial on-ramp.

This handoff specifies a restructure that:

1. **Regroups all 26 views under five plain-language questions** (the core deliverable).
2. Adds an **editorial landing page** that orients a first-time visitor and routes into
   the five sections.
3. Adds a **section-hub** pattern (each question → a page of its views).
4. Adds a **site footer** with the standard pages (About, How it works, Data sources,
   Privacy, Terms & Disclaimer, Contact).
5. Adds a **phone-native mobile experience** with a bottom tab bar carrying the five
   sections.

It deliberately **does not** change the internals of the 26 existing view pages (their
charts, KPIs, data wiring). This is a navigation / landing / chrome restructure — *how you
find a view*, not *what the view shows*.

---

## About the design files

The files in `frontend/` (the `Wattlas Redesign.html` prototype + `redesign/`) are **design
references created in HTML** — a clickable prototype that demonstrates the intended
structure, layout, copy and behaviour. They are **not production code to copy verbatim.**

This bundle is **self-contained and runnable**: it ships the prototype *and* the current
site's real pages, shared JS/CSS, map basemaps and the full `data/` set, mirroring the
repo's `frontend/` + `data/` layout. See **Running this bundle** below.

Wattlas's real codebase is a **multi-page static site** (vanilla JS, no framework,
GitHub Pages): each of the 26 views is its own `.html` file that loads `nav.js` for site
chrome and fetches `data/*.json`. Your task is to **recreate this design within that
existing environment and its patterns** — primarily by rewriting `frontend/nav.js`, adding
a landing page, a footer, and the standard pages.

> ### ⚠️ Critical: do NOT reproduce the prototype's iframe mechanism
> The prototype is a **single-page app** that fakes multi-page navigation with a hash
> router and embeds each real view in an `<iframe src="…?embed=1">`. That iframe approach
> exists **only because a prototype has to live in one file.** The real site already has 26
> standalone pages — in production you simply **apply the new `nav.js` to each existing
> page** and add the new landing/footer/standard pages as real files. No iframes, no SPA
> router, no `embed=1` in production. (The `embed` branch added to `nav.js` is included as
> `frontend/nav.js` for reference only; drop it in the real build.)

---

## Running this bundle

The bundle mirrors the live repo layout (`frontend/` beside `data/`), so the view pages
resolve their `../data/*.json` fetches when served over HTTP. From the bundle root:

```
python -m http.server 8000
```

then open:
- `http://localhost:8000/frontend/Wattlas%20Redesign.html` — the redesign prototype
  (desktop + mobile; resize the window below 900px for the bottom-tab mobile layout).
- `http://localhost:8000/frontend/Wattlas%20Mobile.html` — the mobile screens in device frames.
- `http://localhost:8000/frontend/pulse.html` (etc.) — the current standalone views, live.

> Serve it — don't open via `file://`, or the `fetch()` calls for the JSON will be blocked.

---

## Fidelity

**High-fidelity** for layout, typography, colour, spacing, copy and interaction — recreate
those pixel-faithfully. The **information architecture (the 5-section mapping below) is the
authoritative deliverable** and must be implemented exactly. The schematic canvas
“thumbnails” on the landing cards are illustrative placeholders — keep them, replace with
real sparklines, or drop them, at your discretion.

---

## The new information architecture (authoritative)

Five sections, in order. Every one of the 26 destinations maps to exactly one section.
The canonical source of this mapping is `design/redesign/ia.js` (`WATTLAS_IA.sections`).

### 01 · The Daily Rhythm — *“When does power move?”* — accent `--s-blue`
Lede: *Electricity has no single price — it has a price every hour. This is how it swings
between cheap and expensive, day to day and year to year.*
| View | Existing page |
|---|---|
| Pulse | `pulse.html` |
| Spread | `index.html` |
| Negative Prices | `negative_prices.html` |
| Capture Price | `capture_price.html` |
| History | `history.html` |

### 02 · What's on the Grid — *“What's flowing through the wires?”* — accent `--s-green`
Lede: *Behind every price is a physical mix of fuels. This is what generates Europe's power
hour to hour — and how clean, or dirty, each hour really is.*
| View | Existing page |
|---|---|
| Generation Mix | `mix.html` |
| Carbon Intensity | `carbon.html` |
| Residual Load (Mismatch) | `mismatch.html` |
| Marginal Fuel | `marginal_fuel.html` |

### 03 · Geography of Price — *“Where does power flow — and why do prices split?”* — accent `--s-amber`
Lede: *One country, one price — until the grid can't carry the power across it. Four
countries, four answers to the same congestion problem, on the map.*
| View | Existing page |
|---|---|
| Divergence | `divergence.html` |
| Germany North–South | `wasted_wind.html` |
| France Nuclear | `fr_nuclear.html` |
| Nordic Price Zones | `nordic_zones.html` |
| UK Regional | `uk_regional.html` |
| Curtailment | `curtailment.html` |
| Locational Signal | `locational_signal.html` |

### 04 · When the Grid is Tested — *“What happens when supply runs tight?”* — accent `--s-red`
Lede: *A renewable grid's hardest hours — the windless, sunless spells it must plan for, the
batteries that ride the gap, and the day the lights actually went out.*
| View | Existing page |
|---|---|
| Dunkelflaute | `dunkelflaute.html` |
| Storage | `storage.html` |
| Capacity & Adequacy | `capacity_adequacy.html` |
| Iberian Blackout | `iberian_blackout.html` |

### 05 · The Bill — *“What does it cost, and who pays?”* — accent `--s-plum`
Lede: *The wholesale price is only the start. This is the economic and consumer half — what
flexibility is worth, and how a megawatt-hour becomes your monthly bill.*
| View | Existing page |
|---|---|
| Flexibility | `flexibility.html` |
| Retail Wedge | `retail_wedge.html` |
| Industrial Prices | `industrial.html` |
| Curtailment in € | `curtailment.html#cost` |

> Each view also carries a one-line description, a headline stat + label, and a `tag`
> (`chart` / `map` / `model` / `historical`). All of it is in `ia.js` — reuse that file as
> your data source; it is plain JSON-shaped JS with no dependencies.

---

## Screens / Views

### A. Landing / Home (`#/home` in the prototype → in production, the site root / `dashboard.html`)
- **Purpose:** orient a first-time visitor and route them into one of the five questions.
- **Layout:** single centered column, `max-width: 1000px`, `padding: 40px 48px 110px`.
  - **Hero** (`max-width: 760px`): eyebrow (uppercase, `letter-spacing:.13em`, `--hint`);
    `<h1>` in **Newsreader 500, 52px, line-height 1.06, letter-spacing −.015em**, with one
    word (“electricity”) in italic `--s-amber`; lead paragraph 17px `--muted`; two buttons
    (primary pill `--text` bg / `--bg` text; ghost pill with border).
  - **“Five questions” divider row:** label + hairline rule + “26 views”, 11px uppercase.
  - **Section grid:** `grid-template-columns: 1fr 1fr; gap: 18px`. Each **section card**:
    surface bg, `.5px` border, `radius 14px`, `padding 22px`, a **3px left accent bar** in
    the section colour, a section number, a schematic `<canvas>` thumb (120×72), the
    question (12.5px, accent, semibold), the title (Newsreader 500, 27px), the lede (13.5px
    `--muted`), and the view names as **chips** (`--surface-2` pills, 11px). Hover:
    `box-shadow: 0 6px 26px rgba(43,42,39,.09); translateY(-2px)`.
  - **“What changed” note block** linking to the audit.

### B. Section hub (`#/s/<id>`)
- **Purpose:** present one question and its views.
- **Layout:** breadcrumb; **section hero** with a 3px left accent bar, number, question
  (15px accent), title (Newsreader 500, 44px), lede (16px `--muted`, `max-width 66ch`);
  then a **view grid** (`1fr 1fr`, gap 16px) of **view cards**: title (Newsreader 500,
  21px) + a `tag` pill (uppercase 10px; map=amber, historical=red, model=plum tints), a
  one-line description, and a footer stat (Newsreader 500, 24px, accent) + label, divided by
  a hairline. Ends with a **“Next question”** card linking to the following section in its
  own accent.

### C. View page (the 26 existing pages, with the new chrome)
- In production these stay as they are **internally**. Wrap each with the new sidebar
  (desktop) / top bar + bottom tabs (mobile), and add a **“More in this question”** rail of
  3–4 sibling-view links at the foot so pages stop dead-ending. The active section/ view is
  reflected in the nav.
- *(The prototype shows this view framed; ignore the frame — only the surrounding nav,
  the breadcrumb, and the “More in …” rail are the real spec.)*

### D. Standard pages (`#/p/<id>`)
- **About**, **How it works** (method + honesty notes), **Data sources & licences**,
  **Privacy**, **Terms & Disclaimer**, **Contact**. Copy is authored in full in `ia.js`
  (`WATTLAS_IA.pages`) — lift it verbatim.
- **Layout:** breadcrumb; page hero (kicker uppercase 11px; `<h1>` Newsreader 500, 40px);
  body `max-width: 680px` with Newsreader `<h3>` subheads (21px), 15.5px `--muted` body,
  amber-bulleted lists, monospace `<code>` chips.

### E. Footer (site-wide)
- Appears at the foot of every page. Spec + copy in `ia.js` (`WATTLAS_IA.footer`).
- **Layout:** top border; `.foot-top` grid `1.4fr 1fr 1fr 1fr` (collapses to `1fr 1fr` ≤760px,
  brand spans full width). Brand column: ◐ + “Wattlas” (20px, 600) + tagline (13px `--muted`).
  Three link columns — **Explore** (the five sections), **About**, **Legal**. Each column
  head: 10.5px uppercase `--hint`; links 13px `--muted` → `--text` on hover. Bottom bar:
  hairline + meta line (“Open data … Not financial advice.”) + “© <year> Wattlas · open data”.

### F. Mobile (≤ 900px)
- **Sidebar is hidden;** replaced by:
  - a **sticky top bar** (blurred translucent `--bg`): a `☰` menu button (opens the full
    sidebar as a left **drawer** with a scrim, for power-user access to every view, the
    nav-mode toggle and the audit) **OR** a `‹` **back button** (shown on any non-home
    route; hides the menu button), and a brand wordmark that links home.
  - a **fixed bottom tab bar** = the **five sections**. Each tab: section number (9px
    tabular), a 7px accent **dot** (outlined when inactive, filled when active), and a short
    label (`Rhythm / Grid / Geography / Stress / The Bill`). Active tab: accent colour + a
    2.5px accent indicator bar above it. `env(safe-area-inset-bottom)` respected. Content
    gets `padding-bottom: 96px` to clear it.
- Section/view/page layouts all collapse to a single column; hero type steps down
  (home h1 → 33px, section h1 → 30px, etc.).
- `design/Wattlas Mobile.html` previews these screens inside device frames.

---

## Interactions & behaviour

- **Desktop sidebar = grouped accordion.** Five section groups; the **current section's
  children auto-expand**, others collapse. A section header links to its hub; child links go
  to views. Active item: `--surface-2` bg, semibold, accent left-border.
- **“By question / Original” toggle** (top of sidebar): a debugging/storytelling device that
  flips the sidebar between the new 5-question structure and the **old flat 26-link list**
  (verbatim in `ia.js → audit.original`). *Optional in production* — it's there to
  demonstrate the before/after; keep it behind a dev flag or drop it. Choice persists in
  `localStorage` (`wattlas_navmode`).
- **Mobile drawer** opens/closes via the `☰` button and a tap-scrim; closes on navigate.
- **Back button** (mobile) goes to the route's parent: a view → its section hub; everything
  else → home.
- **Hover lifts** on all cards: `translateY(-2px)` + soft shadow, `transition .16s`.
- **No entrance animations required.** Transitions are limited to hover and the drawer
  slide (`transform .22s`).
- **Responsive breakpoints:** `900px` (sidebar → top bar + tabs; grids → 1 col) and
  `760px` (footer grid) and `380px` (type/tab-label step-down).

## State management

Minimal — this is a content site.
- `navMode` (`"question" | "original"`) persisted to `localStorage["wattlas_navmode"]`.
- Current route derived from the URL (hash in the prototype; in production, the actual page
  URL + the active section computed from which view's page you're on — `nav.js` already does
  this kind of `location.pathname` matching today).
- Mobile drawer open/closed = a body class (`nav-open`); back-button visibility = a body
  class (`show-back`). No data fetching is introduced by this restructure.

## Design tokens

```css
/* Surfaces & ink — warm paper, dark ink (unchanged from current Wattlas) */
--bg:#faf9f5;  --surface:#ffffff;  --surface-2:#f3f1ea;  --surface-3:#ece9df;
--text:#2b2a27;  --muted:#5f5e5a;  --hint:#8a8880;
--border:rgba(43,42,39,.13);  --border-2:rgba(43,42,39,.08);

/* Section accents — shared chroma/lightness, varied hue (oklch) */
--s-blue: oklch(.50 .10 248);   /* 01 The Daily Rhythm     */
--s-green:oklch(.50 .10 150);   /* 02 What's on the Grid   */
--s-amber:oklch(.55 .10 75);    /* 03 Geography of Price   */
--s-red:  oklch(.52 .12 28);    /* 04 When the Grid is Tested */
--s-plum: oklch(.50 .10 312);   /* 05 The Bill             */

/* Type */
--serif:"Newsreader",Georgia,"Times New Roman",serif;  /* display headlines */
--sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; /* UI + body */

/* Radius */
--radius:14px;  --radius-sm:9px;
```

**Type scale (Newsreader 500 unless noted):** home h1 52 / section h1 44 / page & view h1 40 / section-card title 27 / view-card & ns title 21–22 / view stat 24 / body 13.5–17 sans / eyebrows & col-heads 10.5–11 uppercase `letter-spacing:.09–.13em`.
**Shadows:** card hover `0 6px 26px rgba(43,42,39,.09)` (home) / `0 6px 22px rgba(43,42,39,.08)` (view); drawer `0 0 40px rgba(0,0,0,.12)`.
**Spacing:** 8-ish rhythm; card padding 20–22px; content gutter 48px desktop / 18px mobile.

> Note: the existing site already uses `--bg/--text/--muted/--hint/--border` and accent
> hexes `--blue:#185fa5 --green:#3b6d11 --amber:#b8860b --red:#a32d2d`. The five **oklch
> section accents above are the new addition** — they're tuned to sit beside the existing
> palette. You may either adopt them or map the five sections onto the existing hexes; keep
> them consistent across nav, cards and section heroes.

## Assets

- **Font:** Newsreader (Google Fonts) for display; system sans for everything else. No
  other fonts. No image assets — section thumbnails are drawn with `<canvas>` (see
  `app.js → drawThumbs`) and are optional/illustrative. Brand mark is the “◐” glyph.
- **Fonts already in repo flow:** load Newsreader via a `<link>` (weights 400/500/600).

## Screenshots

In `screenshots/` (visual reference for the specs above):
- `desktop-home.png` / `desktop-home-sections.png` — the editorial landing + the five section cards.
- `desktop-section-hub.png` / `desktop-section-hub-cards.png` — a section hub (sidebar group expanded, view cards).
- `desktop-audit.png` / `desktop-audit-before-after.png` — the “Why this changed” audit and the before/after.
- `desktop-standard-page.png` — a standard page (Data sources & licences).
- `desktop-footer.png` — the site footer.
- `view-content-pulse.png` — a real view's content (Pulse) as it loads inside a framed view.
- `mobile-home.png` / `mobile-section-hub.png` — the phone-native layout with the five-question bottom tab bar.

## Files

The prototype + design source (`frontend/`):
- `frontend/Wattlas Redesign.html` — the full desktop + mobile prototype (shell, styles, all screens).
- `frontend/Wattlas Mobile.html` — the mobile screens previewed inside device frames.
- `frontend/redesign/ia.js` — **the data source of record**: the 5 sections + 26 views, all
  copy, the standard-page content, the footer, and the old flat nav (for the toggle/audit).
  Lift copy and structure straight from here.
- `frontend/redesign/app.js` — prototype render + router + canvas thumbs + footer/page
  renderers. Reference for layout and behaviour; **the SPA router and iframe embedding are
  prototype-only — see the warning above.**
- `frontend/nav.js` — the current site nav, with the prototype's `embed` branch added at
  the top (reference only; drop the `embed` branch in the real build).

The runnable current site (apply the new design to these):
- `frontend/*.html` — the 23 standalone view pages + `dashboard.html`.
- `frontend/{styles.css,util.js,fuels.js,geo.js}`, `frontend/dash/*`, `frontend/geo/*.topo.json`.
- `data/*.json` — the full committed view data (35 files).

In the real repo, the files you'll most likely touch:
- `frontend/nav.js` — rewrite the link model + sidebar markup to the 5-section grouping;
  add the mobile top bar + bottom tab bar; add the footer injection.
- a landing page (replace/augment `frontend/dashboard.html`, or a new root `index`).
- new `frontend/{about,methodology,sources,privacy,terms,contact}.html` standard pages (or a
  single templated page).
- the 26 existing view pages — add the “More in this question” foot-rail; no internal change.
