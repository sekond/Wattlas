// Wattlas Dashboard v2 — panels: Mismatch, Divergence, Carbon, Curtailment, History.
"use strict";

// ---------- 4 · MISMATCH ----------
function renderMis() {
  const m = D.mis;
  if (!m) { noData("boxMis", "cMis", "No data."); return; }
  const ch = draw("boxMis", "cMis", { type: "line",
    data: { labels: m.hours.map(hh), datasets: [
      { label: "Total demand", data: m.total_load_gw, borderColor: "#9b9a94", borderDash: [5, 4], backgroundColor: "transparent", borderWidth: 1.4, pointRadius: 0, tension: 0.35, spanGaps: true },
      { label: "Left for conventional", data: m.residual_load_gw, borderColor: "#185fa5",
        backgroundColor: "rgba(74,166,160,0.18)", fill: { target: 0 }, borderWidth: 2.4, pointRadius: 0, tension: 0.35, spanGaps: true } ] },
    options: baseOpts({ x: axX({ ticks: Object.assign({}, TICK, { maxTicksLimit: 9, maxRotation: 0 }) }), y: axY({ ticks: Object.assign({}, TICK, { callback: (v) => v + " GW" }) }) },
      { tooltip: { callbacks: { title: (c) => hh(c[0].dataIndex), label: (c) => {
        if (c.datasetIndex === 1) { const t = m.total_load_gw[c.dataIndex];
          const renew = t != null && c.parsed.y != null ? t - c.parsed.y : null;
          return ["Left for conventional: " + Math.round(c.parsed.y) + " GW"].concat(renew != null ? ["Covered by wind+solar: " + Math.round(renew) + " GW"] : []); }
        return c.dataset.label + ": " + Math.round(c.parsed.y) + " GW"; } } } }) });
  linkChart(ch, "hour", m.hours);
  const pk = extreme(m.residual_load_gw, "max"), tr = extreme(m.residual_load_gw, "min");
  setStory("storyMis", "After wind and solar do their bit, Germany's grid still needs " + hi(Math.round(pk.val) + " GW", "red") +
    " at " + hi(hh(pk.idx), "red") + " — the evening ramp that sets the price peak.");
  let over = 0; for (let h = 0; h < 24; h++) { const t = m.total_load_gw[h], r = m.residual_load_gw[h];
    if (t != null && r != null && t > 0 && (t - r) > 0.5 * t) over++; }
  setStats("statsMis", [
    { label: "Residual trough", val: hh(tr.idx) + " · " + Math.round(tr.val) + " GW", cls: "pos" },
    { label: "Residual peak", val: hh(pk.idx) + " · " + Math.round(pk.val) + " GW", cls: "neg" },
    { label: "Midday→evening swing", val: "+" + Math.round(pk.val - tr.val) + " GW" },
    { label: "Hours wind+solar > 50%", val: over + " h" },
  ]);
}

