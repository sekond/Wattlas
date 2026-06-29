/* Wattlas redesign — render + router + schematic charts.
 * Pure client-side prototype: no data fetch, so it always renders.
 * Demonstrates the proposed information architecture end to end. */
(function () {
  var IA = window.WATTLAS_IA;
  var SECTIONS = IA.sections;
  var byId = {};
  SECTIONS.forEach(function (s) { s.views.forEach(function (v) { v._section = s; byId[v.id] = v; }); });

  var navMode = localStorage.getItem("wattlas_navmode") || "question"; // "question" | "original"
  var app = document.getElementById("view");
  var sideNav = document.getElementById("sidenav");

  // ---------- helpers ----------
  function el(html) { var t = document.createElement("template"); t.innerHTML = html.trim(); return t.content.firstElementChild; }
  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function tagLabel(t) {
    return { chart: "Chart", map: "Map view", model: "Model", historical: "Historical" }[t] || t;
  }

  // ---------- sidebar nav ----------
  function renderNav(active) {
    var route = parseHash();
    var h = '';
    h += '<a class="brandlink" href="#/home"><span class="mark">◐</span><span class="bt">Wattlas<small>European electricity, explained</small></span></a>';

    h += '<div class="navmode">' +
      '<button data-mode="question" class="' + (navMode === "question" ? "on" : "") + '">By question</button>' +
      '<button data-mode="original" class="' + (navMode === "original" ? "on" : "") + '">Original</button>' +
      '</div>';

    h += '<nav class="snav" aria-label="Site">';
    h += '<a class="nlink home ' + (route.name === "home" ? "active" : "") + '" href="#/home"><span class="ni">⌂</span>Home</a>';
    h += '<a class="nlink home ' + (route.name === "audit" ? "active" : "") + '" href="#/audit"><span class="ni">✦</span>Why this changed</a>';

    if (navMode === "question") {
      SECTIONS.forEach(function (s) {
        var open = (route.section === s.id);
        h += '<div class="ngroup" style="--ga:' + s.accent + '">';
        h += '<a class="ghead ' + (route.name === "section" && route.section === s.id ? "active" : "") + '" href="#/s/' + s.id + '">' +
          '<span class="gn">' + s.n + '</span><span class="gt">' + esc(s.title) + '</span><span class="gq">' + esc(s.kicker) + '</span></a>';
        h += '<div class="gkids ' + (open ? "open" : "") + '">';
        s.views.forEach(function (v) {
          var on = route.name === "view" && route.view === v.id;
          h += '<a class="nkid ' + (on ? "active" : "") + '" href="#/v/' + v.id + '">' + esc(v.title) + '</a>';
        });
        h += '</div></div>';
      });
    } else {
      IA.audit.original.forEach(function (g) {
        if (g.group) h += '<div class="ogroup">' + esc(g.group) + '</div>';
        g.items.forEach(function (it) {
          h += '<a class="nlink flat" href="#/audit"><span class="ni mono">' + esc(it.m) + '</span>' + esc(it.t) + '</a>';
        });
      });
      h += '<div class="oflat-note">26 links, one weight, no path through them. This is what we\u2019re replacing.</div>';
    }
    h += '</nav>';
    h += '<div class="nfoot">Open data, pre-computed and static. ENTSO-E · RTE/ODR\u00c9 · SMARD · MaStR · NESO.</div>';
    sideNav.innerHTML = h;

    sideNav.querySelectorAll(".navmode button").forEach(function (b) {
      b.addEventListener("click", function () {
        navMode = b.getAttribute("data-mode");
        localStorage.setItem("wattlas_navmode", navMode);
        renderNav();
      });
    });
  }

  // ---------- HOME ----------
  function renderHome() {
    var h = '';
    h += '<header class="home-hero">' +
      '<p class="eyebrow">A field guide to European power markets</p>' +
      '<h1>When — and how much — the price of <em>electricity</em> moves in Europe.</h1>' +
      '<p class="lead">Open data on Germany and its neighbours, pre-computed into views you can actually read. Everything answers one of five questions. Start with whichever you came for.</p>' +
      '<div class="hero-actions"><a class="btn" href="#/s/rhythm">Start with the daily rhythm</a>' +
      '<a class="btn ghost" href="#/audit">Why we restructured \u2192</a></div>' +
      '</header>';

    h += '<div class="five-head"><span>Five questions</span><span class="rule"></span><span>' + countViews() + ' views</span></div>';

    h += '<div class="sgrid">';
    SECTIONS.forEach(function (s) {
      h += '<a class="scard" href="#/s/' + s.id + '" style="--a:' + s.accent + '">' +
        '<div class="scard-top"><span class="sn">' + s.n + '</span>' +
        '<canvas class="thumb" width="200" height="120" data-thumb="' + s.thumb + '"></canvas></div>' +
        '<p class="sq">' + esc(s.kicker) + '</p>' +
        '<h2>' + esc(s.title) + '</h2>' +
        '<p class="sl">' + esc(s.lede) + '</p>' +
        '<div class="chips">' + s.views.map(function (v) { return '<span class="chip">' + esc(v.title) + '</span>'; }).join("") + '</div>' +
        '</a>';
    });
    h += '</div>';

    h += '<section class="home-note"><h3>What changed</h3>' +
      '<p>The old menu listed all ' + countViews() + ' destinations in one flat column, grouped by how the data was built — “The Eight Views”, “Deep dives”, “Value layer.” Useful to the engineer, opaque to everyone else. We regrouped every view under the question it answers, gave the strongest stories room to lead, and connected them so each one points to where to go next. ' +
      '<a href="#/audit">See the full audit \u2192</a></p></section>';

    app.innerHTML = h;
    drawThumbs();
  }

  function countViews() { var n = 0; SECTIONS.forEach(function (s) { n += s.views.length; }); return n + 2; }

  // ---------- SECTION HUB ----------
  function renderSection(id) {
    var s = SECTIONS.find(function (x) { return x.id === id; });
    if (!s) return renderHome();
    var idx = SECTIONS.indexOf(s);
    var next = SECTIONS[(idx + 1) % SECTIONS.length];

    var h = '';
    h += '<div class="crumb"><a href="#/home">Home</a><span>/</span><span>' + esc(s.title) + '</span></div>';
    h += '<header class="sec-hero" style="--a:' + s.accent + '">' +
      '<span class="sec-n">' + s.n + '</span>' +
      '<p class="sec-q">' + esc(s.kicker) + '</p>' +
      '<h1>' + esc(s.title) + '</h1>' +
      '<p class="sec-lede">' + esc(s.lede) + '</p>' +
      '</header>';

    h += '<div class="vgrid">';
    s.views.forEach(function (v) {
      h += '<a class="vcard" href="#/v/' + v.id + '" style="--a:' + s.accent + '">' +
        '<div class="vcard-head"><h3>' + esc(v.title) + '</h3><span class="vtag ' + v.tag + '">' + tagLabel(v.tag) + '</span></div>' +
        '<p class="vone">' + esc(v.one) + '</p>' +
        '<div class="vstat"><span class="vs-val">' + esc(v.stat) + '</span><span class="vs-lbl">' + esc(v.statlbl) + '</span></div>' +
        '</a>';
    });
    h += '</div>';

    h += '<a class="next-sec" href="#/s/' + next.id + '" style="--a:' + next.accent + '">' +
      '<span class="ns-lbl">Next question</span>' +
      '<span class="ns-title">' + esc(next.kicker) + ' \u2192</span>' +
      '<span class="ns-sub">' + esc(next.title) + '</span></a>';

    app.innerHTML = h;
  }

  // ---------- VIEW DETAIL ----------
  function renderView(id) {
    var v = byId[id];
    if (!v) return renderHome();
    var s = v._section;
    var sib = s.views.filter(function (x) { return x.id !== v.id; }).slice(0, 4);

    var h = '';
    h += '<div class="crumb"><a href="#/home">Home</a><span>/</span><a href="#/s/' + s.id + '">' + esc(s.title) + '</a><span>/</span><span>' + esc(v.title) + '</span></div>';
    h += '<header class="view-hero" style="--a:' + s.accent + '">' +
      '<span class="vh-q">' + esc(s.kicker) + '</span>' +
      '<h1>' + esc(v.title) + '</h1>' +
      '<p class="vh-one">' + esc(v.one) + '</p>' +
      '<span class="vtag ' + v.tag + '">' + tagLabel(v.tag) + '</span>' +
      '</header>';

    // live, wired view — the real page framed with all its own chrome stripped
    var src = embedSrc(v.page);
    h += '<div class="live-wrap"><div class="live-bar"><span class="lb-dot" style="background:' + s.accent + '"></span>' +
      '<span class="lb-t">Live view \u00b7 real data</span>' +
      '<a class="lb-open" href="' + esc(v.page) + '" target="_blank" rel="noopener">Open standalone \u2197</a></div>' +
      '<div class="live-frame" id="liveFrame"><div class="frame-load">Loading live view\u2026</div>' +
      '<iframe id="vframe" title="' + esc(v.title) + '" src="' + esc(src) + '" scrolling="no"></iframe></div></div>';

    // keep reading within the same question
    h += '<div class="readon"><div class="ro-head">More in \u201c' + esc(s.title) + '\u201d</div><div class="ro-grid">';
    sib.forEach(function (x) {
      h += '<a class="ro-card" href="#/v/' + x.id + '" style="--a:' + s.accent + '"><span class="ro-t">' + esc(x.title) + '</span><span class="ro-o">' + esc(x.one) + '</span></a>';
    });
    h += '</div></div>';

    app.innerHTML = h;
    wireFrame();
  }

  // append ?embed=1 (and forward an anchor) so nav.js suppresses its own chrome
  function embedSrc(page) {
    var hash = "", p = page;
    var hi = page.indexOf("#");
    if (hi >= 0) { hash = page.slice(hi); p = page.slice(0, hi); }
    return p + (p.indexOf("?") >= 0 ? "&" : "?") + "embed=1" + hash;
  }

  // auto-size the framed page to its content (same-origin, so we can measure)
  function wireFrame() {
    var f = document.getElementById("vframe");
    var wrap = document.getElementById("liveFrame");
    if (!f) return;
    var loaded = false;
    function fit() {
      try {
        var d = f.contentDocument;
        if (!d || !d.body) return;
        var hgt = Math.max(d.body.scrollHeight, d.documentElement.scrollHeight);
        if (hgt > 80) { f.style.height = (hgt + 8) + "px"; if (!loaded) { loaded = true; wrap.classList.add("ready"); } }
      } catch (e) { /* cross-origin shouldn't happen locally */ }
    }
    f.addEventListener("load", function () {
      fit();
      // charts/maps draw async — re-measure a few times, then observe
      [120, 350, 700, 1400, 2500].forEach(function (t) { setTimeout(fit, t); });
      try {
        var d = f.contentDocument;
        if (d && window.ResizeObserver) new ResizeObserver(fit).observe(d.body);
      } catch (e) {}
    });
    window.addEventListener("resize", fit);
  }

  // ---------- AUDIT ----------
  function renderAudit() {
    var a = IA.audit;
    var h = '';
    h += '<div class="crumb"><a href="#/home">Home</a><span>/</span><span>The audit</span></div>';
    h += '<header class="audit-hero">' +
      '<p class="eyebrow">UX audit</p>' +
      '<h1>' + esc(a.headline) + '</h1>' +
      '<p class="lead">' + esc(a.body) + '</p>' +
      '</header>';

    // before / after
    h += '<div class="ba">';
    h += '<div class="ba-col before"><div class="ba-tag">Before</div>' +
      '<div class="ba-frame">' + IA.audit.original.map(function (g) {
        return (g.group ? '<div class="ba-grp">' + esc(g.group) + '</div>' : '') +
          g.items.map(function (it) { return '<div class="ba-row"><span class="bm">' + esc(it.m) + '</span>' + esc(it.t) + '</div>'; }).join("");
      }).join("") + '</div>' +
      '<p class="ba-cap">One flat column. 26 links, grouped by build order.</p></div>';

    h += '<div class="ba-col after"><div class="ba-tag on">After</div>' +
      '<div class="ba-frame">' + SECTIONS.map(function (s) {
        return '<div class="ba-sec" style="--a:' + s.accent + '"><div class="ba-sh"><span class="ba-sn">' + s.n + '</span>' + esc(s.title) + '<span class="ba-sq">' + esc(s.kicker) + '</span></div>' +
          '<div class="ba-vs">' + s.views.map(function (v) { return '<span class="ba-v">' + esc(v.title) + '</span>'; }).join("") + '</div></div>';
      }).join("") + '</div>' +
      '<p class="ba-cap">Five questions. Each view under the one it answers, strongest stories leading.</p></div>';
    h += '</div>';

    // problems
    h += '<div class="prob-head">What was getting in the way</div>';
    h += '<div class="probs">';
    a.problems.forEach(function (p, i) {
      h += '<div class="prob"><span class="pn">' + (i + 1) + '</span><div><h4>' + esc(p.t) + '</h4><p>' + esc(p.d) + '</p></div></div>';
    });
    h += '</div>';

    h += '<a class="btn" href="#/home">See the redesigned home \u2192</a>';
    app.innerHTML = h;
  }

  // ---------- STANDARD PAGE ----------
  function renderPage(id) {
    var pg = (IA.pages || []).find(function (p) { return p.id === id; });
    if (!pg) return renderHome();
    var h = '';
    h += '<div class="crumb"><a href="#/home">Home</a><span>/</span><span>' + esc(pg.title) + '</span></div>';
    h += '<header class="page-hero"><p class="pk">' + esc(pg.kicker || "") + '</p><h1>' + esc(pg.title) + '</h1></header>';
    h += '<div class="page-body">';
    pg.blocks.forEach(function (b) {
      if (b.h) h += '<h3>' + esc(b.h) + '</h3>';
      if (b.p) h += '<p>' + b.p + '</p>';
      if (b.list) h += '<ul>' + b.list.map(function (li) { return '<li>' + li + '</li>'; }).join("") + '</ul>';
    });
    h += '</div>';
    app.innerHTML = h;
  }

  // ---------- site footer (rendered once) ----------
  function renderFooter() {
    var ft = IA.footer, foot = document.getElementById("sitefoot");
    var cols = ft.columns.map(function (c) {
      var links;
      if (c.kind === "sections") links = SECTIONS.map(function (s) { return { t: s.title, href: "#/s/" + s.id }; });
      else links = c.links;
      return '<div class="foot-col"><h4>' + esc(c.title) + '</h4>' +
        links.map(function (l) { return '<a href="' + l.href + '"' + (l.href.indexOf("http") === 0 ? ' target="_blank" rel="noopener"' : "") + '>' + esc(l.t) + '</a>'; }).join("") + '</div>';
    }).join("");
    foot.innerHTML =
      '<div class="foot-top">' +
        '<div class="foot-brand"><div class="fb-mark"><span>\u25d0</span>Wattlas</div><p>' + esc(ft.tagline) + '</p></div>' +
        cols +
      '</div>' +
      '<div class="foot-bot"><span class="fb-meta">' + esc(ft.meta) + '</span>' +
        '<span class="fb-copy">\u00a9 ' + new Date().getFullYear() + ' Wattlas \u00b7 open data</span></div>';
  }

  // ---------- schematic charts ----------
  function drawThumbs() {
    document.querySelectorAll("canvas[data-thumb]").forEach(function (c) {
      var ctx = c.getContext("2d");
      var w = c.width, hgt = c.height;
      ctx.clearRect(0, 0, w, hgt);
      var big = c.getAttribute("data-big");
      var kind = c.getAttribute("data-thumb");
      var ink = "#2b2a27", hint = "rgba(43,42,39,.18)";
      var ac = getComputedStyle(c).getPropertyValue("--draw") || "#185fa5";
      ctx.lineWidth = big ? 2.5 : 2;
      if (kind === "duck") drawDuck(ctx, w, hgt, big);
      else if (kind === "mix") drawMix(ctx, w, hgt, big);
      else if (kind === "map") drawMap(ctx, w, hgt, big);
      else if (kind === "stress") drawStress(ctx, w, hgt, big);
      else if (kind === "bill") drawBill(ctx, w, hgt, big);
    });
  }
  function pad(w, hgt, p) { return { x0: p, y0: p, x1: w - p, y1: hgt - p }; }
  function grid(ctx, b) { ctx.strokeStyle = "rgba(43,42,39,.10)"; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(b.x0, b.y1); ctx.lineTo(b.x1, b.y1); ctx.stroke(); }
  function drawDuck(ctx, w, hgt, big) {
    var b = pad(w, hgt, big ? 28 : 14); grid(ctx, b);
    var pts = [0.62, 0.5, 0.34, 0.2, 0.32, 0.6, 0.92, 0.78];
    ctx.strokeStyle = "#185fa5"; ctx.lineWidth = big ? 3 : 2.2; ctx.lineJoin = "round"; ctx.beginPath();
    pts.forEach(function (p, i) { var x = b.x0 + (b.x1 - b.x0) * i / (pts.length - 1); var y = b.y1 - (b.y1 - b.y0) * p; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.stroke();
    // negative zone marker
    ctx.fillStyle = "rgba(163,45,45,.5)"; var nx = b.x0 + (b.x1 - b.x0) * 3 / 7, ny = b.y1 - (b.y1 - b.y0) * 0.2; ctx.beginPath(); ctx.arc(nx, ny, big ? 5 : 3.5, 0, 7); ctx.fill();
  }
  function drawMix(ctx, w, hgt, big) {
    var b = pad(w, hgt, big ? 28 : 14);
    var cols = ["#3b6d11", "#b8860b", "#185fa5", "#7a756c", "#a32d2d"];
    var n = big ? 9 : 6, bw = (b.x1 - b.x0) / n * 0.7, gap = (b.x1 - b.x0) / n * 0.3;
    for (var i = 0; i < n; i++) {
      var x = b.x0 + i * (bw + gap), yb = b.y1, total = b.y1 - b.y0;
      var segs = [0.18 + 0.12 * Math.sin(i), 0.22, 0.16, 0.12, 0.1].map(function (s) { return Math.max(0.05, s); });
      var sum = segs.reduce(function (a, c) { return a + c; }, 0);
      segs.forEach(function (s, k) { var hh = total * (s / sum); ctx.fillStyle = cols[k]; ctx.fillRect(x, yb - hh, bw, hh); yb -= hh; });
    }
  }
  function drawMap(ctx, w, hgt, big) {
    var b = pad(w, hgt, big ? 24 : 10);
    // schematic choropleth grid of regions, shaded
    var cols = ["#e7ddc7", "#d8be84", "#c79a3f", "#b8860b", "#7a5c08"];
    var rows = big ? 5 : 4, colsN = big ? 8 : 5, cw = (b.x1 - b.x0) / colsN, ch = (b.y1 - b.y0) / rows;
    for (var r = 0; r < rows; r++) for (var cc = 0; cc < colsN; cc++) {
      var v = (Math.sin(r * 1.3 + cc * 0.7) + 1) / 2; var ci = Math.min(cols.length - 1, Math.floor(v * cols.length));
      ctx.fillStyle = cols[ci]; ctx.strokeStyle = "rgba(250,249,245,.9)"; ctx.lineWidth = 1.5;
      ctx.fillRect(b.x0 + cc * cw, b.y0 + r * ch, cw, ch); ctx.strokeRect(b.x0 + cc * cw, b.y0 + r * ch, cw, ch);
    }
  }
  function drawStress(ctx, w, hgt, big) {
    var b = pad(w, hgt, big ? 28 : 14); grid(ctx, b);
    // renewables collapsing toward zero, price climbing
    var ren = [0.7, 0.55, 0.3, 0.12, 0.06, 0.05, 0.18, 0.4];
    var price = [0.2, 0.3, 0.5, 0.78, 0.9, 0.88, 0.6, 0.4];
    function line(arr, col) { ctx.strokeStyle = col; ctx.lineWidth = big ? 3 : 2.2; ctx.lineJoin = "round"; ctx.beginPath(); arr.forEach(function (p, i) { var x = b.x0 + (b.x1 - b.x0) * i / (arr.length - 1); var y = b.y1 - (b.y1 - b.y0) * p; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }); ctx.stroke(); }
    line(ren, "#3b6d11"); line(price, "#a32d2d");
  }
  function drawBill(ctx, w, hgt, big) {
    var b = pad(w, hgt, big ? 28 : 14);
    var segs = [0.42, 0.33, 0.25]; var cols = ["#6b4ea3", "#a08bcf", "#d6cbe9"]; var labels = ["wholesale", "grid", "tax"];
    var yb = b.y1, total = b.y1 - b.y0, x = b.x0, bw = (b.x1 - b.x0) * (big ? 0.34 : 0.5);
    segs.forEach(function (s, k) { var hh = total * s; ctx.fillStyle = cols[k]; ctx.fillRect(x, yb - hh, bw, hh); yb -= hh; });
  }

  // ---------- bottom tab bar (mobile) ----------
  function renderTabs(r) {
    var tb = document.getElementById("tabbar");
    tb.innerHTML = SECTIONS.map(function (s) {
      var active = (r.section === s.id);
      return '<a class="' + (active ? "active" : "") + '" style="--ta:' + s.accent + '" href="#/s/' + s.id + '">' +
        '<span class="tn">' + s.n + '</span><span class="tdot"></span><span class="tl">' + esc(s.short || s.title) + '</span></a>';
    }).join("");
  }

  function parentHash(r) {
    if (r.name === "view" && r.section) return "#/s/" + r.section;
    return "#/home";
  }

  // ---------- router ----------
  function parseHash() {
    var hsh = (location.hash || "#/home").replace(/^#\/?/, "");
    var parts = hsh.split("/");
    if (parts[0] === "s" && parts[1]) return { name: "section", section: parts[1] };
    if (parts[0] === "v" && parts[1]) { var v = byId[parts[1]]; return { name: "view", view: parts[1], section: v ? v._section.id : null }; }
    if (parts[0] === "audit") return { name: "audit" };
    if (parts[0] === "p" && parts[1]) return { name: "page", page: parts[1] };
    return { name: "home" };
  }
  function route() {
    var r = parseHash();
    if (r.name === "section") renderSection(r.section);
    else if (r.name === "view") renderView(r.view);
    else if (r.name === "audit") renderAudit();
    else if (r.name === "page") renderPage(r.page);
    else renderHome();
    renderNav();
    renderTabs(r);
    document.body.classList.toggle("show-back", r.name !== "home");
    document.querySelector(".content").scrollTop = 0;
    // close mobile drawer on navigate
    document.body.classList.remove("nav-open");
  }
  window.addEventListener("hashchange", route);

  // mobile drawer + back
  document.getElementById("menuBtn").addEventListener("click", function () { document.body.classList.toggle("nav-open"); });
  document.getElementById("scrim").addEventListener("click", function () { document.body.classList.remove("nav-open"); });
  document.getElementById("backBtn").addEventListener("click", function () { location.hash = parentHash(parseHash()); });

  renderFooter();
  route();
})();
