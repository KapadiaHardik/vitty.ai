from uuid import UUID
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.domain import (
    GSTRunStatus,
    GSTSourceType,
    GSTDocType,
    GSTMatchStage,
    GSTDiscrepancyCategory,
    GSTReviewStatus,
)


class ColumnMappingPreviewResponse(BaseModel):
    document_id: UUID
    filename: str
    sheets: List[str]
    active_sheet: str
    detected_headers: List[str]
    suggested_mapping: Dict[str, str]  # standard_field -> raw_column_name
    preview_rows: List[Dict[str, Any]]
    total_preview_rows: int


class RunCreateRequest(BaseModel):
    company_gstin: str = Field(..., min_length=15, max_length=15, description="15-digit Company GSTIN")
    tax_period: str = Field(..., description="e.g. 04-2024 or 2024-04")
    gstr2b_document_id: UUID
    purchase_register_document_id: UUID
    gstr2b_column_mapping: Optional[Dict[str, str]] = None
    purchase_register_column_mapping: Optional[Dict[str, str]] = None
    tolerances: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {"tax_diff_max": 1.0, "date_days_diff": 30}
    )


class NormalizedInvoiceResponse(BaseModel):
    id: UUID
    source_type: GSTSourceType
    supplier_gstin: Optional[str] = None
    supplier_name: Optional[str] = None
    invoice_number_raw: Optional[str] = None
    invoice_number_norm: Optional[str] = None
    invoice_date: Optional[date] = None
    doc_type: GSTDocType
    taxable_value: Decimal
    igst: Decimal
    cgst: Decimal
    sgst: Decimal
    cess: Decimal
    invoice_total: Decimal
    pos: Optional[str] = None
    source_file: Optional[str] = None
    source_sheet: Optional[str] = None
    source_row_index: Optional[int] = None
    is_valid: bool
    validation_errors: Optional[List[str]] = None


class DiscrepancyDetailResponse(BaseModel):
    id: UUID
    match_id: UUID
    category: GSTDiscrepancyCategory
    books_value: Optional[str] = None
    gstr2b_value: Optional[str] = None
    difference: Optional[Decimal] = None
    explanation: Optional[str] = None
    suggested_action: Optional[str] = None
    review_status: GSTReviewStatus
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    match_stage: Optional[GSTMatchStage] = None
    confidence_score: Optional[float] = None
    books_invoice: Optional[NormalizedInvoiceResponse] = None
    gstr2b_invoice: Optional[NormalizedInvoiceResponse] = None


class DiscrepancyReviewRequest(BaseModel):
    discrepancy_id: UUID
    review_status: GSTReviewStatus
    reviewer_notes: Optional[str] = None


class ManualLinkRequest(BaseModel):
    books_invoice_id: UUID
    gstr2b_invoice_id: UUID
    notes: Optional[str] = None


class ReconciliationMetrics(BaseModel):
    total_books_records: int = 0
    total_gstr2b_records: int = 0
    matched_count: int = 0
    books_only_count: int = 0
    gstr2b_only_count: int = 0
    taxable_mismatch_count: int = 0
    tax_mismatch_count: int = 0
    date_mismatch_count: int = 0
    duplicate_count: int = 0
    potential_match_count: int = 0
    invalid_record_count: int = 0
    
    # Financial sums
    total_books_taxable: Decimal = Decimal("0.00")
    total_gstr2b_taxable: Decimal = Decimal("0.00")
    diff_taxable: Decimal = Decimal("0.00")
    total_books_igst: Decimal = Decimal("0.00")
    total_gstr2b_igst: Decimal = Decimal("0.00")
    diff_igst: Decimal = Decimal("0.00")
    total_books_cgst: Decimal = Decimal("0.00")
    total_gstr2b_cgst: Decimal = Decimal("0.00")
    diff_cgst: Decimal = Decimal("0.00")
    total_books_sgst: Decimal = Decimal("0.00")
    total_gstr2b_sgst: Decimal = Decimal("0.00")
    diff_sgst: Decimal = Decimal("0.00")
    total_books_cess: Decimal = Decimal("0.00")
    total_gstr2b_cess: Decimal = Decimal("0.00")
    diff_cess: Decimal = Decimal("0.00")
    
    # Review counts
    pending_reviews: int = 0
    resolved_reviews: int = 0


class ReconciliationRunDetailResponse(BaseModel):
    id: UUID
    company_gstin: str
    tax_period: str
    status: GSTRunStatus
    error_message: Optional[str] = None
    created_at: datetime
    metrics: ReconciliationMetrics
    gstr2b_filename: Optional[str] = None
    purchase_register_filename: Optional[str] = None


class ReconciliationRunListItem(BaseModel):
    id: UUID
    company_gstin: str
    tax_period: str
    status: GSTRunStatus
    created_at: datetime
    total_books_records: int = 0
    total_gstr2b_records: int = 0
    matched_count: int = 0
    mismatch_count: int = 0
    pending_reviews: int = 0
