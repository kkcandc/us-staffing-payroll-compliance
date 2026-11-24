// Pure, read-only query helpers over the bundled dataset. No network, no filesystem writes.
import { readFileSync } from "node:fs";
import { calculate, defaultsFromDataset } from "./data/calculator.mjs";

const DATA = JSON.parse(readFileSync(new URL("./data/facts.json", import.meta.url), "utf-8"));
export const META = DATA.meta;
const FACTS = DATA.facts;
const NAMES = {};
for (const f of FACTS) NAMES[f.jurisdiction] = f.jurisdiction_name;

const CITE = (f) => ({
  id: f.id, field: f.field, value: f.value, applies_to: f.applies_to, summary: f.summary,
  status: f.status, source_url: f.source_url, source_title: f.source_title,
  evidence_quote: f.evidence_quote, last_checked: f.last_checked, notes: f.notes,
});

export function resolveState(s) {
  if (!s) throw new Error("state is required");
  const t = String(s).trim();
  const code = t.toUpperCase();
  if (NAMES[code]) return code;
  const hit = Object.entries(NAMES).find(([, n]) => n.toLowerCase() === t.toLowerCase());
  if (hit) return hit[0];
  throw new Error(`unknown state: ${s}. Use a two-letter code (e.g. TX) or a full name.`);
}

export function listJurisdictions() {
  return Object.entries(NAMES).filter(([c]) => c !== "US").map(([code, name]) => ({ code, name }));
}

export function listFields() {
  return [...new Set(FACTS.map((f) => f.field))].sort();
}

export function getStateRules(state, fields) {
  const code = resolveState(state);
  const want = fields && fields.length ? new Set(fields) : null;
  return { jurisdiction: code, name: NAMES[code], facts: FACTS.filter((f) => f.jurisdiction === code && (!want || want.has(f.field))).map(CITE) };
}

export function getFact(state, field) {
  const code = resolveState(state);
  const rows = FACTS.filter((f) => f.jurisdiction === code && f.field === field);
  if (!rows.length) return { jurisdiction: code, field, found: false, note: "No row for this field yet. A blank is intentional: the dataset never guesses." };
  return { jurisdiction: code, field, found: true, facts: rows.map(CITE) };
}

export function compareStates(states, fields) {
  if (!Array.isArray(states) || states.length < 2 || states.length > 10) throw new Error("pass 2 to 10 states");
  const codes = states.map(resolveState);
  const fl = fields && fields.length ? fields : ["suta_taxable_wage_base", "suta_new_employer_rate", "total_new_employer_rate", "state_minimum_wage", "final_pay_discharge", "final_pay_resignation", "new_hire_reporting_deadline", "wc_monopolistic_state_fund"];
  return {
    fields: fl,
    states: codes.map((c) => ({
      jurisdiction: c, name: NAMES[c],
      cells: Object.fromEntries(fl.map((field) => {
        const f = FACTS.find((r) => r.jurisdiction === c && r.field === field && r.status === "verified");
        return [field, f ? { value: f.value, source_url: f.source_url, last_checked: f.last_checked } : null];
      })),
    })),
  };
}

export function searchFacts(query, limit = 20) {
  const q = String(query || "").toLowerCase().split(/\s+/).filter(Boolean);
  if (!q.length) throw new Error("query is required");
  const scored = FACTS.map((f) => {
    const hay = `${f.jurisdiction_name} ${f.jurisdiction} ${f.field} ${f.category} ${f.summary} ${f.value}`.toLowerCase();
    return [q.filter((w) => hay.includes(w)).length, f];
  }).filter(([s]) => s > 0).sort((a, b) => b[0] - a[0]);
  return scored.slice(0, Math.min(limit, 50)).map(([, f]) => CITE(f));
}

export function estimateBillRate(input) {
  const code = resolveState(input.state);
  const st = FACTS.filter((f) => f.jurisdiction === code);
  const us = FACTS.filter((f) => f.jurisdiction === "US");
  const d = defaultsFromDataset(st, us, { naicsSector: input.naics_sector });
  const args = {
    ...d,
    payRate: input.pay_rate, hoursPerWeek: input.hours_per_week ?? 40, weeks: input.weeks ?? 52,
    wcRatePer100: input.wc_rate_per_100 ?? 0, otherBurdenPct: input.other_burden_pct ?? 0,
  };
  if (input.suta_rate_pct != null) args.sutaRatePct = input.suta_rate_pct;
  for (const [k, v] of [["markupPct", input.markup_pct], ["billRate", input.bill_rate], ["targetMarginPct", input.target_margin_pct]]) if (v != null) args[k] = v;
  const r = calculate(args);
  return {
    jurisdiction: code,
    inputs_used: { pay_rate: args.payRate, hours_per_week: args.hoursPerWeek, weeks: args.weeks, suta_rate_pct: args.sutaRatePct, suta_rate_basis: input.suta_rate_pct != null ? "user input" : d.sutaRateBasis, suta_wage_base: args.sutaWageBase, futa_credit_reduction_pct: args.futaCreditReductionPct, wc_rate_per_100: args.wcRatePer100, other_burden_pct: args.otherBurdenPct },
    result: { bill_rate: round(r.billRate), markup_pct: round(r.markupPct), gross_margin_pct: round(r.grossMarginPct), loaded_cost_per_hour: round(r.loadedCost), burden_per_hour: round(r.burdenPerHour), burden_pct_of_pay: round(r.burdenPctOfPay), per_hour: Object.fromEntries(Object.entries(r.perHour).map(([k, v]) => [k, round(v)])) },
    sources: d.sources,
    disclaimer: "Estimate only. Not tax or legal advice. Workers' comp and other burden are your inputs; local taxes, PFML and disability programs are not included.",
  };
}
const round = (x) => (x == null ? null : Math.round(x * 100) / 100);
