from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from app.models.domain import DocumentStatus

class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    status: DocumentStatus
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
