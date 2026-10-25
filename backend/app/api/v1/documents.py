import os
import aiofiles
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import get_settings
from app.models.domain import Document, User
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.services.document import extract_and_index_document

settings = get_settings()
router = APIRouter()

# Simple mock for user injection. In a real scenario, this would check the JWT.
async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    # Retrieve the first user as a mock for Milestone 1.
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        # Create a dummy user if none exists
        user = User(email="test@vitty.ai", hashed_password="fake")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Ensure storage directory exists
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    
    # Save file locally
    file_path = os.path.join(settings.STORAGE_DIR, f"{user.id}_{file.filename}")
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
        
    # Create DB Record
    new_doc = Document(
        user_id=user.id,
        filename=file.filename,
        original_path=file_path
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    # Fire off background extraction task
    background_tasks.add_task(extract_and_index_document, new_doc.id, file_path)
    
    return new_doc

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(select(Document).where(Document.user_id == user.id))
    docs = result.scalars().all()
    return DocumentListResponse(items=docs)

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    doc = await db.get(Document, document_id)
    if not doc or doc.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
