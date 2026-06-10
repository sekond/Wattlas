// Wattlas Dashboard v2 — unified boot for the responsive dashboard.html.
// dashboard.html carries BOTH shells (desktop sidebar layout + mobile tab app);
// they share panel/canvas ids, so the inactive shell is removed from the DOM
// before anything renders. Crossing the 900px breakpoint reloads once — the two
// shells differ structurally (static sections vs lazy tab panels), so a clean
// re-boot is simpler and safer than live migration.
"use strict";

const MOBILE_MQ = window.matchMedia("(max-width: 900px)");
const IS_MOBILE = MOBILE_MQ.matches;
MOBILE_MQ.addEventListener("change", () => location.reload());
// Fallback: some environments resize without firing the matchMedia change event.
window.addEventListener("resize", () => {
  if (window.matchMedia("(max-width: 900px)").matches !== IS_MOBILE) location.reload();
});

const TIPS = {
  pulse: "Each line is the average price at that hour across the period, in local time. The midday dip is solar; the evening peak is when solar fades but demand stays high. Computed over the whole data period.",
  tb1: "Spread (TB1) = the gap between a day's most and least expensive hour, on hourly-averaged prices. Since Germany's Oct-2025 switch to quarter-hourly settlement, true 15-minute spreads are wider — this is a conservative lower bound.",
  arb: "Upper bound only — not achievable revenue. Assumes perfect next-day foresight, a 2-hour battery charging at the day's cheapest hours and discharging at the priciest, and zero round-trip losses. Real revenue is materially lower. Computed over the full period.",
  mix: "Average generation by fuel type, stacked. A fuel is the same colour in every view. Missing reporting shows as a gap, never a fabricated zero. Bidding zones, not countries (DE-LU = Germany + Luxembourg).",
  residual: "Residual load = demand − wind − solar: the demand left for conventional plants and batteries. It can go negative when renewables exceed demand. Shown for DE-LU over the whole period.",
  divergence: "Average monthly day-ahead price per bidding zone, plus the physical flow vs price gap on a German border. Where flow saturates capacity, prices can't converge.",
  carbon: typeof CARBON_METHODOLOGY !== "undefined" ? CARBON_METHODOLOGY : "Production-based, IPCC AR5 lifecycle factors.",
  curtail: "Curtailed = clean energy thrown away when the grid can't absorb or move it. Source: netztransparenz.de redispatch (renewable down-regulation, MWh). German total, not zone-specific.",
  history: "Daily spread across several years, Germany. Drag horizontally or scroll to zoom, double-click to reset. Not affected by the window control.",
  yoy: "Average daily spread over the last 12 months vs the prior 12. The multi-year trend single-year views can't show.",
};

// ---------- Shared chrome ----------
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
  const hint = document.getElementById("zoneHint");                   // desktop only
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

// ---------- Desktop-only chrome ----------
function initScrollSpy() {
  const links = [...document.querySelectorAll(".sidenav a, .topnav a")];
  const obs = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting)
      links.forEach((l) => l.classList.toggle("active", l.getAttribute("href") === "#" + e.target.id)); });
  }, { rootMargin: "-20% 0px -70% 0px" });
  document.querySelectorAll("section.panel").forEach((s) => obs.observe(s));
}

// ---------- Mobile-only chrome ----------
const MOBILE_TABS = [
  { id: "pulse", label: "Pulse", render: () => renderPulse() },
  { id: "spread", label: "Spread", render: () => renderSpread() },
  { id: "mix", label: "Mix", render: () => renderMix() },
  { id: "mismatch", label: "Mismatch", render: () => renderMis() },
  { id: "divergence", label: "Divergence", render: () => renderDiv() },
  { id: "carbon", label: "Carbon", render: () => renderCarbon() },
  { id: "curtailment", label: "Curtailment", render: () => renderCurtail() },
  { id: "history", label: "History", render: () => renderHistory() },
];
let activePanel = "pulse";

function activate(id) {
  activePanel = id;
  document.querySelectorAll("section.panel").forEach((s) => s.classList.toggle("active", s.id === id));
  document.querySelectorAll(".mnav button").forEach((b) => b.classList.toggle("active", b.dataset.p === id));
  window.scrollTo(0, 0);
  // Render synchronously: the class toggle above is already applied for layout
  // reads, and rAF can be suspended in background tabs (panel would stay blank).
  const p = MOBILE_TABS.find((p) => p.id === id); if (p) p.render();
}
function renderActivePanel() { const p = MOBILE_TABS.find((p) => p.id === activePanel); if (p) p.render(); }

function initTabBar() {
  const nav = document.getElementById("mnav");
  nav.innerHTML = MOBILE_TABS.map((p, i) =>
    '<button data-p="' + p.id + '"><span class="n">' + (i + 1) + "</span>" + p.label + "</button>").join("");
  nav.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => activate(b.dataset.p)));
}

// ---------- Boot ----------
(async function main() {
  // Drop the inactive shell first so panel/canvas ids are unique in the DOM.
  const inactive = document.getElementById(IS_MOBILE ? "desktopShell" : "mobileShell");
  if (inactive) inactive.remove();
  const shell = document.getElementById(IS_MOBILE ? "mobileShell" : "desktopShell");
  if (shell) shell.hidden = false;
  if (IS_MOBILE) buildMobilePanels();

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

  if (IS_MOBILE) {
    initTabBar();
    rerenders.push(renderActivePanel);   // zone/window changes re-render only the visible panel
    updatePeriodNote();
    activate("pulse");
  } else {
    initBrush();
    rerenders.push(renderPulse, renderSpread, renderMix, renderMis, renderDiv, renderCarbon, renderCurtail);
    renderAll();
    renderHistory();                     // window-independent
    initScrollSpy();
  }
})();
