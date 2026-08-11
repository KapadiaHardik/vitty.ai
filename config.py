import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen3:8b"
)

VISION_MODEL = os.getenv(
    "VISION_MODEL",
    "qwen2.5vl:3b"
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "nomic-embed-text"
)

UPLOAD_DIR = Path(
    os.getenv("UPLOAD_DIR", "storage/uploads")
)

METADATA_DIR = Path(
    os.getenv("METADATA_DIR", "storage/metadata")
)

IMAGE_DIR = Path(
    os.getenv("IMAGE_DIR", "storage/images")
)

TABLE_DIR = Path(
    os.getenv("TABLE_DIR", "storage/tables")
)

VECTOR_DIR = Path(
    os.getenv("VECTOR_DIR", "storage/vectors")
)

CHUNK_SIZE = int(
    os.getenv("CHUNK_SIZE", "1000")
)

CHUNK_OVERLAP = int(
    os.getenv("CHUNK_OVERLAP", "150")
)

TOP_K = int(
    os.getenv("TOP_K", "5")
)


for directory in [
    UPLOAD_DIR,
    METADATA_DIR,
    IMAGE_DIR,
    TABLE_DIR,
    VECTOR_DIR
]:
    directory.mkdir(parents=True, exist_ok=True)