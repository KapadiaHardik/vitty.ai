import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer, Text
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
