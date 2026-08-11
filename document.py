import json
import uuid
from pathlib import Path

from docling.document_converter import DocumentConverter

from config import (
    UPLOAD_DIR,
    METADATA_DIR,
    IMAGE_DIR,
    TABLE_DIR
)

from llm import (
    analyze_document,
    analyze_image
)

from rag import add_document_to_vectorstore


converter = DocumentConverter()


def save_uploaded_file(
    file_bytes: bytes,
    filename: str
) -> tuple[str, Path]:

    document_id = str(uuid.uuid4())

    extension = Path(filename).suffix.lower()

    if extension != ".pdf":
        raise ValueError(
            "Only PDF files are supported."
        )

    file_path = UPLOAD_DIR / f"{document_id}.pdf"

    file_path.write_bytes(file_bytes)

    return document_id, file_path


def parse_document(
    file_path: Path,
    document_id: str
) -> dict:

    result = converter.convert(
        str(file_path)
    )

    document = result.document

    markdown = document.export_to_markdown()

    if not markdown.strip():
        raise ValueError(
            "Could not extract text from document."
        )

    elements = []

    # Text representation
    elements.append({
        "type": "text",
        "page": None,
        "content": markdown
    })

    # Extract tables
    for index, table in enumerate(
        document.tables
    ):

        try:
            table_text = table.export_to_markdown()

        except Exception:
            table_text = str(table)

        table_path = (
            TABLE_DIR /
            f"{document_id}_table_{index}.md"
        )

        table_path.write_text(
            table_text,
            encoding="utf-8"
        )

        elements.append({
            "type": "table",
            "page": None,
            "content": table_text,
            "path": str(table_path)
        })

    # Extract pictures
    for index, picture in enumerate(
        document.pictures
    ):

        image_path = (
            IMAGE_DIR /
            f"{document_id}_image_{index}.png"
        )

        try:
            picture.image.pil_image.save(
                image_path
            )

            elements.append({
                "type": "image",
                "page": None,
                "path": str(image_path)
            })

        except Exception:
            continue

    return {
        "markdown": markdown,
        "elements": elements
    }


def save_metadata(
    document_id: str,
    filename: str,
    metadata: dict,
    elements: list
) -> Path:

    data = {
        "document_id": document_id,
        "filename": filename,
        **metadata,
        "elements": elements
    }

    metadata_path = (
        METADATA_DIR /
        f"{document_id}.json"
    )

    metadata_path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    return metadata_path


def process_document(
    file_bytes: bytes,
    filename: str
) -> dict:

    document_id, file_path = save_uploaded_file(
        file_bytes,
        filename
    )

    parsed = parse_document(
        file_path,
        document_id
    )

    markdown = parsed["markdown"]
    elements = parsed["elements"]

    metadata = analyze_document(
        markdown
    )

    # Generate searchable descriptions for images
    for element in elements:

        if element["type"] != "image":
            continue

        try:
            description = analyze_image(
                element["path"]
            )

            element["description"] = description

        except Exception as exc:
            element["description"] = (
                f"Visual analysis failed: {exc}"
            )

    # Add text, tables and visual descriptions
    # to vector index.
    chunk_count = add_document_to_vectorstore(
        document_id=document_id,
        filename=filename,
        elements=elements
    )

    metadata_path = save_metadata(
        document_id=document_id,
        filename=filename,
        metadata=metadata,
        elements=elements
    )

    return {
        "document_id": document_id,
        "filename": filename,
        "document_type": metadata.get(
            "document_type"
        ),
        "client_name": metadata.get(
            "client_name"
        ),
        "financial_year": metadata.get(
            "financial_year"
        ),
        "summary": metadata.get(
            "summary"
        ),
        "elements": len(elements),
        "indexed_chunks": chunk_count,
        "metadata_path": str(metadata_path)
    }