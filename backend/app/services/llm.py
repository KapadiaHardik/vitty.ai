import logging
from typing import Optional, List
import httpx
from openai import AsyncOpenAI
from ollama import AsyncClient
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize Ollama client for local fallback
ollama_client = AsyncClient(host=settings.OLLAMA_BASE_URL)


async def generate_embedding(text: str) -> List[float]:
    """
    Generate embeddings for text using the configured provider:
    - 'gemini': Google text-embedding-004 (768 dimensions)
    - 'openai': OpenAI text-embedding-3-small (with 768 dimensions)
    - 'ollama': local nomic-embed-text (768 dimensions)
    """
    provider = (settings.EMBEDDING_PROVIDER or "ollama").lower()

    if provider == "gemini":
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set when EMBEDDING_PROVIDER is 'gemini'")
        
        model_name = settings.EMBEDDING_MODEL or "text-embedding-004"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:embedContent?key={api_key}"
        payload = {
            "model": f"models/{model_name}",
            "content": {"parts": [{"text": text}]}
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["embedding"]["values"]

    elif provider == "openai":
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set when EMBEDDING_PROVIDER is 'openai'")
        client = AsyncOpenAI(api_key=api_key)
        resp = await client.embeddings.create(
            model=settings.EMBEDDING_MODEL or "text-embedding-3-small",
            input=text,
            dimensions=settings.EMBEDDING_DIMENSIONS or 768,
        )
        return resp.data[0].embedding

    else:
        # Default: Ollama
        response = await ollama_client.embeddings(
            model=settings.EMBEDDING_MODEL or "nomic-embed-text",
            prompt=text,
        )
        return response["embedding"]


async def generate_completion(
    prompt: str,
    max_tokens: int = 300,
    temperature: float = 0.2,
    json_mode: bool = False,
    think: bool = False,
) -> str:
    """
    Generate text completion using the configured provider:
    - 'groq': Ultra fast cloud LLM (e.g. llama-3.3-70b-versatile, llama-3.1-8b-instant)
    - 'gemini': Google Gemini API (e.g. gemini-2.0-flash, gemini-1.5-flash)
    - 'openai': OpenAI API (e.g. gpt-4o-mini)
    - 'ollama': Local Ollama (e.g. llama3, qwen2.5)
    """
    provider = (settings.LLM_PROVIDER or "ollama").lower()

    if provider == "groq":
        api_key = settings.GROQ_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_KEY must be set when LLM_PROVIDER is 'groq'")
        
        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        kwargs = {
            "model": settings.LLM_MODEL or "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await client.chat.completions.create(**kwargs)
        return (response.choices[0].message.content or "").strip()

    elif provider == "gemini":
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set when LLM_PROVIDER is 'gemini'")
        
        # Gemini provides OpenAI-compatible endpoint
        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        kwargs = {
            "model": settings.LLM_MODEL or "gemini-2.0-flash",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await client.chat.completions.create(**kwargs)
        return (response.choices[0].message.content or "").strip()

    elif provider == "openai":
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set when LLM_PROVIDER is 'openai'")
        client = AsyncOpenAI(api_key=api_key)
        kwargs = {
            "model": settings.LLM_MODEL or "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await client.chat.completions.create(**kwargs)
        return (response.choices[0].message.content or "").strip()

    else:
        # Default: Local Ollama
        options = {
            "num_predict": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
        }
        kwargs = {
            "model": settings.LLM_MODEL or "llama3",
            "prompt": prompt,
            "keep_alive": "30m",
            "options": options,
        }
        if think is False:
            kwargs["think"] = False
        if json_mode:
            kwargs["format"] = "json"

        try:
            response = await ollama_client.generate(**kwargs)
            ans = getattr(response, "response", None) or (response.get("response") if isinstance(response, dict) else "")
            return (ans or "").strip()
        except Exception as e:
            if "think" in kwargs:
                kwargs.pop("think")
                response = await ollama_client.generate(**kwargs)
                ans = getattr(response, "response", None) or (response.get("response") if isinstance(response, dict) else "")
                return (ans or "").strip()
            raise e
