import logging
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import async_session_factory

from app.models.domain import (
    GSTReconciliationRun,
    GSTRunStatus,
    GSTSourceDocument,
    GSTSourceType,
    GSTNormalizedInvoice,
    GSTInvoiceMatch,
    GSTDiscrepancy,
    GSTReviewAudit,
)
from app.services.gst.ingestion import parse_file_records
from app.services.gst.normalization import normalize_record
from app.services.gst.matching import execute_matching_engine
from app.services.gst.discrepancy import classify_match_discrepancies

logger = logging.getLogger(__name__)


async def execute_gst_reconciliation(run_id: UUID, session: AsyncSession) -> None:
    """
    Background worker orchestrating the full GST reconciliation run.
    """
    stmt = (
        select(GSTReconciliationRun)
        .options(selectinload(GSTReconciliationRun.documents))
        .where(GSTReconciliationRun.id == run_id)
    )
    res = await session.execute(stmt)
    run = res.scalar_one_or_none()

    if not run:
        logger.error(f"GST Reconciliation Run {run_id} not found.")
        return

    try:
        run.status = GSTRunStatus.PARSING
        await session.commit()

        # Step 1: Identify GSTR-2B and Purchase Register source documents
        gstr2b_doc = next((d for d in run.documents if d.source_type == GSTSourceType.GSTR_2B), None)
        pr_doc = next((d for d in run.documents if d.source_type == GSTSourceType.PURCHASE_REGISTER), None)

        if not gstr2b_doc or not pr_doc:
            raise ValueError("Reconciliation requires both GSTR-2B and Purchase Register source documents.")

        # Step 2: Ingest & map raw records
        raw_gstr2b_records = parse_file_records(
            file_path=gstr2b_doc.original_path,
            column_mapping=gstr2b_doc.column_mapping or {}
        )
        raw_pr_records = parse_file_records(
            file_path=pr_doc.original_path,
            column_mapping=pr_doc.column_mapping or {}
        )

        gstr2b_doc.row_count = len(raw_gstr2b_records)
        pr_doc.row_count = len(raw_pr_records)

        # Step 3: Normalize and validate records
        books_db_invoices = []
        for r in raw_pr_records:
            norm = normalize_record(r)
            inv = GSTNormalizedInvoice(
                run_id=run.id,
                source_type=GSTSourceType.PURCHASE_REGISTER,
                source_document_id=pr_doc.id,
                supplier_gstin=norm["supplier_gstin"],
                supplier_name=norm["supplier_name"],
                invoice_number_raw=norm["invoice_number_raw"],
                invoice_number_norm=norm["invoice_number_norm"],
                invoice_date=norm["invoice_date"],
                doc_type=norm["doc_type"],
                taxable_value=norm["taxable_value"],
                igst=norm["igst"],
                cgst=norm["cgst"],
                sgst=norm["sgst"],
                cess=norm["cess"],
                invoice_total=norm["invoice_total"],
                pos=norm["pos"],
                source_file=norm["source_file"],
                source_sheet=norm["source_sheet"],
                source_row_index=norm["source_row_index"],
                raw_record_data=norm["raw_record_data"],
                is_valid=norm["is_valid"],
                validation_errors=norm["validation_errors"],
            )
            session.add(inv)
            books_db_invoices.append(inv)

        gstr2b_db_invoices = []
        for r in raw_gstr2b_records:
            norm = normalize_record(r)
            inv = GSTNormalizedInvoice(
                run_id=run.id,
                source_type=GSTSourceType.GSTR_2B,
                source_document_id=gstr2b_doc.id,
                supplier_gstin=norm["supplier_gstin"],
                supplier_name=norm["supplier_name"],
                invoice_number_raw=norm["invoice_number_raw"],
                invoice_number_norm=norm["invoice_number_norm"],
                invoice_date=norm["invoice_date"],
                doc_type=norm["doc_type"],
                taxable_value=norm["taxable_value"],
                igst=norm["igst"],
                cgst=norm["cgst"],
                sgst=norm["sgst"],
                cess=norm["cess"],
                invoice_total=norm["invoice_total"],
                pos=norm["pos"],
                source_file=norm["source_file"],
                source_sheet=norm["source_sheet"],
                source_row_index=norm["source_row_index"],
                raw_record_data=norm["raw_record_data"],
                is_valid=norm["is_valid"],
                validation_errors=norm["validation_errors"],
            )
            session.add(inv)
            gstr2b_db_invoices.append(inv)

        await session.flush()

        # Step 4: Deterministic Matching Engine
        run.status = GSTRunStatus.MATCHING
        await session.commit()

        books_inputs = [
            (
                inv.id,
                {
                    "supplier_gstin": inv.supplier_gstin,
                    "supplier_name": inv.supplier_name,
                    "invoice_number_raw": inv.invoice_number_raw,
                    "invoice_number_norm": inv.invoice_number_norm,
                    "invoice_date": inv.invoice_date,
                    "doc_type": inv.doc_type,
                    "taxable_value": inv.taxable_value,
                    "igst": inv.igst,
                    "cgst": inv.cgst,
                    "sgst": inv.sgst,
                    "cess": inv.cess,
                    "invoice_total": inv.invoice_total,
                    "is_valid": inv.is_valid,
                    "validation_errors": inv.validation_errors,
                }
            ) for inv in books_db_invoices
        ]

        gstr2b_inputs = [
            (
                inv.id,
                {
                    "supplier_gstin": inv.supplier_gstin,
                    "supplier_name": inv.supplier_name,
                    "invoice_number_raw": inv.invoice_number_raw,
                    "invoice_number_norm": inv.invoice_number_norm,
                    "invoice_date": inv.invoice_date,
                    "doc_type": inv.doc_type,
                    "taxable_value": inv.taxable_value,
                    "igst": inv.igst,
                    "cgst": inv.cgst,
                    "sgst": inv.sgst,
                    "cess": inv.cess,
                    "invoice_total": inv.invoice_total,
                    "is_valid": inv.is_valid,
                    "validation_errors": inv.validation_errors,
                }
            ) for inv in gstr2b_db_invoices
        ]

        tolerances = run.tolerances or {"tax_diff_max": 1.0, "date_days_diff": 30}
        matches_result, books_dups, gstr2b_dups = execute_matching_engine(
            books_records=books_inputs,
            gstr2b_records=gstr2b_inputs,
            tolerances=tolerances,
        )

        # Step 5: Classify discrepancies and persist matches
        for m_data in matches_result:
            b_cand = m_data.get("books_candidate")
            g_cand = m_data.get("gstr2b_candidate")

            match_row = GSTInvoiceMatch(
                run_id=run.id,
                books_invoice_id=b_cand.id if b_cand else None,
                gstr2b_invoice_id=g_cand.id if g_cand else None,
                match_stage=m_data.get("stage"),
                confidence_score=m_data.get("confidence_score", 1.0),
                match_rule_reason=m_data.get("reason"),
                is_manually_linked=False,
            )
            session.add(match_row)
            await session.flush()

            discrepancy_list = classify_match_discrepancies(
                match_dict=m_data,
                books_duplicates=books_dups,
                gstr2b_duplicates=gstr2b_dups,
                tolerances=tolerances,
            )

            for d in discrepancy_list:
                disc_row = GSTDiscrepancy(
                    match_id=match_row.id,
                    category=d["category"],
                    books_value=str(d.get("books_value")) if d.get("books_value") is not None else None,
                    gstr2b_value=str(d.get("gstr2b_value")) if d.get("gstr2b_value") is not None else None,
                    difference=d.get("difference", Decimal("0.00")),
                    explanation=d.get("explanation"),
                    suggested_action=d.get("suggested_action"),
                )
                session.add(disc_row)

        run.status = GSTRunStatus.COMPLETED
        audit = GSTReviewAudit(
            run_id=run.id,
            user_id=run.user_id,
            action=f"Reconciliation completed successfully with {len(matches_result)} matched/unmatched records."
        )
        session.add(audit)
        await session.commit()
        logger.info(f"GST Reconciliation Run {run_id} finished successfully.")

    except Exception as e:
        logger.exception(f"GST Reconciliation Run {run_id} failed: {e}")
        try:
            await session.rollback()
        except Exception:
            pass
        try:
            async with async_session_factory() as err_session:
                err_run = await err_session.get(GSTReconciliationRun, run_id)
                if err_run:
                    err_run.status = GSTRunStatus.FAILED
                    err_run.error_message = str(e)[:500]
                    audit = GSTReviewAudit(
                        run_id=run_id,
                        user_id=err_run.user_id,
                        action=f"Reconciliation failed: {str(e)[:200]}"
                    )
                    err_session.add(audit)
                    await err_session.commit()
        except Exception as persist_err:
            logger.error(f"Failed to persist failure status for run {run_id}: {persist_err}")
