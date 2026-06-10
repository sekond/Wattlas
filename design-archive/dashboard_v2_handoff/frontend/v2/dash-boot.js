// Wattlas Dashboard v2 — boot: data load, zone chips, controls, scroll-spy.
"use strict";

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
  const others = S.compare.map(zoneShort);
  const list = others.length <= 1 ? others.join("")
    : others.slice(0, -1).join(", ") + " & " + others[others.length - 1];
  hint.textContent = S.compare.length
    ? zoneShort(S.zone) + " leads · vs " + list
    : "Tap another zone to compare (up to 6)";
}

function initScrollSpy() {
  const links = [...document.querySelectorAll(".sidenav a, .topnav a")];
  const obs = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting)
      links.forEach((l) => l.classList.toggle("active", l.getAttribute("href") === "#" + e.target.id)); });
  }, { rootMargin: "-20% 0px -70% 0px" });
  document.querySelectorAll("section.panel").forEach((s) => obs.observe(s));
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
  if (!spread) { document.getElementById("status").textContent = "Could not load data. Serve the project folder so /data is reachable."; return; }
  document.getElementById("status").style.display = "none";

  renderZoneChips();
  initBrush();
  initTips(TIPS);

  wireSeg("winSeg", (b) => applyPresetWindow(+b.dataset.days));
  wireSeg("mixSeg", (b) => setMixView(b.dataset.v));
  wireSeg("mixUnit", (b) => { S.tweaks.mixStyle = b.dataset.u; renderMix(); });
  wireSeg("divSeg", (b) => setDivMode(b.dataset.m));
  wireSeg("histSeg", (b) => setHistMode(b.dataset.m));

  rerenders.push(renderPulse, renderSpread, renderMix, renderMis, renderDiv, renderCarbon, renderCurtail);
  renderAll();
  renderHistory(); // window-independent
  initScrollSpy();
})();
