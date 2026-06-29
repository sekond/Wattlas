# Wattlas — European electricity data source catalogue

A working reference of open data sources for European electricity markets, ordered
for one purpose: **finding more local, more punctual insight than the bidding-zone
view Wattlas runs on today.** It maps each source to its granularity, access model,
resolution, the story it unlocks, and whether it can stay inside Wattlas's static,
pre-computed architecture.

Today Wattlas uses two sources: the **ENTSO-E Transparency Platform** (day-ahead
prices, load, generation by type, cross-border flows, NTC) and
**netztransparenz.de** (German curtailment/redispatch). Everything below is a
candidate for going deeper.

---

## The one idea: granularity is the open lane

The worldwide incumbents (Electricity Maps, Ember) stop at the **bidding-zone /
country** line. Everything more local than that is where differentiated insight
lives. Think in zoom levels:

| Level | Resolution | Example sources |
|------|------------|-----------------|
| **L0** | Bidding zone / country | ENTSO-E, most national TSOs |
| **L1** | TSO control area / market price-zone | DE 4 control areas (SMARD); SE1–SE4, IT & NO price zones; FR régions (RTE) |
| **L2** | Distribution grid / region / province / département | Enedis (FR); ned.nl provinces (NL); GB DNO regions (carbon) |
| **L3** | Commune / postcode / IRIS | Enedis IRIS (FR); GB postcode carbon |
| **L4** | Individual installation | MaStR (DE); SEMO unit-level (IE); offshore wind farm (NL) |

**Critical caveat — there is no sub-zonal _price_.** Wholesale prices clear per
bidding zone; that's the entire "should Germany split into 4–5 zones?" debate.
Below the zone, only **physical** quantities vary — generation, consumption,
flows, congestion/redispatch, curtailment, carbon intensity, weather. So granular
insight in Wattlas is a *physical* story, not a price story. (That gap is itself a
great explainer.)

### How to read the tables

- **Access:** `Open` = no auth · `Key` = free API key after sign-up · `OAuth` =
  registered app (client id/secret) · `Token` = request by email/account.
- **Static:** `Y` = pre-aggregates cleanly into committed JSON · `Y*` = static but
  large or rate-limited, so pre-aggregate and split by year/zone.
- Every new source is its **own isolated pipeline module** (different auth, units,
  language, resolution, lag). See *Landmines* at the bottom before integrating.

---

## Pan-European & aggregators

