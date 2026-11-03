import pytest
import datetime
import io
import openpyxl
from decimal import Decimal
from uuid import uuid4

from app.models.domain import (
    GSTDocType,
    GSTMatchStage,
    GSTDiscrepancyCategory,
    GSTReconciliationRun,
    GSTRunStatus,
    GSTInvoiceMatch,
    GSTNormalizedInvoice,
    GSTSourceType,
)
from app.services.gst.ingestion import auto_map_columns, detect_header_row_in_sheet
from app.services.gst.normalization import (
    normalize_gstin,
    normalize_invoice_number,
    parse_date,
    parse_decimal,
    normalize_document_type,
    normalize_record,
)
from app.services.gst.matching import execute_matching_engine, levenshtein_ratio
from app.services.gst.discrepancy import classify_match_discrepancies
from app.services.gst.reporting import generate_reconciliation_excel_report


# ========================================================
# 1. Ingestion & Column Mapping Tests
# ========================================================

def test_detect_header_row():
    rows = [
        ["GSTR-2B Auto-Drafted Statement", None, None],
        ["Generated on: 2024-05-01", None, None],
        [None, None, None],
        ["GSTIN of Supplier", "Trade Name", "Invoice number", "Invoice Date", "Taxable Value", "Integrated Tax"],
        ["27ABCDE1234F1Z5", "Acme Corp", "INV-101", "01/04/2024", "10000.00", "1800.00"],
    ]
    header_idx = detect_header_row_in_sheet(rows)
    assert header_idx == 3


def test_auto_map_columns_gstr2b_standard():
    headers = [
        "GSTIN of supplier",
        "Trade/Legal name",
        "Invoice number",
        "Invoice type",
        "Invoice Date",
        "Invoice Value",
        "Place of supply",
        "Taxable Value",
        "Integrated Tax",
        "Central Tax",
        "State/UT Tax",
        "Cess",
    ]
    mapping = auto_map_columns(headers)
    assert mapping["supplier_gstin"] == "GSTIN of supplier"
    assert mapping["supplier_name"] == "Trade/Legal name"
    assert mapping["invoice_number"] == "Invoice number"
    assert mapping["taxable_value"] == "Taxable Value"
    assert mapping["igst"] == "Integrated Tax"
    assert mapping["cgst"] == "Central Tax"
    assert mapping["sgst"] == "State/UT Tax"
    assert mapping["cess"] == "Cess"


def test_auto_map_columns_tally_purchase_register():
    headers = [
        "Party GSTIN",
        "Party Name",
        "Voucher No",
        "Date",
        "Basic Amount",
        "IGST Amount",
        "CGST Amount",
        "SGST Amount",
        "Grand Total",
    ]
    mapping = auto_map_columns(headers)
    assert mapping["supplier_gstin"] == "Party GSTIN"
    assert mapping["supplier_name"] == "Party Name"
    assert mapping["invoice_number"] == "Voucher No"
    assert mapping["taxable_value"] == "Basic Amount"
    assert mapping["igst"] == "IGST Amount"


# ========================================================
# 2. Normalization Tests
# ========================================================

def test_normalize_gstin():
    valid_gstin, err = normalize_gstin(" 27abcde1234f1z5 ")
    assert valid_gstin == "27ABCDE1234F1Z5"
    assert err is None

    invalid_gstin, err2 = normalize_gstin("INVALID_GSTIN")
    assert err2 is not None


def test_normalize_invoice_number():
    raw, norm = normalize_invoice_number("  inv/00452/23-24  ")
    assert raw == "inv/00452/23-24"
    assert norm == "INV/452/23-24"

    raw2, norm2 = normalize_invoice_number("0000987")
    assert norm2 == "987"


def test_parse_date():
    d1, err1 = parse_date("15/04/2024")
    assert d1 == datetime.date(2024, 4, 15)
    assert err1 is None

    d2, err2 = parse_date("2024-04-15")
    assert d2 == datetime.date(2024, 4, 15)

    d3, err3 = parse_date("15-Apr-2024")
    assert d3 == datetime.date(2024, 4, 15)


def test_parse_decimal_monetary():
    val1, _ = parse_decimal(" ₹ 12,345.67 ")
    assert val1 == Decimal("12345.67")

    val_neg, _ = parse_decimal("(500.00)")
    assert val_neg == Decimal("-500.00")

    val_zero, _ = parse_decimal(None)
    assert val_zero == Decimal("0.00")


def test_normalize_document_type():
    assert normalize_document_type("Tax Invoice", Decimal("100.00")) == GSTDocType.INV
    assert normalize_document_type("Credit Note", Decimal("-50.00")) == GSTDocType.CRN
    assert normalize_document_type("Debit Note", Decimal("50.00")) == GSTDocType.DBN


