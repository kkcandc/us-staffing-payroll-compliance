#!/usr/bin/env node
// Read-only MCP server (stdio) for the US Staffing Payroll Compliance Dataset.
// Every tool is read-only: it answers from the bundled dataset and never writes, fetches or executes anything else.
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { META, listJurisdictions, listFields, getStateRules, getFact, compareStates, searchFacts, estimateBillRate } from "./lib.mjs";

const server = new McpServer({ name: "payroll-compliance", version: META.version });
const RO = { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false };
const ok = (obj) => ({ content: [{ type: "text", text: JSON.stringify({ ...obj, dataset: { version: META.version, license: META.license, disclaimer: META.disclaimer } }, null, 1) }] });
const wrap = (fn) => async (args) => {
  try { return ok(await fn(args)); } catch (e) { return { isError: true, content: [{ type: "text", text: String(e.message || e) }] }; }
};

server.registerTool("list_jurisdictions", { title: "List jurisdictions", description: "List the 50 states plus DC covered by the dataset, with two-letter codes.", inputSchema: {}, annotations: RO },
  wrap(() => ({ jurisdictions: listJurisdictions(), fields: listFields() })));
server.registerTool("get_state_rules", { title: "Get a state's payroll rules", description: "All payroll compliance facts for one state (SUTA, FUTA credit reduction, minimum wage, pay frequency, final pay, new hire reporting, workers' comp). Each fact includes its official source URL, quote and last_checked date.",
  inputSchema: { state: z.string().describe("Two-letter code or full name, e.g. TX or Texas"), fields: z.array(z.string()).optional().describe("Optional list of field names to return") }, annotations: RO },
  wrap(({ state, fields }) => getStateRules(state, fields)));
server.registerTool("get_fact", { title: "Get one fact", description: "One field for one state, with citation. Use list_jurisdictions to see field names.",
  inputSchema: { state: z.string(), field: z.string() }, annotations: RO }, wrap(({ state, field }) => getFact(state, field)));
server.registerTool("compare_states", { title: "Compare states", description: "Side-by-side verified values for 2 to 10 states.",
  inputSchema: { states: z.array(z.string()).min(2).max(10), fields: z.array(z.string()).optional() }, annotations: RO },
  wrap(({ states, fields }) => compareStates(states, fields)));
server.registerTool("search_facts", { title: "Search facts", description: "Keyword search across all facts (state names, topics, values).",
  inputSchema: { query: z.string(), limit: z.number().int().min(1).max(50).optional() }, annotations: RO },
  wrap(({ query, limit }) => ({ results: searchFacts(query, limit) })));
server.registerTool("estimate_bill_rate", { title: "Estimate a staffing bill rate", description: "Estimate employer burden, bill rate and gross margin for a W-2 temp in a state, using the dataset's sourced SUTA, FUTA and FICA figures. Provide exactly one of markup_pct, bill_rate or target_margin_pct.",
  inputSchema: {
    state: z.string(), pay_rate: z.number().positive(), hours_per_week: z.number().positive().optional(), weeks: z.number().positive().max(53).optional(),
    suta_rate_pct: z.number().min(0).max(20).optional().describe("Your assigned SUTA rate; defaults to the state's total new-employer rate where published"),
    naics_sector: z.string().optional().describe("e.g. 56 for staffing (affects IL)"),
    wc_rate_per_100: z.number().min(0).optional(), other_burden_pct: z.number().min(0).optional(),
    markup_pct: z.number().optional(), bill_rate: z.number().optional(), target_margin_pct: z.number().max(99).optional(),
  }, annotations: RO }, wrap((a) => estimateBillRate(a)));

await server.connect(new StdioServerTransport());
