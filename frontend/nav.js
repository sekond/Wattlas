/* Wattlas — single source of site navigation (chrome CSS + links + behaviour).
 *
 * Information architecture: the 26 destinations are regrouped under FIVE
 * question-led sections (see ia.js → WATTLAS_IA.sections). This file renders
 * that IA as site chrome around every page:
 *   • Desktop: a grouped accordion sidebar (the active section auto-expands).
 *   • Mobile (≤900px): a sticky top bar (☰ drawer / ‹ back) + a fixed bottom
 *     tab bar carrying the five sections.
 *   • A site-wide footer, and — on a view page — a "More in this question" rail
 *     of sibling links so pages stop dead-ending.
 *
 * Production is a multi-PAGE static site (no SPA, no iframes). The prototype's
 * hash router (#/s/…, #/p/…) is translated to real page URLs here:
 *   #/home → dashboard.html · #/s/<id> → section.html?s=<id>
 *   #/p/<id> → page.html?p=<id> · #/v/<id> → view page
 *
 * A page only needs:  …<div class="shell"><main class="main"> … </main></div>
 * <script src="ia.js"></script><script src="nav.js"></script>  — nav.js does the rest.
 *
 * Note: no localStorage/sessionStorage — per CLAUDE.md this site keeps no
 * browser state. The prototype's "By question / Original" nav-mode toggle was a
 * demo device and is intentionally dropped in production.
 */
