

"""
CA Firm Audit & GST Reconciliation Dataset Generator
Generates ~25 statutory compliance documents used by CA firms for audit and reconciliation.

Document Categories:
  G  - GST Returns (GSTR-1, GSTR-3B, GSTR-2B)
  ITC- Input Tax Credit Reconciliation
  EW - e-Way Bill Records
  TDS- TDS / Form 26AS / AIS Statements
  AUD- Audit Workpapers & Trial Balance Extracts
"""

import sys, os, json, random, datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

try:
    import pymupdf as fitz
except ImportError:
    import fitz

# ── Output directory ──────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent.parent / "test_dataset"
CA_DIR     = BASE_DIR / "ca_gst_documents"
CA_DIR.mkdir(parents=True, exist_ok=True)

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY   = (0.06, 0.18, 0.38)
GREEN  = (0.04, 0.52, 0.30)
RED    = (0.75, 0.12, 0.12)
ORANGE = (0.85, 0.45, 0.05)
GREY   = (0.50, 0.50, 0.50)
BLACK  = (0.05, 0.05, 0.05)
WHITE  = (1.0,  1.0,  1.0)
CREAM  = (0.98, 0.97, 0.93)

# ── Helpers ───────────────────────────────────────────────────────────────────
def new_doc():
    doc  = fitz.open()
    page = doc.new_page(width=595, height=842)
    return doc, page

def rect(x0, y0, x1, y1): return fitz.Rect(x0, y0, x1, y1)

def fill_rect(page, r, color):
    page.draw_rect(r, color=None, fill=color, width=0)

def text(page, txt, x, y, size=9, color=BLACK, bold=False):
    font = "helv" if not bold else "hebo"
    page.insert_text((x, y), txt, fontsize=size, fontname=font, color=color)

def hline(page, y, x0=40, x1=555, color=GREY, width=0.5):
    page.draw_line((x0, y), (x1, y), color=color, width=width)

def header_bar(page, title, subtitle="", color=NAVY):
    fill_rect(page, rect(0, 0, 595, 60), color)
    text(page, title,    42, 24, size=14, color=WHITE, bold=True)
    text(page, subtitle, 42, 44, size=9,  color=(0.85,0.90,0.98))

def section_head(page, label, y, color=NAVY):
    fill_rect(page, rect(38, y-2, 557, y+13), color)
    text(page, label, 42, y+9, size=8.5, color=WHITE, bold=True)
    return y + 18

def table_row(page, cols, y, widths, bold=False, bg=None, color=BLACK):
    if bg:
        fill_rect(page, rect(38, y-2, 557, y+12), bg)
    x = 42
    for val, w in zip(cols, widths):
        text(page, str(val), x, y+9, size=8, color=color, bold=bold)
        x += w
    return y + 14

def footer(page, doc_id, page_no=1):
    hline(page, 820, color=GREY, width=0.3)
    text(page, f"Document ID: {doc_id}   |   Page {page_no}   |   Generated for audit purposes only",
         42, 830, size=7, color=GREY)

# ── Company master ────────────────────────────────────────────────────────────
FIRMS = [
    {"name": "Mehta Textiles Pvt Ltd",    "gstin": "27AAACM1234F1ZK", "pan": "AAACM1234F", "state": "Maharashtra"},
    {"name": "Sharma Electronics Ltd",    "gstin": "07AABCS5678G1ZP", "pan": "AABCS5678G", "state": "Delhi"},
    {"name": "Patel Pharma Pvt Ltd",      "gstin": "24AAECP9012H1ZQ", "pan": "AAECP9012H", "state": "Gujarat"},
    {"name": "Gupta Auto Components Ltd", "gstin": "08AACPG3456I1ZR", "pan": "AACPG3456I", "state": "Rajasthan"},
    {"name": "Krishnan IT Services Ltd",  "gstin": "33AAHCK7890J1ZS", "pan": "AAHCK7890J", "state": "Tamil Nadu"},
]
CA_FIRM = "M/s Kapadia & Associates, Chartered Accountants  |  ICAI Reg. 112345W  |  Mumbai"

MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
FY = "2024-25"

RANDOM = random.Random(42)   # deterministic seed

def fmt(n): return f"{n:,.2f}"

# ═════════════════════════════════════════════════════════════════════════════
#  DOCUMENT GENERATORS
# ═════════════════════════════════════════════════════════════════════════════

