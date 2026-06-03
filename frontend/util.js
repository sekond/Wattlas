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

// "2025-06-03" -> "3 Jun 2025"
function fmtDate(iso) {
  const [y, m, d] = iso.split("-");
  return `${parseInt(d, 10)} ${MONTHS_SHORT[parseInt(m, 10) - 1]} ${y}`;
}

// Whole months between two ISO dates (rounded). Computed, not hard-coded, so the
// label stays correct if the rolling window length ever changes.
function monthsBetween(start, end) {
  const days = (new Date(end + "T00:00:00Z") - new Date(start + "T00:00:00Z")) / 86400000;
  return Math.max(1, Math.round(days / 30.4375));
}

// ("2025-06-03","2026-06-02") -> "the 12 months to 2 Jun 2026"
function fmtPeriod(start, end) { return `the ${monthsBetween(start, end)} months to ${fmtDate(end)}`; }
