// Wattlas Mobile — boot: data load, zone chips, tab navigation, lazy panel render.
"use strict";

const TIPS = {
  pulse: "Each line is the average price at that hour across the period, in local time. The midday dip is solar; the evening peak is when solar fades but demand stays high.",
  tb1: "Spread (TB1) = the gap between a day's most and least expensive hour, on hourly-averaged prices. Since Oct-2025 quarter-hourly settlement, true 15-minute spreads are wider — this is a conservative lower bound.",
  arb: "Upper bound only — not achievable revenue. Assumes perfect next-day foresight, a 2-hour battery and zero losses.",
  mix: "Average generation by fuel type, stacked. A fuel is the same colour in every view. Missing reporting shows as a gap, never a fabricated zero.",
  residual: "Residual load = demand − wind − solar: what's left for conventional plants and batteries. Shown for DE-LU over the whole period.",
  divergence: "Average monthly day-ahead price per bidding zone. Where interconnector flow saturates capacity, prices can't converge.",
  carbon: typeof CARBON_METHODOLOGY !== "undefined" ? CARBON_METHODOLOGY : "Production-based, IPCC AR5 lifecycle factors.",
  curtail: "Curtailed = clean energy thrown away when the grid can't absorb or move it. Source: netztransparenz.de. German total.",
  history: "Daily spread across several years, Germany. Not affected by the window control.",
  yoy: "Average daily spread over the last 12 months vs the prior 12.",
};

const PANELS = [
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
  const main = document.querySelector(".mmain");
  if (main) window.scrollTo(0, 0);
  requestAnimationFrame(() => { const p = PANELS.find((p) => p.id === id); if (p) p.render(); });
}

function renderActivePanel() { const p = PANELS.find((p) => p.id === activePanel); if (p) p.render(); }

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
    if (z === S.zone) { if (S.compare.length) S.zone = S.compare.shift(); }
    else if (S.compare.includes(z)) S.compare = S.compare.filter((x) => x !== z);
    else S.compare.push(z);
    renderZoneChips(); renderAll();
  }));
}

function wireSeg(id, fn) {
  document.querySelectorAll("#" + id + " button").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll("#" + id + " button").forEach((x) => x.classList.remove("active"));
    b.classList.add("active"); fn(b);
  }));
}

(async function main() {
  const [spread, pulse, mix, carbon, div, flows, mis, hist, curtail, spreadDE] = await Promise.all([
    loadJSON("spread_by_zone.json"), loadJSON("pulse_by_zone.json"), loadJSON("mix.json"), loadJSON("carbon.json"),
    loadJSON("divergence.json"), loadJSON("flows.json"), loadJSON("mismatch.json"), loadJSON("spread_history.json"),
    loadJSON("curtailment.json"), loadJSON("spread.json"),
  ]);
  Object.assign(D, { spread, pulse, mix, carbon, div, flows, mis, hist, curtail, spreadDE });
  if (!spread) { document.getElementById("status").textContent = "Could not load data."; return; }
  document.getElementById("status").style.display = "none";

  renderZoneChips();
  initTips(TIPS);
  wireSeg("winSeg", (b) => applyPresetWindow(+b.dataset.days));
  wireSeg("mixSeg", (b) => setMixView(b.dataset.v));
  wireSeg("mixUnit", (b) => { S.tweaks.mixStyle = b.dataset.u; renderMix(); });
  wireSeg("divSeg", (b) => setDivMode(b.dataset.m));
  wireSeg("histSeg", (b) => setHistMode(b.dataset.m));

  const nav = document.getElementById("mnav");
  nav.innerHTML = PANELS.map((p, i) =>
    '<button data-p="' + p.id + '"><span class="n">' + (i + 1) + "</span>" + p.label + "</button>").join("");
  nav.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => activate(b.dataset.p)));

  rerenders.push(renderActivePanel);   // window/zone changes re-render only the visible panel
  updatePeriodNote();
  activate("pulse");
})();
