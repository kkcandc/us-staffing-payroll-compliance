# Schema

The canonical table is `data/facts.csv` (mirrored in `data/facts.json`). It is long format: **one row per fact**, so every single value carries its own source and check date.

| Column | Type | Description |
|---|---|---|
| `id` | string | Stable key, `{JURISDICTION}.{topic}.{field}`, for example `TX.final_pay.discharge`. Never reused. |
| `jurisdiction` | string | USPS code for the 50 states and DC, or `US` for federal rows. |
| `jurisdiction_name` | string | Full name. |
| `category` | enum | `unemployment_insurance`, `minimum_wage`, `pay_frequency`, `final_pay`, `workers_comp`, `federal_payroll_tax` (later: `staffing_registration`, `new_hire_reporting`). |
| `field` | string | Machine name of the fact, see the field list below. |
| `value` | string | The fact in plain words or as printed by the source (for example `$9,000`, `2.70%`). Blank when not verified. |
| `value_numeric` | number | Numeric form where it makes sense (dollars, percent points). Blank otherwise. |
| `unit` | string | Unit of `value_numeric` or `text` / `URL`. |
| `applies_to` | string | Period or version the value applies to (for example `Calendar year 2026`, `Rate year July 1 - June 30`). |
| `summary` | string | One plain-English sentence, suitable for a state page. |
| `evidence_quote` | string | Short verbatim excerpt from the source that supports the value. `...` marks an omission. |
| `source_title` | string | Title of the official page or document. |
| `source_url` | URL | Full https URL of the official source. Must be a government domain (see `pipeline/validate.py`). |
| `source_publisher` | string | Agency or legislature that publishes the source. |
| `source_level` | enum | `federal_agency`, `state_agency`, `state_statute`. |
| `source_date` | date | Publication, revision or effective date shown on the source, if any. |
| `retrieval` | string | How we read it: `fetched_html`, `fetched_pdf`, `fetched_html_parsed`, `fetched_pdf_parsed`, `fetched_xlsx_parsed`. |
| `last_checked` | date | ISO date we last opened the source and confirmed the value. |
| `status` | enum | `verified` (value read from the cited official source), `needs_review` (value present but flagged), `unverified_blank` (no value yet; `notes` explains why). |
| `notes` | string | Caveats, exceptions, footnotes from the source, and reasons for blanks. |

## Fields

| Category | Field | Meaning |
|---|---|---|
| unemployment_insurance | `suta_taxable_wage_base` | Wages per employee per year subject to state UI tax. |
| unemployment_insurance | `suta_new_employer_rate` | The BASE UI rate a new employer is assigned, in every state. All-in rates (with mandatory surcharges, fund-building rates and assessments) never go here; they go only in `total_new_employer_rate`. Where the DOL value already equals the state's published total (for example PA, NJ), `notes` says so. Industry-average states (for example WA) have no single numeric value. |
| unemployment_insurance | `total_new_employer_rate` | Optional. The total new-employer rate including mandatory surcharges, fund-building rates and assessments, only where a state agency publishes it (or publishes every component on the same wage base). Industry variants use an id suffix such as `_naics56`. The calculator uses this as its default SUTA rate when present. |
| unemployment_insurance | `suta_rate_range` | Minimum to maximum experience-rated UI rate. |
| unemployment_insurance | `futa_credit_reduction` | Extra FUTA owed by employers in the state for the tax year. |
| minimum_wage | `state_minimum_wage` | Basic state hourly minimum as listed by U.S. DOL. Local minimums excluded. |
| pay_frequency | `dol_payday_table` | Frequencies marked in the U.S. DOL State Payday Requirements table. |
| pay_frequency | `pay_frequency_state_rule` | Pay frequency rule read from the state statute or agency. |
| final_pay | `final_pay_discharge` | Deadline for final wages when the employer ends employment. |
| final_pay | `final_pay_resignation` | Deadline for final wages when the employee quits. |
| workers_comp | `wc_agency` | State workers' compensation agency website. |
| workers_comp | `wc_monopolistic_state_fund` | Whether coverage must come from a state fund. |
| federal_payroll_tax | `futa_*`, `social_security_*`, `medicare_*` | Federal rates and wage bases used by the bill-rate calculator. |

## Other files

- `data/states/XX.json`: all rows for one jurisdiction (what the state pages and API read).
- `data/compare.csv`: wide table, one row per state, verified values only (what the compare view reads).
- `COVERAGE.md`: state x field matrix, regenerated on every build.
