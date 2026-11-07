import os
import aiofiles
from datetime import datetime, timezone, timedelta
from uuid import UUID
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db, async_session_factory
from app.core.config import get_settings
from app.models.domain import (
    User,
    Document,
    GSTReconciliationRun,
    GSTRunStatus,
    GSTSourceDocument,
    GSTSourceType,
    GSTNormalizedInvoice,
    GSTInvoiceMatch,
    GSTDiscrepancy,
    GSTDiscrepancyCategory,
    GSTReviewStatus,
    GSTReviewAudit,
    GSTMatchStage,
)
from app.schemas.gst import (
    ColumnMappingPreviewResponse,
    RunCreateRequest,
    ReconciliationRunListItem,
    ReconciliationRunDetailResponse,
    ReconciliationMetrics,
    DiscrepancyDetailResponse,
    DiscrepancyReviewRequest,
    ManualLinkRequest,
    NormalizedInvoiceResponse,
)
from app.services.gst.ingestion import get_file_preview
from app.services.gst.reporting import generate_reconciliation_excel_report
from app.services.gst.workflow import execute_gst_reconciliation
from app.api.v1.documents import get_current_user

settings = get_settings()
router = APIRouter()


async def execute_gst_reconciliation_bg(run_id: UUID) -> None:
    """Wrapper that opens an independent DB session for the background reconciliation task."""
    async with async_session_factory() as session:
        await execute_gst_reconciliation(run_id, session)


