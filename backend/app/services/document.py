import os
import pymupdf
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.domain import Document, DocumentChunk, DocumentStatus
from app.services.llm import generate_embedding
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def extract_and_index_document(document_id: UUID, file_path: str):
    """Background task to extract text, chunk it, and index it into pgvector."""
    
    # We need a new session since this runs in a background task thread
    async with AsyncSessionLocal() as session:
        # Fetch the document
        doc = await session.get(Document, document_id)
        if not doc:
            logger.error(f"Document {document_id} not found for indexing.")
            return

        doc.status = DocumentStatus.PROCESSING
        await session.commit()

        try:
            # 1. Extract Text
            text_content = ""
            if file_path.endswith(".pdf"):
                with pymupdf.open(file_path) as pdf_doc:
                    for page in pdf_doc:
                        text_content += page.get_text() + "\n"
            else:
                # Fallback for plain text or markdown
                with open(file_path, "r", encoding="utf-8") as f:
                    text_content = f.read()

            # 2. Chunk Text (Very basic naive chunking for Milestone 1)
            # In later phases, use LangChain text splitters or better semantic chunking
            chunk_size = 1000
            chunks = [text_content[i:i+chunk_size] for i in range(0, len(text_content), chunk_size)]

            # 3. Embed and Store
            for i, chunk_text in enumerate(chunks):
                # Clean text a bit
                clean_text = chunk_text.strip()
                if not clean_text:
                    continue

                embedding = await generate_embedding(clean_text)
                
                doc_chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=i,
                    text_content=clean_text,
                    embedding=embedding
                )
                session.add(doc_chunk)

            doc.status = DocumentStatus.INDEXED
            await session.commit()
            logger.info(f"Successfully indexed document {document_id} into {len(chunks)} chunks.")

        except Exception as e:
            logger.exception(f"Failed to process document {document_id}: {e}")
            doc.status = DocumentStatus.FAILED
            await session.commit()
