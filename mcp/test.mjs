import test from "node:test";
import assert from "node:assert/strict";
import { getFact, compareStates, searchFacts, estimateBillRate, resolveState, listJurisdictions } from "./lib.mjs";

test("51 jurisdictions", () => assert.equal(listJurisdictions().length, 51));
test("resolves names", () => { assert.equal(resolveState("texas"), "TX"); assert.throws(() => resolveState("Atlantis")); });
test("facts carry citations", () => {
  const f = getFact("TX", "final_pay_discharge").facts[0];
  assert.match(f.source_url, /^https:\/\//); assert.ok(f.last_checked); assert.ok(f.evidence_quote);
});
test("compare", () => assert.equal(compareStates(["TX", "CA"]).states.length, 2));
test("search", () => assert.ok(searchFacts("ohio final pay").length > 0));
test("bill rate TX matches the hand-checked case", () => {
  const r = estimateBillRate({ state: "TX", pay_rate: 25, hours_per_week: 40, weeks: 52, wc_rate_per_100: 2, markup_pct: 40 });
  assert.equal(r.result.bill_rate, 35);
  assert.equal(r.result.burden_per_hour, Math.round(((3224 + 754 + 42 + 243 + 1040) / 2080) * 100) / 100);
});
