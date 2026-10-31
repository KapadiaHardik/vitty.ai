import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.domain import DocumentChunk, Document
from app.services.llm import generate_embedding

logger = logging.getLogger(__name__)


async def search_similar_chunks(
    db: AsyncSession,
    query: str,
    user_id: UUID,
    top_k: int = 3,
) -> list[DocumentChunk]:
    """Search for the most semantically similar chunks to the query, scoped to a user's documents."""

    # 1. Try vector similarity search with pgvector
    try:
        query_embedding = await generate_embedding(query)
        stmt = (
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.user_id == user_id)
            .where(DocumentChunk.embedding.isnot(None))
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        result = await db.execute(stmt)
        chunks = list(result.scalars().all())
        if chunks:
            return chunks
    except Exception as e:
        logger.warning(f"Vector similarity search failed or returned no match: {e}. Falling back to chunk scan...")

    # 2. Resilient fallback: retrieve available chunks for this user's documents
    try:
        fallback_stmt = (
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.user_id == user_id)
            .limit(top_k)
        )
        fallback_res = await db.execute(fallback_stmt)
        return list(fallback_res.scalars().all())
    except Exception as e:
        logger.error(f"Fallback chunk retrieval failed: {e}")
        return []


def build_rag_context(chunks: list[DocumentChunk], max_chars_per_chunk: int = 750) -> str:
    """Format retrieved chunks into a concise context string for fast LLM prompt evaluation."""
    if not chunks:
        return "No relevant documents found."

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        content = (chunk.text_content or "").strip()
        if len(content) > max_chars_per_chunk:
            content = content[:max_chars_per_chunk] + "..."
        context_parts.append(
            f"[Source {i}]\n{content}\n"
        )
    return "\n---\n".join(context_parts)
