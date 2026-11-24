# Changelog

## 0.1.0-rc (2026-11-24, private release candidate)
- Catalyst Compliance sign-off: 2026-11-24 (12:50 CET), conditional on the fixes below, which need no re-review. All applied and re-checked against the cited official pages fetched the same day.
- Rule: `suta_new_employer_rate` holds the base rate everywhere; all-in rates live only in `total_new_employer_rate`. CO reverted to 1.53% (CDLE beginning rate); IL reverted to 2.80% (DOL) with a note that the IDES 3.350% includes the 0.550% fund building rate; NY stays 4.025% (base UI rate) with 4.1% in the total field.
- PA and NJ new employer rows: note now says the DOL value equals the state's published total.
- WY workers' comp value reworded to match the WY DOI page.
- FL and GA final pay notes tagged "Basis: absence of statute"; NY total notes the 4.325% rate for employers whose liability began in 2023 or 2024.

## 0.1.1-pilot (2026-11-24, private draft, superseded by 0.1.0-rc)
- Applied the Catalyst Compliance review (pass with corrections). Every changed value was re-checked against the cited official page fetched the same day; corrections live in `data/curated/overrides_compliance_2026-11-24.csv`.
- Resolved all 6 needs_review rows (MD and MO new hire now cite state statutes; MD, MO independent contractor reporting = No; NE and SC resignation confirmed by state agency FAQs).
- Filled all 14 blanks: AL, FL, GA, OH final pay (no state deadline, regular payday; OH R.C. 4113.15(A)); MO and SD resignation; MT new hire (MCA 40-5-922) and contractor reporting; OH and WY monopolistic workers' comp.
- UI corrections from state agency sources (CO and IL new employer values later moved to `total_new_employer_rate` in 0.1.0-rc): CO new employer 3.05% combined; IL new employer 3.350% (3.450% NAICS 56) and range 0.750% to 7.050%; NY range 1.7% to 9.5%; PA range 1.4190% to 10.3734%; TX range 0.32% to 6.32%. Notes added for CA (ETT, SDI), NJ (July to June rate year), WA (115% of industry average; social tax and EAF), NY (UI vs total), and a base-rate note on all DOL-sourced new employer rates.
- New field `total_new_employer_rate` (CA, CO, IL, IL NAICS 56, NJ, NY, PA); calculator default now uses it where present.
- Minimum wage: NY and OR show regional rates with no single numeric default; GA and WY note the $7.25 FLSA minimum.
- New hire reporting 51/51; final pay 43/51 fired and 43/51 quit; monopolistic fund 4/51.

## 0.1.0-pilot (2026-11-24, private draft)
- Schema for 50 states + DC, long format with per-row official source and last_checked.
- 51/51: SUTA wage base, new employer rate, rate range (DOL ETA July 2026); FUTA 2026 credit reduction; state minimum wage (DOL WHD, updated 2026-11-05); DOL payday table; workers' comp agency link (DOL OWCP).
- New hire reporting timeframe (HHS OCSE IRG): 48/51 verified, MD and MO flagged for review, MT blank (parser could not find its entry).
- Final pay (fired / quit) from state statutes and agencies for 39 / 35 jurisdictions; the rest blank with notes.
- Federal rows: FUTA, Social Security (2026 and 2027 wage bases), Medicare.
- Validator and validator self-test; reference bill-rate calculator with tests.
