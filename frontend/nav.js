/* Wattlas — single source of site navigation (styles + links + behaviour).
 * Injects the desktop sidebar (into the page's .shell) and the mobile
 * scroll-nav (at the top of <body>).
 *
 * Navigation model — context-aware "hybrid + nested":
 *   • The eight analytical views are SECTIONS of the dashboard (ids #pulse …
 *     #history) AND each (except Carbon) also has a richer standalone page.
 *     In the sidebar they are nested under "Dashboard" to read as its sections.
 *   • ON the dashboard the view links are in-page anchors and the menu acts as a
 *     SCROLL-SPY: clicking smooth-scrolls to a section, and scrolling the page
 *     highlights the section you're in (so "moving through the dashboard moves
 *     through the menu"). "Dashboard" itself is active when you're at the top.
 *   • OFF the dashboard the same view links resolve to the standalone pages and
 *     the menu is ordinary page-to-page nav with the current page marked active.
 *   • The two map stories are a separate, amber-accented group (standalone only).
 *
 * Everything (links, styles, behaviour) lives here so the nav is defined in
 * exactly one place. The CSS is injected too, so it looks right on every page —
 * including index.html, which is self-contained and doesn't load styles.css.
 *
 * A page only needs:  <body> … <div class="shell"><main class="main"> … </main></div>
 * … <script src="nav.js"></script>  — nav.js does the rest.
 */