# ── G-01  GSTR-3B Tax Summary ─────────────────────────────────────────────────
def gen_gstr3b(firm, month, doc_id, inject_error=False):
    doc, page = new_doc()
    header_bar(page, "GSTR-3B  |  Monthly Tax Summary Return",
               f"FY {FY}  |  Period: {month} 2024  |  Filed on GST Portal", color=NAVY)

    text(page, f"Taxpayer:  {firm['name']}", 42, 76, bold=True)
    text(page, f"GSTIN:     {firm['gstin']}", 42, 90)
    text(page, f"PAN:       {firm['pan']}", 42, 104)
    text(page, f"State:     {firm['state']}", 300, 76)
    text(page, f"Return Period: {month} 2024", 300, 90)
    text(page, f"Status:    {'Filed' if not inject_error else 'Pending'}", 300, 104,
         color=GREEN if not inject_error else RED)

    y = section_head(page, "3.1  Outward Supplies (Taxable)", 122)

    taxable   = RANDOM.uniform(800000, 5000000)
    igst_out  = round(taxable * 0.18, 2)
    cgst_out  = round(taxable * 0.09, 2)
    sgst_out  = round(taxable * 0.09, 2)
    total_out = igst_out + cgst_out + sgst_out

    widths = [210, 90, 90, 90, 90]
    y = table_row(page, ["Nature", "Taxable Value (₹)", "IGST (₹)", "CGST (₹)", "SGST (₹)"],
                  y, widths, bold=True, bg=CREAM)
    y = table_row(page, ["Taxable Supplies (Other than zero rated)",
                          fmt(taxable), fmt(igst_out), fmt(cgst_out), fmt(sgst_out)], y, widths)
    y = table_row(page, ["Zero-rated supply (Export)", fmt(0), fmt(0), fmt(0), fmt(0)], y, widths)
    hline(page, y); y += 10

    y = section_head(page, "4.  ITC Available (Input Tax Credit)", y)

    itc_base  = round(taxable * RANDOM.uniform(0.30, 0.55), 2)
    if inject_error:
        itc_base = round(total_out * 1.15, 2)   # ITC > Tax – suspicious

    widths2 = [250, 100, 100, 100]
    y = table_row(page, ["ITC Head", "IGST (₹)", "CGST (₹)", "SGST (₹)"],
                  y, widths2, bold=True, bg=CREAM)
    igst_itc = round(itc_base * 0.40, 2)
    cgst_itc = round(itc_base * 0.30, 2)
    sgst_itc = round(itc_base * 0.30, 2)
    y = table_row(page, ["(A) Import of Goods",    fmt(igst_itc), fmt(0), fmt(0)], y, widths2)
    y = table_row(page, ["(B) Inward Supplies from ISD", fmt(0), fmt(cgst_itc), fmt(sgst_itc)], y, widths2)
    y = table_row(page, ["(C) All Other ITC",      fmt(igst_itc*0.5), fmt(cgst_itc*0.5), fmt(sgst_itc*0.5)], y, widths2)
    hline(page, y); y += 10

    y = section_head(page, "5.  Net Tax Payable", y)
    net_igst = round(igst_out - igst_itc - igst_itc*0.5, 2)
    net_cgst = round(cgst_out - cgst_itc - cgst_itc*0.5, 2)
    net_sgst = round(sgst_out - sgst_itc - sgst_itc*0.5, 2)

    widths3 = [300, 90, 90, 90]
    y = table_row(page, ["Tax Head", "IGST (₹)", "CGST (₹)", "SGST (₹)"], y, widths3, bold=True, bg=CREAM)
    y = table_row(page, ["Total Outward Tax",   fmt(igst_out), fmt(cgst_out), fmt(sgst_out)], y, widths3)
    y = table_row(page, ["(-) ITC Claimed",     fmt(igst_itc+igst_itc*0.5), fmt(cgst_itc+cgst_itc*0.5), fmt(sgst_itc+sgst_itc*0.5)], y, widths3)
    y = table_row(page, ["Net Tax Payable",     fmt(net_igst), fmt(net_cgst), fmt(net_sgst)], y, widths3,
                  bold=True, bg=CREAM if not inject_error else (1,0.9,0.9))

    if inject_error:
        text(page, "⚠ AUDIT FLAG: ITC claimed exceeds outward tax liability — possible over-claim",
             42, y+6, size=8, color=RED)
        y += 20

    text(page, f"Prepared by: {CA_FIRM}", 42, 790, size=7.5, color=GREY)
    footer(page, doc_id)
    return doc, doc_id

# ── G-02  GSTR-1 Outward Supplies Detail ─────────────────────────────────────
def gen_gstr1(firm, month, doc_id, inject_error=False):
    doc, page = new_doc()
    header_bar(page, "GSTR-1  |  Outward Supplies Return – B2B Detail",
               f"FY {FY}  |  Period: {month} 2024  |  Due: 11th of next month", color=(0.05, 0.35, 0.55))

    text(page, f"Supplier:  {firm['name']}", 42, 76, bold=True)
    text(page, f"GSTIN:     {firm['gstin']}", 42, 90)
    text(page, f"Period:    {month} 2024  |  FY {FY}", 300, 76)

    y = section_head(page, "B2B Invoices — Recipient-wise Summary", 112, color=(0.05, 0.35, 0.55))

    buyers = [
        {"name": "ABC Traders Pvt Ltd",    "gstin": "27AABCA1111B1ZT"},
        {"name": "XYZ Distributors Ltd",   "gstin": "29AABCX2222C1ZU"},
        {"name": "PQR Industries Pvt Ltd", "gstin": "06AABCP3333D1ZV"},
    ]

    widths = [130, 120, 70, 65, 65, 60]
    y = table_row(page, ["Recipient Name", "GSTIN", "Inv Value (₹)", "IGST (₹)", "CGST (₹)", "SGST (₹)"],
                  y, widths, bold=True, bg=CREAM)

    grand_taxable = 0
    grand_tax     = 0
    for i, b in enumerate(buyers):
        inv_val  = RANDOM.uniform(200000, 1500000)
        rate     = RANDOM.choice([0.05, 0.12, 0.18, 0.28])
        tax      = round(inv_val * rate / (1 + rate), 2)
        taxable  = round(inv_val - tax, 2)
        igst     = round(tax * 0.5, 2) if inject_error and i == 1 else round(tax, 2)
        cgst     = round(tax * 0.25, 2) if not inject_error else 0
        sgst     = round(tax * 0.25, 2) if not inject_error else 0
        grand_taxable += taxable; grand_tax += tax
        flag = " ← IGST/CGST split error" if inject_error and i == 1 else ""
        y = table_row(page, [b["name"], b["gstin"], fmt(inv_val), fmt(igst), fmt(cgst), fmt(sgst)],
                      y, widths, color=RED if flag else BLACK)
        if flag:
            text(page, flag, 42, y-4, size=7.5, color=RED)

    hline(page, y); y += 6
    y = table_row(page, ["TOTAL", "", fmt(grand_taxable+grand_tax), "", "", fmt(grand_tax)],
                  y, widths, bold=True, bg=CREAM)

    y = section_head(page, "HSN-wise Summary (Section 12)", y+10, color=(0.05, 0.35, 0.55))
    hsn_rows = [
        ("5208", "Cotton Fabrics",          "Nos", 500, 1200.00),
        ("8542", "Electronic Components",   "Pcs", 300, 8500.00),
        ("3004", "Pharmaceutical Products", "Pkgs",200, 2300.00),
    ]
    widths2 = [70, 160, 50, 60, 90, 90]
    y = table_row(page, ["HSN Code", "Description", "UoM", "Qty", "Taxable Value", "Tax Amount"],
                  y, widths2, bold=True, bg=CREAM)
    for hsn, desc, uom, qty, rate2 in hsn_rows:
        taxval = round(qty * rate2, 2)
        tax2   = round(taxval * 0.18, 2)
        y = table_row(page, [hsn, desc, uom, qty, fmt(taxval), fmt(tax2)], y, widths2)

    text(page, f"Prepared by: {CA_FIRM}", 42, 790, size=7.5, color=GREY)
    footer(page, doc_id)
    return doc, doc_id

