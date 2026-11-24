"""Build the static, read-only JSON API (api/v1/) from data/facts.csv.

The API is plain files: host them on any static host or CDN (the site copies them to /data/v1/).
No keys, no writes, no server code.
Run after build.py: python3 pipeline/build_api.py
"""
import csv, json, os, re, shutil
from collections import defaultdict
from common import FIELDS, JURISDICTIONS, CORE_FIELDS, DATA, ROOT, read_rows
import build

API = os.path.join(ROOT, "api", "v1")
BASE_URL = "https://getcatalystworks.com/data/v1"

FIELD_LABELS = {
    "suta_taxable_wage_base": "State unemployment (SUTA) taxable wage base",
    "suta_new_employer_rate": "SUTA new employer base rate",
    "total_new_employer_rate": "SUTA new employer total rate (with surcharges)",
    "suta_rate_range": "SUTA rate range",
    "futa_credit_reduction": "FUTA credit reduction",
    "state_minimum_wage": "State minimum wage",
    "dol_payday_table": "Pay frequency (U.S. DOL table)",
    "pay_frequency_state_rule": "Pay frequency (state law)",
    "final_pay_discharge": "Final pay when fired or laid off",
    "final_pay_resignation": "Final pay when an employee quits",
    "wc_agency": "Workers' comp agency",
    "wc_monopolistic_state_fund": "Monopolistic state workers' comp fund",
    "staffing_or_peo_registration": "Staffing or PEO registration",
    "new_hire_reporting_deadline": "New hire reporting deadline",
    "new_hire_independent_contractor_reporting": "Independent contractor reporting",
}

def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))

def main():
    rows = read_rows(os.path.join(DATA, "facts.csv"))
    if os.path.isdir(API):
        shutil.rmtree(API)
    meta = {"name": "US Staffing Payroll Compliance Dataset", "version": build.VERSION, "built": build.BUILT,
            "license": "CC-BY-4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "publisher": "Catalyst Works", "homepage": "https://getcatalystworks.com/payroll-compliance",
            "disclaimer": "Reference information compiled from official government sources. Not legal or tax advice. Check the cited source before relying on any value."}
    by = defaultdict(list)
    for r in rows:
        by[r["jurisdiction"]].append(r)
    core = [f for _, f in CORE_FIELDS]
    juris = []
    for code, name in JURISDICTIONS.items():
        rs = by.get(code, [])
        ver = {r["field"] for r in rs if r["status"] == "verified" and r["value"]}
        lc = max((r["last_checked"] for r in rs), default="")
        juris.append({"code": code, "name": name, "slug": slug(name), "verified_core_fields": sum(f in ver for f in core),
                      "core_fields": len(core), "last_checked": lc, "url": f"{BASE_URL}/states/{code}.json",
                      "page": f"https://getcatalystworks.com/payroll-compliance/{slug(name)}"})
        dump(os.path.join(API, "states", f"{code}.json"), {"meta": dict(meta, jurisdiction=code, jurisdiction_name=name, last_checked=lc), "facts": rs})
    dump(os.path.join(API, "states", "US.json"), {"meta": dict(meta, jurisdiction="US", jurisdiction_name="United States (federal)"), "facts": by["US"]})
    dump(os.path.join(API, "jurisdictions.json"), {"meta": meta, "jurisdictions": juris})
    dump(os.path.join(API, "fields.json"), {"meta": meta, "columns": FIELDS, "fields": [{"field": k, "label": v, "core": k in core} for k, v in FIELD_LABELS.items()]})
    cmp_fields = core + ["total_new_employer_rate", "pay_frequency_state_rule"]
    compare = []
    for j in juris:
        cells = {}
        for r in by.get(j["code"], []):
            if r["field"] in cmp_fields and r["status"] == "verified" and r["value"] and r["field"] not in cells:
                cells[r["field"]] = {"value": r["value"], "source_url": r["source_url"], "last_checked": r["last_checked"], "id": r["id"]}
        compare.append({"code": j["code"], "name": j["name"], "slug": j["slug"], "cells": cells})
    dump(os.path.join(API, "compare.json"), {"meta": meta, "fields": cmp_fields, "labels": {k: FIELD_LABELS[k] for k in cmp_fields}, "states": compare})
    dump(os.path.join(API, "facts.json"), {"meta": dict(meta, row_count=len(rows)), "facts": rows})
    shutil.copy(os.path.join(DATA, "facts.csv"), os.path.join(API, "facts.csv"))
    shutil.copy(os.path.join(DATA, "compare.csv"), os.path.join(API, "compare.csv"))
    dump(os.path.join(API, "index.json"), {"meta": meta, "endpoints": {
        "jurisdictions": f"{BASE_URL}/jurisdictions.json", "state": f"{BASE_URL}/states/{{CODE}}.json",
        "federal": f"{BASE_URL}/states/US.json", "compare": f"{BASE_URL}/compare.json", "fields": f"{BASE_URL}/fields.json",
        "facts_json": f"{BASE_URL}/facts.json", "facts_csv": f"{BASE_URL}/facts.csv", "compare_csv": f"{BASE_URL}/compare.csv"},
        "notes": "Read-only static files. CORS open. Every fact carries source_url, evidence_quote and last_checked."})
    print(f"api files written to {API}: {sum(len(f) for _, _, f in os.walk(API))}")

if __name__ == "__main__":
    main()
