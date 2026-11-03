import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer, Text, Numeric, Date, Boolean, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base
import enum

class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_path = Column(String(512), nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    owner = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=False)
    
    # pgvector embedding column. We use 768 dimensions for nomic-embed-text
    embedding = Column(Vector(768), nullable=True)

    document = relationship("Document", back_populates="chunks")

class WorkflowStatus(str, enum.Enum):
    STARTED = "STARTED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"

class DiscrepancyType(str, enum.Enum):
    SUPPLIER_MISMATCH = "SUPPLIER_MISMATCH"
    PO_MISMATCH = "PO_MISMATCH"
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
    PRICE_MISMATCH = "PRICE_MISMATCH"
    TAX_MISMATCH = "TAX_MISMATCH"
    TOTAL_MISMATCH = "TOTAL_MISMATCH"
    MISSING_FIELD = "MISSING_FIELD"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"

class Severity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class ReviewDecision(str, enum.Enum):
    ACCEPTED = "ACCEPTED"
    DISMISSED = "DISMISSED"
    CORRECTED = "CORRECTED"

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    invoice_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    reference_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.STARTED, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User")
    invoice_document = relationship("Document", foreign_keys=[invoice_document_id])
    reference_document = relationship("Document", foreign_keys=[reference_document_id])
    findings = relationship("DiscrepancyFinding", back_populates="workflow", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="workflow", cascade="all, delete-orphan")

class DiscrepancyFinding(Base):
    __tablename__ = "discrepancy_findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, index=True)
    type = Column(Enum(DiscrepancyType), nullable=False)
    severity = Column(Enum(Severity), nullable=False)
    field = Column(String(255), nullable=True)
    invoice_value = Column(Text, nullable=True)
    reference_value = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    review_status = Column(Enum(ReviewDecision), nullable=True)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    workflow = relationship("Workflow", back_populates="findings")
    reviewer = relationship("User")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(255), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    workflow = relationship("Workflow", back_populates="audit_logs")
    user = relationship("User")


# ==========================================
# GST Reconciliation Engine Domain Models
# ==========================================

class GSTRunStatus(str, enum.Enum):
    PENDING = "PENDING"
    PARSING = "PARSING"
    MATCHING = "MATCHING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class GSTSourceType(str, enum.Enum):
    GSTR_2B = "GSTR_2B"
    PURCHASE_REGISTER = "PURCHASE_REGISTER"

class GSTDocType(str, enum.Enum):
    INV = "INV"
    CRN = "CRN"
    DBN = "DBN"

class GSTMatchStage(str, enum.Enum):
    STAGE_1_EXACT = "STAGE_1_EXACT"
    STAGE_2_STRONG = "STAGE_2_STRONG"
    STAGE_3_FLEXIBLE = "STAGE_3_FLEXIBLE"
    STAGE_4_POTENTIAL = "STAGE_4_POTENTIAL"
    MANUAL = "MANUAL"

class GSTDiscrepancyCategory(str, enum.Enum):
    MATCHED = "MATCHED"
    BOOKS_ONLY = "BOOKS_ONLY"
    GSTR2B_ONLY = "GSTR2B_ONLY"
    TAXABLE_VALUE_MISMATCH = "TAXABLE_VALUE_MISMATCH"
    IGST_MISMATCH = "IGST_MISMATCH"
    CGST_MISMATCH = "CGST_MISMATCH"
    SGST_MISMATCH = "SGST_MISMATCH"
    CESS_MISMATCH = "CESS_MISMATCH"
    INVOICE_DATE_MISMATCH = "INVOICE_DATE_MISMATCH"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"
    CREDIT_DEBIT_NOTE_MISMATCH = "CREDIT_DEBIT_NOTE_MISMATCH"
    POTENTIAL_MATCH = "POTENTIAL_MATCH"
    INVALID_OR_INCOMPLETE_RECORD = "INVALID_OR_INCOMPLETE_RECORD"

class GSTReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
    ACCEPTED_DIFF = "ACCEPTED_DIFF"
    REJECTED_MATCH = "REJECTED_MATCH"
    VENDOR_FOLLOW_UP = "VENDOR_FOLLOW_UP"