# ── G-03  GSTR-2B vs Purchase Register ITC Reconciliation ────────────────────
def gen_gstr2b_recon(firm, month, doc_id, inject_error=False):
    doc, page = new_doc()
    header_bar(page, "GSTR-2B vs Purchase Register — ITC Reconciliation",
               f"FY {FY}  |  {month} 2024  |  Auto-drafted Statement", color=(0.20, 0.40, 0.15))

    text(page, f"Recipient:  {firm['name']}   GSTIN: {firm['gstin']}", 42, 72, bold=True)
    text(page, f"Reconciliation as at: {month} 2024  |  FY {FY}", 42, 86)

    y = section_head(page, "Part A — ITC as per GSTR-2B (Auto-populated)", 104, color=(0.20, 0.40, 0.15))

    suppliers = [
        {"name": "Vendor Alpha Pvt Ltd",  "gstin": "27AABCV1111A1ZA"},
        {"name": "Beta Supplies Ltd",     "gstin": "07AABCB2222B1ZB"},
        {"name": "Gamma Traders Pvt Ltd", "gstin": "29AABCG3333C1ZC"},
        {"name": "Delta Imports Ltd",     "gstin": "06AABCD4444D1ZD"},
    ]

    widths = [130, 110, 65, 65, 65, 65]
    hdr = ["Supplier", "GSTIN", "IGST (₹)", "CGST (₹)", "SGST (₹)", "Total ITC (₹)"]
    y = table_row(page, hdr, y, widths, bold=True, bg=CREAM)

    itc_2b = []
    for s in suppliers:
        igst = round(RANDOM.uniform(20000, 150000), 2)
        cgst = round(RANDOM.uniform(10000,  80000), 2)
        sgst = cgst
        total = igst + cgst + sgst
        itc_2b.append({"name": s["name"], "gstin": s["gstin"],
                        "igst": igst, "cgst": cgst, "sgst": sgst, "total": total})
        y = table_row(page, [s["name"], s["gstin"], fmt(igst), fmt(cgst), fmt(sgst), fmt(total)],
                      y, widths)
    hline(page, y); y += 4
    tot2b = sum(r["total"] for r in itc_2b)
    y = table_row(page, ["TOTAL 2B", "", "", "", "", fmt(tot2b)], y, widths, bold=True, bg=CREAM)

    y = section_head(page, "Part B — ITC as per Purchase Register (Books)", y+10, color=(0.20, 0.40, 0.15))
    y = table_row(page, hdr, y, widths, bold=True, bg=CREAM)

    itc_pr = []
    for i, s in enumerate(suppliers):
        # Inject a mismatch in row 2
        variance = RANDOM.uniform(-5000, 5000) if inject_error and i == 2 else 0
        igst = round(itc_2b[i]["igst"] + variance, 2)
        cgst = itc_2b[i]["cgst"]
        sgst = cgst
        total = igst + cgst + sgst
        itc_pr.append(total)
        flag_color = RED if abs(variance) > 1 else BLACK
        y = table_row(page, [s["name"], s["gstin"], fmt(igst), fmt(cgst), fmt(sgst), fmt(total)],
                      y, widths, color=flag_color)
    hline(page, y); y += 4
    tot_pr = sum(itc_pr)
    y = table_row(page, ["TOTAL PR", "", "", "", "", fmt(tot_pr)], y, widths, bold=True, bg=CREAM)

    y = section_head(page, "Part C — Reconciliation Summary & Audit Observations", y+10, color=(0.20, 0.40, 0.15))
    diff = round(tot2b - tot_pr, 2)
    widths3 = [300, 200]
    y = table_row(page, ["Total ITC as per GSTR-2B",        fmt(tot2b)],  y, widths3)
    y = table_row(page, ["Total ITC as per Purchase Reg",   fmt(tot_pr)], y, widths3)
    diff_color = RED if abs(diff) > 100 else GREEN
    y = table_row(page, ["Difference (2B – PR)",            fmt(diff)],   y, widths3, color=diff_color)
    y += 8

    if inject_error and abs(diff) > 100:
        text(page, f"⚠ AUDIT FLAG: ITC mismatch of ₹{fmt(diff)} — investigate Vendor Gamma billing discrepancy",
             42, y, size=8, color=RED); y += 14
    else:
        text(page, "✓ ITC Reconciled — No material difference", 42, y, size=8, color=GREEN); y += 14

    text(page, f"Reviewed by: {CA_FIRM}", 42, 790, size=7.5, color=GREY)
    footer(page, doc_id)
    return doc, doc_id

# ── EW-01  e-Way Bill Register ────────────────────────────────────────────────
def gen_eway_bill_register(firm, month, doc_id, inject_error=False):
    doc, page = new_doc()
    header_bar(page, "e-Way Bill Register — Monthly Summary",
               f"FY {FY}  |  Period: {month} 2024  |  Rule 138 Compliance", color=(0.50, 0.20, 0.05))

    text(page, f"Taxpayer:  {firm['name']}   GSTIN: {firm['gstin']}", 42, 72, bold=True)

    y = section_head(page, "Outward Movement — e-Way Bills Generated", 92, color=(0.50, 0.20, 0.05))

    widths = [85, 80, 80, 90, 65, 65, 65]
    y = table_row(page, ["EWB No.", "Invoice No.", "Invoice Date", "Consignee", "Value (₹)", "Distance", "Validity"],
                  y, widths, bold=True, bg=CREAM)

    bills = []
    base_date = datetime.date(2024, 10 if month == "Oct" else 4, 1)
    for i in range(8):
        ewb_no  = f"EWB{RANDOM.randint(100000000, 999999999)}"
        inv_no  = f"INV-{firm['name'][:3].upper()}-{RANDOM.randint(1000,9999)}"
        inv_dt  = base_date + datetime.timedelta(days=RANDOM.randint(0, 28))
        value   = round(RANDOM.uniform(60000, 800000), 2)
        dist    = RANDOM.randint(50, 800)
        valid   = "1 Day" if dist <= 100 else f"{dist//200+1} Days"
        consign = RANDOM.choice(["Mumbai", "Delhi", "Chennai", "Kolkata", "Ahmedabad"])
        expired = inject_error and i == 3   # inject one expired EWB
        bills.append({"ewb": ewb_no, "inv": inv_no, "date": inv_dt.strftime("%d/%m/%Y"),
                       "consign": consign, "value": value, "dist": dist, "valid": valid, "expired": expired})
        color = RED if expired else BLACK
        suffix = " [EXPIRED]" if expired else ""
        y = table_row(page, [ewb_no, inv_no, inv_dt.strftime("%d/%m/%Y"),
                               consign, fmt(value), f"{dist} km", valid+suffix],
                      y, widths, color=color)

    hline(page, y); y += 8
    total_val = sum(b["value"] for b in bills)
    y = table_row(page, ["TOTAL", "", "", "", fmt(total_val), "", ""], y, widths, bold=True)

    y = section_head(page, "Compliance Analysis", y+10, color=(0.50, 0.20, 0.05))
    text(page, f"Total EWBs Generated: {len(bills)}", 42, y); y += 14
    text(page, f"Total Consignment Value: ₹ {fmt(total_val)}", 42, y); y += 14
    expired_count = sum(1 for b in bills if b["expired"])
    if expired_count:
        text(page, f"⚠ AUDIT FLAG: {expired_count} EWB(s) expired during transit — verify penalty applicability u/s 129",
             42, y, size=8, color=RED); y += 14
    else:
        text(page, "✓ All EWBs valid for stated consignment period", 42, y, size=8, color=GREEN)

    text(page, f"Compiled by: {CA_FIRM}", 42, 790, size=7.5, color=GREY)
    footer(page, doc_id)
    return doc, doc_id

