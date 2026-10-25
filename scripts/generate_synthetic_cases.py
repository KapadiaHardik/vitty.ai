"""
Synthetic Invoice & PO Dataset Generator for Vitty.ai Phase 2 Verification Engine.
Generates 60 real, styled PDF invoices and purchase orders spanning:
- Category A: Clean Compliant Cases (Control Group)
- Category B: Tax & Arithmetic Discrepancies
- Category C: Missing Mandatory Fields
- Category D: 2-Way PO vs Invoice Mismatches
- Category E: Duplicate Invoice Detection
- Category F: Diverse Currencies & Multi-Line Invoices
"""

import os
import json
import pymupdf

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test_dataset"))
INVOICE_DIR = os.path.join(OUTPUT_DIR, "invoices")
PO_DIR = os.path.join(OUTPUT_DIR, "purchase_orders")

os.makedirs(INVOICE_DIR, exist_ok=True)
os.makedirs(PO_DIR, exist_ok=True)


def draw_header_bar(page, title="TAX INVOICE", is_invoice=True):
    # Top banner
    color = (0.2, 0.35, 0.65) if is_invoice else (0.15, 0.5, 0.35)
    page.draw_rect(pymupdf.Rect(40, 35, 555, 75), color=color, fill=color)
    page.insert_text((55, 62), title, fontsize=18, fontname="helv", color=(1, 1, 1))
    badge = "ORIGINAL FOR RECIPIENT" if is_invoice else "COMMERCIAL CONTRACT"
    page.insert_text((400, 60), badge, fontsize=9, fontname="helv", color=(0.9, 0.9, 0.9))


def draw_meta_box(page, meta_dict, x0=40, y0=90, width=250, height=90, title="Document Details"):
    page.draw_rect(pymupdf.Rect(x0, y0, x0 + width, y0 + height), color=(0.85, 0.88, 0.92), fill=(0.98, 0.98, 0.99))
    page.insert_text((x0 + 10, y0 + 18), title.upper(), fontsize=9, fontname="helv", color=(0.3, 0.4, 0.5))
    y = y0 + 34
    for k, v in meta_dict.items():
        if v is not None:
            text = f"{k}: {v}"
            page.insert_text((x0 + 10, y), text, fontsize=9, fontname="helv", color=(0.1, 0.15, 0.2))
            y += 14


def draw_table(page, line_items, currency="INR", y_start=200):
    # Table header
    header_rect = pymupdf.Rect(40, y_start, 555, y_start + 24)
    page.draw_rect(header_rect, color=(0.85, 0.88, 0.92), fill=(0.92, 0.94, 0.97))
    page.insert_text((50, y_start + 16), "Description", fontsize=9, fontname="helv", color=(0.2, 0.25, 0.3))
    page.insert_text((320, y_start + 16), "Qty", fontsize=9, fontname="helv", color=(0.2, 0.25, 0.3))
    page.insert_text((390, y_start + 16), f"Unit Rate ({currency})", fontsize=9, fontname="helv", color=(0.2, 0.25, 0.3))
    page.insert_text((480, y_start + 16), f"Amount ({currency})", fontsize=9, fontname="helv", color=(0.2, 0.25, 0.3))

    y = y_start + 24
    for item in line_items:
        page.draw_line((40, y + 24), (555, y + 24), color=(0.9, 0.92, 0.95), width=0.5)
        page.insert_text((50, y + 16), str(item.get("description", "-")), fontsize=8.5, fontname="helv", color=(0.15, 0.2, 0.25))
        page.insert_text((325, y + 16), str(item.get("qty", "-")), fontsize=8.5, fontname="helv", color=(0.15, 0.2, 0.25))
        page.insert_text((395, y + 16), f"{item.get('rate', 0):,.2f}", fontsize=8.5, fontname="helv", color=(0.15, 0.2, 0.25))
        page.insert_text((485, y + 16), f"{item.get('amount', 0):,.2f}", fontsize=8.5, fontname="helv", color=(0.15, 0.2, 0.25))
        y += 24

    return y + 15


