# Content Analysis chatbot

Content Analysis chatbot is a local Retrieval-Augmented Generation (RAG) application for chatting with your own documents. It uses a FastAPI backend, a lightweight HTML/CSS/JavaScript frontend, Ollama for local LLM inference, and SQLite for storing document chunks and embeddings.

## What We Built

- A backend API for document ingestion and chat
- A frontend interface for uploading files and asking questions
- Local RAG retrieval over uploaded documents
- Ollama integration for embeddings and answer generation
- SQLite storage for indexed document chunks
- Source citations so answers can be traced back to uploaded content

## Current Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | FastAPI, Python |
| LLM | Ollama `llama3.1` |
| Embeddings | Ollama `nomic-embed-text` |
| Storage | SQLite |
| Supported files | `.txt`, `.md`, `.pdf`, `.docx` |

## Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── ollama_client.py
│   │   ├── text_processing.py
│   │   └── vector_store.py
│   ├── sample_data/
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── README.md
```

## How It Works

```text
User uploads documents
-> backend extracts text
-> text is split into chunks
-> Ollama creates embeddings
-> chunks and embeddings are stored in SQLite
-> user asks a question
-> backend retrieves relevant chunks
-> Ollama generates an answer using retrieved context
-> frontend shows answer and sources
```

## Prerequisites

- Python 3.11+
- Ollama installed and running
- Git and GitHub CLI if you want to push the project to GitHub

Pull the required Ollama models:

```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Backend URLs:

- Health check: `http://127.0.0.1:8000/health`
- Swagger API docs: `http://127.0.0.1:8000/docs`

## Frontend Setup

Open a second terminal from the project root:

```bash
cd frontend
python3 -m http.server 5173
```

Frontend URL:

```text
http://127.0.0.1:5173
```

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Check backend and Ollama connection |
| `POST` | `/ingest` | Upload and index documents |
| `POST` | `/chat` | Ask questions over indexed content |
| `GET` | `/documents` | List indexed documents |
| `DELETE` | `/documents` | Clear indexed documents |

Example chat request:

```json
{
  "message": "What is the email address in the resume?",
  "top_k": 5
}
```

## What Has Been Tested

- Backend health endpoint
- Ollama connection
- `llama3.1` chat model availability
- `nomic-embed-text` embedding model availability
- Uploading and indexing a sample policy file
- Uploading and querying a resume PDF
- Asking questions and receiving source-backed answers
- Frontend served locally on port `5173`

## GitHub Notes

Recommended repo name:

```text
content-analysis-chatbot
```

Recommended visibility while building:

```text
Private
```

Files that should not be pushed:

- `backend/.env`
- `backend/.venv/`
- `backend/data/`
- uploaded private documents
- API keys or secrets

## Next Steps

- Add per-document delete
- Add chat history
- Improve retrieval ranking and source filtering
- Add document-specific search filters
- Add authentication if deploying for multiple users
- Add Docker setup for easier deployment
- Deploy frontend and backend to the cloud