# ── TDS-01  Form 26AS TDS Credit Statement ───────────────────────────────────
def gen_form26as(firm, doc_id, inject_error=False):
    doc, page = new_doc()
    header_bar(page, "Form 26AS  |  Annual Tax Credit Statement",
               f"FY {FY}  |  PAN: {firm['pan']}  |  Income Tax Dept.", color=(0.30, 0.05, 0.50))

    text(page, f"Taxpayer Name: {firm['name']}", 42, 72, bold=True)
    text(page, f"PAN:           {firm['pan']}", 42, 86)
    text(page, f"Assessment Year: 2025-26  |  FY {FY}", 300, 72)
    text(page, "Source: TRACES Portal (traces.gov.in)", 300, 86, color=GREY)

    y = section_head(page, "Part A — TDS on Salary & Professional Receipts (Sec 192/194J)", 104, color=(0.30, 0.05, 0.50))
    widths = [90, 120, 90, 80, 80, 70]
    y = table_row(page, ["TAN", "Deductor Name", "Quarter", "Gross Amt (₹)", "TDS (₹)", "Status"],
                  y, widths, bold=True, bg=CREAM)
    tds_records = [
        ("MUMM12345B", "Client Alpha Ltd",    "Q1", 500000, 50000, "Booked"),
        ("DELB98765C", "Beta Services Pvt Ltd","Q2",320000, 32000, "Booked"),
        ("CHEC11111D", "Gamma Corp Ltd",       "Q3", 180000, 18000, "Unmatched" if inject_error else "Booked"),
        ("AHMD22222E", "Delta Consulting",     "Q4", 250000, 25000, "Booked"),
    ]
    total_gross = 0; total_tds = 0
    for tan, name, qtr, gross, tds, status in tds_records:
        flag = status == "Unmatched"
        total_gross += gross; total_tds += tds
        y = table_row(page, [tan, name, qtr, fmt(gross), fmt(tds), status],
                      y, widths, color=RED if flag else BLACK)
    hline(page, y); y += 4
    y = table_row(page, ["", "TOTAL", "", fmt(total_gross), fmt(total_tds), ""],
                  y, widths, bold=True, bg=CREAM)

    y = section_head(page, "Part B — TDS on Interest (Sec 194A)", y+10, color=(0.30, 0.05, 0.50))
    interest_tds = RANDOM.uniform(5000, 40000)
    text(page, f"Interest Income (FDs): ₹{fmt(RANDOM.uniform(50000,400000))}   TDS Deducted: ₹{fmt(interest_tds)}", 42, y+8); y += 22

    y = section_head(page, "Part C — Advance Tax & Self Assessment Tax", y+6, color=(0.30, 0.05, 0.50))
    adv_tax = RANDOM.uniform(100000, 500000)
    text(page, f"Advance Tax Paid:          ₹{fmt(adv_tax)}", 42, y+8); y += 16
    text(page, f"Self Assessment Tax Paid:  ₹{fmt(RANDOM.uniform(10000, 80000))}", 42, y+4); y += 20

    y = section_head(page, "Reconciliation with Books of Account", y+6, color=(0.30, 0.05, 0.50))
    if inject_error:
        text(page, "⚠ AUDIT FLAG: Q3 TDS (₹18,000) from Gamma Corp unmatched — deductor may not have deposited",
             42, y+8, size=8, color=RED); y += 22
        text(page, "   Action: Issue Form 15G/15H or follow up with deductor for correction", 42, y, size=8, color=ORANGE)
    else:
        text(page, "✓ All TDS credits matched with Form 26AS — no unmatched entries", 42, y+8, size=8, color=GREEN)

    text(page, f"Verified by: {CA_FIRM}", 42, 790, size=7.5, color=GREY)
    footer(page, doc_id)
    return doc, doc_id

# ── TDS-02  TDS Certificate (Form 16A) ───────────────────────────────────────
def gen_form16a(firm, deductor, doc_id, inject_error=False):
    doc, page = new_doc()
    header_bar(page, "Form 16A  |  TDS Certificate (Non-Salary)",
               f"u/s 203 of IT Act 1961  |  FY {FY}  |  AY 2025-26", color=(0.35, 0.05, 0.45))

    text(page, "DEDUCTOR DETAILS", 42, 75, bold=True, size=9)
    text(page, f"Name:   {deductor['name']}", 42, 89)
    text(page, f"TAN:    {deductor['tan']}", 42, 103)
    text(page, f"PAN:    {deductor['pan']}", 42, 117)
    text(page, f"Address: {deductor['address']}", 42, 131)

    hline(page, 146)
    text(page, "DEDUCTEE DETAILS", 42, 158, bold=True, size=9)
    text(page, f"Name:   {firm['name']}", 42, 172)
    text(page, f"PAN:    {firm['pan']}", 42, 186)

    y = section_head(page, "Details of Tax Deducted & Deposited", 204, color=(0.35, 0.05, 0.45))

    quarters = [
        ("Q1 (Apr–Jun 2024)", RANDOM.uniform(30000, 150000)),
        ("Q2 (Jul–Sep 2024)", RANDOM.uniform(30000, 150000)),
        ("Q3 (Oct–Dec 2024)", RANDOM.uniform(30000, 150000)),
        ("Q4 (Jan–Mar 2025)", RANDOM.uniform(30000, 150000)),
    ]
    if inject_error:
        quarters[1] = ("Q2 (Jul–Sep 2024) — NOT DEPOSITED", 0)

    widths = [180, 100, 100, 100]
    y = table_row(page, ["Quarter", "Gross Payment (₹)", "TDS Rate", "TDS Amount (₹)"],
                  y, widths, bold=True, bg=CREAM)
    total_gross = 0; total_tds = 0
    for qtr, gross in quarters:
        tds_amt = round(gross * 0.10, 2)
        total_gross += gross; total_tds += tds_amt
        flag = "NOT DEPOSITED" in qtr
        y = table_row(page, [qtr, fmt(gross), "10%", fmt(tds_amt) if not flag else "NIL"],
                      y, widths, color=RED if flag else BLACK)

    hline(page, y); y += 4
    y = table_row(page, ["TOTAL", fmt(total_gross), "", fmt(total_tds if not inject_error else total_tds*0.75)],
                  y, widths, bold=True, bg=CREAM)

    if inject_error:
        text(page, "⚠ AUDIT FLAG: Q2 TDS not deposited — interest u/s 201(1A) applicable @ 1.5% per month",
             42, y+10, size=8, color=RED)

    text(page, f"Certified by Deductor:    {deductor['name']}",   42, 750, size=8)
    text(page, f"Reviewed by CA:           {CA_FIRM}",            42, 764, size=7.5, color=GREY)
    footer(page, doc_id)
    return doc, doc_id

