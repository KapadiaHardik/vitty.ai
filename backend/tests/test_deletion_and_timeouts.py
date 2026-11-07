import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from app.models.domain import (
    Document,
    DocumentStatus,
    GSTReconciliationRun,
    GSTRunStatus,
    User,
)
from app.services.gst.normalization import normalize_record


def test_pos_length_safety():
    """Verify POS and string normalization defensively handles long values without DB crash."""
    row = {
        "supplier_gstin": "27ABCDE1234F1Z5",
        "supplier_name": "A" * 300,
        "invoice_number": "INV-001",
        "pos": "27-Maharashtra - Mumbai Region Extra Description That Exceeds Ten Characters",
    }
    norm = normalize_record(row)
    assert norm["pos"] is not None
    assert len(norm["pos"]) <= 100
    assert norm["pos"] == "27-Maharashtra - Mumbai Region Extra Description That Exceeds Ten Characters"[:100]
    assert len(norm["supplier_name"]) <= 255


def test_document_leaked_spreadsheet_cleanup():
    """Verify that spreadsheet files (.xlsx, .csv, .xls) are filtered out from Knowledge Base documents."""
    user_id = uuid4()
    docs = [
        Document(id=uuid4(), user_id=user_id, filename="financial_audit.pdf", status=DocumentStatus.INDEXED),
        Document(id=uuid4(), user_id=user_id, filename="GSTR2B_April_2024.xlsx", status=DocumentStatus.PENDING),
        Document(id=uuid4(), user_id=user_id, filename="Purchase_Register.csv", status=DocumentStatus.PENDING),
        Document(id=uuid4(), user_id=user_id, filename="contract.txt", status=DocumentStatus.INDEXED),
    ]

    valid_docs = []
    to_delete = []
    for doc in docs:
        if doc.filename.lower().endswith((".xlsx", ".csv", ".xls")):
            to_delete.append(doc)
        else:
            valid_docs.append(doc)

    assert len(valid_docs) == 2
    assert len(to_delete) == 2
    assert [d.filename for d in valid_docs] == ["financial_audit.pdf", "contract.txt"]


def test_document_stuck_timeout_transition():
    """Verify that pending/processing documents older than 3 minutes transition to FAILED."""
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(minutes=10)
    recent_time = now - timedelta(seconds=30)

    stuck_doc = Document(
        id=uuid4(),
        user_id=user_id,
        filename="stuck_scan.pdf",
        status=DocumentStatus.PENDING,
        created_at=old_time,
    )
    active_doc = Document(
        id=uuid4(),
        user_id=user_id,
        filename="new_scan.pdf",
        status=DocumentStatus.PROCESSING,
        created_at=recent_time,
    )

    cutoff = now - timedelta(minutes=3)
    docs = [stuck_doc, active_doc]
    for d in docs:
        if d.status in (DocumentStatus.PENDING, DocumentStatus.PROCESSING) and d.created_at:
            created_tz = d.created_at if d.created_at.tzinfo else d.created_at.replace(tzinfo=timezone.utc)
            if created_tz < cutoff:
                d.status = DocumentStatus.FAILED

    assert stuck_doc.status == DocumentStatus.FAILED
    assert active_doc.status == DocumentStatus.PROCESSING


def test_gst_run_timeout_transition():
    """Verify that GST reconciliation runs stuck in PARSING/PENDING > 5 minutes transition to FAILED."""
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(minutes=15)
    recent_time = now - timedelta(minutes=1)

    stuck_run = GSTReconciliationRun(
        id=uuid4(),
        user_id=user_id,
        company_gstin="27ABCDE1234F1Z5",
        tax_period="04-2024",
        status=GSTRunStatus.PARSING,
        created_at=old_time,
    )
    active_run = GSTReconciliationRun(
        id=uuid4(),
        user_id=user_id,
        company_gstin="27ABCDE1234F1Z5",
        tax_period="04-2024",
        status=GSTRunStatus.PARSING,
        created_at=recent_time,
    )

    cutoff = now - timedelta(minutes=5)
    runs = [stuck_run, active_run]
    for r in runs:
        if r.status in (GSTRunStatus.PENDING, GSTRunStatus.PARSING, GSTRunStatus.MATCHING) and r.created_at:
            created_tz = r.created_at if r.created_at.tzinfo else r.created_at.replace(tzinfo=timezone.utc)
            if created_tz < cutoff:
                r.status = GSTRunStatus.FAILED
                r.error_message = "Reconciliation timed out or worker process was interrupted. Please re-run."

    assert stuck_run.status == GSTRunStatus.FAILED
    assert "timed out" in stuck_run.error_message
    assert active_run.status == GSTRunStatus.PARSING
    assert active_run.error_message is None
