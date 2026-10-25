from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db, async_session_factory
from app.models.domain import User, Workflow, WorkflowStatus, DiscrepancyFinding, AuditLog
from app.schemas.workflow import (
    WorkflowStartRequest,
    WorkflowResponse,
    WorkflowListItemResponse,
    ReviewRequest,
    WorkflowDecisionRequest,
)
from app.workflows.invoice_verification import execute_invoice_verification

# Re-use current user mock from documents.py
async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        user = User(email="test@vitty.ai", hashed_password="fake")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user

router = APIRouter()

@router.get("/", response_model=List[WorkflowListItemResponse])
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all invoice verification workflows for the authenticated user."""
    stmt = (
        select(Workflow)
        .options(
            selectinload(Workflow.findings),
            selectinload(Workflow.invoice_document),
            selectinload(Workflow.reference_document),
        )
        .where(Workflow.user_id == user.id)
        .order_by(desc(Workflow.created_at))
    )
    result = await db.execute(stmt)
    workflows = result.scalars().all()

    items = []
    for wf in workflows:
        findings = wf.findings or []
        pending = sum(1 for f in findings if f.review_status is None)
        items.append(
            WorkflowListItemResponse(
                id=wf.id,
                invoice_document_id=wf.invoice_document_id,
                reference_document_id=wf.reference_document_id,
                invoice_filename=wf.invoice_document.filename if wf.invoice_document else None,
                reference_filename=wf.reference_document.filename if wf.reference_document else None,
                status=wf.status,
                created_at=wf.created_at,
                total_findings=len(findings),
                pending_reviews=pending,
            )
        )
    return items


@router.post("/invoice-verification", response_model=WorkflowResponse)
async def start_workflow(
    request: WorkflowStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    workflow = Workflow(
        user_id=user.id,
        invoice_document_id=request.invoice_document_id,
        reference_document_id=request.reference_document_id,
        status=WorkflowStatus.STARTED
    )
    db.add(workflow)
    await db.flush()

    audit = AuditLog(
        workflow_id=workflow.id,
        user_id=user.id,
        action="Started invoice verification workflow"
    )
    db.add(audit)
    await db.commit()

    workflow_id = workflow.id
    response_data = WorkflowResponse(
        id=workflow.id,
        user_id=workflow.user_id,
        invoice_document_id=workflow.invoice_document_id,
        reference_document_id=workflow.reference_document_id,
        status=workflow.status,
        created_at=workflow.created_at,
        findings=[]
    )

    background_tasks.add_task(execute_invoice_verification_bg, workflow_id)
    return response_data


async def execute_invoice_verification_bg(workflow_id: UUID) -> None:
    """Wrapper that opens its own DB session for the background task."""
    async with async_session_factory() as session:
        await execute_invoice_verification(workflow_id, session)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    stmt = (
        select(Workflow)
        .options(
            selectinload(Workflow.findings),
            selectinload(Workflow.invoice_document),
            selectinload(Workflow.reference_document),
        )
        .where(Workflow.id == workflow_id)
    )
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()

    if not workflow or workflow.user_id != user.id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    response = WorkflowResponse(
        id=workflow.id,
        user_id=workflow.user_id,
        invoice_document_id=workflow.invoice_document_id,
        reference_document_id=workflow.reference_document_id,
        invoice_filename=workflow.invoice_document.filename if workflow.invoice_document else None,
        reference_filename=workflow.reference_document.filename if workflow.reference_document else None,
        status=workflow.status,
        created_at=workflow.created_at,
        findings=workflow.findings or [],
    )
    return response


@router.post("/{workflow_id}/review")
async def review_finding(
    workflow_id: UUID,
    request: ReviewRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    stmt = (
        select(Workflow)
        .options(selectinload(Workflow.findings))
        .where(Workflow.id == workflow_id)
    )
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()

    if not workflow or workflow.user_id != user.id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    finding = await db.get(DiscrepancyFinding, request.finding_id)
    if not finding or finding.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Finding not found")

    finding.review_status = request.decision
    finding.reviewer_id = user.id

    audit = AuditLog(
        workflow_id=workflow.id,
        user_id=user.id,
        action=f"Reviewed finding {finding.id}: {request.decision.value}" + (f" ({request.reason})" if request.reason else "")
    )
    db.add(audit)

    # Check if all findings are reviewed
    all_reviewed = all(f.review_status is not None for f in workflow.findings)
    if all_reviewed and workflow.status == WorkflowStatus.IN_REVIEW:
        workflow.status = WorkflowStatus.APPROVED

    await db.commit()
    return {"success": True, "workflow_status": workflow.status}


@router.post("/{workflow_id}/decision")
async def decide_workflow(
    workflow_id: UUID,
    request: WorkflowDecisionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Final decision (APPROVE/REJECT) on the workflow report by the CA/Auditor."""
    workflow = await db.get(Workflow, workflow_id)
    if not workflow or workflow.user_id != user.id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow.status = request.status
    audit = AuditLog(
        workflow_id=workflow.id,
        user_id=user.id,
        action=f"Auditor marked workflow as {request.status.value}" + (f" - Reason: {request.reason}" if request.reason else "")
    )
    db.add(audit)
    await db.commit()
    return {"success": True, "workflow_status": workflow.status}


@router.get("/{workflow_id}/report")
async def get_workflow_report(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    stmt = (
        select(Workflow)
        .options(
            selectinload(Workflow.findings),
            selectinload(Workflow.invoice_document),
            selectinload(Workflow.reference_document),
            selectinload(Workflow.audit_logs),
        )
        .where(Workflow.id == workflow_id)
    )
    result = await db.execute(stmt)
    workflow = result.scalar_one_or_none()

    if not workflow or workflow.user_id != user.id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    findings = workflow.findings or []
    pending_count = sum(1 for f in findings if f.review_status is None)
    reviewed_count = len(findings) - pending_count

    return {
        "workflow_id": str(workflow.id),
        "invoice_id": str(workflow.invoice_document_id),
        "invoice_filename": workflow.invoice_document.filename if workflow.invoice_document else None,
        "reference_id": str(workflow.reference_document_id) if workflow.reference_document_id else None,
        "reference_filename": workflow.reference_document.filename if workflow.reference_document else None,
        "status": workflow.status,
        "created_at": workflow.created_at,
        "summary": {
            "total_findings": len(findings),
            "pending_review": pending_count,
            "reviewed": reviewed_count,
        },
        "findings": [
            {
                "id": str(f.id),
                "rule_id": f.type.value if f.type else None,
                "severity": f.severity.value if f.severity else None,
                "description": f.explanation,
                "status": f.review_status.value if f.review_status else "PENDING",
                "decision": f.review_status.value if f.review_status else None,
                "source_evidence": {"field": f.field, "invoice_value": f.invoice_value, "reference_value": f.reference_value},
            } for f in findings
        ],
        "audit_trail": [
            {
                "id": str(a.id),
                "action": a.action,
                "timestamp": a.timestamp,
            } for a in (workflow.audit_logs or [])
        ]
    }
