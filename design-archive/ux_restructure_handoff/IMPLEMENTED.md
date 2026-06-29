# Implementation note

This handoff (see `README.md`) was implemented in production. The bundled
`frontend/Wattlas Redesign.html` + `frontend/redesign/{ia.js,app.js}` are the
**design reference** (a single-file prototype with a hash router + iframes); they
are kept here verbatim and are not run by the live site.

What landed in the real `frontend/` (multi-page static, no SPA, no iframes):

| Handoff concept | Production file(s) |
|---|---|
| IA source of record (`redesign/ia.js`) | `frontend/ia.js` (copied verbatim) |
| Sidebar accordion + mobile top bar + bottom tab bar + footer + "More in this question" rail | `frontend/nav.js` (rewritten; injected on every page) |
| Editorial landing (`#/home`) | `frontend/dashboard.html` (old panel dashboard preserved as `panels.html`) |
| Section hub (`#/s/<id>`) | `frontend/section.html?s=<id>` |
| Standard pages (`#/p/<id>`) | `frontend/page.html?p=<id>` |
| Audit (`#/audit`) | `frontend/audit.html` |
| Editorial component styles | `frontend/redesign.css` |
| Render/router for the chrome pages | `frontend/redesign.js` |

Deliberate deviations from the prototype:
- **No iframes / no SPA router** — production applies `nav.js` to each existing
  standalone page, per the README's own "Critical" warning.
- **No `localStorage`** — the "By question / Original" nav-mode toggle was a demo
  device; dropped because `CLAUDE.md` forbids browser storage.
- The five-section accent palette uses the handoff's `--s-*` oklch tokens.
