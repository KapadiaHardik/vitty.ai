from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    top_k: int = 3


class SourceReference(BaseModel):
    chunk_index: int
    text_snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceReference]