// ---------- 5 · DIVERGENCE ----------
let divMode = "prices";
function renderDiv() {
  const d = D.div; if (!d) { noData("boxDiv", "cDiv", "No divergence data."); return; }
  const inPlay = zonesInPlay();
  const sp = d.de_fr_spread.filter((v) => v != null);
  const avg = sp.length ? mean(sp) : null;
  const de = d.series.DE_LU, coupl = {};
  d.zones.filter((z) => z !== "DE_LU").forEach((z) => {
    const diffs = d.series[z].map((v, i) => (v == null || de[i] == null) ? null : Math.abs(v - de[i])).filter((v) => v != null);
    coupl[z] = diffs.length ? mean(diffs) : Infinity; });
  const sorted = Object.entries(coupl).sort((a, b) => a[1] - b[1]);
  setStory("storyDiv", "Germany and France diverged by " + hi(eur(avg) + "/MWh", "amber") + " a month on average; " +
    hi(zoneShort(sorted[0][0]), "green") + " tracks German prices closest, " + hi(zoneShort(sorted[sorted.length - 1][0]), "red") + " least.");
  setStats("statsDiv", [
    { label: "Avg DE−FR gap", val: eur(avg) + "/MWh" },
    { label: "Most coupled to DE", val: zoneShort(sorted[0][0]), cls: "pos" },
    { label: "Most divergent", val: zoneShort(sorted[sorted.length - 1][0]), cls: "neg" },
  ]);

  if (divMode === "prices") {
    const monIdx = d.months.map((m, i) => (!S.range || (m + "-28") >= S.range[0] && (m + "-01") <= S.range[1]) ? i : -1).filter((i) => i >= 0);
    draw("boxDiv", "cDiv", { type: "line",
      data: { labels: monIdx.map((i) => monthLabel(d.months[i])), datasets: d.zones.map((z) => {
        const active = inPlay.includes(z);
        return { label: zoneShort(z), data: monIdx.map((j) => d.series[z][j]),
          borderColor: active ? zoneColor(z) : "rgba(120,118,110,0.28)", borderWidth: z === S.zone ? 2.8 : (active ? 2 : 1.1),
          backgroundColor: "transparent", pointRadius: 0, tension: 0.3, spanGaps: true }; }) },
      options: baseOpts({ x: axX(), y: axY({ ticks: Object.assign({}, TICK, { callback: eur }) }) },
        { tooltip: { itemSort: (a, b) => b.parsed.y - a.parsed.y, callbacks: { label: (c) => c.dataset.label + ": " + eur(c.parsed.y) + "/MWh" } } }) });
    document.getElementById("capDiv").textContent = "Monthly mean day-ahead price by zone — selected zones in colour, the rest greyed. Monthly resolution. Source: ENTSO-E.";
  } else {
    const f = D.flows;
    if (!f || !f.borders || !f.borders.length) { noData("boxDiv", "cDiv", "No flow data."); return; }
    const nb = (S.zone !== "DE_LU" && f.borders.includes(S.zone)) ? S.zone
      : (S.compare.find((z) => f.borders.includes(z)) || (f.borders.includes("FR") ? "FR" : f.borders[0]));
    const b = f.data[nb];
    const di = {}; d.months.forEach((m, i) => { di[m] = i; });
    const gap = f.months.map((m) => { const i = di[m];
      return (i == null || d.series.DE_LU[i] == null || d.series[nb][i] == null) ? null : Math.round((d.series.DE_LU[i] - d.series[nb][i]) * 10) / 10; });
    const cong = (b.congestion_pct || []).map((p, i) => (p != null && p >= 20) ? i : -1).filter((i) => i >= 0);
    draw("boxDiv", "cDiv", {
      data: { labels: f.months.map(monthLabel), datasets: [
        { type: "bar", label: "Net flow", yAxisID: "yF", data: b.net_flow_mw,
          backgroundColor: b.net_flow_mw.map((v) => v == null ? "#ccc" : (v >= 0 ? "rgba(24,95,165,0.55)" : "rgba(24,95,165,0.22)")), borderWidth: 0 },
        { type: "line", label: "Price gap", yAxisID: "yP", data: gap, borderColor: "#a32d2d", backgroundColor: "transparent", borderWidth: 2, tension: 0.3, spanGaps: true,
          pointBackgroundColor: f.months.map((_, i) => cong.includes(i) ? "#b8860b" : "#a32d2d"),
          pointRadius: f.months.map((_, i) => cong.includes(i) ? 4.5 : 0) } ] },
      options: baseOpts({ x: axX(), yF: axY({ position: "left", ticks: Object.assign({}, TICK, { callback: (v) => v + " MW" }) }),
        yP: { position: "right", grid: { display: false }, border: { display: false }, ticks: Object.assign({}, TICK, { color: "#a32d2d", callback: eur }) } },
        { tooltip: { callbacks: { label: (c) => c.dataset.label === "Net flow"
          ? "Net flow: " + (c.parsed.y == null ? "n/a" : Math.round(c.parsed.y) + " MW")
          : "DE-LU − " + zoneShort(nb) + ": " + (c.parsed.y == null ? "n/a" : eur(c.parsed.y) + "/MWh") } } }) });
    document.getElementById("capDiv").innerHTML = "DE-LU ↔ " + zoneShort(nb) + ". Bars = net flow (+ = Germany exporting); red line = price gap. " +
      (b.capacity_available ? "Amber dots = congested months (flow at/near capacity)." : "No published capacity on this border, so congestion isn't flagged.") + " Source: ENTSO-E.";
  }
}
function setDivMode(m) { divMode = m; renderDiv(); }

