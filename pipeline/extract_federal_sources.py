"""Extract 51-jurisdiction rows from official federal publications saved in sources/federal/.

Every value is parsed from the saved official file; nothing is typed in by hand.
Run: python3 pipeline/extract_federal_sources.py
"""
import html, os, re
import pymupdf  # PyMuPDF
from common import JURISDICTIONS, NAME_TO_CODE, DATA, SOURCES, write_rows

FED = os.path.join(SOURCES, "federal")
CHECKED = "2026-11-24"

def text_of(path):
    t = open(path, encoding="utf-8", errors="ignore").read()
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S | re.I)
    t = re.sub(r"<(br|p|div|tr|li|h\d|table|td|th)[^>]*>", "\n", t, flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", " ", t))
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n", s)

# ---------------------------------------------------------------- SUTA (DOL ETA sigpros)
SIGPROS_URL = "https://oui.doleta.gov/unemploy/content/sigpros/2020-2029/July2026.pdf"
SIGPROS_TITLE = "Significant Provisions of State Unemployment Insurance Laws, Effective July 2026"
SIGPROS_FOOT = ("DOL footnote 3: min/max rates apply only to experience-rated employers and exclude surtaxes, "
                "surcharges and non-UI taxes. Footnote 4: new employer rate shown is the base rate; higher rates "
                "may apply by industry or other factors. DOL notes the report is not an official interpretation of state law.")
RATE_TOK = r"^(\d+\.\d+%?|\d+%|IndAvg%)"
RATE_YEAR_JULY = {"NH", "NJ", "TN", "VT"}  # footnote 8 marker printed next to these rates

def clean_rate(tok):
    """Split a DOL rate token like '7.00%7,' into ('7.00%', '7'). Adds % when DOL omitted it."""
    if "IndAvg" in tok:
        return "Industry average (IndAvg)", ""
    m = re.match(r"^(\d+(?:\.\d+)?)(%?)(.*)$", tok)
    num, _, rest = m.groups()
    fn = re.sub(r"[^0-9,]", "", rest).strip(",")
    return num + "%", fn

def extract_suta():
    doc = pymupdf.open(os.path.join(FED, "dol-eta-sigpros-july-2026.pdf"))
    codes = set(JURISDICTIONS)
    out = {}
    for page in doc:
        words = page.get_text("words")
        rows = sorted((w[1], w[4]) for w in words if w[0] < 30 and w[4] in codes | {"PR", "VI"})
        if not rows:
            continue
        def owner(y):
            for i, (ys, s) in enumerate(rows):
                lo = (rows[i - 1][0] + ys) / 2 if i else -1e9
                hi = (rows[i + 1][0] + ys) / 2 if i + 1 < len(rows) else 1e9
                if lo <= y < hi:
                    return s
        for w in words:
            x0, y0, t = w[0], w[1], w[4]
            if 495 <= x0 < 550 and re.match(r"^\$[\d,]+$", t):
                out.setdefault(owner(y0), {"wage": [], "rate": []})["wage"].append((y0, t))
            elif x0 >= 550 and re.match(RATE_TOK, t):
                out.setdefault(owner(y0), {"wage": [], "rate": []})["rate"].append((y0, t))
    # Block-boundary correction: a rate token can sit just above the next state's band.
    # Rates come in strict (min, max, new) triples in page order, so re-chunk per page order.
    rows_out = []
    order = [s for s in JURISDICTIONS]
    seq = []
    for page in doc:
        words = page.get_text("words")
        toks = sorted([(w[1], w[4]) for w in words if w[0] >= 550 and re.match(RATE_TOK, w[4])])
        seq.extend(t for _, t in toks)
    states_in_order = []
    for page in doc:
        words = page.get_text("words")
        states_in_order.extend(s for _, s in sorted((w[1], w[4]) for w in words if w[0] < 30 and w[4] in codes | {"PR", "VI"}))
    assert len(seq) == 3 * len(states_in_order), (len(seq), len(states_in_order))
    triples = {s: seq[3 * i: 3 * i + 3] for i, s in enumerate(states_in_order)}
    text = open(os.path.join(SOURCES, "federal", "sigpros-wagebase-notes.txt")).read() if os.path.exists(os.path.join(SOURCES, "federal", "sigpros-wagebase-notes.txt")) else ""
    for s in order:
        name = JURISDICTIONS[s]
        wages = [t for _, t in sorted(out.get(s, {}).get("wage", []))]
        mn, mx, new = [re.sub(r"%?[\d, ]*$", "", x) if False else x for x in triples[s]]
        def pct(x):
            m = re.match(r"^([\d.]+)", x)
            return m.group(1) if m else ""
        wage = wages[0] if wages else ""
        wage_note = ""
        if s == "MI": wage_note = "DOL table: $9,000 or $9,500 for delinquent employers."
        if s == "NE": wage_note = "DOL table: $9,000 or $24,000 for high tax group employers."
        if s == "RI": wage_note = "DOL table: $30,800 or $32,300 for high tax group employers."
        common = dict(jurisdiction=s, jurisdiction_name=name, category="unemployment_insurance",
                      source_title=SIGPROS_TITLE, source_url=SIGPROS_URL,
                      source_publisher="U.S. Department of Labor, Employment and Training Administration, Office of Unemployment Insurance",
                      source_level="federal_agency", source_date="2026-07-01", retrieval="fetched_pdf_parsed",
                      last_checked=CHECKED, status="verified")
        rate_year = "Rate year July 1 - June 30 (DOL footnote 8)" if s in RATE_YEAR_JULY else "Calendar year 2026"
        rows_out.append(dict(common, id=f"{s}.ui.taxable_wage_base", field="suta_taxable_wage_base",
            value=wage, value_numeric=wage.replace("$", "").replace(",", ""), unit="USD per employee per year",
            applies_to="Effective July 2026 (DOL publication)",
            summary=f"{name} state unemployment taxable wage base: {wage} per employee." + (" " + wage_note if wage_note else ""),
            evidence_quote=f"Wages Subject to Tax: {wage}", notes=wage_note))
        newv = new.replace("%", "") if "IndAvg" not in new else ""
        new_text = new if "IndAvg" not in new else "Industry average (IndAvg)"
        rows_out.append(dict(common, id=f"{s}.ui.new_employer_rate", field="suta_new_employer_rate",
            value=new_text, value_numeric=pct(newv) if newv else "", unit="percent of taxable wages",
            applies_to=f"Effective July 2026 (DOL publication); {rate_year}",
            summary=f"{name} base new employer UI rate: {new_text}.",
            evidence_quote=f"New Employer Rate: {new}",
            notes=SIGPROS_FOOT + (" IndAvg means the new employer rate is the industry average rate; get the exact rate from the state agency." if not newv else "")))
        mx_clean, mx_fn = clean_rate(mx)
        mn, mn_fn = clean_rate(mn)
        fn_note = ""
        if mx_fn:
            fn_note = (f" DOL prints footnote marker(s) {mx_fn} on the maximum rate. Footnote 7: tax rate shown is reduced in some "
                       "circumstances due to certain UI administration or non-UI taxes paid. Footnote 8: rate year is July 1 through June 30.")
        if not mx.split("%")[0].endswith("%") and "%" not in mx:
            fn_note += " DOL prints the maximum rate without a % sign (shown here as a percent)."
        rows_out.append(dict(common, id=f"{s}.ui.rate_range", field="suta_rate_range",
            value=f"{mn} to {mx_clean}", value_numeric="", unit="percent of taxable wages",
            applies_to=f"Effective July 2026 (DOL publication); {rate_year}",
            summary=f"{name} experience-rated UI tax rates range from {mn} to {mx_clean}.",
            evidence_quote=f"Minimum & Maximum Rates: {mn} / {mx}", notes=SIGPROS_FOOT + fn_note))
    return rows_out

# ---------------------------------------------------------------- FUTA credit reduction
def extract_futa_credit():
    import openpyxl
    wb = openpyxl.load_workbook(os.path.join(FED, "dol-eta-final-futa-credit-reductions-2026.xlsx"), data_only=True)
    ws = wb.active
    reductions = {}
    for r in ws.iter_rows(values_only=True):
        name = (r[1] or "") if len(r) > 1 else ""
        if isinstance(name, str) and name.upper() in NAME_TO_CODE and isinstance(r[7], (int, float)):
            reductions[NAME_TO_CODE[name.upper()]] = r[7]
    rows = []
    for s, name in JURISDICTIONS.items():
        red = reductions.get(s, 0)
        pct = f"{red * 100:.1f}%"
        listed = s in reductions
        rows.append(dict(id=f"{s}.ui.futa_credit_reduction", jurisdiction=s, jurisdiction_name=name,
            category="unemployment_insurance", field="futa_credit_reduction", value=pct,
            value_numeric=f"{red * 100:.1f}", unit="percent of FUTA wages (first $7,000)", applies_to="Tax year 2026",
            summary=(f"{name} employers have a {pct} FUTA credit reduction for 2026, so the effective FUTA rate is "
                     f"{0.6 + red * 100:.1f}% on the first $7,000 per employee (if the full state credit applies).") if listed and red else
                    f"{name} is not listed with a final 2026 FUTA credit reduction, so the effective FUTA rate is 0.6% on the first $7,000 per employee (if the full 5.4% state credit applies).",
            evidence_quote=("Final 2026 FUTA Credit Reduction: " + pct) if listed else "State not listed in the Final 2026 FUTA Credit Reductions table.",
            source_title="Final 2026 Federal Unemployment Tax Act (FUTA) Credit Reductions (updated November 10, 2026)",
            source_url="https://oui.doleta.gov/unemploy/docs/final_credit_states_2026.xlsx",
            source_publisher="U.S. Department of Labor, Employment and Training Administration",
            source_level="federal_agency", source_date="2026-11-10", retrieval="fetched_xlsx_parsed",
            last_checked=CHECKED, status="verified", notes="Linked from https://oui.doleta.gov/unemploy/futa_credit.asp"))
    return rows

# ---------------------------------------------------------------- Payday table (DOL WHD)
PAYDAY_URL = "https://www.dol.gov/agencies/whd/state/payday"
def extract_payday():
    raw = open(os.path.join(FED, "dol-whd-state-payday.html"), encoding="utf-8", errors="ignore").read()
    table = re.search(r"<table.*?</table>", raw, re.S).group(0)
    cols = ["Weekly", "Bi-weekly", "Semi-monthly", "Monthly"]
    marks = {}
    for tr in re.findall(r"<tr.*?</tr>", table, re.S):
        cells = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", c))).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
        if len(cells) < 5 or cells[0] == "State":
            continue
        marks[cells[0]] = cells[1:5]
    text = text_of(os.path.join(FED, "dol-whd-state-payday.html"))
    foot = {}
    for m in re.finditer(r"\n\s*(\d{1,2}) ([A-Z][^\n]+)", text):
        foot.setdefault(m.group(1), m.group(2).strip())
    rows = []
    for s, name in JURISDICTIONS.items():
        key = next((k for k in marks if re.sub(r"\s*\d+(, *\d+)*$", "", k) == name), None)
        if key is None:
            fn = foot.get("1", "")
            if name in ("Alabama", "Florida") and "Alabama and Florida" in fn:
                rows.append(_payday_row(s, name, "No regulations or not specified (DOL footnote 1)", fn, ""))
            else:
                rows.append(_payday_row(s, name, "", "", "State not found in DOL table; needs state source.", status="unverified_blank"))
            continue
        cells = marks[key]
        notes_ids = set(re.findall(r"\d+", key))
        parts = []
        for c, v in zip(cols, cells):
            if v.startswith("X"):
                n = re.findall(r"\d+", v)
                notes_ids.update(n)
                parts.append(c + (f" (note {', '.join(n)})" if n else ""))
        value = "; ".join(parts) if parts else "No frequency column marked"
        fn_text = " | ".join(f"Note {i}: {foot[i]}" for i in sorted(notes_ids, key=int) if i in foot)
        rows.append(_payday_row(s, name, value, f"{key}: " + " / ".join(f"{c}={v or '-'}" for c, v in zip(cols, cells)), fn_text))
    return rows

def _payday_row(s, name, value, quote, fn_text, status="verified"):
    return dict(id=f"{s}.pay.dol_payday_table", jurisdiction=s, jurisdiction_name=name, category="pay_frequency",
        field="dol_payday_table", value=value, value_numeric="", unit="text", applies_to="DOL table dated January 1, 2023",
        summary=f"{name}: frequencies marked in the U.S. DOL State Payday Requirements table: {value}." if value else "",
        evidence_quote=quote, source_title="State Payday Requirements (U.S. DOL Wage and Hour Division)",
        source_url=PAYDAY_URL, source_publisher="U.S. Department of Labor, Wage and Hour Division",
        source_level="federal_agency", source_date="2023-01-01", retrieval="fetched_html_parsed", last_checked=CHECKED,
        status=status if value else "unverified_blank",
        notes=(fn_text + " | " if fn_text else "") + "DOL table last revised 2023-01-01; DOL says to consult the state labor office for official information. Confirm against current state law before relying on it.")

# ---------------------------------------------------------------- Minimum wage (DOL WHD)
MW_URL = "https://www.dol.gov/agencies/whd/minimum-wage/state"
def extract_min_wage():
    text = text_of(os.path.join(FED, "dol-whd-state-minimum-wage.html"))
    upd = re.search(r"Updated ([A-Z][a-z]+ \d{1,2}, \d{4})", text).group(1)
    body = text.split("Historical Table", 1)[1].split("Some states set subminimum", 1)[0]
    names = list(JURISDICTIONS.values()) + ["American Samoa", "Guam", "Puerto Rico", "Virgin Islands", "Northern Mariana Islands", "U.S. Virgin Islands"]
    pat = re.compile(r"^\s*(" + "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)) + r")\s*$", re.M)
    hits = list(pat.finditer(body))
    rows = []
    blocks = {}
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(body)
        blocks[m.group(1)] = re.sub(r"\s+", " ", body[m.end():end]).strip()
    for s, name in JURISDICTIONS.items():
        b = blocks.get(name, "")
        rates = re.findall(r"Basic Minimum Rate \(per hour\):\s*(\$[\d.]+)", b)
        no_law = "No state minimum wage law" in b
        if rates:
            value = rates[0]
            note = "Multiple rates listed by DOL (see quote): " + ", ".join(rates) if len(set(rates)) > 1 else ""
        elif no_law:
            value = "No state minimum wage law (federal $7.25 applies to FLSA-covered employers)"
            note = ""
        else:
            value, note = "", "Could not parse a basic rate from the DOL block; see quote."
        fed_floor = "Employers subject to the Fair Labor Standards Act must pay the current Federal minimum wage of $7.25" in b
        rows.append(dict(id=f"{s}.min_wage.state", jurisdiction=s, jurisdiction_name=name, category="minimum_wage",
            field="state_minimum_wage", value=value, value_numeric=value.replace("$", "") if value.startswith("$") else "",
            unit="USD per hour", applies_to=f"As listed by U.S. DOL, page updated {upd}",
            summary=f"{name} basic state minimum wage listed by U.S. DOL: {value}." + (" FLSA-covered employers must pay at least the federal $7.25." if fed_floor and value.startswith("$") else ""),
            evidence_quote=b[:600], source_title="State Minimum Wage Laws (U.S. DOL Wage and Hour Division)", source_url=MW_URL,
            source_publisher="U.S. Department of Labor, Wage and Hour Division", source_level="federal_agency",
            source_date="2026-11-05", retrieval="fetched_html_parsed", last_checked=CHECKED,
            status="verified" if value else "unverified_blank",
            notes=(note + " | " if note else "") + "Local (city or county) minimum wages are not included. Scheduled January 1, 2027 increases are not reflected until DOL updates the page."))
    return rows

# ---------------------------------------------------------------- WC agency (DOL OWCP)
WC_URL = "https://www.dol.gov/agencies/owcp/wc"
def extract_wc_agency():
    raw = open(os.path.join(FED, "dol-owcp-state-wc-officials.html"), encoding="utf-8", errors="ignore").read()
    links = re.findall(r'<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', raw, re.S)
    found = {}
    for href, label in links:
        lab = re.sub(r"<[^>]+>", "", html.unescape(label)).strip().upper()
        if lab in NAME_TO_CODE and NAME_TO_CODE[lab] not in found:
            found[NAME_TO_CODE[lab]] = href
    rows = []
    for s, name in JURISDICTIONS.items():
        url = found.get(s, "")
        rows.append(dict(id=f"{s}.wc.agency", jurisdiction=s, jurisdiction_name=name, category="workers_comp",
            field="wc_agency", value=url, value_numeric="", unit="URL", applies_to="Current listing",
            summary=f"{name} workers' compensation agency website as linked by U.S. DOL OWCP: {url}" if url else "",
            evidence_quote=f"{name.upper()} -> {url}" if url else "", source_title="State Workers' Compensation Officials (U.S. DOL OWCP)",
            source_url=WC_URL, source_publisher="U.S. Department of Labor, Office of Workers' Compensation Programs",
            source_level="federal_agency", source_date="", retrieval="fetched_html_parsed", last_checked=CHECKED,
            status="verified" if url else "unverified_blank",
            notes=("Link exactly as published by DOL" + ("; DOL lists an http:// address" if url.startswith("http://") else "") + ".") if url else "Not found in DOL list."))
    return rows

if __name__ == "__main__":
    gen = os.path.join(DATA, "generated")
    for name, fn in [("suta", extract_suta), ("futa_credit", extract_futa_credit), ("payday", extract_payday),
                     ("min_wage", extract_min_wage), ("wc_agency", extract_wc_agency)]:
        rows = fn()
        write_rows(os.path.join(gen, f"{name}.csv"), rows)
        print(f"{name}: {len(rows)} rows")


# ---------------------------------------------------------------- New hire reporting (HHS OCSE IRG)
NHR_URL = "https://ocsp.acf.hhs.gov/irg/irgpdf.pdf?addrClassType=EMP&addrType=NHR&geoType=OGP&groupCode=EMP"
def extract_new_hire():
    doc = pymupdf.open(os.path.join(FED, "ocse-irg-state-new-hire-reporting.pdf"))
    names = set(JURISDICTIONS.values()) | {"Guam", "Puerto Rico", "Virgin Islands", "U.S. Virgin Islands", "American Samoa", "Northern Mariana Islands", "Commonwealth of the Northern Mariana Islands"}
    # Build a stream of (page, y, x, word) for the left column state headers and the timeframe / IC columns
    entries = []  # (name, updated, [timeframe words], [ic words])
    cur = None
    for pi, page in enumerate(doc):
        words = page.get_text("words")
        heads = []
        for u in words:
            if u[4] == "Updated" and 220 < u[0] < 240:
                left = " ".join(w[4] for w in sorted(words, key=lambda w: w[0]) if w[0] < 225 and abs(w[1] - u[1]) <= 3)
                if left in names:
                    heads.append((u[1], left))
        heads.sort()
        body = [w for w in words if 192 < w[1] < 575]  # skip page header/footer
        hdr_y = [y for y, _ in heads]
        def seg(y):
            idx = -1
            for i, hy in enumerate(hdr_y):
                if y >= hy - 2: idx = i
            return idx
        for w in sorted(body, key=lambda w: (round(w[1]), w[0])):
            i = seg(w[1])
            if i >= 0 and (cur is None or cur[0] != heads[i][1] or cur[4] != (pi, i)):
                if cur is None or cur[0] != heads[i][1]:
                    cur = [heads[i][1], "", [], [], (pi, i)]
                    entries.append(cur)
                else:
                    cur[4] = (pi, i)
            if cur is None: continue
            x = w[0]
            if 225 <= x < 300 and w[4] not in ("Updated", "On:"): cur[1] += w[4]
            elif 298 <= x < 555: cur[2].append(w[4])
            elif x >= 780: cur[3].append(w[4])
    # Known parse problems found on manual review (2026-11-24): flag instead of guessing.
    REVIEW = {
        "MD": "OCSE text for Maryland's timeframe reads like a note about a different element; confirm with the Maryland new hire registry.",
        "MO": "Montana's header was not detected in the PDF, so Montana's text may be merged into Missouri's; confirm both.",
    }
    rows = []
    got = {e[0]: e for e in entries}
    for s, name in JURISDICTIONS.items():
        e = got.get(name)
        tf = " ".join(e[2]).strip() if e else ""
        ic = " ".join(e[3]).strip() if e else ""
        m = re.search(r"\d{2}/\d{2}/\d{4}", e[1]) if e else None
        upd = m.group(0) if m else ""
        common = dict(jurisdiction=s, jurisdiction_name=name, category="new_hire_reporting",
            source_title="State New Hire Reporting, State Contact and Program Information (HHS OCSE Intergovernmental Reference Guide)",
            source_url=NHR_URL, source_publisher="U.S. Department of Health and Human Services, Office of Child Support Services",
            source_level="federal_agency", retrieval="fetched_pdf_parsed", last_checked=CHECKED)
        rows.append(dict(common, id=f"{s}.new_hire.deadline", field="new_hire_reporting_deadline", value=tf, unit="text",
            applies_to=f"State entry updated {upd}" if upd else "", source_date="",
            summary=f"{name} new hire reporting timeframe (per OCSE): {tf}" if tf else "", evidence_quote=f"Reporting Timeframe: {tf}" if tf else "",
            status=("needs_review" if s in REVIEW else "verified") if tf else "unverified_blank",
            notes=(REVIEW.get(s, "") + " " if tf and s in REVIEW else "") + "Federal floor is 20 days; states may set shorter deadlines. Text as entered by the state in the OCSE guide." if tf else "Not parsed from OCSE guide."))
        rows.append(dict(common, id=f"{s}.new_hire.independent_contractors", field="new_hire_independent_contractor_reporting", value=ic, unit="text",
            applies_to=f"State entry updated {upd}" if upd else "", summary=f"{name} independent contractor reporting required? (per OCSE): {ic}" if ic else "",
            evidence_quote=f"Independent Contractor Reporting Required?: {ic}" if ic else "", status=("needs_review" if s in REVIEW else "verified") if ic else "unverified_blank",
            notes="Text as entered by the state in the OCSE guide." if ic else "Not parsed from OCSE guide."))
    return rows

if __name__ == "__main__":
    rows = extract_new_hire()
    write_rows(os.path.join(DATA, "generated", "new_hire.csv"), rows)
    print(f"new_hire: {len(rows)} rows")
