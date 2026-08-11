from pathlib import Path

from langchain_ollama import (
    OllamaEmbeddings,
    ChatOllama
)

from langchain_core.documents import Document

from langchain_community.vectorstores import FAISS

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    EMBEDDING_MODEL,
    VECTOR_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K
)

from prompts import RAG_PROMPT


embeddings = OllamaEmbeddings(
    model=EMBEDDING_MODEL,
    base_url=OLLAMA_BASE_URL
)


llm = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0
)


def create_documents(
    document_id: str,
    filename: str,
    elements: list
) -> list[Document]:

    documents = []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    for element in elements:

        element_type = element["type"]

        if element_type == "text":

            chunks = splitter.split_text(
                element["content"]
            )

            for index, chunk in enumerate(chunks):

                documents.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "document_id": document_id,
                            "filename": filename,
                            "element_type": "text",
                            "page": element.get("page"),
                            "chunk_id": index
                        }
                    )
                )

        elif element_type == "table":

            documents.append(
                Document(
                    page_content=element["content"],
                    metadata={
                        "document_id": document_id,
                        "filename": filename,
                        "element_type": "table",
                        "page": element.get("page"),
                        "path": element.get("path")
                    }
                )
            )

        elif element_type == "image":

            description = element.get(
                "description"
            )

            if not description:
                continue

            documents.append(
                Document(
                    page_content=description,
                    metadata={
                        "document_id": document_id,
                        "filename": filename,
                        "element_type": "image",
                        "page": element.get("page"),
                        "path": element.get("path")
                    }
                )
            )

    return documents


def load_vectorstore():

    index_path = VECTOR_DIR / "faiss_index"

    if not index_path.exists():
        raise ValueError(
            "No documents have been indexed yet."
        )

    return FAISS.load_local(
        str(index_path),
        embeddings,
        allow_dangerous_deserialization=True
    )


def add_document_to_vectorstore(
    document_id: str,
    filename: str,
    elements: list
) -> int:

    documents = create_documents(
        document_id=document_id,
        filename=filename,
        elements=elements
    )

    if not documents:
        raise ValueError(
            "No searchable content found."
        )

    index_path = VECTOR_DIR / "faiss_index"

    if index_path.exists():

        vectorstore = load_vectorstore()

        vectorstore.add_documents(
            documents
        )

    else:

        vectorstore = FAISS.from_documents(
            documents,
            embeddings
        )

    vectorstore.save_local(
        str(index_path)
    )

    return len(documents)


def search_documents(
    query: str,
    top_k: int = TOP_K
):

    vectorstore = load_vectorstore()

    return vectorstore.similarity_search(
        query,
        k=top_k
    )


def build_context(
    results: list[Document]
) -> str:

    context_parts = []

    for doc in results:

        metadata = doc.metadata

        source = (
            f"Document: {metadata.get('filename')}\n"
            f"Page: {metadata.get('page')}\n"
            f"Type: {metadata.get('element_type')}\n"
        )

        context_parts.append(
            f"{source}\n"
            f"Content:\n{doc.page_content}"
        )

    return "\n\n---\n\n".join(
        context_parts
    )


def chat_with_documents(
    question: str,
    top_k: int = TOP_K
) -> dict:

    results = search_documents(
        query=question,
        top_k=top_k
    )

    if not results:
        return {
            "answer": (
                "The information is not available "
                "in the provided documents."
            ),
            "sources": []
        }

    context = build_context(results)

    prompt = RAG_PROMPT.format(
        context=context,
        question=question
    )

    response = llm.invoke(prompt)

    sources = []

    for doc in results:

        sources.append({
            "document": doc.metadata.get(
                "filename"
            ),
            "page": doc.metadata.get(
                "page"
            ),
            "type": doc.metadata.get(
                "element_type"
            ),
            "chunk_id": doc.metadata.get(
                "chunk_id"
            )
        })

    return {
        "answer": response.content,
        "sources": sources
    }