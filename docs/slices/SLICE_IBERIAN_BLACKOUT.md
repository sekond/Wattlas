# Vertical slice spec — "The Iberian blackout: the day the grid went dark"

> **Status:** spec only. No code until each step is approved under the `RUN.md`
> protocol. Driven by `RUN_V8.md` + `prompts/v8_prompts.md`. **Stays static.**
> **Sensitivity:** this is a real event that affected millions of people. Be factual,
> measured, non-sensational, and **do not assert a single definitive cause** — cite the
> official investigation and present what the data shows vs. what was examined.

A forensic, data-led replay of the **28 April 2025** blackout across the Iberian
Peninsula (Spain & Portugal) — what the grid data showed before, during and after, and
what it raised about operating a low-inertia, high-renewable grid.

## 1. The one question

**"On 28 April 2025 the Spanish and Portuguese grid collapsed. What did the data show in
the hours around it, how did the system come back, and what did it raise about grid
stability?"**

## 2. The panels

### Panel 1 — The collapse, hour by hour
**Shows:** demand/generation (and frequency if available) in the hours around the event
— a normal morning, the sudden collapse, the trough near zero.
**Data:** ENTSO-E load/generation for ES & PT around 28 Apr 2025 (a fixed historical
window); link official figures from REE/REN where published.
**Acceptance:** the timeline is clearly dated and sourced; the collapse is shown as the
data records it, without inferring an unverified cause.

### Panel 2 — The restoration
**Shows:** how supply was rebuilt over the following hours — staged restoration, the role
of hydro black-start and interconnection with France/Morocco.
**Data:** ENTSO-E ES/PT recovery curve; official restoration milestones.
**Acceptance:** the staged recovery renders with sourced milestones; no overclaiming.

### Panel 3 — What it raised (the lesson, carefully)
**Shows:** the questions the event put on the table — system inertia and stability when a
large share of supply is inverter-based, the speed of cascading trips, the value of
interconnection — framed as **what investigators examined**, with a link to the official
report.
**Acceptance:** evenhanded; explicitly avoids blaming any single technology; cause
attribution is sourced to the official investigation, not asserted by Wattlas.

## 3. Datasets

| Dataset | Feeds | Access | Static |
|---------|-------|--------|--------|
| [ENTSO-E](https://transparency.entsoe.eu) load/generation, ES & PT, 28 Apr 2025 window | Panels 1–2 | Token (held) | Y |
| [REE](https://www.ree.es/en) / [REN](https://datahub.ren.pt/en/) + official incident report | Panels 1–3 | Open | Y |

## 4. New pipeline module (isolated)

- `pipeline/build_iberian_blackout.py` — fetch the fixed ES/PT window around 28 Apr 2025,
  assemble the collapse + restoration series → `data/iberian_blackout.json`. A one-off
  historical pull (not a daily refresh).

## 5. Data contract (update `data/schema.md`)

```jsonc
// data/iberian_blackout.json
{ "generated_at":"ISO-8601","event_date":"2025-04-28","zones":["ES","PT"],
  "sources":["ENTSO-E","REE","REN","official report (cite)"],
  "timeline": [ { "t":"ISO-8601","es_load_gw":0,"pt_load_gw":0,"note":"" } ],
  "milestones": [ { "t":"ISO-8601","label":"" } ] }
```

## 6. Frontend

- Reuses Chart.js. New page `frontend/iberian_blackout.html`. Sober styling; no
  dramatised language.

## 7. Honest-framing copy blocks

**Block A — framing (top of page):**
> On 28 April 2025 a large-scale blackout hit the Iberian Peninsula, cutting power to
> much of Spain and Portugal for hours. This view replays what the grid data recorded
> around the event and how the system was restored. It does not assign a cause — that is
> the work of the official investigation, which it links to; it shows what the data shows.

**Block B — the stability question (Panel 3):**
> The event renewed a hard engineering question: as grids run on more inverter-based
> generation and less spinning, synchronous mass, they carry less *inertia* to resist
> sudden disturbances. Investigators examined system stability, the sequence of
> disconnections, and the role of interconnection. Wattlas presents these as open,
> sourced questions — not a verdict, and not a claim about any single technology.

## 8. Risks & caveats

- **Cause attribution:** do not assert it; cite the official report; update as findings
  are published.
- Data around an outage is irregular and revised — note provisional figures; render gaps
  honestly.
- Keep tone sober (real event, real harm). Timestamps UTC + local (Iberia).
- A fixed historical window, not a live/refreshing view.

## 9. Out of scope

Real-time monitoring; political/causal commentary beyond the official findings.

## 10. Build sequence (gated)

0. Pre-flight (read spec + SOURCES + schema; landmine: never assert cause; sober tone).
1. `build_iberian_blackout.py` — assemble the ES/PT window → JSON; schema; tests. **🧑 USER sanity-checks** against the public record + official report.
2. `iberian_blackout.html` shell + Panel 1 (the collapse) + copy block A.
3. Panel 2 (restoration) with sourced milestones.
4. Panel 3 (what it raised) + copy block B; link the official report.
5. Integrate & polish; tests; static. (No daily refresh — historical.)

## 11. Definition of done

Panels render from committed JSON; dated + sourced; **no asserted cause**; copy blocks
A/B present with the official-report link; schema updated; offline tests pass; static.
