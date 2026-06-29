/* Wattlas — proposed information architecture.
 * The 26 destinations regrouped from "how the pipeline made them"
 * (8 views / 7 deep dives / 10 value layer) into FIVE question-led sections.
 * One source of truth for the redesigned nav, home and section hubs. */

window.WATTLAS_IA = {
  // The five question-led sections, in reading order.
  sections: [
    {
      id: "rhythm",
      n: "01",
      short: "Rhythm",
      accent: "var(--s-blue)",
      kicker: "When does power move?",
      title: "The Daily Rhythm",
      lede: "Electricity has no single price — it has a price every hour. This is how it swings between cheap and expensive, day to day and year to year.",
      thumb: "duck",
      views: [
        { id: "pulse",          title: "Pulse",          tag: "chart", page: "pulse.html",          one: "The duck curve — prices crater at midday when solar floods in, then spike after dark.", stat: "−€18 → €142", statlbl: "midday vs evening, avg hour" },
        { id: "spread",         title: "Spread",         tag: "chart", page: "index.html",          one: "The daily gap between the cheapest and most expensive hour — the signal storage lives on.", stat: "€96/MWh", statlbl: "avg daily top–bottom spread" },
        { id: "negative",       title: "Negative Prices",tag: "chart", page: "negative_prices.html", one: "Hours the grid pays you to consume, promoted from a footnote to a metric of its own.", stat: "468 h", statlbl: "below zero, last 12 months" },
        { id: "capture",        title: "Capture Price",  tag: "chart", page: "capture_price.html",   one: "What a solar or wind MWh actually earns once it's worth least exactly when there's most of it.", stat: "0.55×", statlbl: "DE solar value factor" },
        { id: "history",        title: "History",        tag: "chart", page: "history.html",         one: "Several years of daily spread, free to roam — zoom, fold onto a seasonal curve, read the trend.", stat: "3 yr", statlbl: "of daily data" },
      ],
    },
    {
      id: "grid",
      n: "02",
      short: "Grid",
      accent: "var(--s-green)",
      kicker: "What's flowing through the wires?",
      title: "What's on the Grid",
      lede: "Behind every price is a physical mix of fuels. This is what generates Europe's power hour to hour — and how clean, or dirty, each hour really is.",
      thumb: "mix",
      views: [
        { id: "mix",           title: "Generation Mix", tag: "chart", page: "mix.html",          one: "Full generation by fuel for any zone — France's flat nuclear against Germany's volatile wind and solar.", stat: "2-zone", statlbl: "side-by-side compare" },
        { id: "carbon",        title: "Carbon Intensity",tag: "chart", page: "carbon.html",       one: "How many grams of CO₂ each kilowatt-hour carries, computed from the live mix.", stat: "30 → 550", statlbl: "gCO₂/kWh, FR vs PL" },
        { id: "mismatch",      title: "Residual Load",  tag: "chart", page: "mismatch.html",     one: "Demand minus wind and solar — the load conventional plants and batteries must still cover.", stat: "evening", statlbl: "peak residual hour" },
        { id: "marginal_fuel", title: "Marginal Fuel",  tag: "model", page: "marginal_fuel.html",one: "A model of when gas sets the price — CCGT cost against the day-ahead, hour by hour.", stat: "~77%", statlbl: "of days gas is marginal" },
      ],
    },
    {
      id: "place",
      n: "03",
      short: "Geography",
      accent: "var(--s-amber)",
      kicker: "Where does power flow — and why do prices split?",
      title: "Geography of Price",
      lede: "One country, one price — until the grid can't carry the power across it. Four countries, four answers to the same congestion problem, on the map.",
      thumb: "map",
      views: [
        { id: "divergence",   title: "Divergence",            tag: "chart", page: "divergence.html",   one: "How far neighbouring zones' prices drift apart — and the cross-border flow that explains it.", stat: "DE↔FR", statlbl: "the headline price gap" },
        { id: "wasted_wind",  title: "Germany North–South",   tag: "map",   page: "wasted_wind.html",  one: "Wind in the north, demand in the south, one price between them — so clean power gets curtailed.", stat: "~400", statlbl: "Landkreise mapped" },
        { id: "fr_nuclear",   title: "France Nuclear",        tag: "map",   page: "fr_nuclear.html",   one: "The centralised mirror: 57 reactors, who exports, who imports, and what it really costs.", stat: "~63 GW", statlbl: "nuclear fleet, 18 sites" },
        { id: "nordic_zones", title: "Nordic Price Zones",    tag: "map",   page: "nordic_zones.html", one: "The split Germany debates, already live — twelve zones, a cheap hydro north, a dear south.", stat: "12 zones", statlbl: "€26 → €90/MWh" },
        { id: "uk_regional",  title: "UK Regional",           tag: "map",   page: "uk_regional.html",  one: "Britain's answer: keep one price, pay Scottish wind ~£2 bn a year to switch off.", stat: "£2 bn/yr", statlbl: "constraint payments" },
        { id: "curtailment",  title: "Curtailment",           tag: "chart", page: "curtailment.html",  one: "Clean power thrown away when the grid can't move it — the cost of the bottleneck, in MWh and €.", stat: "stormy days", statlbl: "spikes on neg-price hours" },
        { id: "locational",   title: "Locational Signal",     tag: "chart", page: "locational_signal.html", one: "The internal north–south congestion made legible — and the single-zone debate, even-handed.", stat: "1 zone", statlbl: "DE-LU, debate annotated" },
      ],
    },
    {
      id: "stress",
      n: "04",
      short: "Stress",
      accent: "var(--s-red)",
      kicker: "What happens when supply runs tight?",
      title: "When the Grid is Tested",
      lede: "A renewable grid's hardest hours — the windless, sunless spells it must plan for, the batteries that ride the gap, and the day the lights actually went out.",
      thumb: "stress",
      views: [
        { id: "dunkelflaute", title: "Dunkelflaute",      tag: "chart",      page: "dunkelflaute.html",    one: "The cold, dark, windless spells when wind and solar all but vanish and the price climbs.", stat: "~1.5%", statlbl: "renewables of demand, Nov '25" },
        { id: "storage",      title: "Storage",           tag: "chart",      page: "storage.html",         one: "The batteries that live off the daily spread — charging cheap midday, discharging into the peak.", stat: "~6×", statlbl: "grid storage since 2021" },
        { id: "capacity",     title: "Capacity & Adequacy",tag: "chart",     page: "capacity_adequacy.html",one: "Can firm capacity cover the worst residual-load hours — and what the policy to ensure it costs.", stat: "12 GW", statlbl: "gas tender, provisional" },
        { id: "iberian",      title: "Iberian Blackout",  tag: "historical", page: "iberian_blackout.html",one: "A sober, sourced replay of 28 April 2025 — what the grid data recorded, asserting no cause.", stat: "~0.1 GW", statlbl: "PT load at the floor" },
      ],
    },
    {
      id: "bill",
      n: "05",
      short: "The Bill",
      accent: "var(--s-plum)",
      kicker: "What does it cost, and who pays?",
      title: "The Bill",
      lede: "The wholesale price is only the start. This is the economic and consumer half — what flexibility is worth, and how a megawatt-hour becomes your monthly bill.",
      thumb: "bill",
      views: [
        { id: "flexibility",  title: "Flexibility",      tag: "chart", page: "flexibility.html",  one: "What a shiftable load — EV, heat pump, battery — charging in the cheapest hours saves a year.", stat: "upper bound", statlbl: "€/yr vs flat tariff" },
        { id: "retail_wedge", title: "Retail Wedge",     tag: "chart", page: "retail_wedge.html", one: "Your bill decomposed: wholesale, grid fees, levies and taxes — and how the wedge has shifted.", stat: "3 parts", statlbl: "wholesale | grid | taxes" },
        { id: "industrial",   title: "Industrial Prices",tag: "chart", page: "industrial.html",   one: "What heavy industry pays — DE against France, Spain and Norway, country-level and honestly bounded.", stat: "DE vs FR/ES/NO", statlbl: "Eurostat, country-level" },
        { id: "curt_cost",    title: "Curtailment in €",  tag: "chart", page: "curtailment.html#cost", one: "The price tag on wasted wind: curtailed MWh × a reference rate, a labelled estimate.", stat: "€ est.", statlbl: "running annual total" },
      ],
    },
  ],

  // The audit: what was wrong, stated plainly, and the original flat structure
  // for the before/after toggle.
  audit: {
    headline: "26 destinations, sorted by how they were built — not by what you came to learn.",
    body: "Wattlas grew in layers: eight core views, then seven deep dives, then a ten-view value layer. Each layer was bolted onto the sidebar as its own flat list, so the menu mirrors the project's build history instead of a visitor's questions. A newcomer faces a wall of 26 near-equal links — “Mismatch”, “Divergence”, “Locational Signal”, “Capture Price” — with no path through them and no sense of which three actually matter.",
    problems: [
      { t: "Grouped by origin, not by question", d: "“The Eight Views / Deep dives / Value layer” are pipeline categories. They mean nothing to someone who just wants to know why power is cheap at noon." },
      { t: "No hierarchy", d: "All 26 links sit at the same visual weight. The map stories — the strongest material — are buried two scrolls down, level with a thin Eurostat comparison." },
      { t: "Related things sit far apart", d: "Spread, Negative Prices and Capture Price are the same story told three ways, scattered across two different groups." },
      { t: "Dead-end pages", d: "Each standalone view is an island. Nothing suggests what to read next, so the deep dives never connect into the trilogy they actually form." },
      { t: "No on-ramp", d: "The home is a dense dashboard. There's no editorial entry that says “start here” for a first-time visitor." },
    ],
    // The original navigation, verbatim from nav.js, for the toggle.
    original: [
      { group: "", items: [{ t: "Dashboard", m: "⌂" }] },
      { group: "The Eight Views", items: [
        { t: "Pulse", m: "1" }, { t: "Spread", m: "2" }, { t: "Mix", m: "3" }, { t: "Mismatch", m: "4" },
        { t: "Divergence", m: "5" }, { t: "Carbon", m: "6" }, { t: "Curtailment", m: "7" }, { t: "History", m: "8" },
      ]},
      { group: "Deep dives", items: [
        { t: "Germany North-South Grid", m: "DE" }, { t: "France Nuclear", m: "FR" }, { t: "Nordic Price Zones", m: "NZ" },
        { t: "UK Regional Carbon", m: "UK" }, { t: "Dunkelflaute", m: "DF" }, { t: "Storage", m: "ST" }, { t: "Iberian Blackout", m: "IB" },
      ]},
      { group: "Value layer", items: [
        { t: "Capture Price", m: "CP" }, { t: "Negative Prices", m: "NP" }, { t: "Flexibility", m: "FX" }, { t: "Locational Signal", m: "LO" },
        { t: "Retail Wedge", m: "RW" }, { t: "Capacity & Adequacy", m: "CA" }, { t: "Marginal Fuel", m: "MF" }, { t: "Industrial", m: "IC" },
        { t: "Storage Cannibalization", m: "SC" }, { t: "Curtailment in €", m: "C€" },
      ]},
    ],
  },

  // Standard site pages reachable from the footer (#/p/<id>).
  pages: [
    {
      id: "about",
      title: "About Wattlas",
      kicker: "What this is",
      blocks: [
        { h: "", p: "Wattlas turns open European electricity-market data into a set of explorable views of how — and when — the price of power moves across Europe, centred on Germany (the DE-LU bidding zone) and its neighbours: France, the Netherlands, Belgium, Poland, Austria and the Nordics." },
        { h: "Why it exists", p: "It started as a way to learn the data terrain of European power markets, and grew into a small tool that surfaces a few genuinely interesting things about them — from the daily price rhythm to the way a congested grid is handled three different ways across Germany, the Nordics and Britain." },
        { h: "What it is not", p: "Wattlas is a learning project, not a commercial product. It makes no investment or trading recommendations, and nothing here should be read as financial advice. See the <a href=\"#/p/terms\">Terms &amp; Disclaimer</a>." },
        { h: "How it's built", p: "Open-data APIs feed a Python pipeline that pre-computes small JSON files; a static frontend reads them directly. No database, no server, no live backend. The full method is on the <a href=\"#/p/methodology\">How it works</a> page." },
      ],
    },
    {
      id: "methodology",
      title: "How it works",
      kicker: "Method & honesty notes",
      blocks: [
        { h: "The pipeline", p: "Open-data APIs → a Python/pandas pipeline → committed <code>data/*.json</code> → a static JS frontend → GitHub Pages. The pipeline is the only thing that touches the upstream APIs; each source is an isolated module, so a failure in one can't break the others. A scheduled job re-runs it daily and commits the refreshed JSON." },
        { h: "Honesty notes", p: "Energy data is easy to get subtly wrong, so the correctness choices are made explicit in the views rather than hidden:" },
        { list: [
          "Prices are resampled to a consistent hourly resolution. Germany moved to quarter-hourly settlement in October 2025, so hourly spreads are a conservative lower bound — true 15-minute spreads are wider.",
          "All times are handled in local time (Europe/Berlin), including the 23- and 25-hour daylight-saving days.",
          "The battery-arbitrage and flexibility figures are labelled unachievable upper bounds (perfect foresight, no losses) — not achievable revenue.",
          "Carbon intensity is production-based (lifecycle factors); generation gaps render as gaps, never fabricated zeros; negative prices and residual load are kept, never clipped.",
          "Where a metric needs a threshold or a different methodology, the choice is stated in the view, not buried.",
          "The Iberian-blackout view assigns no cause of its own — it shows what the grid data recorded and cites the official ENTSO-E investigation.",
        ] },
      ],
    },
    {
      id: "sources",
      title: "Data sources & licences",
      kicker: "Where the numbers come from",
      blocks: [
        { h: "", p: "Every figure carries its source. The primary upstream data providers are below; attribution is required by several of them and is retained throughout the site." },
        { list: [
          "<b>ENTSO-E Transparency Platform</b> — prices, generation, load and cross-border flows for every zone, including the Nordic zones and the Iberian-blackout window.",
          "<b>netztransparenz.de</b> — the German TSOs' redispatch / curtailment API.",
          "<b>MaStR (Marktstammdatenregister)</b> — Germany's per-installation capacity registry, aggregated to Landkreis level.",
          "<b>SMARD</b> — per-control-area generation and load for the north–south balance.",
          "<b>ODRÉ — RTE éCO2mix</b> — French régional and national generation and consumption.",
          "<b>NESO</b> — Great Britain's regional carbon-intensity API and the constraint-breakdown dataset.",
          "<b>Eurostat</b> — household and industrial electricity price components (country-level).",
          "Region boundaries — pre-simplified TopoJSON from Eurostat GISCO NUTS (© EuroGeographics) and the NESO GB DNO areas.",
        ] },
        { h: "Curated, not live", p: "A few figures are hand-assembled from published studies and carried as committed static tables with a range and a citation — the France cost stack, the storage-capacity series and the marginal-fuel inputs. They are labelled as estimates and take no side. Full per-figure sourcing lives in <code>docs/SOURCES.md</code>." },
      ],
    },
    {
      id: "privacy",
      title: "Privacy",
      kicker: "Your data",
      blocks: [
        { h: "", p: "Wattlas is a static site. It has no accounts, no backend and no database, and it does not collect, store or sell any personal information." },
        { list: [
          "No cookies are set by Wattlas. A small amount of non-personal interface state (such as your last-viewed section) may be kept in your browser's local storage and never leaves your device.",
          "No analytics or third-party trackers are embedded.",
          "Pages are served as static files (GitHub Pages). The host may log standard request metadata (IP, user-agent) for delivery and security, governed by the host's own policy.",
          "Map basemaps and fonts may be loaded from third-party CDNs; those requests are subject to the respective providers' policies.",
        ] },
        { h: "Questions", p: "For anything privacy-related, reach us via the <a href=\"#/p/contact\">contact</a> page." },
      ],
    },
    {
      id: "terms",
      title: "Terms & Disclaimer",
      kicker: "Terms of use",
      blocks: [
        { h: "Provided as-is", p: "Wattlas is provided for informational and educational purposes, on an “as-is” and “as-available” basis, with no warranty of any kind — including accuracy, completeness, timeliness or fitness for a particular purpose." },
        { h: "Not financial advice", p: "Nothing on this site is investment, trading, legal or energy-procurement advice. The battery-arbitrage, flexibility-saving and cost figures are explicitly labelled upper bounds or estimates and must not be relied upon for commercial decisions. Do your own research and consult a qualified professional." },
        { h: "Data accuracy", p: "Figures derive from third-party open-data sources that may be delayed, revised, incomplete or withdrawn. Wattlas reproduces and aggregates them in good faith but cannot guarantee them, and is not liable for any loss arising from their use." },
        { h: "Third-party data & licences", p: "Upstream data and basemaps remain the property of their providers and are subject to those providers' licences and attribution requirements (see <a href=\"#/p/sources\">Data sources</a>)." },
      ],
    },
    {
      id: "contact",
      title: "Contact",
      kicker: "Get in touch",
      blocks: [
        { h: "", p: "Wattlas is an open project. The best way to report a data issue, suggest a view, or ask a question is through the public repository." },
        { list: [
          "<b>Source &amp; issues</b> — <a href=\"https://github.com/sekond/Wattlas\" target=\"_blank\" rel=\"noopener\">github.com/sekond/Wattlas</a>",
          "<b>Bugs &amp; requests</b> — open an issue on the repository's tracker.",
        ] },
        { h: "Corrections", p: "Spotted a number that looks wrong? Energy data is easy to get subtly wrong — corrections with a source are genuinely welcome." },
      ],
    },
    {
      // IMPRESSUM — operator details mirror the sister project's live Impressum
      // (StockScore, frontend/src/app/(redesign)/impressum). Keep the name, address
      // and contact in sync if they ever change. (§ 5 DDG / § 18 Abs. 2 MStV.)
      id: "impressum",
      title: "Impressum",
      kicker: "Legal notice · Angaben gemäß § 5 DDG",
      blocks: [
        { h: "", p: "Angaben gemäß § 5 Digitale-Dienste-Gesetz (DDG). Wattlas wird von einer Privatperson betrieben und ist ein nicht-kommerzielles, kostenloses Lern- und Informationsprojekt." },
        { h: "Diensteanbieter", p: "Sebastian Knödel<br>Urbanstraße 64<br>70182 Stuttgart<br>Deutschland" },
        { h: "Kontakt", p: "E-Mail: contact@sekond.de<br>Telefon: +49 160 4281516" },
        { h: "Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV", p: "Sebastian Knödel, Anschrift wie unter „Diensteanbieter“." },
        { h: "Haftung für Inhalte", p: "Als Diensteanbieter sind wir gemäß § 7 Abs. 1 DDG für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 DDG sind wir als Diensteanbieter jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen. Die Inhalte dienen ausschließlich Informations- und Bildungszwecken und stellen keine Anlage-, Handels- oder Energieberatung dar (siehe <a href=\"#/p/terms\">Terms &amp; Disclaimer</a>)." },
        { h: "Haftung für Links", p: "Unser Angebot enthält Links zu externen Websites Dritter, auf deren Inhalte wir keinen Einfluss haben. Für diese fremden Inhalte ist stets der jeweilige Anbieter oder Betreiber verantwortlich. Bei Bekanntwerden von Rechtsverletzungen werden wir derartige Links umgehend entfernen." },
        { h: "Urheberrecht", p: "Die durch den Seitenbetreiber erstellten Inhalte unterliegen dem deutschen Urheberrecht. Die zugrunde liegenden offenen Daten verbleiben bei ihren jeweiligen Anbietern und unterliegen deren Lizenz- und Namensnennungspflichten (siehe <a href=\"#/p/sources\">Data sources &amp; licences</a>)." },
        { h: "Verbraucherstreitbeilegung", p: "Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen." },
      ],
    },
  ],

  // Footer columns (link groups) shown site-wide.
  footer: {
    tagline: "European electricity, explained — open data on when, where and how much the price of power moves.",
    columns: [
      { title: "Explore", kind: "sections" },
      { title: "About", links: [
        { t: "About Wattlas", href: "#/p/about" },
        { t: "How it works", href: "#/p/methodology" },
        { t: "Data sources", href: "#/p/sources" },
        { t: "Why we restructured", href: "#/audit" },
        { t: "Showcase", href: "showcase.html" },
      ] },
      { title: "Legal", links: [
        { t: "Impressum", href: "#/p/impressum" },
        { t: "Privacy", href: "#/p/privacy" },
        { t: "Terms & Disclaimer", href: "#/p/terms" },
        { t: "Contact", href: "#/p/contact" },
      ] },
    ],
    meta: "Open data from ENTSO-E, RTE/ODRÉ, SMARD, MaStR, NESO and Eurostat. Pre-computed and static — no live backend. Not financial advice.",
  },
};