# ── AUD-01  Trial Balance Extract ────────────────────────────────────────────
def gen_trial_balance(firm, doc_id, inject_error=False):
    doc, page = new_doc()
    header_bar(page, "Trial Balance Extract",
               f"{firm['name']}  |  As at 31 March 2025  |  FY {FY}", color=(0.10, 0.30, 0.50))

    text(page, f"Entity: {firm['name']}   PAN: {firm['pan']}   State: {firm['state']}", 42, 72, bold=True)
    text(page, f"Prepared for Statutory Audit — FY {FY}", 42, 86)

    y = section_head(page, "Balance Sheet Heads", 104, color=(0.10, 0.30, 0.50))
    widths = [200, 90, 90, 90, 90]
    y = table_row(page, ["Account Head", "Dr (₹)", "Cr (₹)", "Net Dr (₹)", "Net Cr (₹)"],
                  y, widths, bold=True, bg=CREAM)

    accounts = [
        ("Share Capital",           0,    5000000,  0,       5000000),
        ("Reserves & Surplus",      0,    2500000,  0,       2500000),
        ("Bank Loans (Term)",       0,    3000000,  0,       3000000),
        ("Trade Payables",          0,    1800000,  0,       1800000),
        ("Fixed Assets (Gross)",    8500000, 0,     8500000, 0),
        ("Accumulated Depreciation",0,   2200000,  0,       2200000),
        ("Inventories",             2800000, 0,     2800000, 0),
        ("Trade Receivables",       3600000, 0,     3600000, 0),
        ("Cash & Bank Balances",    1200000, 0,     1200000, 0),
        ("GST Input Tax Credit",    450000,  0,      450000, 0),
        ("TDS Receivable",          125000,  0,      125000, 0),
        ("Revenue from Operations", 0,    18500000, 0,      18500000),
        ("Cost of Goods Sold",      12000000,0,    12000000,0),
        ("Employee Expenses",       2200000, 0,     2200000, 0),
        ("Admin & Other Expenses",  800000,  0,      800000, 0),
        ("Depreciation",            650000,  0,      650000, 0),
        ("Finance Costs",           380000,  0,      380000, 0),
    ]

    total_dr = 0; total_cr = 0
    for acc, dr, cr, net_dr, net_cr in accounts:
        total_dr += net_dr; total_cr += net_cr
        y = table_row(page, [acc, fmt(dr) if dr else "–", fmt(cr) if cr else "–",
                               fmt(net_dr) if net_dr else "–", fmt(net_cr) if net_cr else "–"],
                      y, widths)

    hline(page, y); y += 4
    if inject_error:
        # Inject imbalance
        total_dr += 50000
    y = table_row(page, ["TOTAL", fmt(total_dr), fmt(total_cr), fmt(total_dr), fmt(total_cr)],
                  y, widths, bold=True, bg=CREAM if not inject_error else (1,0.9,0.9))

    if inject_error:
        text(page, f"⚠ AUDIT FLAG: Trial Balance does not tally — Debit side exceeds Credit by ₹{fmt(50000)}",
             42, y+8, size=8, color=RED)

    text(page, f"Audited by: {CA_FIRM}", 42, 790, size=7.5, color=GREY)
    footer(page, doc_id)
    return doc, doc_id

# ── AUD-02  Audit Observation Memorandum ─────────────────────────────────────
def gen_audit_memo(firm, doc_id, findings):
    doc, page = new_doc()
    header_bar(page, "Audit Observation Memorandum",
               f"{firm['name']}  |  FY {FY}  |  Statutory Audit", color=(0.60, 0.20, 0.05))

    text(page, f"Entity:     {firm['name']}", 42, 74, bold=True)
    text(page, f"GSTIN:      {firm['gstin']}", 42, 88)
    text(page, f"PAN:        {firm['pan']}", 42, 102)
    text(page, f"Audit Date: {datetime.date(2025, 5, 15).strftime('%d %B %Y')}", 300, 74)
    text(page, f"Auditor:    {CA_FIRM}", 300, 88, size=7.5)

    y = section_head(page, "Observations & Findings", 122, color=(0.60, 0.20, 0.05))
    for i, (severity, area, observation, recommendation) in enumerate(findings, 1):
        sev_color = RED if severity == "High" else ORANGE if severity == "Medium" else GREEN
        text(page, f"Finding {i}  [{severity}]  |  Area: {area}", 42, y, size=9, bold=True, color=sev_color); y += 14
        # Wrap observation text
        words = observation.split()
        line = ""; lines = []
        for w in words:
            if len(line + " " + w) < 90: line += (" " if line else "") + w
            else: lines.append(line); line = w
        if line: lines.append(line)
        for ln in lines:
            text(page, ln, 50, y, size=8.5); y += 12
        text(page, f"Recommendation: {recommendation}", 50, y, size=8.5, color=(0.10, 0.35, 0.55)); y += 16
        hline(page, y, color=(0.85, 0.85, 0.85)); y += 8

    text(page, f"This memorandum is confidential and intended solely for management of {firm['name']}.",
         42, 790, size=7.5, color=GREY)
    footer(page, doc_id)
    return doc, doc_id

