"""Validate data/facts.csv. Exit 1 on any error.

Checks:
  - required columns present, ids unique, jurisdiction known
  - every non-blank row has an https source URL on an official domain (.gov, .us, or the allowlist below)
  - every row has last_checked as an ISO date, status in the allowed set
  - verified rows have a value and an evidence quote
  - blank rows carry a note explaining why
  - no em dash (U+2014) anywhere
"""
import csv, os, re, sys
from datetime import date
from urllib.parse import urlparse
from common import FIELDS, JURISDICTIONS, STATUS_VALUES, LEVELS, DATA

# Official government domains that do not end in .gov or .us
OFFICIAL_ALLOWLIST = {
    "workforcesafety.com",      # North Dakota Workforce Safety & Insurance (state agency)
}
EM_DASH = "\u2014"

def official(host):
    host = host.lower()
    if host.endswith(".gov") or host.endswith(".us") or host.endswith(".mil"):
        return True
    return any(host == d or host.endswith("." + d) for d in OFFICIAL_ALLOWLIST)

def main(path=os.path.join(DATA, "facts.csv")):
    errs, warns = [], []
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    missing = set(FIELDS) - set(rows[0].keys()) if rows else set(FIELDS)
    if missing:
        errs.append(f"missing columns: {sorted(missing)}")
    seen = set()
    for i, r in enumerate(rows, start=2):
        rid = r["id"]
        where = f"line {i} ({rid})"
        if rid in seen: errs.append(f"{where}: duplicate id")
        seen.add(rid)
        if r["jurisdiction"] not in JURISDICTIONS and r["jurisdiction"] != "US":
            errs.append(f"{where}: unknown jurisdiction {r['jurisdiction']}")
        if r["status"] not in STATUS_VALUES:
            errs.append(f"{where}: bad status {r['status']!r}")
        try:
            d = date.fromisoformat(r["last_checked"])
            if d > date.today(): errs.append(f"{where}: last_checked in the future")
        except ValueError:
            errs.append(f"{where}: last_checked not ISO date")
        for k, v in r.items():
            if v and EM_DASH in v: errs.append(f"{where}: em dash in {k}")
        if r["status"] == "unverified_blank":
            if r["value"]: errs.append(f"{where}: unverified_blank row must not carry a value")
            if not r["notes"]: errs.append(f"{where}: blank row needs a note explaining why")
            continue
        url = r["source_url"]
        u = urlparse(url)
        if u.scheme != "https": errs.append(f"{where}: source_url must be https: {url!r}")
        elif not official(u.hostname or ""): errs.append(f"{where}: source_url not an official government domain: {u.hostname}")
        if r["source_level"] not in LEVELS: errs.append(f"{where}: bad source_level {r['source_level']!r}")
        if not r["value"]: errs.append(f"{where}: verified/needs_review row without value")
        if r["status"] == "verified" and not r["evidence_quote"]: errs.append(f"{where}: verified row without evidence_quote")
        if not r["source_title"] or not r["source_publisher"]: errs.append(f"{where}: missing source title/publisher")
        if r["value_numeric"]:
            try: float(r["value_numeric"])
            except ValueError: errs.append(f"{where}: value_numeric not numeric")
        if r["value"].startswith("http://"): warns.append(f"{where}: value is an http:// link as published by the source")
    for e in errs: print("ERROR", e)
    print(f"checked {len(rows)} rows: {len(errs)} errors, {len(warns)} warnings (http links as published)")
    return 1 if errs else 0

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
