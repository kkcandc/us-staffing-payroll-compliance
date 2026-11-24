# US Staffing Payroll Compliance Dataset

Free, state-by-state reference data for US staffing firms and employers of record: state unemployment insurance (SUTA) wage bases and rates, FUTA credit reductions, minimum wage, pay frequency, final pay deadlines, new hire reporting, and workers' compensation basics.

**Every row cites an official government source (a .gov or official state agency page) and the date we last checked it.** If we could not confirm a value from an official source, the cell is blank with a note. We never fill gaps from memory.

- Status: `0.1.0-rc` (private draft, not yet published)
- Coverage: all 50 states plus DC are in the schema; see [COVERAGE.md](COVERAGE.md) for what is verified per state and field
- License: data and docs [CC BY 4.0](LICENSE); code [MIT](LICENSE-CODE)
- Maintainer: Catalyst Works, https://getcatalystworks.com/

> Not legal or tax advice. Rules change and have exceptions. Always open the cited source before relying on a value.

## What is in it

| Topic | Fields | Primary source |
|---|---|---|
| State unemployment insurance | taxable wage base, new employer rate, min/max rate | U.S. DOL ETA, Significant Provisions of State UI Laws (July 2026) |
| FUTA | 2026 credit reduction per state | U.S. DOL ETA, Final 2026 FUTA Credit Reductions |
| Minimum wage | basic state hourly minimum | U.S. DOL WHD, State Minimum Wage Laws |
| Pay frequency | DOL payday table, plus state statute or agency rule where verified | U.S. DOL WHD; state codes and labor departments |
| Final pay | deadline when fired or laid off, and when the employee quits | State statutes and labor departments |
| New hire reporting | reporting deadline, independent contractor reporting | HHS Office of Child Support Services, Intergovernmental Reference Guide |
| Workers' compensation | state agency, monopolistic state fund | U.S. DOL OWCP; state agencies |
| Federal payroll taxes | FUTA, Social Security, Medicare rates and wage bases | IRS, SSA |

## Files

```
data/facts.csv        canonical table, one row per fact (see SCHEMA.md)
data/facts.json       same rows plus metadata
data/states/XX.json   one file per jurisdiction (and US.json for federal rows)
data/compare.csv      one row per state, verified values only (side-by-side view)
data/generated/       rows parsed from saved official federal files (do not edit)
data/curated/         rows read from state statutes and agency pages (edit here, with a quote and source)
sources/federal/      saved copies of the federal source files the parsers read
pipeline/             extract, build and validate scripts
tools/calculator.mjs  reference bill-rate calculator that reads this dataset
```

## Using it

CSV: open `data/facts.csv` in any spreadsheet. Filter by `jurisdiction` and `field`.

JSON (one state):

```bash
curl -s https://getcatalystworks.com/data/states/TX.json   # planned public URL, not live yet
```

Each fact looks like:

```json
{
  "id": "TX.final_pay.discharge",
  "value": "not later than the sixth day after discharge",
  "evidence_quote": "Sec. 61.014. (a) An employer shall pay in full an employee who is discharged from employment not later than the sixth day after the date the employee is discharged.",
  "source_url": "https://statutes.capitol.texas.gov/Docs/LA/htm/LA.61.htm",
  "last_checked": "2026-11-24",
  "status": "verified"
}
```

## Rebuilding and validating

```bash
pip install pymupdf openpyxl
python3 pipeline/extract_federal_sources.py   # parse saved federal files into data/generated/
python3 pipeline/build.py                     # merge, write facts.csv/json, per-state JSON, compare.csv, COVERAGE.md
python3 pipeline/validate.py                  # fails on any row without an official https source, a last_checked date, or a note on blanks
python3 pipeline/test_validate.py             # proves the validator rejects bad rows
node --test tools/calculator.test.mjs         # calculator tests against the dataset
```

The validator rejects: non-government or non-https sources, missing `last_checked`, verified rows without an evidence quote, blanks without a note, duplicate ids, and the em dash character.

## How we verify

1. Open the official page or document (state legislature, state agency, or federal agency).
2. Copy the supporting sentence into `evidence_quote` and record `source_url`, `source_date` and `last_checked`.
3. Federal tables are parsed by script from saved copies in `sources/federal/`, then spot-checked by hand.
4. A second reviewer (Catalyst Works compliance) checks every value before a release.
5. Values that change on a schedule (wage bases, rates, minimum wage) are re-checked at least each January and July.

## Citing

See [CITATION.cff](CITATION.cff). Suggested: "US Staffing Payroll Compliance Dataset, Catalyst Works, version 0.1.0-rc, https://getcatalystworks.com/ (CC BY 4.0)."

## Corrections

Found an error? Open an issue with the state, field, and a link to the official source. We fix verified errors quickly and note them in the changelog.

## Read-only JSON API and MCP server

- `python3 pipeline/build_api.py` writes static files to `api/v1/` (index, jurisdictions, fields, compare, facts, one file per state). Host them on any static host; the site serves them at https://getcatalystworks.com/data/v1/ once deployed.
- `mcp/` is a read-only MCP server (stdio) with tools `list_jurisdictions`, `get_state_rules`, `get_fact`, `compare_states`, `search_facts`, `estimate_bill_rate`. It reads a bundled copy of the data, makes no network calls and writes nothing. See `mcp/README.md`.
