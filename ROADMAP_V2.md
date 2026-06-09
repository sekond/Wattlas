# ROADMAP v2 — From four views to a European energy dashboard

This plans the next evolution: more data, more depth, and a consolidated dense
dashboard. It deliberately sequences the work so each phase is independently
shippable and verifiable, and so the dashboard arrives *after* the data layers
exist to fill it.

**Read this first, then follow `RUN_V2.md` to execute.** The detailed per-step
prompts are in `prompts/v2_prompts.md`.

---

## Why this order (the one thing to understand)

Each new data source is a new pipeline with its own auth, quirks, and failure
modes. Adding several at once produces tangled failures you can't isolate. So we
add capability in clean increments, each verified against reality before the next.

The dashboard is **last among the data work**, not first — a dense multi-panel
surface is only worth building once there's rich, multi-source, multi-zone data
to make it dense *with*. Building the shell first means building it twice.

Phases 1–2 are pure ENTSO-E (data you already fetch or can fetch with the same
client — cheapest, highest value). Phase 3 is the dashboard consolidation. Phases
4–5 are genuinely new external sources (more work, add deliberately). Phase 6 is
the time-investigation layer that ties it together.

You do **not** have to do all phases. Each is a sensible stopping point. After
each, the right question is "did this earn the next one?" — ideally answered by
showing it to your field contact.

---

## Phase 1 — Full generation mix (the France-vs-Germany story)
**Source:** ENTSO-E generation-per-type (you already fetch a slice for Mismatch).
**Build:** a new "Mix" view — stacked area of all generation types (nuclear,
lignite, hard coal, gas, wind on/offshore, solar, hydro variants, biomass, etc.)
by hour/day for a zone; plus a side-by-side two-zone comparison (e.g. DE-LU vs
FR) that makes the structural contrast visible — France's flat nuclear baseload
vs Germany's volatile renewables + gas/coal fill.
**Why first:** highest value, lowest cost. Data largely in hand. This is the most
illustrative chart for "understand the European transition."
**Ship test:** the France/Germany contrast is visible at a glance and the fuel
colours are consistent with the rest of the app.

## Phase 2 — Cross-border physical flows (make Divergence explain itself)
**Source:** ENTSO-E cross-border physical flows + day-ahead NTC (capacity).
**Build:** add physical-flow data to Divergence — show MW actually flowing between
DE and each neighbour, and flag hours where flow is at/near transmission capacity
(congestion). The insight upgrade: prices diverge *because* the interconnector is
full, not just *that* they diverge.
**Why second:** deepens an existing view, same source, no new auth.
**Ship test:** a congested border visibly coincides with a price gap.

## Phase 3 — Consolidated dense dashboard
**Source:** none new — consolidates Phases 1–2 + existing views.
**Build:** one page, a global control bar (zone + time window), and the
approaches as reactive panels in a grid: Pulse, Spread, Divergence (+flows), Mix,
Mismatch. Change zone/window once → all panels update together. One inline KPI
per panel, consistent visual grammar, desktop-dense / mobile-stacked.
**Why here:** now there's enough richness to justify density. Keep the standalone
pages until the dashboard proves better to work in.
**Ship test:** changing the time window once and watching every panel snap to it
*feels like investigating*.

## Phase 4 — Curtailment / "wasted" renewables (German deep-dive)
**Source:** NEW — SMARD.de (Bundesnetzagentur) redispatch & curtailment data.
**Build:** a "Curtailment" view — when and how much renewable generation was
throttled because the grid couldn't absorb/transmit it, and the cost. This is a
politically charged, under-visualised story (the north-south grid bottleneck).
**Why fourth:** first genuinely new source — own auth/format/quirks. Add only
once the ENTSO-E-based phases are solid. High narrative payoff.
**Ship test:** curtailment events line up sensibly with high-wind, negative-price
periods from the Spread view.

## Phase 5 — Carbon intensity (the sustainability lens)
**Source:** NEW — a grid carbon-intensity feed (gCO2/kWh by zone/hour).
**Build:** overlay carbon intensity on the Mix/Pulse views — tie "renewable
share" to "how clean is this hour." Optionally a "cleanest/dirtiest hours" view.
**Why fifth:** second new source. Connects the whole app to the question a
sustainability audience actually asks.
**Ship test:** carbon intensity drops when renewable share rises (sanity), and
the France-low / coal-heavy-hour-high contrast is visible.

## Phase 6 — Time investigation layer (ties it together)
**Source:** none new — re-aggregates existing data over more windows.
**Build:** custom date-range + click-drag zoom on the time-series panels;
multi-year (3–5y) windows; season/month-of-year overlays. Pre-compute the longer
history into JSON; slice client-side. Finally populates the "YoY change" KPI with
a real multi-year trend.
**Why last:** most valuable *once* there are many rich views to investigate
across. Cheap (stays static) but only shines on a full app.
**Ship test:** an analyst can spot an anomaly in the year view and drill into the
specific week, across panels.

---

## The architectural line to hold (constructive guardrail)
Phases 1–3 and 6 stay **static** (pre-computed JSON, no backend) — that's free,
unbreakable hosting and it's served you well. Phases 4–5 add sources but can
*still* be static if you pre-compute them at build time.

The honest ceiling: "any metric, any zone, any window, live and on-demand"
eventually wants a real backend + database. That's a deliberate step-up in cost
and maintenance. **Do not cross that line until real usage proves you need it.**
Most of the value above lives below it. When/if you hit the ceiling, that's its
own planning conversation — flag it, don't drift into it.

## The strategic thread
You've shown this to one person. Each phase is a chance to show a sharpened
version to one or two field people and ask "which view would make you open this
weekly?" Their answers should re-order these phases. Build → show → re-prioritise
beats building all six on spec.