(function () {
  var IA = window.WATTLAS_IA;
  if (!IA || !IA.sections) return; // ia.js must load before nav.js
  var SECTIONS = IA.sections;
  var TAGLINE = "European electricity, explained";

  // Foldable sidebar sections — remember which are collapsed across pages.
  var FOLDS = {};
  function saveFolds() { /* no-op: CLAUDE.md forbids localStorage/sessionStorage; folds are session-only */ }

  // Flatten: index views by id and by page, and remember each view's section.
  var byId = {}, byPage = {};
  SECTIONS.forEach(function (s) {
    s.views.forEach(function (v) {
      v._section = s;
      byId[v.id] = v;
      var base = (v.page || "").split("#")[0].split("?")[0].toLowerCase();
      if (base && !byPage[base]) byPage[base] = v; // first wins (primary section)
    });
  });

  // ---- Inject the display font (Newsreader) for editorial headlines + rails --
  // Self-hosted from vendor/fonts/ (SIL OFL) — deliberately NOT loaded from Google
  // Fonts, so opening a page transmits no visitor IP to Google (GDPR: avoids the
  // render-time third-party transfer flagged in LG München I, 3 O 17493/20).
  if (!document.getElementById("wattlas-font")) {
    var fl = document.createElement("link");
    fl.id = "wattlas-font"; fl.rel = "stylesheet";
    fl.href = "vendor/fonts/newsreader.css";
    (document.head || document.documentElement).appendChild(fl);
  }

  // ---- Inject chrome CSS as early as possible -------------------------------
  // Only ADDITIVE tokens are declared here (section accents, serif, extra
  // surfaces); existing page tokens (--bg/--text/--radius…) are left untouched.
  var CSS = `
:root{
  --s-blue:oklch(.50 .10 248); --s-green:oklch(.50 .10 150); --s-amber:oklch(.55 .10 75);
  --s-red:oklch(.52 .12 28); --s-plum:oklch(.50 .10 312);
  --serif:"Newsreader",Georgia,"Times New Roman",serif;
}
body:not([data-wx-tokens]){--surface-3:#ece9df; --border-2:rgba(43,42,39,.08)}

.shell{display:grid;grid-template-columns:248px minmax(0,1fr);min-height:100vh}
.side{position:sticky;top:0;height:100vh;overflow-y:auto;display:flex;flex-direction:column;
  padding:24px 14px 16px 20px;border-right:.5px solid var(--border);background:var(--bg);z-index:40}
.brandlink{display:flex;align-items:center;gap:10px;text-decoration:none;margin:0 0 18px 6px}
.brandlink .mark{font-size:22px;line-height:1;color:var(--text)}
.brandlink .bt{font-size:18px;font-weight:600;letter-spacing:-.01em;line-height:1.1;color:var(--text)}
.brandlink small{display:block;color:var(--hint);font-weight:400;font-size:11.5px}
.snav{display:flex;flex-direction:column;gap:1px}
.snav .nlink{display:flex;align-items:center;gap:9px;text-decoration:none;color:var(--muted);font-size:13.5px;
  padding:8px 10px;border-radius:var(--radius-sm,8px);border-left:2px solid transparent}
.snav .nlink .ni{width:16px;text-align:center;color:var(--hint);font-size:12px;flex:none}
.snav .nlink:hover{color:var(--text);background:var(--surface-2)}
.snav .nlink.active{color:var(--text);font-weight:600;background:var(--surface-2);border-left-color:var(--text)}
.ngroup{margin-top:10px;--ga:var(--text)}
.ghead{display:block;text-decoration:none;padding:7px 10px 6px;border-radius:var(--radius-sm,8px);border-left:2px solid transparent}
.ghead .gn{font-variant-numeric:tabular-nums;font-size:10px;font-weight:600;color:var(--ga);letter-spacing:.04em}
.ghead .gt{display:block;font-size:13.5px;font-weight:600;color:var(--text);margin-top:1px}
.ghead .gq{display:block;font-size:11px;color:var(--hint);font-weight:400;line-height:1.3;margin-top:1px}
.ghead:hover{background:var(--surface-2)}
.ghead.active{background:var(--surface-2);border-left-color:var(--ga)}
.gkids{display:none;flex-direction:column;gap:0;margin:2px 0 4px 11px;padding-left:11px;border-left:1.5px solid var(--border-2)}
.gkids.open{display:flex}
.ghead-row{display:flex;align-items:stretch;gap:2px}
.ghead-row .ghead{flex:1 1 auto;min-width:0}
.gtoggle{flex:none;align-self:center;width:26px;height:26px;padding:0;border:none;background:transparent;cursor:pointer;
  color:var(--hint);display:flex;align-items:center;justify-content:center;border-radius:var(--radius-sm,8px)}
.gtoggle:hover{background:var(--surface-2);color:var(--text)}
.gtoggle svg{width:10px;height:7px;transition:transform .18s ease}
.gtoggle svg path{fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}
.gtoggle[aria-expanded="false"] svg{transform:rotate(-90deg)}
.nkid{text-decoration:none;color:var(--muted);font-size:12.5px;padding:5px 10px;border-radius:7px}
.nkid:hover{color:var(--text);background:var(--surface-2)}
.nkid.active{color:var(--text);font-weight:600;background:var(--surface-2)}
.side .nfoot{margin-top:auto;padding:18px 8px 0;font-size:10.5px;color:var(--hint);line-height:1.6}

.main{padding:0 36px 80px;min-width:0}
.main-inner{max-width:1080px;margin:0 auto;padding-top:26px}
.loading{display:flex;align-items:center;justify-content:center;gap:9px;color:var(--hint);font-size:13px;padding:34px 0;text-align:center}
.loading::before{content:"";flex:none;width:14px;height:14px;border-radius:50%;border:2px solid var(--border);border-top-color:var(--hint);animation:wspin .8s linear infinite}
@keyframes wspin{to{transform:rotate(360deg)}}
.loading.empty,.loading.awaiting{color:var(--muted)} .loading.empty::before,.loading.awaiting::before{display:none}

/* "More in this question" rail (foot of every view page) */
.readon{margin-top:44px}
.readon .ro-head{font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--hint);margin-bottom:14px}
.readon .ro-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.ro-card{display:flex;flex-direction:column;gap:4px;text-decoration:none;border:.5px solid var(--border);border-radius:var(--radius-sm,8px);
  padding:14px 16px;background:var(--surface);transition:background .14s,transform .16s,box-shadow .16s}
.ro-card:hover{background:var(--surface-2);transform:translateY(-2px);box-shadow:0 6px 22px rgba(43,42,39,.08)}
.ro-card .ro-t{font-family:var(--serif);font-size:17px;font-weight:500;color:var(--a,var(--text))}
.ro-card .ro-o{font-size:12.5px;color:var(--muted);line-height:1.45}

/* Site footer */
.sitefoot{margin-top:64px;padding-top:34px;border-top:.5px solid var(--border);font-size:13px}
.sitefoot .foot-top{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:28px;margin-bottom:28px}
.sitefoot .foot-brand .fb-mark{font-size:20px;font-weight:600;letter-spacing:-.01em;display:flex;align-items:center;gap:8px}
.sitefoot .foot-brand .fb-mark span{font-size:22px}
.sitefoot .foot-brand p{font-size:13px;color:var(--muted);line-height:1.6;margin:12px 0 0;max-width:34ch}
.sitefoot h4{font-size:10.5px;font-weight:600;letter-spacing:.09em;text-transform:uppercase;color:var(--hint);margin:0 0 12px}
.sitefoot .foot-col a{display:block;font-size:13px;color:var(--muted);text-decoration:none;padding:3px 0;line-height:1.5}
.sitefoot .foot-col a:hover{color:var(--text)}
.sitefoot .foot-bot{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;flex-wrap:wrap;
  padding:18px 0 6px;border-top:.5px solid var(--border-2);font-size:11.5px;color:var(--hint);line-height:1.6}
.sitefoot .foot-bot .fb-meta{max-width:64ch}
.sitefoot .foot-bot .fb-copy{white-space:nowrap}
@media (max-width:760px){.sitefoot .foot-top{grid-template-columns:1fr 1fr;gap:22px}.sitefoot .foot-brand{grid-column:1 / -1}}

/* Mobile chrome */
.topbar{display:none}
.tabbar{display:none}
#wx-scrim{display:none}
@media (max-width:900px){
  .shell{display:block}
  .side{position:fixed;top:0;left:0;bottom:0;width:280px;height:auto;transform:translateX(-100%);
    transition:transform .22s ease;box-shadow:0 0 40px rgba(0,0,0,.12)}
  body.nav-open .side{transform:none}
  #wx-scrim{display:block;position:fixed;inset:0;background:rgba(0,0,0,.3);opacity:0;pointer-events:none;transition:opacity .2s;z-index:35}
  body.nav-open #wx-scrim{opacity:1;pointer-events:auto}
  .topbar{display:flex;align-items:center;gap:6px;position:sticky;top:0;z-index:30;
    background:color-mix(in oklch,var(--bg) 88%,transparent);
    backdrop-filter:saturate(1.4) blur(10px);-webkit-backdrop-filter:saturate(1.4) blur(10px);
    border-bottom:.5px solid var(--border);padding:11px 14px}
  .topbar.static{position:static}
  .topbar .mb{font:inherit;font-size:21px;line-height:1;border:none;background:none;cursor:pointer;color:var(--text);padding:4px 8px;border-radius:8px}
  .topbar .mb:active{background:var(--surface-2)}
  .topbar .mb.back{display:none;font-size:30px;font-weight:300;width:34px}
  body.show-back .topbar .mb.back{display:block}
  body.show-back .topbar .mb#wx-menuBtn{display:none}
  .topbar .tb-brand{font-size:16px;font-weight:600;text-decoration:none;color:var(--text)}
  .topbar .tb-brand small{color:var(--hint);font-weight:400;font-size:11px;margin-left:6px}
  .main{padding:0 16px calc(96px + env(safe-area-inset-bottom))}
  .tabbar{display:flex;position:fixed;left:0;right:0;bottom:0;z-index:32;
    background:color-mix(in oklch,var(--bg) 90%,transparent);
    backdrop-filter:saturate(1.4) blur(12px);-webkit-backdrop-filter:saturate(1.4) blur(12px);
    border-top:.5px solid var(--border);padding:6px 4px calc(6px + env(safe-area-inset-bottom))}
  .tabbar a{flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;text-decoration:none;color:var(--hint);padding:5px 2px 3px;position:relative;min-width:0}
  .tabbar a .tn{font-variant-numeric:tabular-nums;font-size:9px;font-weight:600;letter-spacing:.04em;color:var(--hint)}
  .tabbar a .tdot{width:7px;height:7px;border-radius:50%;border:1.5px solid currentColor;transition:background .15s}
  .tabbar a .tl{font-size:10px;font-weight:500;line-height:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
  .tabbar a.active{color:var(--ta)} .tabbar a.active .tn{color:var(--ta)}
  .tabbar a.active .tdot{background:var(--ta);border-color:var(--ta)}
  .tabbar a.active::before{content:"";position:absolute;top:-6px;left:50%;transform:translateX(-50%);width:24px;height:2.5px;border-radius:2px;background:var(--ta)}
}
@media (max-width:380px){.tabbar a .tl{font-size:9px}}
`;
  var st = document.createElement("style");
  st.id = "wattlas-nav-css";
  st.textContent = CSS;
  (document.head || document.documentElement).appendChild(st);

  // ---- Route helpers --------------------------------------------------------
  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function qp(name) {
    var m = new RegExp("[?&]" + name + "=([^&#]*)").exec(location.search);
    return m ? decodeURIComponent(m[1]) : null;
  }
  // Translate a prototype hash route to a real production page URL.
  function routeUrl(h) {
    if (!h) return h;
    if (/^https?:/i.test(h)) return h;
    if (h === "#/home") return "dashboard.html";
    var m;
    if ((m = /^#\/s\/(.+)$/.exec(h))) return "section.html?s=" + m[1];
    if ((m = /^#\/p\/(.+)$/.exec(h))) return "page.html?p=" + m[1];
    if ((m = /^#\/v\/(.+)$/.exec(h))) { var v = byId[m[1]]; return v ? v.page : "dashboard.html"; }
    return h;
  }

  var here = (location.pathname.split("/").pop() || "").toLowerCase();
  if (!here) here = "index.html";

  // Determine the current route + active section/view.
  var route = { name: "view" }; // default; refined below
  if (here === "dashboard.html") route = { name: "home" };
  else if (here === "section.html") route = { name: "section", section: qp("s") };
  else if (here === "page.html") route = { name: "page", page: qp("p") };
  else if (byPage[here]) { var cv = byPage[here]; route = { name: "view", view: cv.id, section: cv._section.id }; }
  else route = { name: "other" };

  // ---- Desktop sidebar (grouped accordion) ----------------------------------
  function buildSidebar() {
    var h = "";
    h += '<a class="brandlink" href="dashboard.html"><span class="mark">◐</span>' +
      '<span class="bt">Wattlas<small>' + TAGLINE + '</small></span></a>';
    h += '<nav class="snav" aria-label="Site">';
    h += '<a class="nlink' + (route.name === "home" ? " active" : "") + '" href="dashboard.html"><span class="ni">⌂</span>Home</a>';
    SECTIONS.forEach(function (s) {
      var open = (route.section === s.id) ? true : (FOLDS[s.id] !== true);
      var headActive = (route.name === "section" && route.section === s.id);
      h += '<div class="ngroup" style="--ga:' + s.accent + '">';
      h += '<div class="ghead-row">' +
        '<a class="ghead' + (headActive ? " active" : "") + '" href="section.html?s=' + s.id + '">' +
        '<span class="gn">' + s.n + '</span><span class="gt">' + esc(s.title) + '</span>' +
        '<span class="gq">' + esc(s.kicker) + '</span></a>' +
        '<button class="gtoggle" type="button" data-sec="' + s.id + '" aria-expanded="' + open + '" ' +
        'aria-label="Collapse or expand ' + esc(s.title) + '"><svg viewBox="0 0 10 6" aria-hidden="true">' +
        '<path d="M1 1l4 4 4-4"></path></svg></button>' +
        '</div>';
      h += '<div class="gkids' + (open ? " open" : "") + '" data-sec="' + s.id + '">';
      s.views.forEach(function (v) {
        var on = (route.name === "view" && route.view === v.id);
        h += '<a class="nkid' + (on ? " active" : "") + '" href="' + v.page + '">' + esc(v.title) + '</a>';
      });
      h += "</div></div>";
    });
    h += "</nav>";
    h += '<div class="nfoot">Open data, pre-computed and static. ENTSO-E · RTE/ODRÉ · SMARD · MaStR · NESO.</div>';
    var aside = document.createElement("aside");
    aside.className = "side";
    aside.innerHTML = h;
    return aside;
  }

  // ---- Mobile top bar -------------------------------------------------------
  function buildTopbar() {
    var header = document.createElement("header");
    header.className = "topbar";
    // Pages with their own sticky toolbar can't have a second sticky bar.
    if (document.querySelector(".bar, .jumpnav, .ctrl")) header.classList.add("static");
    header.innerHTML =
      '<button class="mb" id="wx-menuBtn" aria-label="Menu">☰</button>' +
      '<button class="mb back" id="wx-backBtn" aria-label="Back">‹</button>' +
      '<a class="tb-brand" href="dashboard.html">Wattlas <small>European electricity</small></a>';
    return header;
  }

  // ---- Mobile bottom tab bar (the five sections) ----------------------------
  function buildTabbar() {
    var tb = document.createElement("nav");
    tb.className = "tabbar";
    tb.setAttribute("aria-label", "Sections");
    tb.innerHTML = SECTIONS.map(function (s) {
      var active = (route.section === s.id);
      return '<a class="' + (active ? "active" : "") + '" style="--ta:' + s.accent + '" href="section.html?s=' + s.id + '">' +
        '<span class="tn">' + s.n + '</span><span class="tdot"></span>' +
        '<span class="tl">' + esc(s.short || s.title) + '</span></a>';
    }).join("");
    return tb;
  }

  // ---- Site footer ----------------------------------------------------------
  function buildFooter() {
    var ft = IA.footer;
    var cols = ft.columns.map(function (c) {
      var links = (c.kind === "sections")
        ? SECTIONS.map(function (s) { return { t: s.title, href: "section.html?s=" + s.id }; })
        : c.links.map(function (l) { return { t: l.t, href: routeUrl(l.href) }; });
      return '<div class="foot-col"><h4>' + esc(c.title) + '</h4>' +
        links.map(function (l) {
          var ext = /^https?:/i.test(l.href) ? ' target="_blank" rel="noopener"' : "";
          return '<a href="' + l.href + '"' + ext + '>' + esc(l.t) + '</a>';
        }).join("") + "</div>";
    }).join("");
    var year = new Date().getFullYear();
    var footer = document.createElement("footer");
    footer.className = "sitefoot";
    footer.innerHTML =
      '<div class="foot-top">' +
        '<div class="foot-brand"><div class="fb-mark"><span>◐</span>Wattlas</div><p>' + esc(ft.tagline) + "</p></div>" +
        cols +
      "</div>" +
      '<div class="foot-bot"><span class="fb-meta">' + esc(ft.meta) + "</span>" +
        '<span class="fb-copy">© ' + year + " Wattlas · open data</span></div>";
    return footer;
  }

  // ---- "More in this question" rail (view pages only) -----------------------
  function buildReadon() {
    if (route.name !== "view") return null;
    var v = byId[route.view];
    if (!v) return null;
    var s = v._section;
    var sibs = s.views.filter(function (x) { return x.id !== v.id; }).slice(0, 4);
    if (!sibs.length) return null;
    var wrap = document.createElement("div");
    wrap.className = "readon";
    wrap.style.setProperty("--a", s.accent);
    wrap.innerHTML = '<div class="ro-head">More in “' + esc(s.title) + '”</div><div class="ro-grid">' +
      sibs.map(function (x) {
        return '<a class="ro-card" href="' + x.page + '"><span class="ro-t">' + esc(x.title) +
          '</span><span class="ro-o">' + esc(x.one) + "</span></a>";
      }).join("") + "</div>";
    return wrap;
  }

  // ---- Parent route (mobile back button) ------------------------------------
  function parentUrl() {
    if (route.name === "view" && route.section) return "section.html?s=" + route.section;
    return "dashboard.html";
  }

  // ---- Mount ----------------------------------------------------------------
  function mount() {
    var shell = document.querySelector(".shell");
    var sideEl = buildSidebar();
    if (shell) shell.insertBefore(sideEl, shell.firstChild);
    if (sideEl) sideEl.querySelectorAll(".gtoggle").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        var sec = btn.getAttribute("data-sec");
        var kids = sideEl.querySelector('.gkids[data-sec="' + sec + '"]');
        if (!kids) return;
        var nowOpen = kids.classList.toggle("open");
        btn.setAttribute("aria-expanded", String(nowOpen));
        FOLDS[sec] = !nowOpen;
        saveFolds();
      });
    });

    var scrim = document.createElement("div");
    scrim.id = "wx-scrim";
    document.body.insertBefore(scrim, document.body.firstChild);
    document.body.insertBefore(buildTopbar(), document.body.firstChild);
    document.body.appendChild(buildTabbar());

    var mainEl = document.querySelector(".main") || document.querySelector(".content");
    if (mainEl) {
      var ro = buildReadon();
      if (ro) mainEl.appendChild(ro);
      mainEl.appendChild(buildFooter());
    }

    // Mobile: show the back button on any non-home route (hides the ☰ then).
    if (route.name !== "home") document.body.classList.add("show-back");

    var menuBtn = document.getElementById("wx-menuBtn");
    var backBtn = document.getElementById("wx-backBtn");
    if (menuBtn) menuBtn.addEventListener("click", function () { document.body.classList.toggle("nav-open"); });
    if (scrim) scrim.addEventListener("click", function () { document.body.classList.remove("nav-open"); });
    if (backBtn) backBtn.addEventListener("click", function () { location.href = parentUrl(); });

    // Graceful empty state: when a data page swaps the loading text for a message
    // (load failure or "awaiting source"), drop the spinner so it reads as a
    // static state, not a stuck loader.
    var statusEl = document.getElementById("status");
    if (statusEl && window.MutationObserver) {
      new MutationObserver(function () {
        if (getComputedStyle(statusEl).display !== "none") statusEl.classList.add("empty");
      }).observe(statusEl, { childList: true, characterData: true, subtree: true });
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
