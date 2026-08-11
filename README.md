# [VItty.ai](http://VItty.ai) — 3 Sprint PoC Plan



**Goal:** Turn financial documents into structured, searchable data.

- FastAPI setup
- Document upload
- Docling parsing / OCR
- Document classification
- Metadata extraction
- Summarization
- Local file + JSON storage

**Output:**  
`PDF → Parsed Text → Classification → Metadata → Stored Document`

---

## Sprint 2 — RAG & AI Workspace

**Goal:** Make the system understand and search documents.

- Document chunking
- Ollama embeddings
- FAISS vector store
- RAG pipeline
- AI Chat
- Semantic document search
- Source/citation retrieval
- AI document summarization

**Output:**  
`Documents → FAISS → RAG → Q&A / Search`

---



## Sprint 3 — AI Actions & Agentic Workflow

**Goal:** Move from "AI answers" to "AI performs work."

- AI drafting
  - Client email
  - Notice reply
  - Follow-up
- LangGraph integration
- Document Agent
- Workflow Agent
- Task generation
- Human approval step
- End-to-end demo workflow

**Output:**

```text
Document Upload
      ↓
AI Understands
      ↓
Identifies Required Action
      ↓
Creates Task
      ↓
Generates Draft
      ↓
Human Approval

```



### Final PoC

**Upload → Understand → Search → Chat → Draft → Workflow**

This is the complete demo you can take to the first **5 CA/financial firms**.