(function () {
  var TAGLINE = "European electricity, explained";

  // ---- Inject nav chrome CSS as early as possible (script is at end of body,
  //      so <head> already exists). --amber falls back for the one page that
  //      doesn't declare it. ---------------------------------------------------
  var CSS = '' +
    '.shell{display:grid;grid-template-columns:244px minmax(0,1fr);min-height:100vh}' +
    '.side{position:sticky;top:0;height:100vh;overflow-y:auto;display:flex;flex-direction:column;' +
      'padding:26px 16px 20px 22px;border-right:.5px solid var(--border);background:var(--bg)}' +
    '.side .brand{font-size:19px;font-weight:600;letter-spacing:-.01em;margin:0}' +
    '.side .brand small{display:block;color:var(--hint);font-weight:400;font-size:12px;margin:3px 0 0}' +
    '.sidenav{margin-top:22px;display:flex;flex-direction:column;gap:1px}' +
    '.navgroup{font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;' +
      'color:var(--hint);margin:18px 0 6px 10px}' +
    '.navgroup.first{margin-top:2px}' +
    '.sidenav a{display:flex;align-items:flex-start;gap:9px;color:var(--muted);text-decoration:none;' +
      'font-size:13.5px;line-height:1.3;padding:7px 10px;border-radius:var(--radius-sm,8px);' +
      'border-left:2px solid transparent}' +
    '.sidenav a .n{font-variant-numeric:tabular-nums;font-size:10px;color:var(--hint);' +
      'width:16px;flex:none;text-align:center;padding-top:1px}' +
    '.sidenav a .sub{display:block;font-size:11px;color:var(--hint);font-weight:400;margin-top:2px}' +
    '.sidenav a:hover{color:var(--text);background:var(--surface-2)}' +
    '.sidenav a:hover .sub{color:var(--muted)}' +
    '.sidenav a.active{color:var(--text);font-weight:600;background:var(--surface-2);border-left-color:var(--amber,#b8860b)}' +
    '.sidenav a.story .n{color:var(--amber,#b8860b);font-weight:700;font-size:9px;letter-spacing:.03em}' +
    // Nested "Dashboard → its eight views" group: the parent reads as a heading,
    // the views are indented under it with a hairline guide so the hierarchy is
    // unmistakable (they are sections of the dashboard, not unrelated pages).
    '.sidenav a.parent{font-weight:600;color:var(--text)}' +
    '.sidenav .subnav{display:flex;flex-direction:column;gap:1px;margin:1px 0 6px 14px;' +
      'padding-left:6px;border-left:1px solid var(--border)}' +
    '.sidenav .subnav a{font-size:13px}' +
    '.side .foot{margin-top:auto;padding-top:20px;font-size:11px;color:var(--hint);line-height:1.6}' +
    '.main{padding:0 36px 80px;min-width:0}' +
    '.main-inner{max-width:1080px;margin:0 auto;padding-top:26px}' +
    '.topbar{display:none}' +
    '@media (max-width:900px){' +
      '.shell{display:block}' +
      '.side{display:none}' +
      '.topbar{display:block;position:sticky;top:0;z-index:40;background:var(--bg);' +
        'border-bottom:.5px solid var(--border);padding:10px 14px 0}' +
      '.topbar.static{position:static}' +
      '.topbar .brand{font-size:16px;font-weight:600}' +
      '.topbar .brand small{color:var(--hint);font-weight:400;font-size:11px;margin-left:8px}' +
      '.topnav{display:flex;align-items:center;gap:5px;overflow-x:auto;padding:9px 0 10px;' +
        '-webkit-overflow-scrolling:touch;scrollbar-width:thin}' +
      '.topnav a{font-size:12px;color:var(--muted);text-decoration:none;white-space:nowrap;' +
        'padding:6px 12px;border-radius:999px;border:.5px solid transparent}' +
      '.topnav a:hover{color:var(--text)}' +
      '.topnav a.active{color:var(--text);background:var(--surface-2);border-color:var(--border)}' +
      '.topnav .div{flex:none;align-self:stretch;border-left:.5px solid var(--border);margin:5px 3px}' +
      '.topnav a.story{color:var(--amber,#b8860b);font-weight:500;border-color:rgba(184,134,11,.35)}' +
      '.topnav a.story.active{color:var(--bg);background:var(--amber,#b8860b);border-color:var(--amber,#b8860b)}' +
      '.main{padding:0 14px 64px}' +
    '}';
  var st = document.createElement("style");
  st.id = "wattlas-nav-css";
  st.textContent = CSS;
  (document.head || document.documentElement).appendChild(st);

  // ---- Links: one source of truth ------------------------------------------
  // Each view carries both its dashboard `section` id and its standalone `page`
  // (Carbon is a dashboard-only section, so it has no standalone page).
  var DASH = "dashboard.html";
  var VIEWS = [
    { text: "Pulse",       mark: "1", section: "pulse",       page: "pulse.html"       },
    { text: "Spread",      mark: "2", section: "spread",      page: "index.html"       },
    { text: "Mix",         mark: "3", section: "mix",         page: "mix.html"         },
    { text: "Mismatch",    mark: "4", section: "mismatch",    page: "mismatch.html"    },
    { text: "Divergence",  mark: "5", section: "divergence",  page: "divergence.html"  },
    { text: "Carbon",      mark: "6", section: "carbon",      page: null               },
    { text: "Curtailment", mark: "7", section: "curtailment", page: "curtailment.html" },
    { text: "History",     mark: "8", section: "history",     page: "history.html"     },
  ];
  var STORIES = [
    { text: "Germany North - South Grid", mark: "DE", page: "wasted_wind.html" },
    { text: "France Nuclear",             mark: "FR", page: "fr_nuclear.html"  },
  ];

  var here = (location.pathname.split("/").pop() || "").toLowerCase();
  if (!here) here = "index.html";
  var onDash = (here === DASH);

  // On the dashboard, a view points at its in-page section; elsewhere at its own
  // page (Carbon has no page, so it always points back to the dashboard section).
  function viewHref(v) {
    if (onDash) return "#" + v.section;
    return v.page ? v.page : (DASH + "#" + v.section);
  }
  function pageActive(page) { return !onDash && !!page && page.toLowerCase() === here; }

  function attrs(o) {
    return (o.spy ? ' data-spy="' + o.spy + '"' : "") +
           (o.home ? ' data-home="1"' : "") +
           (o.page ? ' data-page="' + o.page.toLowerCase() + '"' : "") +
           (o.active ? ' aria-current="page"' : "");
  }
  // Sidebar link (with marker column); topnav pill (text only).
  function navLink(o) {
    var cls = ((o.parent ? "parent " : "") + (o.story ? "story " : "") + (o.active ? "active" : "")).trim();
    return '<a href="' + o.href + '"' + (cls ? ' class="' + cls + '"' : "") + attrs(o) + '>' +
      '<span class="n">' + o.mark + '</span><span>' + o.text + '</span></a>';
  }
  function pill(o) {
    var cls = ((o.story ? "story " : "") + (o.active ? "active" : "")).trim();
    return '<a href="' + o.href + '"' + (cls ? ' class="' + cls + '"' : "") + attrs(o) + '>' + o.text + '</a>';
  }

  // ---- Desktop sidebar (nested) --------------------------------------------
  var side = '<div class="brand">Wattlas <small>' + TAGLINE + "</small></div>";
  side += '<nav class="sidenav" aria-label="Site">';
  side += navLink({ href: onDash ? "#top" : DASH, text: "Dashboard", mark: "⌂",
                    parent: true, home: true, page: DASH, active: false });
  side += '<div class="subnav">';
  VIEWS.forEach(function (v) {
    side += navLink({ href: viewHref(v), text: v.text, mark: v.mark,
                      spy: v.section, page: v.page, active: pageActive(v.page) });
  });
  side += "</div>";
  side += '<div class="navgroup">Map stories</div>';
  STORIES.forEach(function (s) {
    side += navLink({ href: s.page, text: s.text, mark: s.mark, story: true,
                      page: s.page, active: pageActive(s.page) });
  });
  side += "</nav>";
  side += '<div class="foot">Open data from ENTSO-E, RTE/ODRÉ, SMARD, MaStR and netztransparenz. ' +
    "Pre-computed and static — no live backend.</div>";

  var aside = document.createElement("aside");
  aside.className = "side";
  aside.innerHTML = side;

  // ---- Mobile scroll-nav (flat pills; nesting doesn't apply to a pill row) --
  var top = '<div class="brand">Wattlas <small>' + TAGLINE + "</small></div>";
  top += '<nav class="topnav" aria-label="Site">';
  top += pill({ href: onDash ? "#top" : DASH, text: "Dashboard", home: true, page: DASH, active: false });
  VIEWS.forEach(function (v) {
    top += pill({ href: viewHref(v), text: v.text, spy: v.section, page: v.page, active: pageActive(v.page) });
  });
  top += '<span class="div" aria-hidden="true"></span>';
  STORIES.forEach(function (s) {
    top += pill({ href: s.page, text: s.text, story: true, page: s.page, active: pageActive(s.page) });
  });
  top += "</nav>";

  var header = document.createElement("header");
  header.className = "topbar";
  // Pages with their own sticky controls (e.g. a .bar / .jumpnav toolbar) can't
  // have a second sticky bar fighting for the top — keep the mobile nav in
  // normal flow there. (The dashboard's .ctrl bar is made static on mobile in
  // dash.css instead, so the dashboard keeps a sticky top-nav without colliding.)
  if (document.querySelector(".bar, .jumpnav")) header.classList.add("static");
  header.innerHTML = top;

  function scrollActivePillIntoView() {
    var nav = header.querySelector(".topnav");
    var act = nav && nav.querySelector("a.active");
    if (nav && act) nav.scrollLeft = Math.max(0, act.offsetLeft - 16);
  }

  // ---- Scroll-spy (dashboard only) -----------------------------------------
  function setupSpy() {
    var spyLinks = [].slice.call(document.querySelectorAll("[data-spy]"));
    var homeLinks = [].slice.call(document.querySelectorAll("[data-home]"));
    var sections = VIEWS.map(function (v) { return v.section; });
    var lastSec;  // undefined until first apply

    // The section you're "in" = the last one whose top has scrolled past a line
    // just under the sticky control bar. null => above the first section (top of
    // the dashboard) => "Dashboard" itself is active.
    function currentSection() {
      // At the very bottom of the page the last (often short) section can't
      // scroll its top past the line — treat reaching the bottom as "in the last
      // section" so History still highlights.
      var doc = document.documentElement;
      if (window.innerHeight + window.scrollY >= doc.scrollHeight - 4)
        return sections[sections.length - 1];
      var line = (window.innerWidth <= 900) ? 100 : 150;
      var cur = null;
      for (var i = 0; i < sections.length; i++) {
        var el = document.getElementById(sections[i]);
        if (!el) continue;
        if (el.getBoundingClientRect().top - line <= 0) cur = sections[i];
        else break;
      }
      return cur;
    }
    function apply(sec) {
      spyLinks.forEach(function (a) {
        var on = (a.getAttribute("data-spy") === sec);
        a.classList.toggle("active", on);
        if (on) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current");
      });
      homeLinks.forEach(function (a) {
        var on = (sec === null);
        a.classList.toggle("active", on);
        if (on) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
      });
      scrollActivePillIntoView();
    }
    function update() {
      var s = currentSection();
      if (s !== lastSec) { lastSec = s; apply(s); }
    }

    // "Dashboard" has no section — clicking it smooth-scrolls to the top.
    homeLinks.forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        window.scrollTo({ top: 0, behavior: "smooth" });
        if (history.replaceState) history.replaceState(null, "", location.pathname);
      });
    });
    // Reflect the click immediately; the scroll handler then keeps it honest.
    spyLinks.forEach(function (a) {
      a.addEventListener("click", function () { lastSec = a.getAttribute("data-spy"); apply(lastSec); });
    });

    // Throttle with setTimeout (not requestAnimationFrame): rAF is paused in
    // background/hidden tabs, which would freeze the highlight; setTimeout keeps
    // firing. 60ms is well below the threshold of perceptible highlight lag.
    var scheduled = false;
    window.addEventListener("scroll", function () {
      if (scheduled) return;
      scheduled = true;
      setTimeout(function () { scheduled = false; update(); }, 60);
    }, { passive: true });
    window.addEventListener("resize", update, { passive: true });
    window.addEventListener("hashchange", update);
    update();  // set initial state before paint
  }

  function mount() {
    var shell = document.querySelector(".shell");
    if (shell) shell.insertBefore(aside, shell.firstChild);
    document.body.insertBefore(header, document.body.firstChild);
    if (onDash) setupSpy();
    scrollActivePillIntoView();  // bring the active mobile pill into view on load
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
