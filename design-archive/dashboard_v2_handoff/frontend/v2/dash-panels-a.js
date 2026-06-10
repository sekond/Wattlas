// Wattlas Dashboard v2 — panels: Pulse, Spread, Mix.
"use strict";

// ---------- 1 · PULSE ----------
function renderPulse() {
  const zs = zonesInPlay().filter((z) => has("pulse", z));
  if (!zs.length) { noData("boxPulse", "cPulse", "No price data for this zone."); return; }
  const primary = D.pulse.zones[zs[0]];
  const comparing = zs.length > 1;

  let datasets;
  if (comparing) {
    datasets = zs.map((z) => ({ label: zoneShort(z), data: D.pulse.zones[z].all_mean,
      borderColor: zoneColor(z), backgroundColor: "transparent", borderWidth: z === S.zone ? 2.6 : 1.8,
      pointRadius: 0, tension: 0.35, spanGaps: true }));
  } else if (S.tweaks.pulseSplit) {
    datasets = [
      { label: "Weekday", data: primary.weekday_mean, borderColor: zoneColor(zs[0]), backgroundColor: "transparent", borderWidth: 2.4, pointRadius: 0, tension: 0.35, spanGaps: true },
      { label: "Weekend", data: primary.weekend_mean, borderColor: "#b8860b", borderDash: [5, 4], backgroundColor: "transparent", borderWidth: 1.8, pointRadius: 0, tension: 0.35, spanGaps: true },
    ];
  } else {
    datasets = [{ label: "All days", data: primary.all_mean, borderColor: zoneColor(zs[0]),
      backgroundColor: "rgba(24,95,165,0.07)", fill: true, borderWidth: 2.4, pointRadius: 0, tension: 0.35, spanGaps: true }];
  }
  const ch = draw("boxPulse", "cPulse", { type: "line",
    data: { labels: primary.hours.map(hh), datasets },
    options: baseOpts({ x: axX({ ticks: Object.assign({}, TICK, { maxTicksLimit: 9, maxRotation: 0 }) }), y: axY({ ticks: Object.assign({}, TICK, { callback: eur }) }) },
      { tooltip: { callbacks: { title: (c) => hh(c[0].dataIndex), label: (c) => c.dataset.label + ": " + eur(c.parsed.y) + "/MWh" } } }) });
  linkChart(ch, "hour", primary.hours);

  const peak = extreme(primary.all_mean, "max"), trough = extreme(primary.all_mean, "min");
  if (peak.idx >= 0 && trough.idx >= 0) {
    setStory("storyPulse", "Power in " + zoneShort(zs[0]) + " is cheapest around " + hi(hh(trough.idx), "green") +
      " and dearest around " + hi(hh(peak.idx), "red") + " — a " + hi(eur(peak.val - trough.val), "amber") + " swing in an average day.");
  }
  setStats("statsPulse", [
    { label: "Cheapest hour", val: hh(trough.idx) + " · " + eur(trough.val), cls: "pos" },
    { label: "Priciest hour", val: hh(peak.idx) + " · " + eur(peak.val), cls: "neg" },
    { label: "Daily swing", val: eur(peak.val - trough.val) + "/MWh" },
  ]);
  document.getElementById("legPulse").innerHTML = comparing
    ? zs.map((z) => '<span><span class="line" style="border-color:' + zoneColor(z) + '"></span>' + zoneShort(z) + "</span>").join("")
    : (S.tweaks.pulseSplit
      ? '<span><span class="line" style="border-color:' + zoneColor(zs[0]) + '"></span>Weekday</span><span><span class="line" style="border-color:#b8860b;border-top-style:dashed"></span>Weekend</span>'
      : "");
}

