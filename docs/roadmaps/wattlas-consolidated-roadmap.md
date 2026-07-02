# Wattlas: Consolidated Conclusion & Improvement Roadmap
### Synthesis of ENERGIEZONE, enPower, and Handelsblatt Green & Energy vs. the live platform

---

## The single conclusion

Across all three podcasts — a movement-voice show (ENERGIEZONE), a Fraunhofer science show (enPower), and a business-newspaper show (Handelsblatt) — the European energy conversation in 2025–2026 has moved decisively **from "build renewables" to "value, integrate, and pay for them."** Wattlas already owns the *physical* half of that story better than almost any free tool: it shows the duck curve, residual load, congestion, Dunkelflaute, curtailment, bidding-zone decoupling, and a transparent storage model. What it is missing is the **economic, locational, and consumer** half — and that is precisely where all three shows now spend their airtime.

Three independent editorial lenses converging on the same gaps is the strongest possible signal. The verdict:

> **Wattlas's highest-leverage next step is to add a *price-formation and value* layer on top of its existing *price-and-generation* layer** — turning "what the grid did" into "what it was worth, where, and who paid for it."

---

## What the three shows agree on (the consensus core)

| Theme | ENERGIEZONE | enPower | Handelsblatt | In Wattlas today? |
|---|:---:|:---:|:---:|---|
| **Capture-price cannibalization** (solar/wind value factor collapse) | ●●● | ●●● | ●●● | ❌ Missing — **#1 gap** |
| **Negative prices** (573 h in DE 2025, +25% YoY) | ●●● | ●● | ●●● | ⚠️ Secondary line only |
| **Curtailment → cost in €** (€7.2bn EU 2024) | ●●● | ●● | ●● | ⚠️ MWh only, no € |
| **Wholesale→retail wedge** (grid fees, levies, taxes) | ●● | ●● | ●●● | ❌ Wholesale only |
| **Locational / bidding-zone market design** (DE split decided *against*, Dec 2025) | ● | ●●● | ●● | ⚠️ Decoupling shown, not framed |
| **Storage revenue-stack erosion** (arbitrage → capacity pay) | ● | ●●● | ●● | ⚠️ Arbitrage-only toy model |
| **Capacity market as consumer €-cost** (~€3bn levy 2031) | ●● | ●● | ●●● | ❌ Missing |
| **Dynamic tariffs & flexibility** (DE ~4% smart meters) | ●●● | ●●● | ● | ❌ Missing |

*● = touched · ●● = recurring · ●●● = core theme*

---

## Where each show pulls the analysis

**ENERGIEZONE → the operations & policy-urgency lens.** Grid bottlenecks, the 1,700 GW connection queue, redispatch billions, the EEG/CfD reform fight. Confirms the *structural* gaps and the B2C dynamic-tariff story. (Caveat: explicitly pro-Energiewende, critical of the gas strategy — treat its framing as agenda, not fact.)

**enPower → the technical & market-design lens.** Bidding zones vs. nodal pricing, hybrid co-located parks, storage chemistry and duration, PV direct-marketing mechanics, sector coupling (heat pumps, V2G, electrolysers as flexible demand). This is the show that most directly validates a **market-design view** and a **storage-cannibalization upgrade**.

**Handelsblatt → the business & capital-markets lens.** Industrial competitiveness and relocation risk, utility strategy and M&A (RWE offshore exit, E.ON capex), the capacity levy as an industrial cost, geopolitics as a price driver. Reveals the corporate/financing dimension — and honestly marks **the boundary of what ENTSO-E data can support.**

The synthesis: your two top technical gaps (**capture price, retail wedge**) are validated by all three, while the *surrounding* priority should tilt toward **(a) locational/market-design signals** (enPower) and **(b) industrial & capacity cost** (Handelsblatt).

---

## The improvement roadmap

### Stage 1 — Build now (highest value, fully buildable from ENTSO-E + netztransparenz)

**1. Capture-Price / Value-Factor view** — *the #1 build.*
For solar and wind, by bidding zone: generation-weighted capture price ÷ baseload = value factor, trended over time, with the share of generation falling in negative-price hours. Pure arithmetic on series you already hold. Anchor to 2025 reality (DE solar capture ~50–60% of baseload; ~16% of solar generated at negative prices; 573 negative hours).

