// Wattlas Dashboard v2 — core: state, data, brush, linked hover, shared chart helpers.
"use strict";

// ---------- Formatting ----------
const eur = (n) => "€" + Math.round(n).toLocaleString();
const hh = (h) => String(h).padStart(2, "0") + ":00";
const gw1 = (n) => (Math.round(n * 10) / 10) + " GW";
const mwh = (n) => Math.round(n).toLocaleString() + " MWh";
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const monthLabel = (m) => { const [y, mo] = m.split("-"); return MONTHS[+mo - 1] + " " + y.slice(2); };
const mean = (a) => { const v = a.filter((x) => x != null); return v.length ? v.reduce((x, y) => x + y, 0) / v.length : null; };
const extreme = (arr, want) => { let idx = -1, v = want === "max" ? -Infinity : Infinity;
  (arr || []).forEach((x, i) => { if (x == null) return;
    if ((want === "max" && x > v) || (want === "min" && x < v)) { v = x; idx = i; } });
  return { idx, val: v }; };

// ---------- Zone palette (categorical, sits on the warm-paper tokens) ----------
const ZONE_COLORS = {
  DE_LU: "#185fa5", FR: "#a3402d", NL: "#b8860b", BE: "#2f7d78", PL: "#7d5ba6", AT: "#3b6d11",
};
const zoneColor = (z) => ZONE_COLORS[z] || "#807e74";
const zoneShort = (z) => ({ DE_LU: "Germany", FR: "France", NL: "Netherlands", BE: "Belgium", PL: "Poland", AT: "Austria" }[z] || z);

// ---------- Global state ----------
const D = {};            // loaded JSON
const charts = {};       // canvasId -> Chart
const S = {
  zone: "DE_LU",         // primary zone
  compare: [],           // up to 5 extra zones (6 total in play)
  range: null,           // [isoStart, isoEnd] from brush; null = all
  tweaks: { density: "airy", spreadStyle: "bars", mixStyle: "absolute", carbonStyle: "time", pulseSplit: true },
};
const rerenders = [];    // panels register their render fn here
function renderAll() { rerenders.forEach((fn) => { try { fn(); } catch (e) { console.error(e); } }); updatePeriodNote(); }

// ---------- Data ----------
async function loadJSON(name) {
  for (const path of ["../data/" + name, "data/" + name, "/data/" + name]) {
    try { const r = await fetch(path); if (r.ok) return r.json(); } catch (e) {}
  }
  return null;
}
const has = (file, z) => D[file] && D[file].zones && D[file].zones[z];

// Window filter: [start,end] inclusive, null = everything
const inWin = (iso) => !S.range || (iso >= S.range[0] && iso <= S.range[1]);
function setRange(r) { S.range = r; renderAll(); drawBrushSel(); }

function updatePeriodNote() {
  const el = document.getElementById("periodNote"); if (!el || !D.spread) return;
  const s = S.range ? S.range[0] : D.spread.period_start, e = S.range ? S.range[1] : D.spread.period_end;
  el.textContent = fmtDate(s) + " – " + fmtDate(e);
}

// ---------- Chart helpers ----------
const TICK = { color: "#807e74", font: { size: 11 } };
function draw(boxId, canvasId, cfg) {
  if (charts[canvasId]) { charts[canvasId].destroy(); delete charts[canvasId]; }
  const box = document.getElementById(boxId);
  box.innerHTML = '<canvas id="' + canvasId + '"></canvas>';
  charts[canvasId] = new Chart(document.getElementById(canvasId), cfg);
  return charts[canvasId];
}
function noData(boxId, canvasId, msg) {
  if (charts[canvasId]) { charts[canvasId].destroy(); delete charts[canvasId]; }
  document.getElementById(boxId).innerHTML = '<div class="nodata">' + msg + "</div>";
}
const baseOpts = (scales, extraPlugins = {}) => ({
  responsive: true, maintainAspectRatio: false, animation: false, normalized: true,
  interaction: { mode: "index", intersect: false },
  plugins: Object.assign({ legend: { display: false } }, extraPlugins), scales,
});
const axX = (extra = {}) => Object.assign({ ticks: Object.assign({}, TICK, { maxTicksLimit: 7, maxRotation: 0 }), grid: { display: false }, border: { color: "rgba(40,36,20,0.15)" } }, extra);
const axY = (extra = {}) => Object.assign({ ticks: Object.assign({}, TICK), grid: { color: "rgba(40,36,20,0.05)" }, border: { display: false } }, extra);