// ---------- 2 · SPREAD ----------
function rollMean(vals, w) {
  return vals.map((_, i) => {
    const a = Math.max(0, i - w + 1), seg = vals.slice(a, i + 1).filter((v) => v != null);
    return seg.length ? seg.reduce((x, y) => x + y, 0) / seg.length : null;
  });
}
function renderSpread() {
  const zs = zonesInPlay().filter((z) => has("spread", z));
  if (!zs.length) { noData("boxSpread", "cSpread", "No spread data for this zone."); return; }
  const comparing = zs.length > 1;
  const sp = D.spread.zones[zs[0]];
  const rows = sp.days.filter((d) => inWin(d.date));
  if (!rows.length) { noData("boxSpread", "cSpread", "No days in this window."); return; }
  const dates = rows.map((r) => r.date);

  if (comparing) {
    // Comparison: 14-day rolling mean TB1 per zone (bars don't overlay well)
    const datasets = zs.map((z) => {
      const dz = D.spread.zones[z].days.filter((d) => inWin(d.date));
      const map = {}; dz.forEach((d) => { map[d.date] = d.tb1; });
      const vals = rollMean(dates.map((dt) => map[dt] ?? null), 14);
      return { label: zoneShort(z), data: vals, borderColor: zoneColor(z), backgroundColor: "transparent",
        borderWidth: z === S.zone ? 2.6 : 1.8, pointRadius: 0, tension: 0.25, spanGaps: true };
    });
    const ch = draw("boxSpread", "cSpread", { type: "line",
      data: { labels: dates.map(fmtDate), datasets },
      options: baseOpts({ x: axX({ ticks: Object.assign({}, TICK, { maxTicksLimit: 6, maxRotation: 0 }) }), y: axY({ ticks: Object.assign({}, TICK, { callback: eur }) }) },
        { tooltip: { callbacks: { label: (c) => c.dataset.label + ": " + eur(c.parsed.y) + "/MWh (14-day mean)" } } }) });
    linkChart(ch, "date", dates);
    document.getElementById("capSpread").textContent = "14-day rolling mean of daily spread (TB1), €/MWh, per zone. Source: ENTSO-E.";
  } else if (S.tweaks.spreadStyle === "heatmap") {
    drawSpreadHeatmap(rows);
    document.getElementById("capSpread").textContent = "Calendar heatmap of daily spread — darker is wider; red outline marks days with negative-price hours. Source: ENTSO-E.";
  } else {
    let wi = -1, wv = -1; rows.forEach((r, i) => { if (r.tb1 > wv) { wv = r.tb1; wi = i; } });
    const trend = rollMean(rows.map((r) => r.tb1), 14);
    const ch = draw("boxSpread", "cSpread", {
      data: { labels: dates.map(fmtDate), datasets: [
        { type: "bar", data: rows.map((r) => r.tb1), order: 2,
          backgroundColor: rows.map((r, i) => i === wi ? "#b8860b" : (r.negative_hours > 0 ? "rgba(163,45,45,0.75)" : "rgba(24,95,165,0.55)")), borderWidth: 0 },
        { type: "line", data: trend, order: 1, borderColor: "#26251f", borderWidth: 1.6, pointRadius: 0, tension: 0.3, spanGaps: true } ] },
      options: baseOpts({ x: axX({ ticks: Object.assign({}, TICK, { maxTicksLimit: 6, maxRotation: 0 }) }), y: axY({ ticks: Object.assign({}, TICK, { callback: eur }) }) },
        { tooltip: { filter: (c) => c.datasetIndex === 0, callbacks: {
          title: (c) => fmtDate(rows[c[0].dataIndex].date) + (c[0].dataIndex === wi ? " · widest day" : ""),
          label: (c) => "Spread " + eur(c.parsed.y) + "/MWh · " + rows[c.dataIndex].negative_hours + "h negative" } } }) });
    linkChart(ch, "date", dates);
    document.getElementById("capSpread").textContent = "Daily spread = priciest − cheapest hour (TB1). Red bars had negative-price hours; amber is the widest day; dark line = 14-day mean. Source: ENTSO-E.";
  }

  const avg = mean(rows.map((r) => r.tb1));
  const negDays = rows.filter((r) => r.negative_hours > 0).length;
  const negTot = rows.reduce((a, r) => a + (r.negative_hours || 0), 0);
  const arb = sp.summary ? sp.summary.perfect_arbitrage_eur_per_mw : null;
  let wi2 = -1, wv2 = -1; rows.forEach((r, i) => { if (r.tb1 > wv2) { wv2 = r.tb1; wi2 = i; } });
  setStory("storySpread", "An average day in " + zoneShort(zs[0]) + " swings " + hi(eur(avg), "amber") +
    " between its cheapest and priciest hour" + (negDays ? " — and " + hi(negDays + " days", "red") + " saw prices go below zero." : "."));
  setStats("statsSpread", [
    { label: "Avg daily spread", val: eur(avg) + "/MWh" },
    { label: "Widest day", val: wi2 >= 0 ? fmtDate(rows[wi2].date).replace(/ \d{4}$/, "") + " · " + eur(wv2) : "—" },
    { label: "Negative-price hours", val: negTot.toLocaleString(), cls: negTot ? "neg" : "" },
    { label: "Arbitrage ceiling", val: arb != null ? "€" + Math.round(arb).toLocaleString() + "/MW·yr" : "—", tip: "arb" },
  ]);
}

