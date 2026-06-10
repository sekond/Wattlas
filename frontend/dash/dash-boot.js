// Wattlas Dashboard — boot: data load, zone chips, controls, scroll-spy, lazy render.
// One responsive shell for every width (sidebar on desktop, top scroll-spy nav on
// mobile; the same long-scroll of panels — no bottom tab bar, issue #25). Charts
// render lazily as panels scroll into view, so the phone never renders all eight at
// once and state changes only re-render what's on screen.
"use strict";

const TIPS = {
  pulse: "Each line is the average price at that hour across the period, in local time. The midday dip is solar; the evening peak is when solar fades but demand stays high. Computed over the whole data period.",
  tb1: "Spread (TB1) = the gap between a day's most and least expensive hour, on hourly-averaged prices. Since Germany's Oct-2025 switch to quarter-hourly settlement, true 15-minute spreads are wider — this is a conservative lower bound.",
  arb: "Upper bound only — not achievable revenue. Assumes perfect next-day foresight, a 2-hour battery charging at the day's cheapest hours and discharging at the priciest, and zero round-trip losses. Real revenue is materially lower. Computed over the full period.",
  mix: "Average generation by fuel type, stacked. A fuel is the same colour in every view. Missing reporting shows as a gap, never a fabricated zero. Bidding zones, not countries (DE-LU = Germany + Luxembourg).",
  residual: "Residual load = demand − wind − solar: the demand left for conventional plants and batteries. It can go negative when renewables exceed demand. Per zone, over the whole period.",
  divergence: "Average monthly day-ahead price per bidding zone, plus the physical flow vs price gap on a German border. Where flow saturates capacity, prices can't converge.",
  carbon: typeof CARBON_METHODOLOGY !== "undefined" ? CARBON_METHODOLOGY : "Production-based, IPCC AR5 lifecycle factors.",
  curtail: "Curtailed = clean energy thrown away when the grid can't absorb or move it. Source: netztransparenz.de redispatch (renewable down-regulation, MWh). German total, not zone-specific.",
  history: "Daily spread across several years, Germany. Drag horizontally or scroll to zoom, double-click to reset. Not affected by the window control.",
  yoy: "Average daily spread over the last 12 months vs the prior 12. The multi-year trend single-year views can't show.",
};

// ---------- Chrome ----------
function renderZoneChips() {
  const zones = D.spread.zones_available || ["DE_LU"];
  const el = document.getElementById("zoneChips");
  el.innerHTML = zones.map((z) => {
    const cls = z === S.zone ? "primary" : (S.compare.includes(z) ? "compare" : "");
    return '<button class="zchip ' + cls + '" data-z="' + z + '">' +
      '<span class="dot" style="background:' + zoneColor(z) + '"></span>' + zoneShort(z) + "</button>";
  }).join("");
  el.querySelectorAll(".zchip").forEach((b) => b.addEventListener("click", () => {
    const z = b.dataset.z;
    if (z === S.zone) {
      if (S.compare.length) { S.zone = S.compare.shift(); }           // deselect primary -> next leads
    } else if (S.compare.includes(z)) {
      S.compare = S.compare.filter((x) => x !== z);                   // deselect comparison
    } else if (S.compare.length < 5) {
      S.compare.push(z);                                              // add comparison (up to 6 total)
    } else {
      S.zone = z; S.compare = [];                                     // full -> start over with this zone
    }
    renderZoneChips(); renderAll();
  }));
  const hint = document.getElementById("zoneHint");
  if (hint) {
    const others = S.compare.map(zoneShort);
    const list = others.length <= 1 ? others.join("")
      : others.slice(0, -1).join(", ") + " & " + others[others.length - 1];
    hint.textContent = S.compare.length
      ? zoneShort(S.zone) + " leads · vs " + list
      : "Tap another zone to compare (up to 6)";
  }
}