// ---------- Linked hover (crosshair shared across panels) ----------
// Charts register with a key-space: "date" (daily series) or "hour" (24h profiles).
// Hovering one chart draws a guide line at the same key in every sibling chart.
const linked = { date: new Set(), hour: new Set() };
let hoverKey = { date: null, hour: null };

const crosshairPlugin = {
  id: "wattlasCrosshair",
  afterDraw(chart) {
    const space = chart.$linkSpace; if (!space) return;
    const key = hoverKey[space]; if (key == null) return;
    const keys = chart.$linkKeys; if (!keys) return;
    const i = keys.indexOf(key); if (i < 0) return;
    const x = chart.scales.x.getPixelForValue(i);
    if (!isFinite(x)) return;
    const { top, bottom } = chart.chartArea;
    const ctx = chart.ctx;
    ctx.save();
    ctx.strokeStyle = "rgba(184,134,11,0.55)"; ctx.lineWidth = 1; ctx.setLineDash([3, 3]);
    ctx.beginPath(); ctx.moveTo(x, top); ctx.lineTo(x, bottom); ctx.stroke();
    ctx.restore();
  },
};
Chart.register(crosshairPlugin);

function linkChart(chart, space, keys) {
  chart.$linkSpace = space; chart.$linkKeys = keys;
  linked[space].add(chart);
  chart.canvas.addEventListener("mousemove", (ev) => {
    const els = chart.getElementsAtEventForMode(ev, "index", { intersect: false }, false);
    const k = els.length ? keys[els[0].index] : null;
    if (k !== hoverKey[space]) { hoverKey[space] = k; redrawSpace(space, chart); }
  });
  chart.canvas.addEventListener("mouseleave", () => {
    if (hoverKey[space] != null) { hoverKey[space] = null; redrawSpace(space, chart); }
  });
}
function redrawSpace(space, except) {
  linked[space].forEach((c) => {
    if (!c.canvas || !c.canvas.isConnected) { linked[space].delete(c); return; }
    if (c !== except) c.draw();
    else c.draw(); // also redraw origin so its own guide shows
  });
}
// draw() destroys charts; purge them from link registries via Chart destroy hook
Chart.register({ id: "wattlasUnlink", beforeDestroy(c) { linked.date.delete(c); linked.hour.delete(c); } });