// Calendar heatmap: columns = weeks, rows = Mon–Sun. Plain canvas (not Chart.js).
function drawSpreadHeatmap(rows) {
  if (charts.cSpread) { charts.cSpread.destroy(); delete charts.cSpread; }
  const box = document.getElementById("boxSpread");
  box.innerHTML = '<canvas id="cSpread"></canvas><div class="tip-pop" id="hmTip" style="display:none;position:fixed;"></div>';
  const cv = document.getElementById("cSpread");
  const dpr = window.devicePixelRatio || 1;
  const W = box.clientWidth, H = box.clientHeight;
  cv.width = W * dpr; cv.height = H * dpr; cv.style.width = W + "px"; cv.style.height = H + "px";
  const ctx = cv.getContext("2d"); ctx.scale(dpr, dpr);

  const day0 = new Date(rows[0].date + "T00:00:00Z");
  const dow0 = (day0.getUTCDay() + 6) % 7; // Monday = 0
  const nWeeks = Math.ceil((rows.length + dow0) / 7);
  const padL = 34, padT = 18, padB = 4;
  const cell = Math.min((W - padL) / nWeeks, (H - padT - padB) / 7);
  const max = Math.max(...rows.map((r) => r.tb1));
  const cells = []; // {x,y,w,h,row}

  ["Mon", "Wed", "Fri", "Sun"].forEach((lbl, i) => {
    ctx.fillStyle = "#807e74"; ctx.font = "10px -apple-system, sans-serif"; ctx.textAlign = "left";
    ctx.fillText(lbl, 0, padT + (i * 2 + 0.7) * cell);
  });
  let lastMonth = "";
  rows.forEach((r, i) => {
    const slot = i + dow0, wk = Math.floor(slot / 7), dw = slot % 7;
    const x = padL + wk * cell, y = padT + dw * cell;
    const t = Math.pow(r.tb1 / max, 0.6);
    ctx.fillStyle = "rgba(24,95,165," + (0.08 + 0.84 * t).toFixed(2) + ")";
    ctx.fillRect(x, y, cell - 1.5, cell - 1.5);
    if (r.negative_hours > 0) { ctx.strokeStyle = "#a32d2d"; ctx.lineWidth = 1.2; ctx.strokeRect(x + 0.6, y + 0.6, cell - 2.7, cell - 2.7); }
    const m = r.date.slice(0, 7);
    if (m !== lastMonth && dw === 0) { lastMonth = m;
      ctx.fillStyle = "#807e74"; ctx.font = "10px -apple-system, sans-serif"; ctx.textAlign = "left";
      ctx.fillText(monthLabel(m), x, padT - 6); }
    cells.push({ x, y, w: cell, h: cell, r });
  });
  const tip = document.getElementById("hmTip");
  cv.addEventListener("mousemove", (e) => {
    const rect = cv.getBoundingClientRect(), mx = e.clientX - rect.left, my = e.clientY - rect.top;
    const c = cells.find((c) => mx >= c.x && mx < c.x + c.w && my >= c.y && my < c.y + c.h);
    if (c) { tip.style.display = "block"; tip.style.left = (e.clientX + 12) + "px"; tip.style.top = (e.clientY + 12) + "px";
      tip.textContent = fmtDate(c.r.date) + " — spread " + eur(c.r.tb1) + "/MWh" + (c.r.negative_hours ? " · " + c.r.negative_hours + "h negative" : ""); }
    else tip.style.display = "none";
  });
  cv.addEventListener("mouseleave", () => { tip.style.display = "none"; });
}