def test_normalize_record_complete():
    raw = {
        "supplier_gstin": "27ABCDE1234F1Z5",
        "supplier_name": "Bharat Corp",
        "invoice_number": "INV-0012",
        "invoice_date": "10/05/2024",
        "taxable_value": "1000.00",
        "igst": "180.00",
        "cgst": "0.00",
        "sgst": "0.00",
        "cess": "0.00",
        "_source_file": "pr.xlsx",
        "_source_sheet": "Sheet1",
        "_source_row_index": 5,
        "_raw_record": {"Raw": "Data"}
    }
    norm = normalize_record(raw)
    assert norm["is_valid"] is True
    assert norm["invoice_number_norm"] == "INV-12"
    assert norm["taxable_value"] == Decimal("1000.00")
    assert norm["invoice_total"] == Decimal("1180.00")


# ========================================================
# 3. Deterministic Matching Engine Tests
# ========================================================

def test_stage_1_exact_match():
    books = [(
        1,
        {
            "supplier_gstin": "27ABCDE1234F1Z5",
            "invoice_number_raw": "INV-101",
            "invoice_number_norm": "INV-101",
            "invoice_date": datetime.date(2024, 4, 10),
            "doc_type": GSTDocType.INV,
            "taxable_value": Decimal("1000.00"),
            "igst": Decimal("180.00"),
            "cgst": Decimal("0.00"),
            "sgst": Decimal("0.00"),
            "cess": Decimal("0.00"),
            "invoice_total": Decimal("1180.00"),
            "is_valid": True,
        }
    )]
    gstr2b = [(
        101,
        {
            "supplier_gstin": "27ABCDE1234F1Z5",
            "invoice_number_raw": "INV-101",
            "invoice_number_norm": "INV-101",
            "invoice_date": datetime.date(2024, 4, 10),
            "doc_type": GSTDocType.INV,
            "taxable_value": Decimal("1000.00"),
            "igst": Decimal("180.00"),
            "cgst": Decimal("0.00"),
            "sgst": Decimal("0.00"),
            "cess": Decimal("0.00"),
            "invoice_total": Decimal("1180.00"),
            "is_valid": True,
        }
    )]
    matches, books_dups, gstr2b_dups = execute_matching_engine(books, gstr2b)
    assert len(matches) == 1
    assert matches[0]["stage"] == GSTMatchStage.STAGE_1_EXACT
    assert matches[0]["confidence_score"] == 1.0


def test_stage_2_strong_match_minor_date_variance():
    books = [(
        1,
        {
            "supplier_gstin": "27ABCDE1234F1Z5",
            "invoice_number_raw": "INV-202",
            "invoice_number_norm": "INV-202",
            "invoice_date": datetime.date(2024, 4, 10),
            "doc_type": GSTDocType.INV,
            "taxable_value": Decimal("5000.00"),
            "is_valid": True,
        }
    )]
    gstr2b = [(
        102,
        {
            "supplier_gstin": "27ABCDE1234F1Z5",
            "invoice_number_raw": "INV-202",
            "invoice_number_norm": "INV-202",
            "invoice_date": datetime.date(2024, 4, 15),  # 5 days difference
            "doc_type": GSTDocType.INV,
            "taxable_value": Decimal("5000.00"),
            "is_valid": True,
        }
    )]
    matches, _, _ = execute_matching_engine(books, gstr2b)
    assert len(matches) == 1
    assert matches[0]["stage"] == GSTMatchStage.STAGE_2_STRONG


def test_stage_3_flexible_match_separator_difference():
    books = [(
        1,
        {
            "supplier_gstin": "27ABCDE1234F1Z5",
            "invoice_number_raw": "INV/2024/089",
            "invoice_number_norm": "INV/2024/89",
            "invoice_date": datetime.date(2024, 4, 10),
            "doc_type": GSTDocType.INV,
            "taxable_value": Decimal("3000.00"),
            "is_valid": True,
        }
    )]
    gstr2b = [(
        103,
        {
            "supplier_gstin": "27ABCDE1234F1Z5",
            "invoice_number_raw": "INV-2024-89",
            "invoice_number_norm": "INV-2024-89",
            "invoice_date": datetime.date(2024, 4, 10),
            "doc_type": GSTDocType.INV,
            "taxable_value": Decimal("3000.00"),
            "is_valid": True,
        }
    )]
    matches, _, _ = execute_matching_engine(books, gstr2b)
    assert len(matches) == 1
    assert matches[0]["stage"] == GSTMatchStage.STAGE_3_FLEXIBLE


