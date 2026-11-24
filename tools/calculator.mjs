// Staffing bill-rate calculator (reference implementation for the site page).
// Pure functions, no network. Statutory inputs come from the dataset (data/states/XX.json, data/states/US.json);
// anything employer-specific (assigned SUTA rate, workers' comp rate, benefits) is a user input with no invented default.

const num = (s) => (s === "" || s == null ? null : Number(String(s).replace(/[$,%]/g, "")));

/** Pull the statutory defaults for one state out of the dataset rows. */
export function defaultsFromDataset(stateFacts, usFacts, opts = {}) {
  const get = (rows, field, applies) =>
    rows.find((r) => r.field === field && r.status === "verified" && (!applies || r.applies_to === applies));
  const wb = get(stateFacts, "suta_taxable_wage_base");
  const ne = get(stateFacts, "suta_new_employer_rate");
  // Prefer the total new-employer rate (includes mandatory surcharges, fund-building rates, assessments) where a
  // state agency publishes one. Industry-specific variants (e.g. IL NAICS sector 56, which covers staffing) win
  // when the caller passes that sector.
  const totals = stateFacts.filter((r) => r.field === "total_new_employer_rate" && r.status === "verified" && r.value_numeric !== "");
  const sector = opts.naicsSector ? String(opts.naicsSector) : null;
  const tot = (sector && totals.find((r) => r.id.endsWith(`_naics${sector}`))) || totals.find((r) => !/_naics\d+$/.test(r.id));
  const rateRow = tot || (ne && ne.value_numeric ? ne : null);
  const cr = get(stateFacts, "futa_credit_reduction");
  const year = "2026";
  const out = {
    sutaWageBase: wb ? num(wb.value_numeric) : null,
    sutaRatePct: rateRow ? num(rateRow.value_numeric) : null, // null when the state uses an industry average
    sutaRateBasis: tot ? "total_new_employer_rate" : rateRow ? "suta_new_employer_rate (may exclude surcharges)" : null,
    futaCreditReductionPct: cr ? num(cr.value_numeric) : 0,
    futaGrossPct: num(get(usFacts, "futa_gross_rate").value_numeric),
    futaWageBase: num(get(usFacts, "futa_wage_base").value_numeric),
    futaMaxCreditPct: 5.4, // IRS Topic 759: credit of up to 5.4%; net 0.6% (see US.futa.net_rate)
    ssPct: num(get(usFacts, "social_security_employer_rate").value_numeric),
    ssWageBase: num(get(usFacts, "social_security_wage_base", year).value_numeric),
    medicarePct: num(get(usFacts, "medicare_employer_rate").value_numeric),
    sources: [wb, rateRow, cr].filter(Boolean).map((r) => ({ id: r.id, url: r.source_url, last_checked: r.last_checked })),
  };
  return out;
}

/**
 * @param {object} i
 *  payRate         hourly pay ($)
 *  hoursPerWeek    expected hours per week on assignment
 *  weeks           expected weeks in the calendar year (caps taxes at wage bases)
 *  sutaRatePct     employer's assigned SUTA rate (defaults to the state's total new-employer rate where published,
 *                  else the new-employer rate; null in industry-average states)
 *  sutaWageBase    state taxable wage base
 *  futa*           FUTA inputs; ssPct, ssWageBase, medicarePct are FICA inputs
 *  wcRatePer100    workers' comp rate per $100 of payroll (user input, no default)
 *  otherBurdenPct  other employer costs as % of pay (benefits, PTO, admin), user input
 *  otherPerHour    other fixed $/hour costs, user input
 *  markupPct | billRate | targetMarginPct   exactly one pricing input
 */
export function calculate(i) {
  const req = ["payRate", "hoursPerWeek", "weeks", "sutaWageBase", "futaGrossPct", "futaWageBase", "ssPct", "ssWageBase", "medicarePct"];
  for (const k of req) if (!(Number.isFinite(i[k]) && i[k] >= 0)) throw new Error(`missing or invalid input: ${k}`);
  if (!Number.isFinite(i.sutaRatePct)) throw new Error("missing input: sutaRatePct (enter your assigned state UI rate)");
  const hours = i.hoursPerWeek * i.weeks;
  if (hours <= 0) throw new Error("hoursPerWeek x weeks must be > 0");
  const wages = i.payRate * hours;
  const capped = (base) => Math.min(wages, base);
  const futaNetPct = Math.max(0, i.futaGrossPct - (i.futaMaxCreditPct ?? 5.4) + (i.futaCreditReductionPct ?? 0));
  const annual = {
    socialSecurity: capped(i.ssWageBase) * i.ssPct / 100,
    medicare: wages * i.medicarePct / 100,
    futa: capped(i.futaWageBase) * futaNetPct / 100,
    suta: capped(i.sutaWageBase) * i.sutaRatePct / 100,
    workersComp: wages * (i.wcRatePer100 ?? 0) / 100,
    other: wages * (i.otherBurdenPct ?? 0) / 100 + hours * (i.otherPerHour ?? 0),
  };
  const perHour = Object.fromEntries(Object.entries(annual).map(([k, v]) => [k, v / hours]));
  const burdenPerHour = Object.values(perHour).reduce((a, b) => a + b, 0);
  const loadedCost = i.payRate + burdenPerHour;
  let billRate;
  const set = ["markupPct", "billRate", "targetMarginPct"].filter((k) => Number.isFinite(i[k]));
  if (set.length !== 1) throw new Error("provide exactly one of markupPct, billRate, targetMarginPct");
  if (Number.isFinite(i.markupPct)) billRate = i.payRate * (1 + i.markupPct / 100);
  else if (Number.isFinite(i.billRate)) billRate = i.billRate;
  else {
    if (i.targetMarginPct >= 100) throw new Error("targetMarginPct must be < 100");
    billRate = loadedCost / (1 - i.targetMarginPct / 100);
  }
  const grossProfit = billRate - loadedCost;
  return {
    hours, wages, futaNetPct, annual, perHour,
    burdenPerHour, burdenPctOfPay: (burdenPerHour / i.payRate) * 100,
    loadedCost, billRate,
    markupPct: (billRate / i.payRate - 1) * 100,
    grossProfitPerHour: grossProfit,
    grossMarginPct: billRate > 0 ? (grossProfit / billRate) * 100 : null,
  };
}