// ---------- 3 · MIX ----------
let mixView = "daily"; // daily | profile
function renderMix() {
  const z = has("mix", S.zone) ? S.zone : null;
  if (!z) { noData("boxMix", "cMix", "No generation data for " + zoneShort(S.zone) + "."); 
    setStory("storyMix", "No generation breakdown is available for " + zoneShort(S.zone) + ".");
    setStats("statsMix", []); document.getElementById("legMix").innerHTML = ""; return; }
  const zd = D.mix.zones[z];
  const share = S.tweaks.mixStyle === "share";
  const fuels = orderFuels(Object.keys(zd.daily_gw));

  if (mixView === "profile") {
    const hours = zd.hours;
    const totals = hours.map((_, i) => fuels.reduce((a, f) => a + (zd.profile_gw[f][i] || 0), 0));
    const ch = draw("boxMix", "cMix", { type: "line",
      data: { labels: hours.map(hh), datasets: fuels.map((f) => ({ label: f,
        data: hours.map((_, i) => { const v = zd.profile_gw[f][i]; if (v == null) return null;
          return share ? (totals[i] > 0 ? 100 * v / totals[i] : null) : v; }),
        backgroundColor: fuelColor(f) + "d9", borderWidth: 0, fill: true, pointRadius: 0, tension: 0.3 })) },
      options: baseOpts({ x: axX({ stacked: true, ticks: Object.assign({}, TICK, { maxTicksLimit: 9, maxRotation: 0 }) }),
        y: axY({ stacked: true, max: share ? 100 : undefined, ticks: Object.assign({}, TICK, { callback: (v) => share ? v + "%" : v + " GW" }) }) },
        { tooltip: { itemSort: (a, b) => b.parsed.y - a.parsed.y, callbacks: { title: (c) => hh(c[0].dataIndex),
          label: (c) => c.parsed.y == null ? null : c.dataset.label + ": " + (share ? Math.round(c.parsed.y) + "%" : gw1(c.parsed.y)) } } }) });
    linkChart(ch, "hour", hours);
  } else {
    const idx = zd.days.map((d, i) => inWin(d) ? i : -1).filter((i) => i >= 0);
    const dates = idx.map((i) => zd.days[i]);
    const totals = idx.map((i) => fuels.reduce((a, f) => a + (zd.daily_gw[f][i] || 0), 0));
    const ch = draw("boxMix", "cMix", { type: "line",
      data: { labels: dates.map(fmtDate), datasets: fuels.map((f) => ({ label: f,
        data: idx.map((i, j) => { const v = zd.daily_gw[f][i]; if (v == null) return null;
          return share ? (totals[j] > 0 ? 100 * v / totals[j] : null) : v; }),
        backgroundColor: fuelColor(f) + "d9", borderWidth: 0, fill: true, pointRadius: 0, tension: 0.2 })) },
      options: baseOpts({ x: axX({ stacked: true, ticks: Object.assign({}, TICK, { maxTicksLimit: 6, maxRotation: 0 }) }),
        y: axY({ stacked: true, max: share ? 100 : undefined, ticks: Object.assign({}, TICK, { callback: (v) => share ? v + "%" : v + " GW" }) }) },
        { tooltip: { itemSort: (a, b) => b.parsed.y - a.parsed.y, callbacks: {
          label: (c) => c.parsed.y == null ? null : c.dataset.label + ": " + (share ? Math.round(c.parsed.y) + "%" : gw1(c.parsed.y)) } } }) });
    linkChart(ch, "date", dates);
  }

  // stats over windowed daily data
  const idx2 = zd.days.map((d, i) => inWin(d) ? i : -1).filter((i) => i >= 0);
  let ren = 0, tot = 0; const sums = {};
  fuels.forEach((f) => { const s = idx2.reduce((a, i) => a + (zd.daily_gw[f][i] || 0), 0); sums[f] = s; tot += s; if (RENEWABLE_FUELS.has(f)) ren += s; });
  const top = fuels.slice().sort((a, b) => sums[b] - sums[a])[0];
  const renPct = tot > 0 ? Math.round(100 * ren / tot) : null;
  const ci = (D.carbon && has("carbon", z)) ? mean(D.carbon.zones[z].intensity_daily.filter((_, i) => inWin(D.carbon.zones[z].days[i]))) : null;
  setStory("storyMix", hi(top, "blue") + " leads " + zoneShort(z) + "'s generation; renewables supplied " +
    hi(renPct + "%", "green") + " of the power in this window.");
  setStats("statsMix", [
    { label: "Renewable share", val: renPct != null ? renPct + "%" : "—", cls: "pos" },
    { label: "Top source", val: top || "—" },
    { label: "Carbon intensity", val: ci != null ? Math.round(ci) + " gCO₂/kWh" : "—", tip: "carbon" },
  ]);
  document.getElementById("legMix").innerHTML = fuels.map((f) =>
    '<span><span class="swatch" style="background:' + fuelColor(f) + '"></span>' + f + "</span>").join("");
}
function setMixView(v) { mixView = v; renderMix(); }