| Source | What it adds & granularity | Access | Resolution / lag | Static |
|--------|----------------------------|--------|------------------|--------|
| [ENTSO-E Transparency](https://transparency.entsoe.eu) | The backbone: prices, load, generation/type, flows, NTC for every EU bidding zone. Client: [`entsoe-py`](https://github.com/EnergieID/entsoe-py) | Token (email `transparency@entsoe.eu`, ~3 days; 400 req/min) | 15–60 min; days for some | Y |
| [Electricity Maps](https://app.electricitymaps.com/developer-hub/api/reference) | Carbon intensity + mix, 200+ zones, smallest reliable subdivision. **Benchmark, not a moat** — study its UX | Key (free tier, non-commercial) | 5/15/60 min + forecast | Y* |
| [Ember](https://ember-energy.org/data/electricity-data-explorer/) | Yearly/monthly electricity by country, 215 countries, clean & open | Open (CC BY 4.0) | Monthly/yearly | Y |
| [Open Power System Data](https://open-power-system-data.org/) | Curated historical pan-EU time series + conventional power-plant list | Open | Historical (less frequent updates) | Y |
| [Energy-Charts (Fraunhofer ISE)](https://energy-charts.info/) | Rich DE + EU generation/price charts; has an API | Open | Hourly+ | Y |

---

## Cross-cutting layers (the "why" behind the numbers)

| Source | What it adds | Access | Static |
|--------|--------------|--------|--------|
| [DWD Open Data](https://opendata.dwd.de/) | German weather service: irradiance, wind, temperature — explains generation swings | Open | Y |
| [Copernicus / ERA5 (CDS)](https://cds.climate.copernicus.eu/) | Europe-wide reanalysis weather, historical | Key (free) | Y |
| [renewables.ninja](https://www.renewables.ninja/) | Turns weather into modelled wind/solar output per location | Open (research) | Y |
| [PVGIS (EU JRC)](https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis_en) | Solar potential/irradiance by coordinate | Open | Y |
| [OpenInfraMap / OSM power layer](https://openinframap.org/) | Grid topology — lines, substations, where the bottlenecks physically are | Open (ODbL) | Y |

---

## Germany — the deepest terrain and your strongest story

The north–south split is the headline: wind-rich northeast (50Hertz), demand-heavy
south (TenneT / TransnetBW), and a transmission bottleneck between them that forces
redispatch and curtailment. Germany has the richest open data in Europe to tell it.

| Source | What it adds & granularity | Access | Resolution / lag | Static |
|--------|----------------------------|--------|------------------|--------|
| [SMARD](https://www.smard.de/en) ([API](https://github.com/bundesAPI/smard-api)) | Generation by type, consumption, **by control area** + national. `chart_data` JSON; `bundesAPI/smard-api` wrapper | Open | 15 min / hourly | Y |
| [Marktstammdatenregister (MaStR)](https://www.marktstammdatenregister.de/MaStR) ([open-mastr](https://open-mastr.readthedocs.io/)) | **Every generation unit**, geolocated (restricted <30 kW). The "where is generation" layer | Open (attribution) | Registry, periodic | Y* (large) |
| [netztransparenz.de](https://www.netztransparenz.de/) ([redispatch wrapper](https://stromfee.club/redispatch/)) | EEG, balancing, **redispatch & curtailment at plant level** | Open (TSO data) | 1–3 day lag | Y |
| TSO portals: [50Hertz](https://www.50hertz.com/), [Amprion](https://www.amprion.net/), [TenneT](https://www.tennet.eu/), [TransnetBW](https://www.transnetbw.com/) | Control-area generation, load, flows — the regional view | Open | Varies | Y |

**Stories it unlocks:** "Why Germany throws away northern wind it can't ship
south" (MaStR location + control-area flows + redispatch); where every wind/solar
unit sits vs where demand is; the case for splitting the DE-LU bidding zone.
*Note:* SMARD/MaStR use German field names — isolate and translate.

---

## France — the best open-data terrain in Europe for granularity

| Source | What it adds & granularity | Access | Resolution / lag | Static |
|--------|----------------------------|--------|------------------|--------|
| [ODRÉ](https://opendata.reseaux-energies.fr/) ([API console](https://odre.opendatasoft.com/api/v1/console)) | 200+ datasets (RTE/Enedis/GRTgaz); éCO2mix national + **régional** + métropoles. Filter region → département → commune → **IRIS** | Open (Opendatasoft, ~50k calls/mo) | 15 min, x4/day | Y |
| [RTE Data Portal](https://data.rte-france.com/) | Official APIs: éCO2mix, generation, consumption, interconnections, unavailability | OAuth2 | 15 min | Y |
| [Enedis Open Data](https://data.enedis.fr/) | **Distribution-level** consumption/production by region/département/EPCI/commune/IRIS; daily volumes D+1, 5 yr history | Open | Daily | Y |

**Stories it unlocks:** nuclear fleet location vs demand centres; which régions
import vs export hour by hour; commune-level consumption maps. The France-nuclear
vs Germany-renewables contrast (already in your Mix view) gets a regional layer.

---

## Great Britain — the regional-carbon gold standard

| Source | What it adds & granularity | Access | Resolution / lag | Static |
|--------|----------------------------|--------|------------------|--------|
| [Carbon Intensity API (NESO)](https://carbonintensity.org.uk/) | Carbon intensity + mix across **14 GB regions** (DNO boundaries), forecast (~2 days) + actual, **postcode** endpoint | Open | 30 min | Y |
| [Elexon BMRS Insights](https://bmrs.elexon.co.uk/) ([dev portal](https://developer.data.elexon.co.uk/)) | Generation, demand, balancing, imbalance prices | Open (no key) | 5–30 min | Y |
| [NESO Data Portal](https://www.neso.energy/data-portal) | Embedded solar/wind, constraint/curtailment, system data | Open | Varies | Y |

**Stories it unlocks:** the cleanest regional-carbon UX to emulate; Scottish wind
constraint payments (a direct GB parallel to German redispatch); embedded solar.

---

## Iberia — Spain & Portugal (the MIBEL "island")

| Source | Country | What it adds & granularity | Access | Static |
|--------|---------|----------------------------|--------|--------|
| [ESIOS](https://www.esios.ree.es/en) ([API](https://api.esios.ree.es/)) | ES | ~1,900 indicators: generation, demand, price, balancing | Token | Y |
| [REData](https://www.ree.es/en/datos/apidata) | ES | Simpler REST: national series + some real-time | Open | Y |
| [REN Data Hub](https://datahub.ren.pt/en/) | PT | Production, consumption, networks | Open | Y |

**Stories it unlocks:** how weak interconnection with France makes Iberia a price
"island" that decouples from the rest of Europe; very high solar/wind share.
Electricity 15-min on REN; demand monthly on REData.

---

## Italy & the Alpine zone (IT, AT, CH)

| Source | Country | What it adds & granularity | Access | Static |
|--------|---------|----------------------------|--------|--------|
| [Terna](https://dati.terna.it/en/download-center) ([API](https://developer.terna.it/)) | IT | Load, generation, transmission, market — by Italian **market zone**; [`terna-py`](https://pypi.org/project/terna-py/) | Open / Key | Y |
| [APG Markt / Transparency](https://markt.apg.at/en/) | AT | Generation per type, balancing, congestion (data from 2023) | Open / API | Y |
| [Swissgrid via opendata.swiss](https://opendata.swiss/en/dataset?keywords=swissgrid) | CH | Production/consumption, quarter-hourly aggregated | Open | Y |

**Stories it unlocks:** Italy's strong north–south zonal divide and import
dependence; Austria & Switzerland as **hydro + pumped-storage** flexibility hubs;
Switzerland as a transit corridor outside EU market coupling.

---

## Nordics — high renewables, internal price zones (DK, NO, SE, FI)

The Nordics are a live model of the "split into price areas" idea Germany debates —
Sweden has SE1–SE4, Norway NO1–NO5, Denmark DK1/DK2. Mostly excellent open APIs.

| Source | Country | What it adds & granularity | Access | Static |
|--------|---------|----------------------------|--------|--------|
| [Energinet Energi Data Service](https://www.energidataservice.dk/) | DK | Production, consumption, CO₂, market by **DK1/DK2**. One of Europe's best open APIs | Open (no auth) | Y |
| [Statnett](https://www.statnett.no/en/) | NO | Power balance, flow, production/consumption, reserves; download centre + REST | Open | Y |
| [Svenska kraftnät](https://data.svk.se/) | SE | Production/consumption, transfer capacity, forecasts by **SE1–SE4** (replacing Mimer) | Open | Y |
| [Fingrid Open Data](https://data.fingrid.fi/en) | FI | Prices, transmission, consumption; consumption/small-scale production by accounting point | Key | Y |

**Stories it unlocks:** Denmark's world-leading wind share and gCO₂/kWh; Norway's
~100% hydro acting as Europe's flexible battery via subsea cables; Sweden's north-
hydro/south-demand split (a clean mirror of Germany's bottleneck).

---

## Central-Eastern Europe & Ireland (PL, CZ, IE)

| Source | Country | What it adds & granularity | Access | Static |
|--------|---------|----------------------------|--------|--------|
| [PSE raporty](https://raporty.pse.pl/) | PL | Generation, demand, prices; reports + API | Open | Y |
| [ČEPS](https://www.ceps.cz/en/all-data) | CZ | Consumption, balance, cross-border flows, generation | Open | Y |
| [EirGrid Smart Grid Dashboard](https://www.smartgriddashboard.com/) | IE | Real-time all-island demand, generation, CO₂, wind; SEMO **unit-level** (excludes <5 MW, no weekend update) | Open | Y |

**Stories it unlocks:** Poland's coal-heavy grid (high carbon) starting to see
renewables and negative prices; Ireland's extreme wind penetration and its unique
**system non-synchronous penetration (SNSP)** grid-stability ceiling.

> **Everywhere else** (Baltics — Litgrid/AST/Elering; Greece — IPTO/ADMIE; SE
> Europe) is still reachable at bidding-zone level through **ENTSO-E**, even where
> national open-data portals are thinner.

---

## Recommended integration order for Wattlas

Ranked for the credibility/explainer goal — each is independently shippable and
stays static. Build → show to a field contact → re-prioritise.

1. **Germany, deep** — MaStR + SMARD control areas + redispatch → the north–south
   "wasted wind" explainer. Highest narrative payoff; extends your Curtailment view;
   data largely in hand.
2. **Regional carbon via GB** — the Carbon Intensity API is the best-documented
   regional-carbon source anywhere; use it to set the pattern, then apply the same
   UX to DE/FR.
3. **France, regional** — ODRÉ + Enedis give effortless region→IRIS depth and a
   second country, deepening the nuclear-vs-renewables contrast.
4. **Weather layer** — renewables.ninja / DWD turns *description* ("prices dipped")
   into *explanation* ("because irradiance peaked"). The single biggest credibility
   upgrade per unit of effort.
5. **Nordic price zones** — Energinet (DK) + Svenska kraftnät (SE) are cheap, clean,
   and reinforce the "split into price areas" thread central to the Germany story.

---

## Landmines & conventions (read before integrating any source)

These extend the rules in `../CLAUDE.md`:

1. **Isolate every source** in its own pipeline module — different auth, units,
   languages (German on SMARD/MaStR, French on ODRÉ), resolutions, and lag. A
   failure in one must never break the others.
2. **Validate units in writing** — MWh vs GWh; gCO₂/kWh; and state whether carbon
   is production- or consumption-based. Don't mix methodologies across zones.
3. **Reconcile timestamps explicitly** — no source aligns 1:1 with ENTSO-E.
   Document each join. Keep everything tz-aware; group in local time; expect 23/25-
   hour DST days.
4. **No sub-zonal price** — only physical quantities vary below the bidding zone
   (see top). Don't invent a regional price.
5. **Render gaps as gaps** — never fabricate zeros; many of these sources have
   holes and reporting delays.
6. **Stay static** — pre-aggregate into committed JSON at build time; split large
   outputs (MaStR, multi-year, multi-zone) by year/zone and load on demand. The
   honest ceiling — "any metric, any zone, any window, live" — wants a real backend;
   flag it as a deliberate decision rather than drifting across the line.
7. **Secrets in `.env`** (gitignored): tokens/keys for ENTSO-E, ESIOS, Fingrid,
   ned.nl, RTE OAuth, Electricity Maps. Never commit them.

---

*Compiled June 2026. Endpoints and auth models change — verify against each
linked portal before building. Where a precise endpoint wasn't confirmed, the
link points to the portal's data/API landing page.*
