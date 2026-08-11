import json

import ollama

from config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    VISION_MODEL
)

from prompts import (
    DOCUMENT_ANALYSIS_PROMPT,
    VISION_ANALYSIS_PROMPT
)


def analyze_document(document_text: str) -> dict:

    prompt = DOCUMENT_ANALYSIS_PROMPT.format(
        document_text=document_text[:30000]
    )

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0
        }
    )

    content = response["message"]["content"].strip()

    if content.startswith("```"):
        content = content.replace("```json", "")
        content = content.replace("```", "").strip()

    try:
        return json.loads(content)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM returned invalid JSON: {content}"
        ) from exc


def analyze_image(image_path: str) -> str:

    response = ollama.chat(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": VISION_ANALYSIS_PROMPT,
                "images": [image_path]
            }
        ],
        options={
            "temperature": 0
        }
    )

    return response["message"]["content"].strip()