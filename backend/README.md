# Content Analysis chatbot

FastAPI backend for Content Analysis chatbot, a local RAG chatbot using Ollama for embeddings and chat generation.

## What This Backend Does

- Upload your own files (`.txt`, `.md`, `.pdf`, `.docx`)
- Extract and chunk text
- Create embeddings with Ollama
- Store chunks and embeddings in SQLite
- Retrieve relevant chunks for a question
- Ask an Ollama chat model to answer with source citations

## Default Models

- Chat model: `llama3.1`
- Embedding model: `nomic-embed-text`

Pull them with:

```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

If the Ollama CLI crashes, fix Ollama first or start/reinstall Ollama from the desktop app. This backend talks to Ollama at `http://localhost:11434`.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open:

- API health: `http://localhost:8000/health`
- Swagger docs: `http://localhost:8000/docs`

## API

### Upload Data

`POST /ingest`

Form field:

- `files`: one or more files

### Chat

`POST /chat`

```json
{
  "message": "What does my document say about refunds?",
  "top_k": 5
}
```

### List Documents

`GET /documents`

### Delete Everything

`DELETE /documents`

This clears the local SQLite knowledge base.
