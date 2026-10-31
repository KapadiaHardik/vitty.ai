import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.domain import User
from app.schemas.chat import ChatRequest, ChatResponse, SourceReference
from app.services.retrieval import search_similar_chunks, build_rag_context
from app.services.llm import generate_completion
from app.api.v1.documents import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

RAG_PROMPT_TEMPLATE = """You are Vitty AI, an intelligent document assistant for financial auditors and accountants.
Answer the user's question directly based ONLY on the provided context from their uploaded documents.
Be concise, direct, and factual (2-4 sentences unless more detail is requested).
If the context does not contain enough information to answer, state that clearly.
Always cite which source(s) you used.

CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:"""


@router.post("/", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Ask a question against the user's uploaded documents using RAG."""

    # 1. Retrieve relevant chunks (top_k=3 default for fast inference)
    chunks = await search_similar_chunks(
        db=db,
        query=request.question,
        user_id=user.id,
        top_k=request.top_k or 3,
    )

    # 2. Build context from chunks
    context = build_rag_context(chunks)

    # 3. Generate grounded answer via cloud LLM
    prompt = RAG_PROMPT_TEMPLATE.format(
        context=context,
        question=request.question,
    )
    try:
        answer = await generate_completion(prompt, max_tokens=300, temperature=0.1, think=False)
    except Exception as e:
        logger.exception(f"Error during LLM answer generation: {e}")
        answer = f"I retrieved your document, but encountered an error contacting the AI model: {str(e)}"

    # 4. Build source references
    sources = [
        SourceReference(
            chunk_index=chunk.chunk_index,
            text_snippet=chunk.text_content[:200] + "..." if len(chunk.text_content) > 200 else chunk.text_content,
        )
        for chunk in chunks
    ]

    return ChatResponse(answer=answer, sources=sources)