def test_stage_4_potential_match():
    books = [(
        1,
        {
            "supplier_gstin": "27ABCDE1234F1Z5",
            "invoice_number_raw": "AB/9842",
            "invoice_number_norm": "AB/9842",
            "invoice_date": datetime.date(2024, 4, 10),
            "doc_type": GSTDocType.INV,
            "taxable_value": Decimal("10000.00"),
            "is_valid": True,
        }
    )]
    gstr2b = [(
        104,
        {
            "supplier_gstin": "27ABCDE1234F1Z5",
            "invoice_number_raw": "AB/9842A",
            "invoice_number_norm": "AB/9842A",
            "invoice_date": datetime.date(2024, 4, 10),
            "doc_type": GSTDocType.INV,
            "taxable_value": Decimal("10000.00"),
            "is_valid": True,
        }
    )]
    matches, _, _ = execute_matching_engine(books, gstr2b)
    assert len(matches) == 1
    assert matches[0]["stage"] == GSTMatchStage.STAGE_4_POTENTIAL


def test_one_to_one_matching_constraint():
    books = [
        (1, {"supplier_gstin": "27ABCDE1234F1Z5", "invoice_number_norm": "INV-1", "invoice_date": datetime.date(2024, 4, 1), "doc_type": GSTDocType.INV, "taxable_value": Decimal("100.00"), "is_valid": True}),
        (2, {"supplier_gstin": "27ABCDE1234F1Z5", "invoice_number_norm": "INV-1", "invoice_date": datetime.date(2024, 4, 1), "doc_type": GSTDocType.INV, "taxable_value": Decimal("100.00"), "is_valid": True}),
    ]
    gstr2b = [
        (101, {"supplier_gstin": "27ABCDE1234F1Z5", "invoice_number_norm": "INV-1", "invoice_date": datetime.date(2024, 4, 1), "doc_type": GSTDocType.INV, "taxable_value": Decimal("100.00"), "is_valid": True}),
    ]
    matches, books_dups, _ = execute_matching_engine(books, gstr2b)
    # 1 matched pair, 1 books-only leftover
    paired = [m for m in matches if m["stage"] is not None]
    unpaired = [m for m in matches if m["stage"] is None]
    assert len(paired) == 1
    assert len(unpaired) == 1
    assert 1 in books_dups and 2 in books_dups


# ========================================================
# 4. Discrepancy Classifier Tests (13 categories)
# ========================================================

def test_classify_discrepancies_tax_mismatch():
    from app.services.gst.matching import MatchCandidate
    b = MatchCandidate({
        "supplier_gstin": "27ABCDE1234F1Z5",
        "invoice_number_norm": "INV-1",
        "doc_type": GSTDocType.INV,
        "taxable_value": Decimal("1000.00"),
        "igst": Decimal("180.00"),
        "cgst": Decimal("0.00"),
        "sgst": Decimal("0.00"),
        "cess": Decimal("0.00"),
        "is_valid": True,
    }, 1)
    g = MatchCandidate({
        "supplier_gstin": "27ABCDE1234F1Z5",
        "invoice_number_norm": "INV-1",
        "doc_type": GSTDocType.INV,
        "taxable_value": Decimal("1000.00"),
        "igst": Decimal("120.00"),  # Mismatched IGST (180 vs 120)
        "cgst": Decimal("0.00"),
        "sgst": Decimal("0.00"),
        "cess": Decimal("0.00"),
        "is_valid": True,
    }, 101)

    match_dict = {
        "books_candidate": b,
        "gstr2b_candidate": g,
        "stage": GSTMatchStage.STAGE_1_EXACT,
    }
    discs = classify_match_discrepancies(match_dict, set(), set(), {"tax_diff_max": 1.0, "date_days_diff": 30})
    cats = [d["category"] for d in discs]
    assert GSTDiscrepancyCategory.IGST_MISMATCH in cats


# ========================================================
# 5. Excel Report Generation Tests
# ========================================================

def test_generate_excel_report_all_sheets():
    run = GSTReconciliationRun(
        id=uuid4(),
        company_gstin="27ABCDE1234F1Z5",
        tax_period="04-2024",
        status=GSTRunStatus.COMPLETED,
    )
    metrics = {
        "total_books_records": 10,
        "total_gstr2b_records": 10,
        "matched_count": 8,
        "books_only_count": 1,
        "gstr2b_only_count": 1,
        "taxable_mismatch_count": 0,
        "tax_mismatch_count": 0,
        "duplicate_count": 0,
        "potential_match_count": 0,
        "invalid_record_count": 0,
    }
    excel_stream = generate_reconciliation_excel_report(run, [], [], metrics)
    wb = openpyxl.load_workbook(excel_stream)
    expected_sheets = [
        "Summary",
        "Matched Invoices",
        "Books Only",
        "GSTR-2B Only",
        "Tax Mismatches",
        "Duplicate Invoices",
        "Potential Matches",
        "Invalid Records",
        "Review History",
    ]
    for s in expected_sheets:
        assert s in wb.sheetnames