// ---------- 6 · CARBON ----------
function renderCarbon() {
  const zDef = D.carbon ? D.carbon.zone_default : null;
  const z = has("carbon", S.zone) ? S.zone : zDef;
  if (!D.carbon || !z || !D.carbon.zones[z]) { noData("boxCarbon", "cCarbon", "No carbon data for this zone."); return; }
  const zd = D.carbon.zones[z];
  const idx = zd.days.map((d, i) => inWin(d) ? i : -1).filter((i) => i >= 0);

  if (S.tweaks.carbonStyle === "scatter") {
    const zs = zonesInPlay().filter((zz) => has("carbon", zz));
    const datasets = (zs.length ? zs : [z]).map((zz) => {
      const zzd = D.carbon.zones[zz];
      const ii = zzd.days.map((d, i) => inWin(d) ? i : -1).filter((i) => i >= 0);
      return { label: zoneShort(zz),
        data: ii.map((i) => ({ x: zzd.renewable_share_daily[i], y: zzd.intensity_daily[i], d: zzd.days[i] }))
          .filter((p) => p.x != null && p.y != null),
        backgroundColor: zoneColor(zz) + "8c", pointRadius: 3, pointHoverRadius: 5, borderWidth: 0 }; });
    draw("boxCarbon", "cCarbon", { type: "scatter", data: { datasets },
      options: baseOpts({
        x: { min: 0, max: 100, title: { display: true, text: "Renewable share of generation, %", color: "#807e74", font: { size: 11 } },
          ticks: Object.assign({}, TICK, { callback: (v) => v + "%" }), grid: { color: "rgba(40,36,20,0.05)" }, border: { display: false } },
        y: { title: { display: true, text: "gCO₂/kWh", color: "#807e74", font: { size: 11 } },
          ticks: Object.assign({}, TICK), grid: { color: "rgba(40,36,20,0.05)" }, border: { display: false } } },
        { tooltip: { callbacks: { label: (c) => c.dataset.label + " · " + fmtDate(c.raw.d) + ": " + Math.round(c.raw.y) + " gCO₂/kWh at " + Math.round(c.raw.x) + "% renewable" } } }) });
    document.getElementById("capCarbon").textContent = "Each dot is a day: the more renewable the mix (→), the cleaner the grid (↓). Production-based, IPCC AR5 lifecycle factors.";
  } else {
    const dates = idx.map((i) => zd.days[i]);
    const ch = draw("boxCarbon", "cCarbon", { type: "line",
      data: { labels: dates.map(fmtDate), datasets: [
        { label: "Carbon intensity", data: idx.map((i) => zd.intensity_daily[i]), borderColor: "#5a3a22",
          backgroundColor: "rgba(90,58,34,0.10)", fill: true, borderWidth: 2.2, pointRadius: 0, tension: 0.3, spanGaps: true } ] },
      options: baseOpts({ x: axX({ ticks: Object.assign({}, TICK, { maxTicksLimit: 6, maxRotation: 0 }) }),
        y: axY({ ticks: Object.assign({}, TICK, { callback: (v) => v + " g" }) }) },
        { tooltip: { callbacks: { label: (c) => Math.round(c.parsed.y) + " gCO₂/kWh · " + Math.round(zd.renewable_share_daily[idx[c.dataIndex]]) + "% renewable" } } }) });
    linkChart(ch, "date", dates);
    document.getElementById("capCarbon").textContent = "Daily grid carbon intensity, gCO₂eq/kWh. Hover for the day's renewable share. Production-based, IPCC AR5 lifecycle factors.";
  }
  const meanCI = mean(idx.map((i) => zd.intensity_daily[i]));
  const prof = zd.intensity_profile || [];
  const clean = extreme(prof, "min"), dirty = extreme(prof, "max");
  setStory("storyCarbon", zoneShort(z) + "'s grid averages " + hi(Math.round(meanCI) + " gCO₂/kWh", "amber") +
    " — cleanest around " + hi(hh(clean.idx), "green") + ", when renewables peak.");
  setStats("statsCarbon", [
    { label: "Mean intensity", val: Math.round(meanCI) + " gCO₂/kWh", tip: "carbon" },
    { label: "Cleanest hour", val: hh(clean.idx) + " · " + Math.round(clean.val), cls: "pos" },
    { label: "Dirtiest hour", val: hh(dirty.idx) + " · " + Math.round(dirty.val), cls: "neg" },
  ]);
}

