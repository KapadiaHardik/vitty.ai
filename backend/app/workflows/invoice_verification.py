import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.domain import Document, Workflow, WorkflowStatus, DiscrepancyFinding, DiscrepancyType, Severity, AuditLog
from app.workflows.extraction import extract_document_data
from app.workflows.validation import validate_invoice
from app.workflows.comparison import compare_documents

logger = logging.getLogger(__name__)


async def execute_invoice_verification(workflow_id: UUID, db: AsyncSession):
    """
    Orchestrate the real invoice verification workflow:
    1. Fetch documents from DB.
    2. Extract structured fields via LLM (with deterministic heuristic fallback).
    3. Run deterministic arithmetic and completeness validations.
    4. Cross-compare against reference document (e.g. PO) if provided.
    5. Check for duplicate invoices.
    6. Persist discrepancy findings, update workflow status, and log audit trail.
    """
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        logger.error(f"Workflow {workflow_id} not found.")
        return

    try:
        # Step 1: Fetch documents
        invoice_doc = await db.get(Document, workflow.invoice_document_id)
        if not invoice_doc:
            logger.error(f"Invoice document {workflow.invoice_document_id} not found.")
            workflow.status = WorkflowStatus.FAILED
            await db.commit()
            return

        reference_doc = None
        if workflow.reference_document_id:
            reference_doc = await db.get(Document, workflow.reference_document_id)

        # Step 2: Extract data from documents
        invoice_data = await extract_document_data(invoice_doc, is_invoice=True, session=db)
        logger.info(f"Extracted invoice data: {invoice_data}")

        reference_data = None
        if reference_doc:
            reference_data = await extract_document_data(reference_doc, is_invoice=False, session=db)
            logger.info(f"Extracted reference data: {reference_data}")

        findings = []

        # Step 3: Run deterministic validation on invoice
        validation_findings = validate_invoice(invoice_data)
        findings.extend(validation_findings)

        # Step 4: Run cross-document comparison if reference doc is provided
        if reference_data:
            comparison_findings = compare_documents(invoice_data, reference_data)
            findings.extend(comparison_findings)

        # Step 5: Duplicate invoice detection
        inv_num = invoice_data.get("invoice_number")
        if inv_num:
            # Check if any other workflow for this user recorded the same invoice number
            dup_stmt = (
                select(DiscrepancyFinding)
                .join(Workflow, DiscrepancyFinding.workflow_id == Workflow.id)
                .where(
                    Workflow.user_id == workflow.user_id,
                    Workflow.id != workflow.id,
                    DiscrepancyFinding.field == "invoice_number",
                    DiscrepancyFinding.invoice_value == str(inv_num)
                )
            )
            dup_res = await db.execute(dup_stmt)
            if dup_res.scalars().first():
                findings.append({
                    "type": DiscrepancyType.DUPLICATE_INVOICE,
                    "severity": Severity.HIGH,
                    "field": "invoice_number",
                    "invoice_value": str(inv_num),
                    "reference_value": None,
                    "explanation": f"Potential duplicate invoice: Invoice #{inv_num} was processed previously."
                })

        # Step 6: Persist findings to database
        for f in findings:
            db_finding = DiscrepancyFinding(
                workflow_id=workflow.id,
                type=f["type"],
                severity=f["severity"],
                field=f.get("field"),
                invoice_value=str(f.get("invoice_value")) if f.get("invoice_value") is not None else None,
                reference_value=str(f.get("reference_value")) if f.get("reference_value") is not None else None,
                explanation=f.get("explanation")
            )
            db.add(db_finding)

        # Set status based on findings
        workflow.status = WorkflowStatus.IN_REVIEW if findings else WorkflowStatus.APPROVED

        audit_log = AuditLog(
            workflow_id=workflow.id,
            user_id=workflow.user_id,
            action=f"Verification completed with {len(findings)} finding(s)."
        )
        db.add(audit_log)

        await db.commit()
        logger.info(f"Workflow {workflow_id} executed successfully. Status: {workflow.status}")

    except Exception as e:
        logger.exception(f"Workflow {workflow_id} failed with error: {e}")
        workflow.status = WorkflowStatus.FAILED
        audit_log = AuditLog(
            workflow_id=workflow.id,
            user_id=workflow.user_id,
            action=f"Workflow failed: {str(e)[:200]}"
        )
        db.add(audit_log)
        await db.commit()