class GSTReconciliationRun(Base):
    __tablename__ = "gst_reconciliation_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    company_gstin = Column(String(15), nullable=False, index=True)
    tax_period = Column(String(20), nullable=False, index=True)  # e.g., "04-2024" or "2024-04"
    status = Column(Enum(GSTRunStatus), default=GSTRunStatus.PENDING, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    tolerances = Column(JSON, nullable=True)  # e.g. {"tax_diff_max": 1.0, "date_days_diff": 30}
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User")
    documents = relationship("GSTSourceDocument", back_populates="run", cascade="all, delete-orphan")
    invoices = relationship("GSTNormalizedInvoice", back_populates="run", cascade="all, delete-orphan")
    matches = relationship("GSTInvoiceMatch", back_populates="run", cascade="all, delete-orphan")
    audit_logs = relationship("GSTReviewAudit", back_populates="run", cascade="all, delete-orphan")

class GSTSourceDocument(Base):
    __tablename__ = "gst_source_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("gst_reconciliation_runs.id"), nullable=False, index=True)
    source_type = Column(Enum(GSTSourceType), nullable=False)
    filename = Column(String(255), nullable=False)
    original_path = Column(String(512), nullable=False)
    row_count = Column(Integer, default=0, nullable=False)
    column_mapping = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    run = relationship("GSTReconciliationRun", back_populates="documents")

class GSTNormalizedInvoice(Base):
    __tablename__ = "gst_normalized_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("gst_reconciliation_runs.id"), nullable=False, index=True)
    source_type = Column(Enum(GSTSourceType), nullable=False, index=True)
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("gst_source_documents.id"), nullable=True)

    # Core GST Fields
    supplier_gstin = Column(String(15), nullable=True, index=True)
    supplier_name = Column(String(255), nullable=True)
    invoice_number_raw = Column(String(100), nullable=True)
    invoice_number_norm = Column(String(100), nullable=True, index=True)
    invoice_date = Column(Date, nullable=True, index=True)
    doc_type = Column(Enum(GSTDocType), default=GSTDocType.INV, nullable=False)

    # Financial / Tax amounts (Numeric for decimal precision, no float rounding)
    taxable_value = Column(Numeric(14, 2), default=0.00, nullable=False)
    igst = Column(Numeric(14, 2), default=0.00, nullable=False)
    cgst = Column(Numeric(14, 2), default=0.00, nullable=False)
    sgst = Column(Numeric(14, 2), default=0.00, nullable=False)
    cess = Column(Numeric(14, 2), default=0.00, nullable=False)
    invoice_total = Column(Numeric(14, 2), default=0.00, nullable=False)
    pos = Column(String(10), nullable=True)

    # Source Line Traceability
    source_file = Column(String(255), nullable=True)
    source_sheet = Column(String(100), nullable=True)
    source_row_index = Column(Integer, nullable=True)
    raw_record_data = Column(JSON, nullable=True)  # Preserves the original extracted values

    # Validation
    is_valid = Column(Boolean, default=True, nullable=False)
    validation_errors = Column(JSON, nullable=True)

    run = relationship("GSTReconciliationRun", back_populates="invoices")

class GSTInvoiceMatch(Base):
    __tablename__ = "gst_invoice_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("gst_reconciliation_runs.id"), nullable=False, index=True)
    books_invoice_id = Column(UUID(as_uuid=True), ForeignKey("gst_normalized_invoices.id"), nullable=True, index=True)
    gstr2b_invoice_id = Column(UUID(as_uuid=True), ForeignKey("gst_normalized_invoices.id"), nullable=True, index=True)
    match_stage = Column(Enum(GSTMatchStage), nullable=True)
    confidence_score = Column(Float, default=1.0, nullable=False)
    match_rule_reason = Column(String(255), nullable=True)
    is_manually_linked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    run = relationship("GSTReconciliationRun", back_populates="matches")
    books_invoice = relationship("GSTNormalizedInvoice", foreign_keys=[books_invoice_id])
    gstr2b_invoice = relationship("GSTNormalizedInvoice", foreign_keys=[gstr2b_invoice_id])
    discrepancies = relationship("GSTDiscrepancy", back_populates="match", cascade="all, delete-orphan")

class GSTDiscrepancy(Base):
    __tablename__ = "gst_discrepancies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("gst_invoice_matches.id"), nullable=False, index=True)
    category = Column(Enum(GSTDiscrepancyCategory), nullable=False, index=True)
    books_value = Column(String(255), nullable=True)
    gstr2b_value = Column(String(255), nullable=True)
    difference = Column(Numeric(14, 2), default=0.00, nullable=True)
    explanation = Column(Text, nullable=True)
    suggested_action = Column(String(255), nullable=True)

    # CA Review Status
    review_status = Column(Enum(GSTReviewStatus), default=GSTReviewStatus.PENDING, nullable=False, index=True)
    reviewer_notes = Column(Text, nullable=True)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    match = relationship("GSTInvoiceMatch", back_populates="discrepancies")
    reviewer = relationship("User")

class GSTReviewAudit(Base):
    __tablename__ = "gst_review_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("gst_reconciliation_runs.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    match_id = Column(UUID(as_uuid=True), ForeignKey("gst_invoice_matches.id"), nullable=True)
    discrepancy_id = Column(UUID(as_uuid=True), ForeignKey("gst_discrepancies.id"), nullable=True)
    action = Column(String(255), nullable=False)
    previous_state = Column(String(255), nullable=True)
    new_state = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    run = relationship("GSTReconciliationRun", back_populates="audit_logs")
    user = relationship("User")