**2. Market-Design / Locational-Signal view** — *the most differentiating build.*
Use the regional generation + load you can pull to **simulate a hypothetical north/south DE split**: how often the two zones would price apart, the implied spread, a redispatch proxy. Annotate with the decided policy reality (single zone *retained*, Aktionsplan Gebotszone, 15 Dec 2025) and the ENTSO-E DE5 benchmark (−€613m redispatch / +€339m welfare) — caveating the academic dissent (<€3/MWh spread studies). Leverages your existing Divergence view + DE north-south deep-dive.

**3. Monetize curtailment & promote negative prices.**
Add a € axis and running annual total to the Curtailment view (EU context: €7.2bn across 7 countries, 2024). Promote negative prices to a first-class metric — hours/year per zone, a calendar heatmap, and *episode duration* (the part experts now emphasize).

### Stage 2 — Build next

**4. Wholesale→Retail wedge (decomposed & dynamic).**
Wholesale | grid fees | levies/taxes — not a static gap but a *moving* decomposition that reflects the 2026 ~€6.5bn grid-fee subsidy and its north/east redistribution. Links directly to the locational-signal view via north–south grid-fee divergence. **This is the primary B2C build.**

**5. Storage deep-dive → revenue-stack / cannibalization model.**
Keep the honest arbitrage toy, but add spread compression as assumed battery volume grows, and the shift toward capacity/availability remuneration. Mirrors the solar-cannibalization logic on the storage side.

**6. Flexibility / dynamic-tariff savings calculator (B2C).**
Reuse the Spread engine: "a shiftable load (EV / heat pump / battery) charging in the cheapest N hours saves €X/year vs. flat tariff," per zone. Operationalizes the dynamic-tariff theme all three shows raise. *(Carry the same perfect-foresight caveat your battery model already uses.)*

**7. Capacity-cost / adequacy panel.**
Surface the 12 GW / 10-hour gas tender, 2031 target, and the up-to-€3bn (2031) / up-to-€2.3bn-a-year (2032–2045) levy as a forward consumer-cost line, alongside a Dunkelflaute residual-load stress indicator (you have Mismatch + the Dunkelflaute deep-dive already).

### Stage 3 — Context layers (acknowledge the scope boundary)

**8. Marginal-fuel / gas-CO₂ overlay** on Pulse/Mix — explains *why* the price is set (the geopolitics-as-price-driver theme).

**9. Thin industrial-competitiveness layer** — DE vs. FR/ES/NO industrial-price proxies; who-sets-the-price marginal analysis. **Explicitly flag** that corporate strategy, M&A, PPAs, and capital-markets themes (Handelsblatt) are *out of Wattlas's data scope* — a deliberate boundary, not an omission.

---

## B2C vs. B2B lane split (to guide UX)

**B2C lane** — wholesale→retail wedge · dynamic-tariff savings · prosumer/PV economics · heat-pump price ratio · negative-price-for-consumers explainer

**B2B lane** — capture prices · curtailment/redispatch € · storage revenue stack · capacity adequacy & cost · bidding zones/locational signal · marginal-fuel overlay · industrial-price proxy

---

## What would re-order these priorities

- **EU forces a German bidding-zone split** at the next review → Market-Design view jumps to #1 and needs real split-zone pricing, not a simulation.
- **Capacity levy confirmed in final law** → promote the capacity-cost panel into Stage 1.
- **Solar value factor stops falling** for four straight quarters → downgrade the capture/cannibalization emphasis.
- **DE smart-meter / dynamic-tariff penetration jumps above ~10%** → the B2C flexibility calculator gains a far larger audience; promote it.

---

## Honest limits

- Podcast themes are inferred from feeds, show notes, and guest profiles — not full transcripts; emphasis is sampled, not exhaustive.
- Bidding-zone economics are **contested** (ENTSO-E's figures use 2019-vintage data; academic studies find <€3/MWh spreads). Treat the split's benefits as a range.
- Capacity-strategy numbers (12 GW, the levy) come from a May 2026 cabinet bill pending Bundestag passage — still moving.
- Several high-importance Handelsblatt themes sit *above* the day-ahead-price/physical-generation layer Wattlas occupies. The roadmap deliberately separates "implementable now" from "context only."
- Wattlas's own battery captured-spread is, by its own admission, a perfect-foresight upper bound — any consumer-savings calculator built on the same engine must carry that caveat to stay honest.
