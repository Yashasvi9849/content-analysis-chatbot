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
# Set API_KEY in .env before starting (see Security below).
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

## Security

All data endpoints and `/health` require the `X-API-Key` header. Generate a random
key with `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` and set
`API_KEY` in `backend/.env`. An empty key or one shorter than 32 characters blocks
API access with HTTP 503; missing or incorrect request keys return HTTP 401.
Never commit your real key. Restart the backend after changing it.

Enter that key in the frontend's API key field and select **Connect**. The browser
keeps it only in memory until the page reloads. In Swagger `/docs`, use **Authorize**
to supply it. API documentation remains public but cannot access data without a key.
Command-line clients must send `X-API-Key: <your-key>` on each request.

Browser access defaults to `http://127.0.0.1:5173` and `http://localhost:5173`.
Set `ALLOWED_ORIGINS` to a JSON array of your exact frontend origins if needed.
Serve the frontend over HTTP locally rather than opening it as a file.
Use HTTPS when hosting beyond localhost so the key and documents are encrypted
in transit. This shared key grants access to the entire knowledge base, including
deletion; it does not provide separate accounts or document permissions.

## Input limits

Uploads accept TXT, MD, PDF, and DOCX files, up to 10 files per request and
10 MiB per file by default. Configure positive `MAX_UPLOAD_FILES` and
`MAX_UPLOAD_BYTES` values in `.env`. Oversized uploads return HTTP 413.
Files that fail ingestion are removed from the upload directory. If a later file
fails during processing, earlier successfully indexed files remain available.
These limits apply during ingestion, after multipart parsing; use request-body
limits at your reverse proxy for protection before the server receives uploads.

Chat messages are trimmed and must contain 1–8,000 characters. Invalid messages
return HTTP 422 without calling Ollama, and the frontend displays the validation
message.
