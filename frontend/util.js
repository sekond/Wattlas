// Shared display helpers — keep raw zone codes / ISO dates out of the UI.
const ZONE_NAMES = {
  DE_LU: "Germany (DE-LU)",
  FR: "France",
  NL: "Netherlands",
  BE: "Belgium",
  PL: "Poland",
  AT: "Austria",
};
const MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// "DE_LU" -> "Germany (DE-LU)"; unknown codes fall back to the code itself.
function zoneName(code) { return ZONE_NAMES[code] || code; }

// "2025-06-03" -> "Jun 2025"
function fmtMonthYear(iso) {
  const [y, m] = iso.split("-");
  return `${MONTHS_SHORT[parseInt(m, 10) - 1]} ${y}`;
}

// ("2025-06-03","2026-06-02") -> "Jun 2025 – Jun 2026"
function fmtPeriod(start, end) { return `${fmtMonthYear(start)} – ${fmtMonthYear(end)}`; }
