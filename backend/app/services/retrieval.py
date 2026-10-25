import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
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

    query_embedding = await generate_embedding(query)

    # Use pgvector's cosine distance operator (<=>)
    # We join with documents to enforce user_id scoping
    stmt = (
        select(DocumentChunk)
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(Document.user_id == user_id)
        .where(DocumentChunk.embedding.isnot(None))
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )

    result = await db.execute(stmt)
    return list(result.scalars().all())


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
