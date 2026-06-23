/* Wattlas — single source of site navigation (styles + links + behaviour).
 * Injects the desktop sidebar (into the page's .shell) and the mobile
 * scroll-nav (at the top of <body>), and marks the current page active.
 *
 * The CSS is injected here too, so the nav looks right on every page —
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

  // Grouped so the sidebar can show section labels and the two map stories
  // read as featured content rather than two more links in a list.
  var GROUPS = [
    { label: "", items: [
      { href: "dashboard.html", text: "Dashboard", mark: "\u2302" },   // ⌂
    ]},
    { label: "The eight views", items: [
      { href: "pulse.html",       text: "Pulse",       mark: "1" },
      { href: "index.html",       text: "Spread",      mark: "2" },
      { href: "mix.html",         text: "Mix",         mark: "3" },
      { href: "mismatch.html",    text: "Mismatch",    mark: "4" },
      { href: "divergence.html",  text: "Divergence",  mark: "5" },
      { href: "dashboard.html#carbon", text: "Carbon", mark: "6" },
      { href: "curtailment.html", text: "Curtailment", mark: "7" },
      { href: "history.html",     text: "History",     mark: "8" },
    ]},
    { label: "Map stories", items: [
      { href: "wasted_wind.html", text: "Germany North - South Grid",         mark: "DE", story: true },
      { href: "fr_nuclear.html",  text: "France Nuclear",        mark: "FR", story: true },
    ]},
  ];

  var here = (location.pathname.split("/").pop() || "").toLowerCase();
  if (!here) here = "index.html";

  function isActive(href) {
    if (href.indexOf("#") !== -1) return false;        // section links (Carbon) never own a page
    return href.toLowerCase() === here;
  }

  // ---- Desktop sidebar -----------------------------------------------------
  var side = '<div class="brand">Wattlas <small>' + TAGLINE + "</small></div>";
  side += '<nav class="sidenav" aria-label="Site">';
  GROUPS.forEach(function (g, gi) {
    if (g.label) side += '<div class="navgroup' + (gi === 1 ? " first" : "") + '">' + g.label + "</div>";
    g.items.forEach(function (it) {
      var cls = (it.story ? "story" : "") + (isActive(it.href) ? " active" : "");
      side += '<a href="' + it.href + '"' + (cls.trim() ? ' class="' + cls.trim() + '"' : "") +
        (isActive(it.href) ? ' aria-current="page"' : "") + '>' +
        '<span class="n">' + it.mark + "</span>" +
        "<span>" + it.text + (it.sub ? '<span class="sub">' + it.sub + "</span>" : "") + "</span></a>";
    });
  });
  side += "</nav>";
  side += '<div class="foot">Open data from ENTSO-E, RTE/ODR\u00c9, SMARD, MaStR and netztransparenz. ' +
    "Pre-computed and static \u2014 no live backend.</div>";

  var aside = document.createElement("aside");
  aside.className = "side";
  aside.innerHTML = side;

  // ---- Mobile scroll-nav ---------------------------------------------------
  var top = '<div class="brand">Wattlas <small>' + TAGLINE + "</small></div>";
  top += '<nav class="topnav" aria-label="Site">';
  GROUPS.forEach(function (g, gi) {
    if (gi === GROUPS.length - 1) top += '<span class="div" aria-hidden="true"></span>';
    g.items.forEach(function (it) {
      var cls = (it.story ? "story" : "") + (isActive(it.href) ? " active" : "");
      top += '<a href="' + it.href + '"' + (cls.trim() ? ' class="' + cls.trim() + '"' : "") +
        (isActive(it.href) ? ' aria-current="page"' : "") + ">" + it.text + "</a>";
    });
  });
  top += "</nav>";

  var header = document.createElement("header");
  header.className = "topbar";
  // Pages with their own sticky controls (the dashboard's zone/window bar and
  // jump-nav) can't have a second sticky bar fighting for the top — keep the
  // mobile nav in normal flow there so nothing overlaps.
  if (document.querySelector(".bar, .jumpnav")) header.classList.add("static");
  header.innerHTML = top;

  function mount() {
    var shell = document.querySelector(".shell");
    if (shell) shell.insertBefore(aside, shell.firstChild);
    document.body.insertBefore(header, document.body.firstChild);
    // Bring the active mobile link into view so users see where they are.
    var act = header.querySelector("a.active");
    var nav = header.querySelector(".topnav");
    if (act && nav) nav.scrollLeft = Math.max(0, act.offsetLeft - 16);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