# ── AUD-03  GST Annual Return Reconciliation (GSTR-9 vs Books) ───────────────
def gen_gstr9_recon(firm, doc_id, inject_error=False):
    doc, page = new_doc()
    header_bar(page, "GSTR-9 Annual Return — Books vs Return Reconciliation",
               f"FY {FY}  |  Annual Audit Reconciliation  |  Sec 44 CGST Act", color=(0.05, 0.40, 0.35))

    text(page, f"Entity:  {firm['name']}   GSTIN: {firm['gstin']}", 42, 72, bold=True)
    text(page, f"FY {FY}  |  Due Date: 31 December 2025", 42, 86)

    y = section_head(page, "Turnover Reconciliation (Table 5 vs Audited Accounts)", 104, color=(0.05, 0.40, 0.35))

    turnover_books = RANDOM.uniform(15000000, 80000000)
    turnover_gstr1 = turnover_books + (RANDOM.uniform(-200000, 200000) if inject_error else 0)
    turnover_gstr3b = turnover_books + (RANDOM.uniform(-50000, 50000) if inject_error else 0)

    widths = [280, 120, 120]
    y = table_row(page, ["Particulars", "As per Books (₹)", "As per Return (₹)"],
                  y, widths, bold=True, bg=CREAM)
    rows = [
        ("Total Turnover (as per audited P&L)", turnover_books, turnover_books),
        ("Add: Advances (unreported in GSTR-1)", 0, 0),
        ("Less: Exempted/Nil rated supplies", 0, 0),
        ("Net Taxable Turnover",  turnover_books, turnover_gstr1),
    ]
    for label, bk, ret in rows:
        diff_flag = abs(bk - ret) > 10000
        y = table_row(page, [label, fmt(bk), fmt(ret)], y, widths,
                      color=RED if diff_flag else BLACK)

    y = section_head(page, "ITC Reconciliation (Table 8 — GSTR-2B vs GSTR-3B vs Books)", y+8, color=(0.05, 0.40, 0.35))
    itc_books  = round(turnover_books * RANDOM.uniform(0.08, 0.14), 2)
    itc_2b2    = itc_books + (RANDOM.uniform(-30000, 30000) if inject_error else 0)
    itc_3b2    = itc_books + (RANDOM.uniform(-10000, 10000) if inject_error else 0)
    y = table_row(page, ["Source", "ITC Amount (₹)", "Variance (₹)"], y, widths, bold=True, bg=CREAM)
    for src, val in [("ITC per Books", itc_books), ("ITC per GSTR-2B", itc_2b2), ("ITC per GSTR-3B", itc_3b2)]:
        var = round(val - itc_books, 2)
        y = table_row(page, [src, fmt(val), fmt(var)], y, widths, color=RED if abs(var) > 5000 else BLACK)

    y = section_head(page, "Auditor's Certificate & Observations", y+8, color=(0.05, 0.40, 0.35))
    if inject_error:
        text(page, "⚠ Material difference in turnover and ITC — management explanation required", 42, y+8, size=8.5, color=RED); y += 22
        text(page, "   Recommend filing GSTR-9C (Reconciliation Statement) with auditor certification", 42, y, size=8.5, color=ORANGE); y += 16
    else:
        text(page, "✓ Annual return reconciled with books — no material difference identified", 42, y+8, size=8.5, color=GREEN); y += 22

    text(page, f"Certified by: {CA_FIRM}", 42, 790, size=7.5, color=GREY)
    footer(page, doc_id)
    return doc, doc_id

# ── AUD-04  Cash Flow Statement ───────────────────────────────────────────────
def gen_cash_flow(firm, doc_id, inject_error=False):
    doc, page = new_doc()
    header_bar(page, "Cash Flow Statement (Indirect Method)",
               f"{firm['name']}  |  FY {FY}  |  u/s 2(40) Companies Act 2013", color=(0.15, 0.25, 0.50))

    text(page, f"Entity: {firm['name']}  |  PAN: {firm['pan']}", 42, 72, bold=True)

    y = section_head(page, "A. Cash Flow from Operating Activities", 90, color=(0.15, 0.25, 0.50))
    widths = [310, 120]
    y = table_row(page, ["Particulars", "Amount (₹)"], y, widths, bold=True, bg=CREAM)

    pat   = RANDOM.uniform(2000000, 8000000)
    depr  = RANDOM.uniform(400000, 1200000)
    wc    = RANDOM.uniform(-500000, 500000)
    cfo   = round(pat + depr + wc, 2)

    ops = [("Net Profit After Tax (PAT)", pat),
           ("Add: Depreciation & Amortisation", depr),
           ("Add/(Less): Working Capital Changes", wc),
           ("Net Cash from Operating Activities (A)", cfo)]
    for label, amt in ops:
        bold = label.startswith("Net Cash")
        y = table_row(page, [label, fmt(amt)], y, widths, bold=bold,
                      bg=CREAM if bold else None, color=RED if bold and amt < 0 else BLACK)

    y = section_head(page, "B. Cash Flow from Investing Activities", y+8, color=(0.15, 0.25, 0.50))
    capex  = -RANDOM.uniform(500000, 3000000)
    invest = RANDOM.uniform(-200000, 200000)
    cfi    = round(capex + invest, 2)
    for label, amt in [("Capital Expenditure (CAPEX)", capex),
                        ("Investments Net", invest),
                        ("Net Cash from Investing Activities (B)", cfi)]:
        bold = label.startswith("Net Cash")
        y = table_row(page, [label, fmt(amt)], y, widths, bold=bold,
                      bg=CREAM if bold else None, color=RED if amt < 0 and bold else BLACK)

    y = section_head(page, "C. Cash Flow from Financing Activities", y+8, color=(0.15, 0.25, 0.50))
    loan   = RANDOM.uniform(-500000, 1000000)
    div    = -RANDOM.uniform(100000, 500000)
    cff    = round(loan + div, 2)
    for label, amt in [("Net Borrowings", loan),
                        ("Dividends Paid", div),
                        ("Net Cash from Financing Activities (C)", cff)]:
        bold = label.startswith("Net Cash")
        y = table_row(page, [label, fmt(amt)], y, widths, bold=bold,
                      bg=CREAM if bold else None)

    net_cash = round(cfo + cfi + cff, 2)
    if inject_error:
        net_cash += 250000  # deliberate mismatch

    y = section_head(page, "D. Net Change in Cash & Bank Balances", y+8, color=(0.15, 0.25, 0.50))
    opening = RANDOM.uniform(200000, 800000)
    closing = round(opening + net_cash, 2)
    y = table_row(page, ["Net Cash Change (A+B+C)", fmt(net_cash)], y, widths, bold=True)
    y = table_row(page, ["Opening Balance",          fmt(opening)],  y, widths)
    y = table_row(page, ["Closing Balance",           fmt(closing)],  y, widths, bold=True, bg=CREAM)

    if inject_error:
        text(page, "⚠ AUDIT FLAG: Cash flow closing balance ≠ Trial Balance bank balance — investigate ₹2,50,000 difference",
             42, y+8, size=8, color=RED)

    text(page, f"Reviewed by: {CA_FIRM}", 42, 790, size=7.5, color=GREY)
    footer(page, doc_id)
    return doc, doc_id

