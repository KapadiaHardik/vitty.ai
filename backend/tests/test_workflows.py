import pytest
from app.workflows.validation import validate_invoice
from app.workflows.comparison import compare_documents
from app.workflows.extraction import _heuristic_fallback_extraction
from app.models.domain import DiscrepancyType, Severity


def test_validate_invoice_valid():
    valid_data = {
        "supplier_name": "Acme Global",
        "invoice_number": "INV-2024-001",
        "invoice_date": "2024-05-10",
        "subtotal_amount": 1000.0,
        "tax_amount": 180.0,
        "total_amount": 1180.0,
    }
    findings = validate_invoice(valid_data)
    assert len(findings) == 0


def test_validate_invoice_missing_fields():
    incomplete_data = {
        "supplier_name": "Acme Global",
        # missing invoice_number, invoice_date, total_amount
    }
    findings = validate_invoice(incomplete_data)
    missing_fields = [f["field"] for f in findings if f["type"] == DiscrepancyType.MISSING_FIELD]
    assert "invoice_number" in missing_fields
    assert "invoice_date" in missing_fields
    assert "total_amount" in missing_fields


def test_validate_invoice_arithmetic_mismatch():
    invalid_math_data = {
        "supplier_name": "Acme Global",
        "invoice_number": "INV-2024-001",
        "invoice_date": "2024-05-10",
        "subtotal_amount": 100.0,
        "tax_amount": 10.0,
        "total_amount": 150.0,  # Expected 110.0
    }
    findings = validate_invoice(invalid_math_data)
    assert any(f["type"] == DiscrepancyType.TOTAL_MISMATCH for f in findings)


def test_compare_documents_match():
    invoice = {
        "supplier_name": "Dell Technologies",
        "po_number": "PO-999",
        "total_amount": 5000.0,
    }
    po = {
        "supplier_name": "Dell Technologies",
        "po_number": "PO-999",
        "total_amount": 5000.0,
    }
    findings = compare_documents(invoice, po)
    assert len(findings) == 0


def test_compare_documents_supplier_and_amount_mismatch():
    invoice = {
        "supplier_name": "Dell Corp",
        "po_number": "PO-999",
        "total_amount": 5500.0,
    }
    po = {
        "supplier_name": "Dell Technologies",
        "po_number": "PO-999",
        "total_amount": 5000.0,
    }
    findings = compare_documents(invoice, po)
    types = [f["type"] for f in findings]
    assert DiscrepancyType.SUPPLIER_MISMATCH in types
    assert DiscrepancyType.TOTAL_MISMATCH in types


def test_heuristic_fallback_extraction():
    sample_text = """
    Acme Industrial Supplies
    Invoice #: INV-8842
    Date: 2024-06-15
    PO Reference: PO-3310
    Subtotal: 450.00
    Tax: 50.00
    Grand Total: 500.00
    """
    extracted = _heuristic_fallback_extraction(sample_text, is_invoice=True)
    assert extracted["invoice_number"] == "INV-8842"
    assert extracted["po_number"] == "PO-3310"
    assert extracted["total_amount"] == 500.0
    assert extracted["subtotal_amount"] == 450.0
    assert extracted["tax_amount"] == 50.0