// ---------- 7 · CURTAILMENT ----------
function renderCurtail() {
  const c = D.curtail;
  zoneLock("curtailment");
  if (!c || c.status === "unavailable" || !c.days || !c.days.length) {
    noData("boxCurtail", "cCurtail", "Awaiting data source — needs netztransparenz credentials.");
    setStory("storyCurtail", "Curtailment data is awaiting its source.");
    setStats("statsCurtail", []); return;
  }
  const days = c.days.filter((d) => inWin(d.date));
  if (!days.length) { noData("boxCurtail", "cCurtail", "No curtailment days in this window."); return; }
  const neg = {}; if (D.spreadDE && D.spreadDE.days) D.spreadDE.days.forEach((d) => { neg[d.date] = d.negative_hours; });
  const dates = days.map((d) => d.date);
  const ch = draw("boxCurtail", "cCurtail", {
    data: { labels: dates.map(fmtDate), datasets: [
      { type: "bar", label: "Curtailed", yAxisID: "y", data: days.map((d) => d.curtailed_mwh), backgroundColor: "rgba(59,109,17,0.7)", borderWidth: 0 },
      { type: "line", label: "Neg hours", yAxisID: "y2", data: days.map((d) => (d.date in neg ? neg[d.date] : null)),
        borderColor: "#a32d2d", backgroundColor: "transparent", borderWidth: 1.4, pointRadius: 0, tension: 0.3, spanGaps: true } ] },
    options: baseOpts({ x: axX({ ticks: Object.assign({}, TICK, { maxTicksLimit: 7, maxRotation: 0 }) }),
      y: axY({ position: "left", ticks: Object.assign({}, TICK, { color: "#3b6d11", callback: (v) => Math.round(v / 1000) + "k" }) }),
      y2: { position: "right", grid: { display: false }, border: { display: false }, ticks: Object.assign({}, TICK, { color: "#a32d2d" }) } },
      { tooltip: { callbacks: { label: (ci) => ci.dataset.label === "Curtailed" ? "Curtailed: " + mwh(ci.parsed.y) : ci.parsed.y + " neg-price hours" } } }) });
  linkChart(ch, "date", dates);
  const tot = days.reduce((a, d) => a + (d.curtailed_mwh || 0), 0);
  const peak = days.reduce((b, d) => d.curtailed_mwh > (b ? b.curtailed_mwh : -1) ? d : b, null);
  setStory("storyCurtail", "Germany threw away " + hi(mwh(tot), "green") + " of clean power in this window — wind and solar the grid couldn't absorb or move.");
  setStats("statsCurtail", [
    { label: "Total curtailed", val: mwh(tot) },
    { label: "Days covered", val: String(days.length) },
    { label: "Peak day", val: peak ? fmtDate(peak.date).replace(/ \d{4}$/, "") + " · " + mwh(peak.curtailed_mwh) : "—" },
  ]);
}