# ═════════════════════════════════════════════════════════════════════════════
#  MANIFEST & RUNNER
# ═════════════════════════════════════════════════════════════════════════════
def save(doc, path):
    doc.save(str(path), garbage=4, deflate=True)
    doc.close()

def run():
    manifest = []
    counter  = [0]

    def next_id(prefix):
        counter[0] += 1
        return f"{prefix}-{counter[0]:03d}"

    deductors = [
        {"name": "Alpha Corp Ltd",   "tan": "MUMM55555F", "pan": "AABCA5555F",
         "address": "123 BKC, Mumbai 400051"},
        {"name": "Beta Holdings Ltd","tan": "DELB66666G", "pan": "AABCB6666G",
         "address": "45 Connaught Place, New Delhi 110001"},
    ]

    audit_findings = [
        ("High",   "GST",     "ITC of ₹4,50,000 claimed on blocked credits (Section 17(5)) — ineligible",
                               "Reverse ITC immediately and pay with 24% interest"),
        ("Medium", "TDS",     "TDS not deducted on rent payments exceeding ₹2,40,000 (Section 194-I)",
                               "Deduct TDS @ 10% on all future rent and deposit pending TDS with interest"),
        ("Low",    "Payroll", "Leave encashment provision not made for FY 2024-25",
                               "Provide for leave encashment liability as per actuarial valuation"),
        ("High",   "Revenue", "Revenue recognized on dispatch basis instead of transfer of control — Ind AS 115",
                               "Restate revenue for period between dispatch and delivery for long-transit items"),
    ]

    months_sample = ["Apr", "Jul", "Oct", "Jan"]
    firms_sample  = FIRMS[:3]

    print("Generating CA Firm Audit & GST Reconciliation Dataset...")
    print("=" * 60)

    # ── Batch G: GSTR-3B (3 firms × 2 months) ──
    for firm in firms_sample[:2]:
        for month in ["Apr", "Oct"]:
            did = next_id("G3B")
            doc, _ = gen_gstr3b(firm, month, did, inject_error=False)
            fp = CA_DIR / f"{did}_gstr3b_{firm['name'][:10].replace(' ','_')}_{month}.pdf"
            save(doc, fp)
            manifest.append({"doc_id": did, "type": "GSTR-3B", "firm": firm['name'],
                              "period": month, "errors_injected": False, "path": str(fp)})
            print(f"  ✓ {did} GSTR-3B — {firm['name'][:20]} — {month}")

    # ── GSTR-3B with error ──
    did = next_id("G3B")
    doc, _ = gen_gstr3b(FIRMS[2], "Jul", did, inject_error=True)
    fp = CA_DIR / f"{did}_gstr3b_ERROR_{FIRMS[2]['name'][:10].replace(' ','_')}.pdf"
    save(doc, fp); manifest.append({"doc_id": did, "type": "GSTR-3B", "firm": FIRMS[2]['name'],
                                     "period": "Jul", "errors_injected": True,
                                     "error_type": "ITC_over_claim", "path": str(fp)})
    print(f"  ✓ {did} GSTR-3B [ERROR: ITC over-claim] — {FIRMS[2]['name'][:20]}")

    # ── Batch G: GSTR-1 ──
    for firm in firms_sample:
        did = next_id("G1")
        doc, _ = gen_gstr1(firm, "Oct", did, inject_error=False)
        fp = CA_DIR / f"{did}_gstr1_{firm['name'][:10].replace(' ','_')}.pdf"
        save(doc, fp); manifest.append({"doc_id": did, "type": "GSTR-1", "firm": firm['name'],
                                         "period": "Oct", "errors_injected": False, "path": str(fp)})
        print(f"  ✓ {did} GSTR-1 — {firm['name'][:20]}")

    # ── GSTR-1 with IGST/CGST split error ──
    did = next_id("G1")
    doc, _ = gen_gstr1(FIRMS[3], "Jan", did, inject_error=True)
    fp = CA_DIR / f"{did}_gstr1_ERROR_{FIRMS[3]['name'][:10].replace(' ','_')}.pdf"
    save(doc, fp); manifest.append({"doc_id": did, "type": "GSTR-1", "firm": FIRMS[3]['name'],
                                     "period": "Jan", "errors_injected": True,
                                     "error_type": "IGST_CGST_split_error", "path": str(fp)})
    print(f"  ✓ {did} GSTR-1 [ERROR: IGST/CGST split] — {FIRMS[3]['name'][:20]}")

    # ── Batch ITC: GSTR-2B Reconciliation ──
    for firm in firms_sample:
        did = next_id("ITC")
        doc, _ = gen_gstr2b_recon(firm, "Oct", did, inject_error=False)
        fp = CA_DIR / f"{did}_gstr2b_recon_{firm['name'][:10].replace(' ','_')}.pdf"
        save(doc, fp); manifest.append({"doc_id": did, "type": "GSTR-2B_Recon", "firm": firm['name'],
                                         "period": "Oct", "errors_injected": False, "path": str(fp)})
        print(f"  ✓ {did} GSTR-2B Recon — {firm['name'][:20]}")

    # ── GSTR-2B Recon with mismatch ──
    did = next_id("ITC")
    doc, _ = gen_gstr2b_recon(FIRMS[4], "Jan", did, inject_error=True)
    fp = CA_DIR / f"{did}_gstr2b_recon_ERROR_{FIRMS[4]['name'][:10].replace(' ','_')}.pdf"
    save(doc, fp); manifest.append({"doc_id": did, "type": "GSTR-2B_Recon", "firm": FIRMS[4]['name'],
                                     "period": "Jan", "errors_injected": True,
                                     "error_type": "ITC_mismatch_vendor", "path": str(fp)})
    print(f"  ✓ {did} GSTR-2B Recon [ERROR: ITC mismatch] — {FIRMS[4]['name'][:20]}")

    # ── Batch EW: e-Way Bills ──
    for firm in firms_sample[:2]:
        did = next_id("EW")
        doc, _ = gen_eway_bill_register(firm, "Oct", did, inject_error=False)
        fp = CA_DIR / f"{did}_eway_{firm['name'][:10].replace(' ','_')}.pdf"
        save(doc, fp); manifest.append({"doc_id": did, "type": "eWay_Bill_Register", "firm": firm['name'],
                                         "period": "Oct", "errors_injected": False, "path": str(fp)})
        print(f"  ✓ {did} e-Way Bill Register — {firm['name'][:20]}")

    # ── e-Way with expired EWB ──
    did = next_id("EW")
    doc, _ = gen_eway_bill_register(FIRMS[2], "Jul", did, inject_error=True)
    fp = CA_DIR / f"{did}_eway_ERROR_{FIRMS[2]['name'][:10].replace(' ','_')}.pdf"
    save(doc, fp); manifest.append({"doc_id": did, "type": "eWay_Bill_Register", "firm": FIRMS[2]['name'],
                                     "period": "Jul", "errors_injected": True,
                                     "error_type": "expired_ewb_in_transit", "path": str(fp)})
    print(f"  ✓ {did} e-Way Register [ERROR: expired EWB] — {FIRMS[2]['name'][:20]}")

    # ── Batch TDS: Form 26AS ──
    for firm in FIRMS[:3]:
        did = next_id("TDS")
        inject = firm == FIRMS[2]
        doc, _ = gen_form26as(firm, did, inject_error=inject)
        fp = CA_DIR / f"{did}_form26as_{firm['name'][:10].replace(' ','_')}.pdf"
        save(doc, fp); manifest.append({"doc_id": did, "type": "Form_26AS", "firm": firm['name'],
                                         "errors_injected": inject,
                                         "error_type": "unmatched_TDS_Q3" if inject else None,
                                         "path": str(fp)})
        tag = " [ERROR: unmatched TDS]" if inject else ""
        print(f"  ✓ {did} Form 26AS{tag} — {firm['name'][:20]}")

    # ── Batch TDS: Form 16A ──
    for i, firm in enumerate(FIRMS[:2]):
        did = next_id("TDS")
        inject = i == 1
        doc, _ = gen_form16a(firm, deductors[i], did, inject_error=inject)
        fp = CA_DIR / f"{did}_form16a_{firm['name'][:10].replace(' ','_')}.pdf"
        save(doc, fp); manifest.append({"doc_id": did, "type": "Form_16A", "firm": firm['name'],
                                         "deductor": deductors[i]['name'],
                                         "errors_injected": inject,
                                         "error_type": "TDS_not_deposited_Q2" if inject else None,
                                         "path": str(fp)})
        tag = " [ERROR: TDS not deposited]" if inject else ""
        print(f"  ✓ {did} Form 16A{tag} — {firm['name'][:20]}")

    # ── Batch AUD: Trial Balance ──
    for firm in FIRMS[:3]:
        did = next_id("AUD")
        inject = firm == FIRMS[1]
        doc, _ = gen_trial_balance(firm, did, inject_error=inject)
        fp = CA_DIR / f"{did}_trial_balance_{firm['name'][:10].replace(' ','_')}.pdf"
        save(doc, fp); manifest.append({"doc_id": did, "type": "Trial_Balance", "firm": firm['name'],
                                         "errors_injected": inject,
                                         "error_type": "TB_does_not_tally" if inject else None,
                                         "path": str(fp)})
        tag = " [ERROR: tally mismatch]" if inject else ""
        print(f"  ✓ {did} Trial Balance{tag} — {firm['name'][:20]}")

    # ── AUD: Audit Observation Memo ──
    did = next_id("AUD")
    doc, _ = gen_audit_memo(FIRMS[0], did, audit_findings)
    fp = CA_DIR / f"{did}_audit_memo_{FIRMS[0]['name'][:10].replace(' ','_')}.pdf"
    save(doc, fp); manifest.append({"doc_id": did, "type": "Audit_Memo", "firm": FIRMS[0]['name'],
                                     "errors_injected": False, "path": str(fp)})
    print(f"  ✓ {did} Audit Observation Memo — {FIRMS[0]['name'][:20]}")

    # ── AUD: GSTR-9 Reconciliation ──
    for firm in FIRMS[:2]:
        did = next_id("AUD")
        inject = firm == FIRMS[1]
        doc, _ = gen_gstr9_recon(firm, did, inject_error=inject)
        fp = CA_DIR / f"{did}_gstr9_recon_{firm['name'][:10].replace(' ','_')}.pdf"
        save(doc, fp); manifest.append({"doc_id": did, "type": "GSTR-9_Recon", "firm": firm['name'],
                                         "errors_injected": inject,
                                         "error_type": "turnover_ITC_mismatch" if inject else None,
                                         "path": str(fp)})
        tag = " [ERROR: turnover/ITC mismatch]" if inject else ""
        print(f"  ✓ {did} GSTR-9 Annual Recon{tag} — {firm['name'][:20]}")

    # ── AUD: Cash Flow Statement ──
    for firm in FIRMS[:2]:
        did = next_id("AUD")
        inject = firm == FIRMS[1]
        doc, _ = gen_cash_flow(firm, did, inject_error=inject)
        fp = CA_DIR / f"{did}_cash_flow_{firm['name'][:10].replace(' ','_')}.pdf"
        save(doc, fp); manifest.append({"doc_id": did, "type": "Cash_Flow", "firm": firm['name'],
                                         "errors_injected": inject,
                                         "error_type": "cash_balance_mismatch" if inject else None,
                                         "path": str(fp)})
        tag = " [ERROR: cash mismatch]" if inject else ""
        print(f"  ✓ {did} Cash Flow Statement{tag} — {firm['name'][:20]}")

    # ── Save manifest ──
    manifest_path = CA_DIR / "ca_gst_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.datetime.now().isoformat(),
                   "total_documents": len(manifest),
                   "ca_firm": CA_FIRM,
                   "fiscal_year": FY,
                   "documents": manifest}, f, indent=2)

    print()
    print("=" * 60)
    print(f"✓ Total documents generated: {len(manifest)}")
    print(f"✓ Manifest saved: {manifest_path}")
    print(f"✓ Output directory: {CA_DIR}")
    print()

    # ── Summary table ──
    from collections import Counter
    by_type  = Counter(d["type"]           for d in manifest)
    err_cnt  = sum(1 for d in manifest if d["errors_injected"])
    clean_cnt = len(manifest) - err_cnt
    print(f"  Clean documents : {clean_cnt}")
    print(f"  Error documents : {err_cnt}")
    print()
    print("  Document type breakdown:")
    for dtype, cnt in sorted(by_type.items()):
        print(f"    {dtype:<22} {cnt}")

if __name__ == "__main__":
    run()