def draw_totals(page, subtotal, tax, total, currency="INR", y_start=340, omit_total=False):
    x0 = 340
    width = 215
    y = y_start

    # Subtotal
    if subtotal is not None:
        page.insert_text((x0, y + 14), "Subtotal:", fontsize=9.5, fontname="helv", color=(0.3, 0.35, 0.4))
        page.insert_text((x0 + 110, y + 14), f"{currency} {subtotal:,.2f}", fontsize=9.5, fontname="helv", color=(0.1, 0.15, 0.2))
        y += 20

    # Tax
    if tax is not None:
        page.insert_text((x0, y + 14), "GST / Tax:", fontsize=9.5, fontname="helv", color=(0.3, 0.35, 0.4))
        page.insert_text((x0 + 110, y + 14), f"{currency} {tax:,.2f}", fontsize=9.5, fontname="helv", color=(0.1, 0.15, 0.2))
        y += 20

    # Grand Total
    if not omit_total and total is not None:
        page.draw_rect(pymupdf.Rect(x0 - 10, y + 4, 555, y + 32), color=(0.85, 0.88, 0.95), fill=(0.94, 0.96, 1.0))
        page.insert_text((x0, y + 22), "Grand Total:", fontsize=11, fontname="helv", color=(0.1, 0.2, 0.5))
        page.insert_text((x0 + 105, y + 22), f"{currency} {total:,.2f}", fontsize=11, fontname="helv", color=(0.1, 0.2, 0.5))
        y += 36

    # Footer note
    page.insert_text((40, 780), "This document was generated for automated audit verification. Certified digital record.", fontsize=8, fontname="helv", color=(0.6, 0.65, 0.7))


def create_invoice_pdf(file_path, data):
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)

    title = data.get("title", "TAX INVOICE")
    draw_header_bar(page, title=title, is_invoice=True)

    supplier = data.get("supplier_name")
    meta_supplier = {}
    if supplier:
        meta_supplier["Supplier"] = supplier
        meta_supplier["GSTIN"] = data.get("gstin", "27AABCU9603R1ZM")
        meta_supplier["Address"] = "Mumbai, Maharashtra, India"

    draw_meta_box(page, meta_supplier, x0=40, y0=85, width=245, height=85, title="Vendor Information")

    meta_inv = {}
    if data.get("invoice_number"):
        meta_inv["Invoice No"] = data["invoice_number"]
    if data.get("invoice_date"):
        meta_inv["Date"] = data["invoice_date"]
    if data.get("po_number"):
        meta_inv["PO Reference"] = data["po_number"]
    meta_inv["Payment Terms"] = "Net 30 Days"

    draw_meta_box(page, meta_inv, x0=310, y0=85, width=245, height=85, title="Invoice Reference")

    line_items = data.get("line_items", [])
    y_after_table = draw_table(page, line_items, currency=data.get("currency", "INR"), y_start=185)

    draw_totals(
        page,
        subtotal=data.get("subtotal_amount"),
        tax=data.get("tax_amount"),
        total=data.get("total_amount"),
        currency=data.get("currency", "INR"),
        y_start=y_after_table,
        omit_total=data.get("omit_total", False)
    )

    doc.save(file_path)
    doc.close()


def create_po_pdf(file_path, data):
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)

    draw_header_bar(page, title="PURCHASE ORDER", is_invoice=False)

    meta_buyer = {
        "Buyer": data.get("buyer_name", "Global Enterprise Corp"),
        "PO No": data.get("po_number", "PO-0000"),
        "PO Date": data.get("po_date", "2024-05-01"),
    }
    draw_meta_box(page, meta_buyer, x0=40, y0=85, width=245, height=85, title="Authorized Buyer Order")

    meta_supplier = {
        "Vendor": data.get("supplier_name", "Acme Vendor"),
        "Delivery Terms": "FOB Destination",
        "Authorized By": "Finance Dept - Audit Approved"
    }
    draw_meta_box(page, meta_supplier, x0=310, y0=85, width=245, height=85, title="Contracted Vendor")

    line_items = data.get("line_items", [])
    y_after_table = draw_table(page, line_items, currency=data.get("currency", "INR"), y_start=185)

    draw_totals(
        page,
        subtotal=data.get("subtotal_amount"),
        tax=data.get("tax_amount"),
        total=data.get("total_amount"),
        currency=data.get("currency", "INR"),
        y_start=y_after_table
    )

    doc.save(file_path)
    doc.close()


