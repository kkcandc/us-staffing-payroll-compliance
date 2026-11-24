# payroll-compliance-mcp (read-only)

A Model Context Protocol server that answers questions from the US Staffing Payroll Compliance Dataset. Every answer includes the official source URL, the quoted text and the last-checked date.

Security: read-only by design. The server reads a bundled copy of the dataset, makes no network calls, writes nothing, needs no API key and has no access to any Catalyst Works system.

Tools: `list_jurisdictions`, `get_state_rules`, `get_fact`, `compare_states`, `search_facts`, `estimate_bill_rate`.

```
npm install
npm run prepare-data   # copies ../api/v1/facts.json and ../tools/calculator.mjs into data/
npm test
node server.mjs        # stdio transport
```

Client config example:

```json
{ "mcpServers": { "payroll-compliance": { "command": "node", "args": ["/path/to/mcp/server.mjs"] } } }
```

Not legal or tax advice. Data CC BY 4.0 (Catalyst Works); code MIT.
