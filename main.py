from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException
)

from pydantic import BaseModel, Field

from document import process_document

from rag import (
    chat_with_documents,
    search_documents
)


app = FastAPI(
    title="vitty.ai",
    version="0.2.0"
)


class ChatRequest(BaseModel):

    question: str = Field(
        min_length=1
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=10
    )


class SearchRequest(BaseModel):

    query: str = Field(
        min_length=1
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=10
    )


@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": "vitty.ai",
        "version": "0.2.0"
    }


@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required."
        )

    if not file.filename.lower().endswith(
        ".pdf"
    ):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    try:

        file_bytes = await file.read()

        result = process_document(
            file_bytes=file_bytes,
            filename=file.filename
        )

        return {
            "success": True,
            "document": result
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=422,
            detail=str(exc)
        )

    except Exception as exc:

        print(
            f"Document processing error: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail="Document processing failed."
        )


@app.post("/search")
def search(
    request: SearchRequest
):

    try:

        results = search_documents(
            query=request.query,
            top_k=request.top_k
        )

        return {
            "query": request.query,
            "results": [
                {
                    "document": doc.metadata.get(
                        "filename"
                    ),
                    "page": doc.metadata.get(
                        "page"
                    ),
                    "type": doc.metadata.get(
                        "element_type"
                    ),
                    "content": doc.page_content
                }
                for doc in results
            ]
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@app.post("/chat")
def chat(
    request: ChatRequest
):

    try:

        return chat_with_documents(
            question=request.question,
            top_k=request.top_k
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )