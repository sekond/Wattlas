// Canonical fuel palette + order — the SINGLE source of truth for the frontend
// (mirrors pipeline/fuels.py). A fuel is ALWAYS the same colour in every view
// (CLAUDE.md landmine #9). Colours sit on the warm-paper palette in styles.css:
// fossil fuels in earthy browns/greys, renewables in greens/teals/yellow,
// nuclear neutral grey.
const FUEL_COLORS = {
  "Nuclear":        "#7d7a86",  // neutral violet-grey (FR baseload)
  "Lignite":        "#5a3a22",  // dark brown — dirtiest
  "Hard coal":      "#3a3a3a",  // near-black
  "Gas":            "#d98c3f",  // orange
  "Oil":            "#8a6d5a",  // muted brown
  "Other fossil":   "#a08a72",
  "Biomass":        "#7a8c3a",  // olive
  "Waste":          "#9a7fb0",  // muted purple
  "Geothermal":     "#b5651d",
  "Hydro":          "#3a7ca5",  // blue
  "Pumped storage": "#6fa8c7",  // light blue
  "Wind offshore":  "#2f7d78",  // dark teal
  "Wind onshore":   "#4aa6a0",  // teal
  "Solar":          "#e6b800",  // yellow
  "Other renewable":"#8fae6b",
  "Other":          "#bdbbb3",  // neutral grey
};

// Canonical stacking order: baseload/fossil at the bottom, variable renewables
// on top, "Other" last. Identical to FUEL_ORDER in pipeline/fuels.py.
const FUEL_ORDER = [
  "Nuclear", "Lignite", "Hard coal", "Gas", "Oil", "Other fossil",
  "Biomass", "Waste", "Geothermal", "Hydro", "Pumped storage",
  "Wind offshore", "Wind onshore", "Solar", "Other renewable", "Other",
];

// Renewable fuels (for the "renewable share" line shared by Mix + carbon views).
const RENEWABLE_FUELS = new Set([
  "Biomass", "Geothermal", "Hydro", "Wind offshore", "Wind onshore",
  "Solar", "Other renewable",
]);

function fuelColor(fuel) { return FUEL_COLORS[fuel] || "#bdbbb3"; }

// Order an arbitrary set of fuels canonically (unknowns appended, stable).
function orderFuels(fuels) {
  const set = new Set(fuels);
  const known = FUEL_ORDER.filter((f) => set.has(f));
  const extra = fuels.filter((f) => !FUEL_ORDER.includes(f));
  return known.concat(extra);
}

// Carbon methodology label shown in the UI (mirror of fuels.py CARBON_METHODOLOGY).
const CARBON_METHODOLOGY =
  "Production-based, IPCC AR5 lifecycle median factors. Reflects electricity " +
  "generated within the zone (imports/exports excluded); lifecycle, not " +
  "combustion-only; standard per-fuel factors, not plant-level measurements.";
