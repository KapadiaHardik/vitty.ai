from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.models.domain import WorkflowStatus, DiscrepancyType, Severity, ReviewDecision

class WorkflowStartRequest(BaseModel):
    invoice_document_id: UUID
    reference_document_id: Optional[UUID] = None

class DiscrepancyFindingSchema(BaseModel):
    id: UUID
    type: DiscrepancyType
    severity: Severity
    field: Optional[str] = None
    invoice_value: Optional[str] = None
    reference_value: Optional[str] = None
    explanation: Optional[str] = None
    review_status: Optional[ReviewDecision] = None

    model_config = ConfigDict(from_attributes=True)

class WorkflowResponse(BaseModel):
    id: UUID
    user_id: UUID
    invoice_document_id: UUID
    reference_document_id: Optional[UUID] = None
    invoice_filename: Optional[str] = None
    reference_filename: Optional[str] = None
    status: WorkflowStatus
    created_at: datetime
    findings: List[DiscrepancyFindingSchema] = []

    model_config = ConfigDict(from_attributes=True)

class WorkflowListItemResponse(BaseModel):
    id: UUID
    invoice_document_id: UUID
    reference_document_id: Optional[UUID] = None
    invoice_filename: Optional[str] = None
    reference_filename: Optional[str] = None
    status: WorkflowStatus
    created_at: datetime
    total_findings: int = 0
    pending_reviews: int = 0

    model_config = ConfigDict(from_attributes=True)

class ReviewRequest(BaseModel):
    finding_id: UUID
    decision: ReviewDecision
    reason: Optional[str] = None

class WorkflowDecisionRequest(BaseModel):
    status: WorkflowStatus  # APPROVED or REJECTED
    reason: Optional[str] = None