@router.post("/upload-preview", response_model=ColumnMappingPreviewResponse)
async def upload_file_preview(
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Upload an Excel or CSV file, save to storage, detect columns, and return preview.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    file_path = os.path.join(settings.STORAGE_DIR, f"{user.id}_{file.filename}")

    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    # Create Document record
    doc = Document(
        user_id=user.id,
        filename=file.filename,
        original_path=file_path,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    try:
        preview_data = get_file_preview(file_path, sheet_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to inspect file: {e}")

    return ColumnMappingPreviewResponse(
        document_id=doc.id,
        filename=file.filename,
        sheets=preview_data["sheets"],
        active_sheet=preview_data["active_sheet"],
        detected_headers=preview_data["detected_headers"],
        suggested_mapping=preview_data["suggested_mapping"],
        preview_rows=preview_data["preview_rows"],
        total_preview_rows=preview_data["total_preview_rows"],
    )


@router.post("/runs", response_model=ReconciliationRunDetailResponse)
async def create_reconciliation_run(
    request: RunCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Initiate a new GST reconciliation run between GSTR-2B and Purchase Register.
    """
    gstr2b_doc = await db.get(Document, request.gstr2b_document_id)
    if not gstr2b_doc or gstr2b_doc.user_id != user.id:
        raise HTTPException(status_code=404, detail="GSTR-2B source document not found.")

    pr_doc = await db.get(Document, request.purchase_register_document_id)
    if not pr_doc or pr_doc.user_id != user.id:
        raise HTTPException(status_code=404, detail="Purchase Register source document not found.")

    # 1. Create Run
    run = GSTReconciliationRun(
        user_id=user.id,
        company_gstin=request.company_gstin.strip().upper(),
        tax_period=request.tax_period.strip(),
        status=GSTRunStatus.PENDING,
        tolerances=request.tolerances,
    )
    db.add(run)
    await db.flush()

    # 2. Attach Source Documents
    gstr2b_src = GSTSourceDocument(
        run_id=run.id,
        source_type=GSTSourceType.GSTR_2B,
        filename=gstr2b_doc.filename,
        original_path=gstr2b_doc.original_path,
        column_mapping=request.gstr2b_column_mapping or {},
    )
    pr_src = GSTSourceDocument(
        run_id=run.id,
        source_type=GSTSourceType.PURCHASE_REGISTER,
        filename=pr_doc.filename,
        original_path=pr_doc.original_path,
        column_mapping=request.purchase_register_column_mapping or {},
    )
    db.add(gstr2b_src)
    db.add(pr_src)

    # 3. Audit Log
    audit = GSTReviewAudit(
        run_id=run.id,
        user_id=user.id,
        action="Initiated GST reconciliation run."
    )
    db.add(audit)

    # Clean up preview Document records so they don't pollute the Knowledge Base
    try:
        await db.delete(gstr2b_doc)
        await db.delete(pr_doc)
    except Exception:
        pass

    await db.commit()

    # Enqueue background reconciliation
    background_tasks.add_task(execute_gst_reconciliation_bg, run.id)

    return ReconciliationRunDetailResponse(
        id=run.id,
        company_gstin=run.company_gstin,
        tax_period=run.tax_period,
        status=run.status,
        error_message=None,
        created_at=run.created_at,
        metrics=ReconciliationMetrics(),
        gstr2b_filename=gstr2b_doc.filename,
        purchase_register_filename=pr_doc.filename,
    )


@router.get("/runs", response_model=List[ReconciliationRunListItem])
async def list_reconciliation_runs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    List all reconciliation runs with summary statistics.
    """
    stmt = (
        select(GSTReconciliationRun)
        .options(
            selectinload(GSTReconciliationRun.invoices),
            selectinload(GSTReconciliationRun.matches).selectinload(GSTInvoiceMatch.discrepancies),
        )
        .where(GSTReconciliationRun.user_id == user.id)
        .order_by(desc(GSTReconciliationRun.created_at))
    )
    res = await db.execute(stmt)
    runs = res.scalars().all()

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=5)
    has_timeout_updates = False

    items = []
    for r in runs:
        # Prevent stuck state: if run has been in PENDING, PARSING, or MATCHING for > 5 minutes, mark as FAILED
        if r.status in (GSTRunStatus.PENDING, GSTRunStatus.PARSING, GSTRunStatus.MATCHING) and r.created_at:
            created_tz = r.created_at if r.created_at.tzinfo else r.created_at.replace(tzinfo=timezone.utc)
            if created_tz < cutoff:
                r.status = GSTRunStatus.FAILED
                r.error_message = "Reconciliation timed out or worker process was interrupted. Please re-run."
                has_timeout_updates = True

        invoices = r.invoices or []
        books_count = sum(1 for i in invoices if i.source_type == GSTSourceType.PURCHASE_REGISTER)
        gstr2b_count = sum(1 for i in invoices if i.source_type == GSTSourceType.GSTR_2B)

        matches = r.matches or []
        matched = 0
        mismatch = 0
        pending = 0

        for m in matches:
            discs = m.discrepancies or []
            if any(d.category == GSTDiscrepancyCategory.MATCHED for d in discs):
                matched += 1
            elif discs:
                mismatch += 1
            for d in discs:
                if d.review_status == GSTReviewStatus.PENDING and d.category != GSTDiscrepancyCategory.MATCHED:
                    pending += 1

        items.append(
            ReconciliationRunListItem(
                id=r.id,
                company_gstin=r.company_gstin,
                tax_period=r.tax_period,
                status=r.status,
                created_at=r.created_at,
                total_books_records=books_count,
                total_gstr2b_records=gstr2b_count,
                matched_count=matched,
                mismatch_count=mismatch,
                pending_reviews=pending,
            )
        )

    if has_timeout_updates:
        await db.commit()

    return items


def compute_run_metrics(invoices: List[GSTNormalizedInvoice], matches: List[GSTInvoiceMatch]) -> ReconciliationMetrics:
    """Helper to calculate comprehensive financial and count metrics for a run."""
    m = ReconciliationMetrics()
    books_invs = [i for i in invoices if i.source_type == GSTSourceType.PURCHASE_REGISTER]
    gstr2b_invs = [i for i in invoices if i.source_type == GSTSourceType.GSTR_2B]

    m.total_books_records = len(books_invs)
    m.total_gstr2b_records = len(gstr2b_invs)

    for i in books_invs:
        m.total_books_taxable += i.taxable_value
        m.total_books_igst += i.igst
        m.total_books_cgst += i.cgst
        m.total_books_sgst += i.sgst
        m.total_books_cess += i.cess
        if not i.is_valid:
            m.invalid_record_count += 1

    for i in gstr2b_invs:
        m.total_gstr2b_taxable += i.taxable_value
        m.total_gstr2b_igst += i.igst
        m.total_gstr2b_cgst += i.cgst
        m.total_gstr2b_sgst += i.sgst
        m.total_gstr2b_cess += i.cess
        if not i.is_valid:
            m.invalid_record_count += 1

    m.diff_taxable = m.total_books_taxable - m.total_gstr2b_taxable
    m.diff_igst = m.total_books_igst - m.total_gstr2b_igst
    m.diff_cgst = m.total_books_cgst - m.total_gstr2b_cgst
    m.diff_sgst = m.total_books_sgst - m.total_gstr2b_sgst
    m.diff_cess = m.total_books_cess - m.total_gstr2b_cess

    for match in matches:
        discs = match.discrepancies or []
        for d in discs:
            if d.category == GSTDiscrepancyCategory.MATCHED:
                m.matched_count += 1
            elif d.category == GSTDiscrepancyCategory.BOOKS_ONLY:
                m.books_only_count += 1
            elif d.category == GSTDiscrepancyCategory.GSTR2B_ONLY:
                m.gstr2b_only_count += 1
            elif d.category == GSTDiscrepancyCategory.TAXABLE_VALUE_MISMATCH:
                m.taxable_mismatch_count += 1
            elif d.category in [
                GSTDiscrepancyCategory.IGST_MISMATCH,
                GSTDiscrepancyCategory.CGST_MISMATCH,
                GSTDiscrepancyCategory.SGST_MISMATCH,
                GSTDiscrepancyCategory.CESS_MISMATCH,
            ]:
                m.tax_mismatch_count += 1
            elif d.category == GSTDiscrepancyCategory.INVOICE_DATE_MISMATCH:
                m.date_mismatch_count += 1
            elif d.category == GSTDiscrepancyCategory.DUPLICATE_INVOICE:
                m.duplicate_count += 1
            elif d.category == GSTDiscrepancyCategory.POTENTIAL_MATCH:
                m.potential_match_count += 1

            if d.category != GSTDiscrepancyCategory.MATCHED:
                if d.review_status == GSTReviewStatus.PENDING:
                    m.pending_reviews += 1
                else:
                    m.resolved_reviews += 1

    return m


@router.get("/runs/{run_id}", response_model=ReconciliationRunDetailResponse)
async def get_reconciliation_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get detailed reconciliation run metrics and status.
    """
    stmt = (
        select(GSTReconciliationRun)
        .options(
            selectinload(GSTReconciliationRun.documents),
            selectinload(GSTReconciliationRun.invoices),
            selectinload(GSTReconciliationRun.matches).selectinload(GSTInvoiceMatch.discrepancies),
        )
        .where(GSTReconciliationRun.id == run_id)
    )
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()

    if not run or run.user_id != user.id:
        raise HTTPException(status_code=404, detail="Reconciliation run not found.")

    # Check timeout for stuck states
    if run.status in (GSTRunStatus.PENDING, GSTRunStatus.PARSING, GSTRunStatus.MATCHING) and run.created_at:
        now = datetime.now(timezone.utc)
        created_tz = run.created_at if run.created_at.tzinfo else run.created_at.replace(tzinfo=timezone.utc)
        if created_tz < now - timedelta(minutes=5):
            run.status = GSTRunStatus.FAILED
            run.error_message = "Reconciliation timed out or worker process was interrupted. Please re-run."
            await db.commit()

    metrics = compute_run_metrics(run.invoices or [], run.matches or [])

    gstr2b_doc = next((d for d in run.documents if d.source_type == GSTSourceType.GSTR_2B), None)
    pr_doc = next((d for d in run.documents if d.source_type == GSTSourceType.PURCHASE_REGISTER), None)

    return ReconciliationRunDetailResponse(
        id=run.id,
        company_gstin=run.company_gstin,
        tax_period=run.tax_period,
        status=run.status,
        error_message=run.error_message,
        created_at=run.created_at,
        metrics=metrics,
        gstr2b_filename=gstr2b_doc.filename if gstr2b_doc else None,
        purchase_register_filename=pr_doc.filename if pr_doc else None,
    )


@router.delete("/runs/{run_id}")
async def delete_reconciliation_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Permanently delete a reconciliation run and all associated cascade data.
    """
    stmt = (
        select(GSTReconciliationRun)
        .options(selectinload(GSTReconciliationRun.documents))
        .where(GSTReconciliationRun.id == run_id)
    )
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()

    if not run or run.user_id != user.id:
        raise HTTPException(status_code=404, detail="Reconciliation run not found.")

    # Remove stored source files from disk if present
    for doc in run.documents or []:
        if doc.original_path and os.path.exists(doc.original_path):
            try:
                os.remove(doc.original_path)
            except Exception:
                pass

    await db.delete(run)
    await db.commit()
    return {"success": True, "deleted_id": str(run_id)}


@router.get("/runs/{run_id}/discrepancies", response_model=List[DiscrepancyDetailResponse])
async def list_discrepancies(
    run_id: UUID,
    category: Optional[GSTDiscrepancyCategory] = Query(None),
    review_status: Optional[GSTReviewStatus] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(200, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Retrieve filterable discrepancy items for exception review.
    """
    run = await db.get(GSTReconciliationRun, run_id)
    if not run or run.user_id != user.id:
        raise HTTPException(status_code=404, detail="Reconciliation run not found.")

    stmt = (
        select(GSTDiscrepancy)
        .join(GSTInvoiceMatch, GSTDiscrepancy.match_id == GSTInvoiceMatch.id)
        .options(
            selectinload(GSTDiscrepancy.match).selectinload(GSTInvoiceMatch.books_invoice),
            selectinload(GSTDiscrepancy.match).selectinload(GSTInvoiceMatch.gstr2b_invoice),
        )
        .where(GSTInvoiceMatch.run_id == run_id)
    )

    if category:
        stmt = stmt.where(GSTDiscrepancy.category == category)
    if review_status:
        stmt = stmt.where(GSTDiscrepancy.review_status == review_status)

    res = await db.execute(stmt)
    discrepancies = res.scalars().all()

    # Search filter across GSTIN, invoice number, supplier name
    results = []
    for d in discrepancies:
        match = d.match
        b = match.books_invoice
        g = match.gstr2b_invoice

        if search:
            q = search.lower()
            text_corpus = f"{b.supplier_gstin if b else ''} {g.supplier_gstin if g else ''} {b.invoice_number_norm if b else ''} {g.invoice_number_norm if g else ''} {b.supplier_name if b else ''} {g.supplier_name if g else ''}".lower()
            if q not in text_corpus:
                continue

        b_resp = None
        if b:
            b_resp = NormalizedInvoiceResponse(
                id=b.id,
                source_type=b.source_type,
                supplier_gstin=b.supplier_gstin,
                supplier_name=b.supplier_name,
                invoice_number_raw=b.invoice_number_raw,
                invoice_number_norm=b.invoice_number_norm,
                invoice_date=b.invoice_date,
                doc_type=b.doc_type,
                taxable_value=b.taxable_value,
                igst=b.igst,
                cgst=b.cgst,
                sgst=b.sgst,
                cess=b.cess,
                invoice_total=b.invoice_total,
                pos=b.pos,
                source_file=b.source_file,
                source_sheet=b.source_sheet,
                source_row_index=b.source_row_index,
                is_valid=b.is_valid,
                validation_errors=b.validation_errors,
            )

        g_resp = None
        if g:
            g_resp = NormalizedInvoiceResponse(
                id=g.id,
                source_type=g.source_type,
                supplier_gstin=g.supplier_gstin,
                supplier_name=g.supplier_name,
                invoice_number_raw=g.invoice_number_raw,
                invoice_number_norm=g.invoice_number_norm,
                invoice_date=g.invoice_date,
                doc_type=g.doc_type,
                taxable_value=g.taxable_value,
                igst=g.igst,
                cgst=g.cgst,
                sgst=g.sgst,
                cess=g.cess,
                invoice_total=g.invoice_total,
                pos=g.pos,
                source_file=g.source_file,
                source_sheet=g.source_sheet,
                source_row_index=g.source_row_index,
                is_valid=g.is_valid,
                validation_errors=g.validation_errors,
            )

        results.append(
            DiscrepancyDetailResponse(
                id=d.id,
                match_id=d.match_id,
                category=d.category,
                books_value=d.books_value,
                gstr2b_value=d.gstr2b_value,
                difference=d.difference,
                explanation=d.explanation,
                suggested_action=d.suggested_action,
                review_status=d.review_status,
                reviewer_notes=d.reviewer_notes,
                reviewed_at=d.reviewed_at,
                match_stage=match.match_stage,
                confidence_score=match.confidence_score,
                books_invoice=b_resp,
                gstr2b_invoice=g_resp,
            )
        )

    return results[offset : offset + limit]


@router.post("/runs/{run_id}/review")
async def review_discrepancy(
    run_id: UUID,
    request: DiscrepancyReviewRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Update CA review decision on an exception.
    """
    disc = await db.get(GSTDiscrepancy, request.discrepancy_id)
    if not disc:
        raise HTTPException(status_code=404, detail="Discrepancy not found.")

    prev_status = disc.review_status.value
    disc.review_status = request.review_status
    disc.reviewer_notes = request.reviewer_notes
    disc.reviewer_id = user.id

    audit = GSTReviewAudit(
        run_id=run_id,
        user_id=user.id,
        discrepancy_id=disc.id,
        action=f"Reviewed discrepancy: {request.review_status.value}",
        previous_state=prev_status,
        new_state=request.review_status.value,
        comment=request.reviewer_notes,
    )
    db.add(audit)
    await db.commit()

    return {"success": True, "discrepancy_id": str(disc.id), "review_status": disc.review_status.value}


@router.post("/runs/{run_id}/manual-link")
async def manually_link_records(
    run_id: UUID,
    request: ManualLinkRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Manually link a Books invoice and a GSTR-2B invoice when automatic matching missed it.
    """
    b_inv = await db.get(GSTNormalizedInvoice, request.books_invoice_id)
    g_inv = await db.get(GSTNormalizedInvoice, request.gstr2b_invoice_id)

    if not b_inv or b_inv.run_id != run_id:
        raise HTTPException(status_code=404, detail="Books invoice not found in this run.")
    if not g_inv or g_inv.run_id != run_id:
        raise HTTPException(status_code=404, detail="GSTR-2B invoice not found in this run.")

    # Create new match pair
    new_match = GSTInvoiceMatch(
        run_id=run_id,
        books_invoice_id=b_inv.id,
        gstr2b_invoice_id=g_inv.id,
        match_stage=GSTMatchStage.MANUAL,
        confidence_score=1.0,
        match_rule_reason=f"Manually linked by CA auditor. {request.notes or ''}".strip(),
        is_manually_linked=True,
    )
    db.add(new_match)
    await db.flush()

    # Reclassify discrepancy for the manually linked pair
    taxable_diff = b_inv.taxable_value - g_inv.taxable_value
    disc = GSTDiscrepancy(
        match_id=new_match.id,
        category=GSTDiscrepancyCategory.MATCHED if abs(taxable_diff) <= Decimal("1.00") else GSTDiscrepancyCategory.TAXABLE_VALUE_MISMATCH,
        books_value=f"Inv #{b_inv.invoice_number_norm} | ₹{b_inv.taxable_value}",
        gstr2b_value=f"Inv #{g_inv.invoice_number_norm} | ₹{g_inv.taxable_value}",
        difference=taxable_diff,
        explanation=f"Manually paired: {request.notes or 'CA Auditor manual match confirmation'}",
        review_status=GSTReviewStatus.RESOLVED,
        reviewer_id=user.id,
        reviewer_notes=request.notes,
    )
    db.add(disc)

    audit = GSTReviewAudit(
        run_id=run_id,
        user_id=user.id,
        match_id=new_match.id,
        action=f"Manually linked Books Inv #{b_inv.invoice_number_norm} with GSTR-2B Inv #{g_inv.invoice_number_norm}",
        comment=request.notes,
    )
    db.add(audit)
    await db.commit()

    return {"success": True, "match_id": str(new_match.id)}


@router.get("/runs/{run_id}/export")
async def export_reconciliation_excel(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Download the 9-sheet Excel Reconciliation Report.
    """
    stmt = (
        select(GSTReconciliationRun)
        .options(
            selectinload(GSTReconciliationRun.invoices),
            selectinload(GSTReconciliationRun.matches).selectinload(GSTInvoiceMatch.books_invoice),
            selectinload(GSTReconciliationRun.matches).selectinload(GSTInvoiceMatch.gstr2b_invoice),
            selectinload(GSTReconciliationRun.matches).selectinload(GSTInvoiceMatch.discrepancies),
            selectinload(GSTReconciliationRun.audit_logs),
        )
        .where(GSTReconciliationRun.id == run_id)
    )
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()

    if not run or run.user_id != user.id:
        raise HTTPException(status_code=404, detail="Reconciliation run not found.")

    # Check timeout for stuck states
    if run.status in (GSTRunStatus.PENDING, GSTRunStatus.PARSING, GSTRunStatus.MATCHING) and run.created_at:
        now = datetime.now(timezone.utc)
        created_tz = run.created_at if run.created_at.tzinfo else run.created_at.replace(tzinfo=timezone.utc)
        if created_tz < now - timedelta(minutes=5):
            run.status = GSTRunStatus.FAILED
            run.error_message = "Reconciliation timed out or worker process was interrupted. Please re-run."
            await db.commit()

    metrics = compute_run_metrics(run.invoices or [], run.matches or [])
    excel_stream = generate_reconciliation_excel_report(
        run=run,
        matches=run.matches or [],
        audit_logs=run.audit_logs or [],
        metrics=metrics.dict(),
    )

    filename = f"GST_Reconciliation_{run.company_gstin}_{run.tax_period}.xlsx"
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