// ---------- Brush (range selector over the full period) ----------
const brush = { days: [], vals: [], dragging: false, x0: 0 };
function initBrush() {
  const H = D.hist, sp = D.spread && D.spread.zones && D.spread.zones.DE_LU;
  // context series: daily TB1 for DE-LU over the dashboard period
  const rows = sp ? sp.days : [];
  brush.days = rows.map((r) => r.date);
  brush.vals = rows.map((r) => r.tb1);
  const cv = document.getElementById("brushCanvas");
  const wrap = document.getElementById("brushWrap");
  const dpr = window.devicePixelRatio || 1;
  function paint() {
    const w = wrap.clientWidth, h = wrap.clientHeight;
    cv.width = w * dpr; cv.height = h * dpr;
    const ctx = cv.getContext("2d"); ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);
    const max = Math.max(...brush.vals.filter((v) => v != null), 1);
    const n = brush.vals.length;
    ctx.fillStyle = "rgba(24,95,165,0.35)";
    for (let i = 0; i < n; i++) {
      const v = brush.vals[i]; if (v == null) continue;
      const x = (i / (n - 1)) * w, bh = Math.max(1, (v / max) * (h - 6));
      ctx.fillRect(x, h - bh, Math.max(1, w / n - 0.4), bh);
    }
  }
  paint();
  new ResizeObserver(paint).observe(wrap);

  const pos2idx = (clientX) => {
    const r = wrap.getBoundingClientRect();
    const f = Math.min(1, Math.max(0, (clientX - r.left) / r.width));
    return Math.round(f * (brush.days.length - 1));
  };
  let i0 = 0;
  const down = (x) => { brush.dragging = true; i0 = pos2idx(x); };
  const move = (x) => {
    if (!brush.dragging) return;
    const i1 = pos2idx(x);
    const a = Math.min(i0, i1), b = Math.max(i0, i1);
    if (b - a >= 3) setRangeQuiet([brush.days[a], brush.days[b]]);
  };
  const up = (x) => {
    if (!brush.dragging) return; brush.dragging = false;
    const i1 = pos2idx(x);
    const a = Math.min(i0, i1), b = Math.max(i0, i1);
    if (b - a < 3) { setRange(null); clearSegActive(); }
    else { setRange([brush.days[a], brush.days[b]]); clearSegActive(); }
  };
  wrap.addEventListener("mousedown", (e) => { e.preventDefault(); down(e.clientX); });
  window.addEventListener("mousemove", (e) => move(e.clientX));
  window.addEventListener("mouseup", (e) => up(e.clientX));
  wrap.addEventListener("touchstart", (e) => down(e.touches[0].clientX), { passive: true });
  wrap.addEventListener("touchmove", (e) => move(e.touches[0].clientX), { passive: true });
  wrap.addEventListener("touchend", (e) => up(e.changedTouches[0].clientX));
  wrap.addEventListener("dblclick", () => { setRange(null); clearSegActive(); });
}
function setRangeQuiet(r) { S.range = r; drawBrushSel(); updatePeriodNote(); } // live preview while dragging (no full rerender)
function drawBrushSel() {
  const sel = document.getElementById("brushSel");
  if (!S.range || !brush.days.length) { sel.style.display = "none"; return; }
  const n = brush.days.length - 1;
  const ia = Math.max(0, brush.days.indexOf(S.range[0]));
  let ib = brush.days.indexOf(S.range[1]); if (ib < 0) ib = n;
  sel.style.display = "block";
  sel.style.left = (ia / n) * 100 + "%";
  sel.style.width = ((ib - ia) / n) * 100 + "%";
}
function clearSegActive() { document.querySelectorAll("#winSeg button").forEach((b) => b.classList.remove("active")); 
  if (!S.range) { const all = document.querySelector('#winSeg button[data-days="9999"]'); if (all) all.classList.add("active"); } }

function applyPresetWindow(days) {
  if (!D.spread) return;
  if (days >= 9999) { setRange(null); return; }
  const end = D.spread.period_end;
  const d = new Date(end + "T00:00:00Z"); d.setUTCDate(d.getUTCDate() - days);
  setRange([d.toISOString().slice(0, 10), end]);
}

// ---------- Zones in play (primary + comparisons) ----------
const zonesInPlay = () => [S.zone].concat(S.compare);

// ---------- Info tooltips ----------
function initTips(TIPS) {
  let pop = null, owner = null;
  const close = () => { if (pop) { pop.remove(); pop = null; owner = null; } };
  function open(btn) {
    close(); const txt = TIPS[btn.dataset.tip]; if (!txt) return;
    pop = document.createElement("div"); pop.className = "tip-pop"; pop.setAttribute("role", "tooltip"); pop.textContent = txt;
    document.body.appendChild(pop);
    const r = btn.getBoundingClientRect();
    pop.style.top = (window.scrollY + r.bottom + 6) + "px";
    pop.style.left = Math.max(8, Math.min(window.scrollX + r.left - 4, window.scrollX + window.innerWidth - pop.offsetWidth - 12)) + "px";
    owner = btn;
  }
  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".info");
    if (btn) { e.preventDefault(); e.stopPropagation(); owner === btn ? close() : open(btn); }
    else if (!e.target.closest(".tip-pop")) close();
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
  window.addEventListener("scroll", close, { passive: true });
}

// ---------- Story headline / stat chips ----------
function setStory(id, html) { const el = document.getElementById(id); if (el) el.innerHTML = html; }
function setStats(id, items) {
  const el = document.getElementById(id); if (!el) return;
  el.innerHTML = items.map((s) =>
    '<span class="stat">' + s.label + ' <b class="' + (s.cls || "") + '">' + s.val + "</b>" +
    (s.tip ? ' <button class="info" data-tip="' + s.tip + '" aria-label="More on ' + s.label + '">i</button>' : "") +
    "</span>").join("");
}
const hi = (txt, c) => '<strong class="hi-' + (c || "amber") + '">' + txt + "</strong>";
