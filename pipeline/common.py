"""Shared constants for the US staffing payroll compliance dataset pipeline."""
import csv, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SOURCES = os.path.join(ROOT, "sources")

FIELDS = [
    "id", "jurisdiction", "jurisdiction_name", "category", "field", "value",
    "value_numeric", "unit", "applies_to", "summary", "evidence_quote",
    "source_title", "source_url", "source_publisher", "source_level",
    "source_date", "retrieval", "last_checked", "status", "notes",
]

# 50 states + DC. Territories are out of scope for v0.
JURISDICTIONS = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia",
    "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}
NAME_TO_CODE = {v.upper(): k for k, v in JURISDICTIONS.items()}

# Fields every jurisdiction should eventually have (drives COVERAGE.md).
CORE_FIELDS = [
    ("unemployment_insurance", "suta_taxable_wage_base"),
    ("unemployment_insurance", "suta_new_employer_rate"),
    ("unemployment_insurance", "suta_rate_range"),
    ("unemployment_insurance", "futa_credit_reduction"),
    ("minimum_wage", "state_minimum_wage"),
    ("pay_frequency", "dol_payday_table"),
    ("final_pay", "final_pay_discharge"),
    ("final_pay", "final_pay_resignation"),
    ("workers_comp", "wc_agency"),
    ("workers_comp", "wc_monopolistic_state_fund"),
    ("staffing_registration", "staffing_or_peo_registration"),
    ("new_hire_reporting", "new_hire_reporting_deadline"),
]

STATUS_VALUES = {"verified", "needs_review", "unverified_blank"}
LEVELS = {"federal_agency", "state_agency", "state_statute"}

def write_rows(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})

def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
