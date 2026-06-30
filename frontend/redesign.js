/* Wattlas — render logic for the editorial chrome pages (home, section hub,
 * standard page). Reads window.WATTLAS_IA (the source of record) and renders
 * into #view. Which view to render is chosen by body[data-wx].
 *
 * Multi-page production: prototype hash routes (#/s/…, #/p/…) are translated to
 * real page URLs (section.html?s=… etc.). No router, no iframes. */
(function () {
  var IA = window.WATTLAS_IA;
  if (!IA) return;
  var SECTIONS = IA.sections;
  var byId = {};
  SECTIONS.forEach(function (s) { s.views.forEach(function (v) { v._section = s; byId[v.id] = v; }); });
  var app = document.getElementById("view");
  if (!app) return;

  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function qp(name) { var m = new RegExp("[?&]" + name + "=([^&#]*)").exec(location.search); return m ? decodeURIComponent(m[1]) : null; }
  function tagLabel(t) { return { chart: "Chart", map: "Map view", model: "Model", historical: "Historical" }[t] || t; }
  // "26" matches the design headline: the original flat nav listed 26
  // destinations, regrouped here into the section cards. Keep in sync with copy.
  function countViews() { var n = 0; SECTIONS.forEach(function (s) { n += s.views.length; }); return n + 2; }

  // Translate prototype hash routes to real page URLs (used in authored copy).
  function fixHrefs(html) {
    return String(html)
      .replace(/href="#\/home"/g, 'href="dashboard.html"')
      .replace(/href="#\/s\/([^"]+)"/g, 'href="section.html?s=$1"')
      .replace(/href="#\/p\/([^"]+)"/g, 'href="page.html?p=$1"')
      .replace(/href="#\/v\/([^"]+)"/g, function (_, id) { var v = byId[id]; return 'href="' + (v ? v.page : "dashboard.html") + '"'; });
  }
  function setTitle(t) { document.title = t + " · Wattlas"; }

  // ---------- HOME ----------
  function renderHome() {
    document.title = "Wattlas — European electricity, explained";
    var h = "";
    h += '<header class="home-hero">' +
      '<p class="eyebrow">A field guide to European power markets</p>' +
      "<h1>When — and how much — the price of <em>electricity</em> moves in Europe.</h1>" +
      '<p class="lead">Open data on Germany and its neighbours, pre-computed into views you can actually read. ' +
      "Everything answers one of five questions. Start with whichever you came for.</p></header>";
    h += '<div class="five-head"><span>Five questions</span><span class="rule"></span><span>' + countViews() + " views</span></div>";
    h += '<div class="sgrid">';
    SECTIONS.forEach(function (s) {
      h += '<div class="scard" style="--a:' + s.accent + '">' +
        '<div class="scard-head">' +
          '<a class="scard-htext" href="section.html?s=' + s.id + '">' +
            '<span class="sn">' + s.n + "</span>" +
            '<p class="sq">' + esc(s.kicker) + "</p>" +
            "<h2>" + esc(s.title) + "</h2>" +
          "</a>" +
          '<a class="thumb-wrap" href="section.html?s=' + s.id + '" tabindex="-1" aria-hidden="true">' +
            '<canvas class="thumb" width="200" height="120" data-thumb="' + s.thumb + '"></canvas>' +
          "</a>" +
        "</div>" +
        '<p class="sl">' + esc(s.lede) + "</p>" +
        '<p class="chips-lbl">Jump straight in</p>' +
        '<div class="chips">' + s.views.map(function (v) { return '<a class="chip" href="' + v.page + '">' + esc(v.title) + "</a>"; }).join("") + "</div></div>";
    });
    h += "</div>";
    app.innerHTML = h;
    drawThumbs();
  }

  // ---------- SECTION HUB ----------
  function renderSection(id) {
    var s = SECTIONS.find(function (x) { return x.id === id; });
    if (!s) return renderHome();
    setTitle(s.title);
    var next = SECTIONS[(SECTIONS.indexOf(s) + 1) % SECTIONS.length];
    var h = "";
    h += '<div class="crumb"><a href="dashboard.html">Home</a><span>/</span><span>' + esc(s.title) + "</span></div>";
    h += '<header class="sec-hero" style="--a:' + s.accent + '"><span class="sec-n">' + s.n + "</span>" +
      '<p class="sec-q">' + esc(s.kicker) + "</p><h1>" + esc(s.title) + "</h1>" +
      '<p class="sec-lede">' + esc(s.lede) + "</p></header>";
    h += '<div class="vgrid">';
    s.views.forEach(function (v) {
      h += '<a class="vcard" href="' + v.page + '" style="--a:' + s.accent + '">' +
        '<div class="vcard-head"><h3>' + esc(v.title) + '</h3><span class="vtag ' + v.tag + '">' + tagLabel(v.tag) + "</span></div>" +
        '<p class="vone">' + esc(v.one) + "</p>" +
        '<div class="vstat"><span class="vs-val">' + esc(v.stat) + '</span><span class="vs-lbl">' + esc(v.statlbl) + "</span></div></a>";
    });
    h += "</div>";
    h += '<a class="next-sec" href="section.html?s=' + next.id + '" style="--a:' + next.accent + '">' +
      '<span class="ns-lbl">Next question</span><span class="ns-title">' + esc(next.kicker) + " →</span>" +
      '<span class="ns-sub">' + esc(next.title) + "</span></a>";
    app.innerHTML = h;
  }

  // ---------- STANDARD PAGE ----------
  function renderPage(id) {
    var pg = (IA.pages || []).find(function (p) { return p.id === id; });
    if (!pg) return renderHome();
    setTitle(pg.title);
    var h = "";
    h += '<div class="crumb"><a href="dashboard.html">Home</a><span>/</span><span>' + esc(pg.title) + "</span></div>";
    h += '<header class="page-hero"><p class="pk">' + esc(pg.kicker || "") + "</p><h1>" + esc(pg.title) + "</h1></header>";
    h += '<div class="page-body">';
    pg.blocks.forEach(function (b) {
      if (b.h) h += "<h3>" + esc(b.h) + "</h3>";
      if (b.p) h += "<p>" + fixHrefs(b.p) + "</p>";
      if (b.list) h += "<ul>" + b.list.map(function (li) { return "<li>" + fixHrefs(li) + "</li>"; }).join("") + "</ul>";
    });
    h += "</div>";
    app.innerHTML = h;
  }

  // ---------- schematic thumbnails (home section cards) ----------
  function drawThumbs() {
    document.querySelectorAll("canvas[data-thumb]").forEach(function (c) {
      var ctx = c.getContext("2d"), w = c.width, hgt = c.height;
      ctx.clearRect(0, 0, w, hgt);
      var kind = c.getAttribute("data-thumb");
      ctx.lineWidth = 2;
      if (kind === "duck") drawDuck(ctx, w, hgt);
      else if (kind === "mix") drawMix(ctx, w, hgt);
      else if (kind === "map") drawMap(ctx, w, hgt);
      else if (kind === "stress") drawStress(ctx, w, hgt);
      else if (kind === "bill") drawBill(ctx, w, hgt);
    });
  }
  function pad(w, hgt, p) { return { x0: p, y0: p, x1: w - p, y1: hgt - p }; }
  function grid(ctx, b) { ctx.strokeStyle = "rgba(43,42,39,.10)"; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(b.x0, b.y1); ctx.lineTo(b.x1, b.y1); ctx.stroke(); }
  function drawDuck(ctx, w, hgt) {
    var b = pad(w, hgt, 14); grid(ctx, b);
    var pts = [0.62, 0.5, 0.34, 0.2, 0.32, 0.6, 0.92, 0.78];
    ctx.strokeStyle = "#185fa5"; ctx.lineWidth = 2.2; ctx.lineJoin = "round"; ctx.beginPath();
    pts.forEach(function (p, i) { var x = b.x0 + (b.x1 - b.x0) * i / (pts.length - 1), y = b.y1 - (b.y1 - b.y0) * p; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.stroke();
    ctx.fillStyle = "rgba(163,45,45,.5)"; var nx = b.x0 + (b.x1 - b.x0) * 3 / 7, ny = b.y1 - (b.y1 - b.y0) * 0.2; ctx.beginPath(); ctx.arc(nx, ny, 3.5, 0, 7); ctx.fill();
  }
  function drawMix(ctx, w, hgt) {
    var b = pad(w, hgt, 14), cols = ["#3b6d11", "#b8860b", "#185fa5", "#7a756c", "#a32d2d"], n = 6,
        bw = (b.x1 - b.x0) / n * 0.7, gap = (b.x1 - b.x0) / n * 0.3;
    for (var i = 0; i < n; i++) {
      var x = b.x0 + i * (bw + gap), yb = b.y1, total = b.y1 - b.y0;
      var segs = [0.18 + 0.12 * Math.sin(i), 0.22, 0.16, 0.12, 0.1].map(function (s) { return Math.max(0.05, s); });
      var sum = segs.reduce(function (a, c) { return a + c; }, 0);
      segs.forEach(function (s, k) { var hh = total * (s / sum); ctx.fillStyle = cols[k]; ctx.fillRect(x, yb - hh, bw, hh); yb -= hh; });
    }
  }
  function drawMap(ctx, w, hgt) {
    var b = pad(w, hgt, 10), cols = ["#e7ddc7", "#d8be84", "#c79a3f", "#b8860b", "#7a5c08"], rows = 4, colsN = 5,
        cw = (b.x1 - b.x0) / colsN, ch = (b.y1 - b.y0) / rows;
    for (var r = 0; r < rows; r++) for (var cc = 0; cc < colsN; cc++) {
      var v = (Math.sin(r * 1.3 + cc * 0.7) + 1) / 2, ci = Math.min(cols.length - 1, Math.floor(v * cols.length));
      ctx.fillStyle = cols[ci]; ctx.strokeStyle = "rgba(250,249,245,.9)"; ctx.lineWidth = 1.5;
      ctx.fillRect(b.x0 + cc * cw, b.y0 + r * ch, cw, ch); ctx.strokeRect(b.x0 + cc * cw, b.y0 + r * ch, cw, ch);
    }
  }
  function drawStress(ctx, w, hgt) {
    var b = pad(w, hgt, 14); grid(ctx, b);
    var ren = [0.7, 0.55, 0.3, 0.12, 0.06, 0.05, 0.18, 0.4], price = [0.2, 0.3, 0.5, 0.78, 0.9, 0.88, 0.6, 0.4];
    function line(arr, col) { ctx.strokeStyle = col; ctx.lineWidth = 2.2; ctx.lineJoin = "round"; ctx.beginPath(); arr.forEach(function (p, i) { var x = b.x0 + (b.x1 - b.x0) * i / (arr.length - 1), y = b.y1 - (b.y1 - b.y0) * p; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }); ctx.stroke(); }
    line(ren, "#3b6d11"); line(price, "#a32d2d");
  }
  function drawBill(ctx, w, hgt) {
    var b = pad(w, hgt, 14), segs = [0.42, 0.33, 0.25], cols = ["#6b4ea3", "#a08bcf", "#d6cbe9"];
    var yb = b.y1, total = b.y1 - b.y0, x = b.x0, bw = (b.x1 - b.x0) * 0.5;
    segs.forEach(function (s, k) { var hh = total * s; ctx.fillStyle = cols[k]; ctx.fillRect(x, yb - hh, bw, hh); yb -= hh; });
  }

  // ---------- dispatch ----------
  function render() {
    var which = document.body.getAttribute("data-wx");
    if (which === "section") renderSection(qp("s"));
    else if (which === "page") renderPage(qp("p"));
    else renderHome();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", render);
  else render();
})();