function wireSeg(id, fn) {
  document.querySelectorAll("#" + id + " button").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll("#" + id + " button").forEach((x) => x.classList.remove("active"));
    b.classList.add("active"); fn(b);
  }));
}
function wireSegs() {
  wireSeg("winSeg", (b) => applyPresetWindow(+b.dataset.days));
  wireSeg("spreadSeg", (b) => { S.tweaks.spreadStyle = b.dataset.s; renderSpread(); });
  wireSeg("mixSeg", (b) => setMixView(b.dataset.v));
  wireSeg("mixUnit", (b) => { S.tweaks.mixStyle = b.dataset.u; renderMix(); });
  wireSeg("divSeg", (b) => setDivMode(b.dataset.m));
  wireSeg("carbonSeg", (b) => { S.tweaks.carbonStyle = b.dataset.c; renderCarbon(); });
  wireSeg("histSeg", (b) => setHistMode(b.dataset.m));
}

function initScrollSpy() {
  const links = [...document.querySelectorAll(".sidenav a, .topnav a")];
  const obs = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting)
      links.forEach((l) => l.classList.toggle("active", l.getAttribute("href") === "#" + e.target.id)); });
  }, { rootMargin: "-20% 0px -70% 0px" });
  document.querySelectorAll("section.panel").forEach((s) => obs.observe(s));
}

// ---------- Lazy rendering ----------
// A panel's chart is (re)built only while it's near the viewport. renderAll() —
// called by every state change (zone/window/brush) — bumps a version and refreshes
// just the on-screen panels; the observer renders the rest as they scroll in.
const PANEL_FN = {
  pulse: renderPulse, spread: renderSpread, mix: renderMix, mismatch: renderMis,
  divergence: renderDiv, carbon: renderCarbon, curtailment: renderCurtail, history: renderHistory,
};
const visiblePanels = new Set();
let stateVersion = 0;
const renderedAt = {};
function renderPanelLazy(id) {
  const fn = PANEL_FN[id]; if (!fn) return;
  if (renderedAt[id] === stateVersion) return;           // already current
  try { fn(); } catch (e) { console.error(e); }
  renderedAt[id] = stateVersion;
}
// Rect-based scan (deterministic everywhere — IntersectionObserver's initial
// callback isn't reliable in every embedded browser). Renders panels within ~300px
// of the viewport and refreshes any whose render is stale for the current state.
function lazyScan() {
  const vh = window.innerHeight || document.documentElement.clientHeight;
  document.querySelectorAll("section.panel").forEach((s) => {
    const r = s.getBoundingClientRect();
    if (r.top < vh + 300 && r.bottom > -300) { visiblePanels.add(s.id); renderPanelLazy(s.id); }
    else visiblePanels.delete(s.id);
  });
}
function initLazyRender() {
  let ticking = false;
  const onScroll = () => { if (ticking) return; ticking = true;
    requestAnimationFrame(() => { ticking = false; lazyScan(); }); };
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll, { passive: true });
  lazyScan();   // initial in-view panels
}

(async function main() {
  const [spread, pulse, mix, carbon, div, flows, misZones, hist, curtail, spreadDE] = await Promise.all([
    loadJSON("spread_by_zone.json"), loadJSON("pulse_by_zone.json"), loadJSON("mix.json"), loadJSON("carbon.json"),
    loadJSON("divergence.json"), loadJSON("flows.json"), loadJSON("mismatch_by_zone.json"), loadJSON("spread_history.json"),
    loadJSON("curtailment.json"), loadJSON("spread.json"),
  ]);
  Object.assign(D, { spread, pulse, mix, carbon, div, flows, misZones, hist, curtail, spreadDE });
  if (!spread) { document.getElementById("status").textContent = "Could not load data. Serve the project folder so /data is reachable."; return; }
  document.getElementById("status").style.display = "none";

  renderZoneChips();
  initTips(TIPS);
  wireSegs();
  initBrush();

  // State changes bump the version and refresh the on-screen panels; off-screen
  // panels re-render when scrolled back into view.
  rerenders.push(() => { stateVersion++; lazyScan(); });

  initLazyRender();   // renders the panels already in view, then more as they scroll in
  initScrollSpy();
  updatePeriodNote();
})();