def generate_all_cases():
    test_cases = []

    # ==========================================
    # GROUP A: Clean Compliant Cases (12 cases)
    # ==========================================
    clean_pairs = [
        ("Acme Industrial Supplies", "INV-2024-001", "PO-9001", 10000.0, 1800.0, 11800.0, [("Machining Tools Set", 10, 1000.0, 10000.0)]),
        ("TechCore Solutions Ltd", "INV-2024-002", "PO-9002", 50000.0, 9000.0, 59000.0, [("Dedicated Cloud Server Hosting", 1, 50000.0, 50000.0)]),
        ("Apex Logistics LLP", "INV-2024-003", "PO-9003", 25000.0, 1250.0, 26250.0, [("Interstate Freight Logistics", 5, 5000.0, 25000.0)]),
        ("Zenith Office Systems", "INV-2024-004", "PO-9004", 42000.0, 7560.0, 49560.0, [("Ergonomic Mesh Task Chairs", 6, 7000.0, 42000.0)]),
        ("BrightStar Electricals", "INV-2024-005", "PO-9005", 15500.0, 2790.0, 18290.0, [("Industrial LED High-Bay Lights", 10, 1550.0, 15500.0)]),
        ("Precision Tools India", "INV-2024-006", "PO-9006", 30000.0, 5400.0, 35400.0, [("Solid Carbide End Mills", 15, 2000.0, 30000.0)]),
    ]

    for idx, (supp, inv_no, po_no, sub, tax, tot, items) in enumerate(clean_pairs, 1):
        case_id = f"TC_{idx:02d}"
        inv_fn = f"{case_id}_INV_{supp.replace(' ', '_')}.pdf"
        po_fn = f"{case_id}_PO_{supp.replace(' ', '_')}.pdf"

        line_items = [{"description": it[0], "qty": it[1], "rate": it[2], "amount": it[3]} for it in items]

        create_invoice_pdf(
            os.path.join(INVOICE_DIR, inv_fn),
            {
                "supplier_name": supp,
                "invoice_number": inv_no,
                "invoice_date": f"2024-05-{idx:02d}",
                "po_number": po_no,
                "subtotal_amount": sub,
                "tax_amount": tax,
                "total_amount": tot,
                "line_items": line_items,
            }
        )

        create_po_pdf(
            os.path.join(PO_DIR, po_fn),
            {
                "supplier_name": supp,
                "po_number": po_no,
                "po_date": f"2024-04-2{idx}",
                "subtotal_amount": sub,
                "tax_amount": tax,
                "total_amount": tot,
                "line_items": line_items,
            }
        )

        test_cases.append({
            "case_id": case_id,
            "category": "A_CLEAN_COMPLIANT",
            "invoice_file": inv_fn,
            "po_file": po_fn,
            "has_po": True,
            "expected_findings_count": 0,
            "expected_findings": [],
            "description": f"Clean 2-way match for {supp} (zero findings expected)."
        })

    # Group A Standalone Clean Invoices (no PO)
    standalone_clean = [
        ("Global Horizon Consulting", "INV-2024-007", 75000.0, 13500.0, 88500.0, [("Financial Advisory & Audit Services", 1, 75000.0, 75000.0)]),
        ("Alpha Security Services", "INV-2024-008", 36000.0, 6480.0, 42480.0, [("Manned Guarding Services (Monthly)", 3, 12000.0, 36000.0)]),
        ("BlueWave Digital Media", "INV-2024-009", 60000.0, 10800.0, 70800.0, [("SEO & Content Marketing Retainer", 1, 60000.0, 60000.0)]),
        ("Silverline Facility Management", "INV-2024-010", 22000.0, 3960.0, 25960.0, [("Corporate Office Deep Cleaning", 2, 11000.0, 22000.0)]),
        ("CyberShield Infotech", "INV-2024-011", 18000.0, 3240.0, 21240.0, [("Endpoint Security Licenses (50 Users)", 50, 360.0, 18000.0)]),
        ("Prime Packaging Corp", "INV-2024-012", 14000.0, 1680.0, 15680.0, [("Heavy Duty Corrugated Boxes", 700, 20.0, 14000.0)]),
    ]

    for idx, (supp, inv_no, sub, tax, tot, items) in enumerate(standalone_clean, 7):
        case_id = f"TC_{idx:02d}"
        inv_fn = f"{case_id}_INV_{supp.replace(' ', '_')}.pdf"
        line_items = [{"description": it[0], "qty": it[1], "rate": it[2], "amount": it[3]} for it in items]

        create_invoice_pdf(
            os.path.join(INVOICE_DIR, inv_fn),
            {
                "supplier_name": supp,
                "invoice_number": inv_no,
                "invoice_date": f"2024-05-{idx:02d}",
                "subtotal_amount": sub,
                "tax_amount": tax,
                "total_amount": tot,
                "line_items": line_items,
            }
        )

        test_cases.append({
            "case_id": case_id,
            "category": "A_CLEAN_COMPLIANT",
            "invoice_file": inv_fn,
            "po_file": None,
            "has_po": False,
            "expected_findings_count": 0,
            "expected_findings": [],
            "description": f"Clean standalone invoice for {supp} (zero findings expected)."
        })

    # ==========================================
    # GROUP B: Tax & Arithmetic Discrepancies (14 cases)
    # ==========================================
    math_errors = [
        # (supp, inv_no, sub, tax, printed_tot, correct_tot, explanation)
        ("Delta Fabrication Works", "INV-2024-013", 10000.0, 1800.0, 12800.0, 11800.0, "Total arithmetic overbilled by 1,000"),
        ("Kavina Infra Solutions", "INV-2024-014", 45000.0, 8100.0, 45000.0, 53100.0, "Tax omitted from printed grand total"),
        ("Omega Electronic Spares", "INV-2024-015", 20000.0, 3600.0, 23000.0, 23600.0, "Transposition error underbilled by 600"),
        ("Rapid Freight Carriers", "INV-2024-016", 8500.0, 1530.0, 10500.0, 10030.0, "Incorrect round-up by 470"),
        ("Quantum Polymer Pipes", "INV-2024-017", 64000.0, 11520.0, 72000.0, 75520.0, "Subtotal addition mismatch by 3,520"),
        ("Starlight Paints LLP", "INV-2024-018", 50000.0, 5000.0, 59000.0, 55000.0, "Tax computed at 10% but total printed as 59,000"),
        ("Everest Safety Equipment", "INV-2024-019", 12000.0, 0.0, 14160.0, 12000.0, "Tax printed as 0 but added to grand total"),
        ("Vertex Chemical Reagents", "INV-2024-020", 30000.0, 5400.0, 34400.0, 35400.0, "Underbilled by 1,000 on total"),
        ("Falcon CNC Components", "INV-2024-021", 15000.0, 2700.0, 18200.0, 17700.0, "Arithmetic error variance of 500"),
        ("Pinnacle Solar Panels", "INV-2024-022", 90000.0, 16200.0, 105000.0, 106200.0, "Total under-sums tax by 1,200"),
        ("Horizon Paper Mill", "INV-2024-023", 28000.0, 5040.0, 33500.0, 33040.0, "Arithmetic total mismatch of 460"),
        ("Crestview Bearings Ltd", "INV-2024-024", 7200.0, 1296.0, 8200.0, 8496.0, "Arithmetic total under by 296"),
        ("Dynamic Valve Controls", "INV-2024-025", 120000.0, 21600.0, 140000.0, 141600.0, "Under-sums total by 1,600"),
        ("Titanium Fasteners Co", "INV-2024-026", 35000.0, 6300.0, 42000.0, 41300.0, "Overbilled arithmetic total by 700"),
    ]

    for idx, (supp, inv_no, sub, tax, printed_tot, correct_tot, exp) in enumerate(math_errors, 13):
        case_id = f"TC_{idx:02d}"
        inv_fn = f"{case_id}_INV_{supp.replace(' ', '_')}.pdf"
        line_items = [{"description": f"Standard Order Supply for {supp}", "qty": 1, "rate": sub, "amount": sub}]

        create_invoice_pdf(
            os.path.join(INVOICE_DIR, inv_fn),
            {
                "supplier_name": supp,
                "invoice_number": inv_no,
                "invoice_date": f"2024-05-{idx % 28 + 1:02d}",
                "subtotal_amount": sub,
                "tax_amount": tax,
                "total_amount": printed_tot,
                "line_items": line_items,
            }
        )

        test_cases.append({
            "case_id": case_id,
            "category": "B_TAX_AND_ARITHMETIC",
            "invoice_file": inv_fn,
            "po_file": None,
            "has_po": False,
            "expected_findings_count": 1,
            "expected_findings": ["TOTAL_MISMATCH"],
            "description": f"Arithmetic mismatch: Subtotal ({sub}) + Tax ({tax}) != Printed Total ({printed_tot}). {exp}"
        })

    # ==========================================
    # GROUP C: Missing Mandatory Fields (10 cases)
    # ==========================================
    missing_field_cases = [
        # (supp, inv_no, date, sub, tax, tot, omit_total, missing_fields, exp)
        ("Aura Tech Solutions", None, "2024-05-15", 25000.0, 4500.0, 29500.0, False, ["invoice_number"], "Missing invoice_number"),
        ("Metro Electrical Works", "INV-2024-028", None, 18000.0, 3240.0, 21240.0, False, ["invoice_date"], "Missing invoice_date"),
        (None, "INV-2024-029", "2024-05-17", 34000.0, 6120.0, 40120.0, False, ["supplier_name"], "Missing supplier_name"),
        ("United Packaging Systems", "INV-2024-030", "2024-05-18", 12000.0, 2160.0, None, True, ["total_amount"], "Missing total_amount"),
        ("Nova Engineering Labs", None, None, 40000.0, 7200.0, 47200.0, False, ["invoice_number", "invoice_date"], "Missing invoice_number and invoice_date"),
        (None, None, "2024-05-20", 22000.0, 3960.0, 25960.0, False, ["supplier_name", "invoice_number"], "Missing supplier_name and invoice_number"),
        ("Swift Global Logistics", "INV-2024-033", None, 15000.0, 2700.0, None, True, ["invoice_date", "total_amount"], "Missing invoice_date and total_amount"),
        ("Imperial Hardware Works", None, "2024-05-22", 8000.0, 1440.0, 9440.0, False, ["invoice_number"], "Quotation layout missing invoice_number"),
        (None, "INV-2024-035", "2024-05-23", 55000.0, 9900.0, 64900.0, False, ["supplier_name"], "Anonymous bill missing supplier_name"),
        ("Vanguard Fire Safety", "INV-2024-036", "2024-05-24", 19000.0, 3420.0, None, True, ["total_amount"], "Incomplete receipt missing total_amount"),
    ]

    for idx, (supp, inv_no, date_val, sub, tax, tot, omit_tot, missing_flds, exp) in enumerate(missing_field_cases, 27):
        case_id = f"TC_{idx:02d}"
        supp_name_safe = (supp or "Anonymous_Vendor").replace(' ', '_')
        inv_fn = f"{case_id}_INV_{supp_name_safe}.pdf"
        line_items = [{"description": "Supplied Commercial Goods", "qty": 1, "rate": sub, "amount": sub}]

        create_invoice_pdf(
            os.path.join(INVOICE_DIR, inv_fn),
            {
                "supplier_name": supp,
                "invoice_number": inv_no,
                "invoice_date": date_val,
                "subtotal_amount": sub,
                "tax_amount": tax,
                "total_amount": tot,
                "omit_total": omit_tot,
                "line_items": line_items,
            }
        )

        test_cases.append({
            "case_id": case_id,
            "category": "C_MISSING_FIELDS",
            "invoice_file": inv_fn,
            "po_file": None,
            "has_po": False,
            "expected_findings_count": len(missing_flds),
            "expected_findings": ["MISSING_FIELD"] * len(missing_flds),
            "missing_fields": missing_flds,
            "description": f"Missing mandatory compliance fields: {exp}."
        })

    # ==========================================
    # GROUP D: 2-Way PO vs Invoice Mismatches (14 cases)
    # ==========================================
    mismatch_cases = [
        # (supp_inv, supp_po, po_inv, po_ref, inv_tot, po_tot, expected_types, exp)
        ("Aero Precision Components", "Aero Precision Components", "PO-7701", "PO-7701", 55000.0, 50000.0, ["TOTAL_MISMATCH"], "Invoice Total (55k) > PO Total (50k)"),
        ("Bluestone Heavy Equipment", "Bluestone Heavy Equipment", "PO-7702", "PO-7702", 118000.0, 94400.0, ["TOTAL_MISMATCH"], "Invoice Total (118k) > PO Total (94.4k)"),
        ("Catalyst Scientific Corp", "Catalyst Scientific Corp", "PO-7703", "PO-7703", 32000.0, 28000.0, ["TOTAL_MISMATCH"], "Invoice Total (32k) > PO Total (28k)"),
        ("Diamond Drill Technologies", "Diamond Drill Technologies", "PO-7704", "PO-7704", 88000.0, 75000.0, ["TOTAL_MISMATCH"], "Invoice Total (88k) > PO Total (75k)"),
        ("Apex Global Trading FZE", "Apex Industrial Supplies Ltd", "PO-7705", "PO-7705", 40000.0, 40000.0, ["SUPPLIER_MISMATCH"], "Supplier name mismatch between entities"),
        ("Matrix Software Inc", "Matrix Hardware Corp", "PO-7706", "PO-7706", 62000.0, 62000.0, ["SUPPLIER_MISMATCH"], "Sister company supplier mismatch"),
        ("Delta Cloud Solutions", "Delta Telecom Networks", "PO-7707", "PO-7707", 35000.0, 35000.0, ["SUPPLIER_MISMATCH"], "Vendor legal name mismatch"),
        ("Krypton Metal Alloys", "Krypton Metal Alloys", "PO-88219", "PO-88291", 45000.0, 45000.0, ["PO_MISMATCH"], "PO number digit transposition"),
        ("Nexus Network Systems", "Nexus Network Systems", "PO-44019", "PO-99104", 28000.0, 28000.0, ["PO_MISMATCH"], "Wrong contract PO reference cited"),
        ("Orbit Hydraulics LLP", "Orbit Hydraulics LLP", "PO-2024-X9", "PO-2024-Z9", 19000.0, 19000.0, ["PO_MISMATCH"], "Suffix mismatch on PO number"),
        ("Sigma Instruments India", "Sigma Sensors Ltd", "PO-7711", "PO-7711", 60000.0, 50000.0, ["SUPPLIER_MISMATCH", "TOTAL_MISMATCH"], "Compound: Supplier AND Total Mismatch"),
        ("Omega Cable Industries", "Omega Cable Industries", "PO-102", "PO-105", 22000.0, 18000.0, ["PO_MISMATCH", "TOTAL_MISMATCH"], "Compound: PO number AND Total Mismatch"),
        ("Vector Automation Systems", "Vector Automation Systems", "PO-7713", "PO-7713", 40000.0, 50000.0, ["TOTAL_MISMATCH"], "Under-billing partial match"),
        ("Zephyr Air Filtration", "Zephyr Air Filtration", "PO-7714", "PO-7714", 47200.0, 35400.0, ["TOTAL_MISMATCH"], "Quantity variance leading to total mismatch"),
    ]

    for idx, (supp_inv, supp_po, po_inv, po_ref, inv_tot, po_tot, exp_types, exp) in enumerate(mismatch_cases, 37):
        case_id = f"TC_{idx:02d}"
        inv_fn = f"{case_id}_INV_{supp_inv.replace(' ', '_')}.pdf"
        po_fn = f"{case_id}_PO_{supp_po.replace(' ', '_')}.pdf"

        inv_sub = round(inv_tot / 1.18, 2)
        inv_tax = round(inv_tot - inv_sub, 2)

        po_sub = round(po_tot / 1.18, 2)
        po_tax = round(po_tot - po_sub, 2)

        create_invoice_pdf(
            os.path.join(INVOICE_DIR, inv_fn),
            {
                "supplier_name": supp_inv,
                "invoice_number": f"INV-2024-{idx:03d}",
                "invoice_date": f"2024-05-{idx % 28 + 1:02d}",
                "po_number": po_inv,
                "subtotal_amount": inv_sub,
                "tax_amount": inv_tax,
                "total_amount": inv_tot,
                "line_items": [{"description": "Industrial Deliverables", "qty": 1, "rate": inv_sub, "amount": inv_sub}],
            }
        )

        create_po_pdf(
            os.path.join(PO_DIR, po_fn),
            {
                "supplier_name": supp_po,
                "po_number": po_ref,
                "po_date": f"2024-04-15",
                "subtotal_amount": po_sub,
                "tax_amount": po_tax,
                "total_amount": po_tot,
                "line_items": [{"description": "Industrial Deliverables", "qty": 1, "rate": po_sub, "amount": po_sub}],
            }
        )

        test_cases.append({
            "case_id": case_id,
            "category": "D_2WAY_MISMATCHES",
            "invoice_file": inv_fn,
            "po_file": po_fn,
            "has_po": True,
            "expected_findings_count": len(exp_types),
            "expected_findings": exp_types,
            "description": f"2-Way Mismatch: {exp}."
        })

    # ==========================================
    # GROUP E: Duplicate Submissions (6 cases)
    # ==========================================
    duplicates = [
        ("Vortex Technologies", "INV-VORTEX-901", 35000.0, 6300.0, 41300.0),
        ("Skyline Freight Carriers", "INV-SKY-4412", 16779.66, 3020.34, 19800.0),
        ("Omni Clean Logistics", "INV-OMNI-1008", 27966.10, 5033.90, 33000.0),
    ]

    dup_idx = 51
    for supp, inv_no, sub, tax, tot in duplicates:
        # Original run (Base)
        case_id_orig = f"TC_{dup_idx:02d}"
        inv_fn_orig = f"{case_id_orig}_INV_{supp.replace(' ', '_')}.pdf"
        line_items = [{"description": f"Logistics & Operations for {supp}", "qty": 1, "rate": sub, "amount": sub}]

        create_invoice_pdf(
            os.path.join(INVOICE_DIR, inv_fn_orig),
            {
                "supplier_name": supp,
                "invoice_number": inv_no,
                "invoice_date": "2024-05-10",
                "subtotal_amount": sub,
                "tax_amount": tax,
                "total_amount": tot,
                "line_items": line_items,
            }
        )

        test_cases.append({
            "case_id": case_id_orig,
            "category": "E_DUPLICATES_BASE",
            "invoice_file": inv_fn_orig,
            "po_file": None,
            "has_po": False,
            "expected_findings_count": 0,
            "expected_findings": [],
            "description": f"Original submission for {supp} (#{inv_no}). Base run."
        })

        dup_idx += 1

        # Duplicate run
        case_id_dup = f"TC_{dup_idx:02d}"
        inv_fn_dup = f"{case_id_dup}_INV_{supp.replace(' ', '_')}_DUP.pdf"

        create_invoice_pdf(
            os.path.join(INVOICE_DIR, inv_fn_dup),
            {
                "supplier_name": supp,
                "invoice_number": inv_no,
                "invoice_date": "2024-05-10",
                "subtotal_amount": sub,
                "tax_amount": tax,
                "total_amount": tot,
                "line_items": line_items,
            }
        )

        test_cases.append({
            "case_id": case_id_dup,
            "category": "E_DUPLICATES",
            "invoice_file": inv_fn_dup,
            "po_file": None,
            "has_po": False,
            "expected_findings_count": 1,
            "expected_findings": ["DUPLICATE_INVOICE"],
            "description": f"Duplicate invoice detection: Repeated submission of invoice #{inv_no} by {supp}."
        })

        dup_idx += 1

    # ==========================================
    # GROUP F: Multi-Currency & Complex Invoices (4 cases)
    # ==========================================
    # TC_57: USD Clean match
    case_id = "TC_57"
    inv_fn = f"{case_id}_INV_CloudMatrix_USD.pdf"
    po_fn = f"{case_id}_PO_CloudMatrix_USD.pdf"
    usd_items = [{"description": "Enterprise Cloud Kubernetes Cluster", "qty": 1, "rate": 4500.0, "amount": 4500.0}]
    create_invoice_pdf(
        os.path.join(INVOICE_DIR, inv_fn),
        {"supplier_name": "CloudMatrix Global Inc", "invoice_number": "INV-USD-501", "invoice_date": "2024-05-25", "currency": "USD", "po_number": "PO-USD-801", "subtotal_amount": 4500.0, "tax_amount": 810.0, "total_amount": 5310.0, "line_items": usd_items}
    )
    create_po_pdf(
        os.path.join(PO_DIR, po_fn),
        {"supplier_name": "CloudMatrix Global Inc", "po_number": "PO-USD-801", "po_date": "2024-05-10", "currency": "USD", "subtotal_amount": 4500.0, "tax_amount": 810.0, "total_amount": 5310.0, "line_items": usd_items}
    )
    test_cases.append({
        "case_id": case_id,
        "category": "F_MULTI_CURRENCY",
        "invoice_file": inv_fn,
        "po_file": po_fn,
        "has_po": True,
        "expected_findings_count": 0,
        "expected_findings": [],
        "description": "Multi-currency clean USD match vs PO (zero findings expected)."
    })

    # TC_58: EUR Clean match
    case_id = "TC_58"
    inv_fn = f"{case_id}_INV_EuroTech_EUR.pdf"
    po_fn = f"{case_id}_PO_EuroTech_EUR.pdf"
    eur_items = [{"description": "High Precision CNC Spindle Assembly", "qty": 1, "rate": 12000.0, "amount": 12000.0}]
    create_invoice_pdf(
        os.path.join(INVOICE_DIR, inv_fn),
        {"supplier_name": "EuroTech Precision GmbH", "invoice_number": "INV-EUR-702", "invoice_date": "2024-05-26", "currency": "EUR", "po_number": "PO-EUR-902", "subtotal_amount": 12000.0, "tax_amount": 2400.0, "total_amount": 14400.0, "line_items": eur_items}
    )
    create_po_pdf(
        os.path.join(PO_DIR, po_fn),
        {"supplier_name": "EuroTech Precision GmbH", "po_number": "PO-EUR-902", "po_date": "2024-05-11", "currency": "EUR", "subtotal_amount": 12000.0, "tax_amount": 2400.0, "total_amount": 14400.0, "line_items": eur_items}
    )
    test_cases.append({
        "case_id": case_id,
        "category": "F_MULTI_CURRENCY",
        "invoice_file": inv_fn,
        "po_file": po_fn,
        "has_po": True,
        "expected_findings_count": 0,
        "expected_findings": [],
        "description": "Multi-currency clean EUR match vs PO (zero findings expected)."
    })

    # TC_59: USD Arithmetic Mismatch
    case_id = "TC_59"
    inv_fn = f"{case_id}_INV_SiliconValley_USD.pdf"
    usd_err_items = [{"description": "Data Analytics SaaS License", "qty": 1, "rate": 3000.0, "amount": 3000.0}]
    create_invoice_pdf(
        os.path.join(INVOICE_DIR, inv_fn),
        {"supplier_name": "Silicon Analytics LLC", "invoice_number": "INV-USD-503", "invoice_date": "2024-05-27", "currency": "USD", "subtotal_amount": 3000.0, "tax_amount": 300.0, "total_amount": 3500.0, "line_items": usd_err_items}
    )
    test_cases.append({
        "case_id": case_id,
        "category": "F_MULTI_CURRENCY",
        "invoice_file": inv_fn,
        "po_file": None,
        "has_po": False,
        "expected_findings_count": 1,
        "expected_findings": ["TOTAL_MISMATCH"],
        "description": "USD invoice arithmetic error: Subtotal (3000) + Tax (300) != Printed Total (3500)."
    })

    # TC_60: Multi-line Complex invoice (Clean)
    case_id = "TC_60"
    inv_fn = f"{case_id}_INV_ApexEnterprise_Complex.pdf"
    po_fn = f"{case_id}_PO_ApexEnterprise_Complex.pdf"
    complex_items = [
        {"description": "Network Switch 48-Port PoE", "qty": 2, "rate": 45000.0, "amount": 90000.0},
        {"description": "Cat6A Patch Cords (Pack of 50)", "qty": 5, "rate": 3000.0, "amount": 15000.0},
        {"description": "Server Rack Cabinet 42U", "qty": 1, "rate": 50000.0, "amount": 50000.0},
        {"description": "Onsite Installation & Cable Dressing", "qty": 1, "rate": 30000.0, "amount": 30000.0},
    ]
    tot_sub = 185000.0
    tot_tax = 33300.0
    tot_grand = 218300.0
    create_invoice_pdf(
        os.path.join(INVOICE_DIR, inv_fn),
        {"supplier_name": "Apex Enterprise Infrastructure Ltd", "invoice_number": "INV-2024-060", "invoice_date": "2024-05-28", "po_number": "PO-9060", "subtotal_amount": tot_sub, "tax_amount": tot_tax, "total_amount": tot_grand, "line_items": complex_items}
    )
    create_po_pdf(
        os.path.join(PO_DIR, po_fn),
        {"supplier_name": "Apex Enterprise Infrastructure Ltd", "po_number": "PO-9060", "po_date": "2024-05-12", "subtotal_amount": tot_sub, "tax_amount": tot_tax, "total_amount": tot_grand, "line_items": complex_items}
    )
    test_cases.append({
        "case_id": case_id,
        "category": "F_MULTI_LINE_COMPLEX",
        "invoice_file": inv_fn,
        "po_file": po_fn,
        "has_po": True,
        "expected_findings_count": 0,
        "expected_findings": [],
        "description": "Multi-line complex infrastructure procurement (zero findings expected)."
    })

    # Save manifest.json
    manifest_path = os.path.join(OUTPUT_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"total_cases": len(test_cases), "cases": test_cases}, f, indent=2)

    print(f"Generated {len(test_cases)} synthetic test cases successfully in '{OUTPUT_DIR}'.")
    print(f"Manifest written to: {manifest_path}")


if __name__ == "__main__":
    generate_all_cases()
