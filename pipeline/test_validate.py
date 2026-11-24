"""Self-test: the validator must reject bad rows. Run: python3 pipeline/test_validate.py"""
import csv, io, os, tempfile, contextlib
from common import FIELDS, DATA
import validate

def run_with(mutator):
    rows = list(csv.DictReader(open(os.path.join(DATA, "facts.csv"), encoding="utf-8")))
    mutator(rows)
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = validate.main(f.name)
    os.unlink(f.name)
    return code, buf.getvalue()

def first_verified(rows):
    return next(r for r in rows if r["status"] == "verified")

cases = {
    "non-government source": lambda rows: first_verified(rows).update(source_url="https://example.com/x"),
    "http source": lambda rows: first_verified(rows).update(source_url="http://www.dol.gov/x"),
    "missing last_checked": lambda rows: first_verified(rows).update(last_checked=""),
    "em dash": lambda rows: first_verified(rows).update(summary="a \u2014 b"),
    "blank without note": lambda rows: first_verified(rows).update(status="unverified_blank", value="", value_numeric="", notes=""),
    "verified without quote": lambda rows: first_verified(rows).update(evidence_quote=""),
}
assert run_with(lambda rows: None)[0] == 0, "clean dataset should pass"
for name, mut in cases.items():
    code, out = run_with(mut)
    assert code == 1, f"validator failed to catch: {name}\n{out}"
    print(f"ok: rejects {name}")
print("all validator self-tests passed")
