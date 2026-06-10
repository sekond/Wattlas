// Wattlas Mobile — builds the 8 panel sections (same ids the dash renderers target).
// Invoked by dash-boot.js only when the mobile shell is active, so these ids never
// coexist with the desktop shell's.
"use strict";

const PANEL_DEFS = [
  { id: "pulse", k: "1 · Pulse — the daily rhythm", tip: "pulse",
    explain: "The average price at each hour of the day. The midday dip is solar; the evening peak is solar fading while demand stays high.",
    body: '<div class="chartwrap" id="boxPulse"><canvas id="cPulse"></canvas></div><div class="legend" id="legPulse"></div><div class="statrow" id="statsPulse"></div><p class="cap">€/MWh, local time, averaged over the whole period. Source: ENTSO-E.</p>',
    story: "storyPulse" },
  { id: "spread", k: "2 · Spread — the daily gap", tip: "tb1",
    explain: "The gap each day between the cheapest and the priciest hour — the swing that batteries and demand-shifting live on.",
    body: '<div class="panel-tools"><span class="seg" id="spreadSeg"><button data-s="bars" class="active">Bars</button><button data-s="heatmap">Calendar</button></span></div><div class="chartwrap" id="boxSpread"><canvas id="cSpread"></canvas></div><div class="statrow" id="statsSpread"></div><p class="cap" id="capSpread"></p>',
    story: "storySpread" },
  { id: "mix", k: "3 · Mix — what makes the power", tip: "mix",
    explain: "What actually generates the electricity, fuel by fuel.",
    body: '<div class="panel-tools"><span class="seg" id="mixSeg"><button data-v="daily" class="active">Day by day</button><button data-v="profile">Average day</button></span><span class="seg" id="mixUnit"><button data-u="absolute" class="active">GW</button><button data-u="share">% share</button></span></div><div class="chartwrap" id="boxMix"><canvas id="cMix"></canvas></div><div class="legend" id="legMix"></div><div class="statrow" id="statsMix"></div><p class="cap">Stacked average generation by fuel. Gaps render as breaks, never fabricated zeros. Source: ENTSO-E.</p>',
    story: "storyMix" },
  { id: "mismatch", k: "4 · Mismatch — residual load", tip: "residual",
    explain: "The demand left for conventional plants after wind and solar have done their bit — it peaks in the evening, and so do prices.",
    body: '<div class="chartwrap" id="boxMis"><canvas id="cMis"></canvas></div><div class="statrow" id="statsMis"></div><p class="cap">Residual load = demand − wind − solar (GW). Hour-of-day average over the whole period. Source: ENTSO-E.</p>',
    story: "storyMis" },
  { id: "divergence", k: "5 · Divergence — geography", tip: "divergence",
    explain: "How far neighbouring zones' prices drift apart when interconnectors fill up.",
    body: '<div class="panel-tools"><span class="seg" id="divSeg"><button data-m="prices" class="active">Prices by zone</button><button data-m="flows">Flow vs gap</button></span></div><div class="chartwrap" id="boxDiv"><canvas id="cDiv"></canvas></div><div class="statrow" id="statsDiv"></div><p class="cap" id="capDiv"></p>',
    story: "storyDiv" },
  { id: "carbon", k: "6 · Carbon — how clean each hour is", tip: "carbon",
    explain: "Grid carbon intensity falls as wind and solar rise.",
    body: '<div class="panel-tools"><span class="seg" id="carbonSeg"><button data-c="time" class="active">Timeline</button><button data-c="scatter">vs renewables</button></span></div><div class="chartwrap" id="boxCarbon"><canvas id="cCarbon"></canvas></div><div class="statrow" id="statsCarbon"></div><p class="cap" id="capCarbon"></p>',
    story: "storyCarbon" },
  { id: "curtailment", k: "7 · Curtailment — wasted clean power", tip: "curtail",
    explain: "Wind and solar thrown away when the grid can't absorb or move it.",
    body: '<div class="chartwrap" id="boxCurtail"><canvas id="cCurtail"></canvas></div><div class="statrow" id="statsCurtail"></div><p class="cap">Green bars = curtailed renewable energy (MWh/day); red line = negative-price hours. Germany. Source: netztransparenz.de.</p>',
    story: "storyCurtail" },
  { id: "history", k: "8 · History — the long view", tip: "history",
    explain: "Years of daily spread at once. Germany; not affected by the window control.",
    body: '<div class="panel-tools"><span class="seg" id="histSeg"><button data-m="multi" class="active">Multi-year</button><button data-m="season">Seasonal</button><button data-m="yearly">Yearly</button></span></div><div class="chartwrap" id="boxHist"><canvas id="cHist"></canvas></div><div class="statrow" id="statsHist"></div><p class="cap" id="capHist"></p>',
    story: "storyHist" },
];

function buildMobilePanels() {
  document.getElementById("panels").innerHTML = PANEL_DEFS.map((p) =>
    '<section class="panel" id="' + p.id + '">' +
      '<div class="panel-kicker"><span class="k">' + p.k + "</span></div>" +
      '<h2 class="story" id="' + p.story + '"></h2>' +
      '<p class="explain">' + p.explain +
        '<button class="info" data-tip="' + p.tip + '" aria-label="More about this view">i</button></p>' +
      p.body +
    "</section>").join("");
}
