# [Vitty.ai](http://Vitty.ai)

Multimodal AI work engine for financial, accounting, legal and BFSI firms.

## Architecture

PDF

→ Docling

→ Multimodal document representation

→ OpenAI embeddings

→ FAISS

→ Retrieval

→ GPT-5.4 mini

→ LangGraph workflow

→ Human review

## Models

Classification:

GPT-5.4 nano

Reasoning:

GPT-5.4 mini

Vision:

GPT-5.4 mini

Embeddings:

text-embedding-3-small

## Setup

Create virtual environment:

python -m venv .venv

Activate it.

Install:

pip install -r requirements.txt

Create `.env`:

OPENAI_API_KEY=your_key

Run:

uvicorn app.main:app --reload

Open:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)