// ---------- 8 · HISTORY ----------
let histMode = "multi";
function renderHistory() {
  const H = D.hist;
  if (!H) { noData("boxHist", "cHist", "No history data."); return; }
  const widest = H.yearly.reduce((b, y) => y.avg_tb1 > (b ? b.avg_tb1 : -1) ? y : b, null);
  const totNeg = H.yearly.reduce((a, y) => a + (y.neg_hours || 0), 0);
  const yoy = H.yoy_tb1_change_pct;
  setStory("storyHist", "Across " + hi(H.years_covered.length + " years", "blue") + ", German daily spreads " +
    (yoy != null ? (yoy >= 0 ? "widened " + hi("+" + yoy + "%", "red") : "narrowed " + hi(yoy + "%", "green")) + " year on year" : "kept shifting") +
    " — the long arc of the energy transition.");
  setStats("statsHist", [
    { label: "Year-on-year", val: yoy != null ? (yoy >= 0 ? "+" : "") + yoy + "%" : "—", cls: yoy != null ? (yoy >= 0 ? "neg" : "pos") : "", tip: "yoy" },
    { label: "Years", val: H.years_covered.join(" · ") },
    { label: "Widest year", val: widest ? widest.year : "—" },
    { label: "Negative hours (all)", val: totNeg.toLocaleString(), cls: "neg" },
  ]);
  zoneLock("history");
  const cap = document.getElementById("capHist");
  if (histMode === "multi") {
    // x must be epoch-ms, not an ISO string: with parsing:false a Chart.js time
    // scale doesn't parse strings, so string x collapsed the axis to ~1 month and
    // the multi-year line rendered off-canvas (issue #18). Keep the ISO date in `d`
    // for the tooltip.
    const pts = H.days.map((d) => ({ x: new Date(d.date + "T00:00:00Z").getTime(), y: d.tb1, d: d.date }));
    draw("boxHist", "cHist", { type: "line",
      data: { datasets: [{ data: pts, parsing: false, borderColor: "#185fa5", backgroundColor: "rgba(24,95,165,0.08)", fill: true, borderWidth: 1, pointRadius: 0, tension: 0 }] },
      options: baseOpts({ x: { type: "time", time: { unit: "month" }, ticks: Object.assign({}, TICK, { maxTicksLimit: 10, maxRotation: 0 }), grid: { display: false }, border: { color: "rgba(40,36,20,0.15)" } },
        y: axY({ ticks: Object.assign({}, TICK, { callback: eur }) }) },
        { tooltip: { callbacks: { title: (c) => fmtDate(c[0].raw.d), label: (c) => "Spread " + eur(c.raw.y) + "/MWh" } },
          zoom: { zoom: { drag: { enabled: true, backgroundColor: "rgba(184,134,11,0.14)" }, wheel: { enabled: true }, mode: "x" } } }) });
    cap.textContent = "Daily spread (TB1), €/MWh, Germany. Drag or scroll to zoom, double-click to reset. Crosses the Oct-2025 resolution break. Source: ENTSO-E.";
  } else if (histMode === "season") {
    const byM = {}; H.seasonal.forEach((s) => { byM[s.month] = s.avg_tb1; });
    draw("boxHist", "cHist", { type: "line",
      data: { labels: MONTHS, datasets: [{ data: MONTHS.map((_, i) => byM[i + 1] ?? null), borderColor: "#b8860b", backgroundColor: "rgba(184,134,11,0.10)", fill: true, borderWidth: 2.2, pointRadius: 3, tension: 0.35, spanGaps: true }] },
      options: baseOpts({ x: axX(), y: axY({ ticks: Object.assign({}, TICK, { callback: eur }) }) },
        { tooltip: { callbacks: { label: (c) => "avg spread " + eur(c.parsed.y) + "/MWh" } } }) });
    cap.textContent = "Every year folded onto twelve months, then averaged — which months run wide regardless of year. €/MWh.";
  } else {
    draw("boxHist", "cHist", { type: "bar",
      data: { labels: H.yearly.map((y) => y.year), datasets: [{ data: H.yearly.map((y) => y.avg_tb1), backgroundColor: "rgba(24,95,165,0.7)", borderWidth: 0, maxBarThickness: 64 }] },
      options: baseOpts({ x: axX(), y: axY({ ticks: Object.assign({}, TICK, { callback: eur }) }) },
        { tooltip: { callbacks: { label: (c) => "avg spread " + eur(c.parsed.y) + "/MWh · " + H.yearly[c.dataIndex].neg_hours + " negative hours" } } }) });
    cap.textContent = "Average daily spread per calendar year, €/MWh, Germany.";
  }
}
function setHistMode(m) { histMode = m; renderHistory(); }
