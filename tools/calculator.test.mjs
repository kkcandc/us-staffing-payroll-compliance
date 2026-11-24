import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { calculate, defaultsFromDataset } from "./calculator.mjs";

const load = (c) => JSON.parse(readFileSync(new URL(`../data/states/${c}.json`, import.meta.url))).facts;
const close = (a, b, eps = 1e-9) => assert.ok(Math.abs(a - b) < eps, `${a} != ${b}`);

test("TX defaults come from the dataset", () => {
  const d = defaultsFromDataset(load("TX"), load("US"));
  assert.equal(d.sutaWageBase, 9000);
  assert.equal(d.sutaRatePct, 2.7);
  assert.equal(d.futaCreditReductionPct, 0);
  assert.equal(d.ssWageBase, 184500);
});

test("CA picks up the 2026 FUTA credit reduction", () => {
  const d = defaultsFromDataset(load("CA"), load("US"));
  assert.equal(d.futaCreditReductionPct, 1.5);
});

test("hand-checked TX example: $25/hr, 40h x 52w, WC 2.00/100, 40% markup", () => {
  const d = defaultsFromDataset(load("TX"), load("US"));
  const r = calculate({ ...d, payRate: 25, hoursPerWeek: 40, weeks: 52, wcRatePer100: 2, markupPct: 40 });
  // wages 52,000. SS 6.2% = 3,224. Medicare 1.45% = 754. FUTA 0.6% x 7,000 = 42. SUTA 2.7% x 9,000 = 243. WC 2% = 1,040.
  const totalAnnual = 3224 + 754 + 42 + 243 + 1040;
  close(r.burdenPerHour, totalAnnual / 2080);
  close(r.billRate, 35);
  close(r.grossProfitPerHour, 35 - 25 - totalAnnual / 2080);
});

test("target margin solves for bill rate", () => {
  const d = defaultsFromDataset(load("TX"), load("US"));
  const r = calculate({ ...d, payRate: 30, hoursPerWeek: 40, weeks: 26, targetMarginPct: 25 });
  close(r.grossMarginPct, 25, 1e-9);
});

test("industry-average states require the user's own SUTA rate", () => {
  const d = defaultsFromDataset(load("WA"), load("US"));
  assert.equal(d.sutaRatePct, null);
  assert.throws(() => calculate({ ...d, payRate: 20, hoursPerWeek: 40, weeks: 52, markupPct: 30 }), /sutaRatePct/);
});

test("total new-employer rate is the default where a state agency publishes one", () => {
  const co = defaultsFromDataset(load("CO"), load("US"));
  assert.equal(co.sutaRatePct, 3.05);
  assert.equal(co.sutaRateBasis, "total_new_employer_rate");
  assert.equal(defaultsFromDataset(load("NY"), load("US")).sutaRatePct, 4.1);
  assert.equal(defaultsFromDataset(load("CA"), load("US")).sutaRatePct, 3.5);
});

test("Illinois staffing firms (NAICS 56) get the sector entry rate", () => {
  assert.equal(defaultsFromDataset(load("IL"), load("US")).sutaRatePct, 3.35);
  assert.equal(defaultsFromDataset(load("IL"), load("US"), { naicsSector: 56 }).sutaRatePct, 3.45);
});

test("states without a published total fall back to the new-employer rate and say so", () => {
  const d = defaultsFromDataset(load("TX"), load("US"));
  assert.equal(d.sutaRatePct, 2.7);
  assert.match(d.sutaRateBasis, /may exclude surcharges/);
});
