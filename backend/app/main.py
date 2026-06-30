from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import get_settings
from app.ollama_client import OllamaClient, OllamaError
from app.text_processing import chunk_text, extract_text
from app.vector_store import VectorStore


settings = get_settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)

ollama = OllamaClient(
    base_url=settings.ollama_base_url,
    chat_model=settings.ollama_chat_model,
    embed_model=settings.ollama_embed_model,
)
store = VectorStore(settings.database_path)

app = FastAPI(title="Content Analysis chatbot", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=12)


class Source(BaseModel):
    filename: str
    chunk_id: int
    score: float
    text: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]


@app.get("/health")
def health() -> dict:
    ollama_health = ollama.health()
    return {
        "api": "ok",
        "ollama": ollama_health,
        "chat_model": settings.ollama_chat_model,
        "embedding_model": settings.ollama_embed_model,
        "database_path": str(settings.database_path),
    }


@app.post("/ingest")
async def ingest(files: list[UploadFile] = File(...)) -> dict:
    ingested = []
    for upload in files:
        original_name = Path(upload.filename or "upload").name
        saved_name = f"{uuid4().hex}_{original_name}"
        saved_path = settings.upload_dir / saved_name
        saved_path.write_bytes(await upload.read())

        try:
            text = extract_text(saved_path)
            chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
            if not chunks:
                raise ValueError("No readable text found in file.")
            embeddings = [ollama.embed(chunk) for chunk in chunks]
            document_id = store.add_document(original_name, saved_path, chunks, embeddings)
        except (ValueError, OllamaError) as exc:
            raise HTTPException(status_code=400, detail=f"{original_name}: {exc}") from exc

        ingested.append(
            {
                "document_id": document_id,
                "filename": original_name,
                "chunks": len(chunks),
            }
        )

    return {"ingested": ingested}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        query_embedding = ollama.embed(request.message)
        results = store.search(query_embedding, request.top_k, request.message)
        if not results:
            return ChatResponse(answer="I do not have any ingested documents to search yet.", sources=[])

        context = "\n\n".join(
            f"Source: {result.filename} | Chunk: {result.chunk_id} | Score: {result.score:.3f}\n{result.text}"
            for result in results
        )
        answer = ollama.chat(request.message, context)
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ChatResponse(
        answer=answer,
        sources=[
            Source(
                filename=result.filename,
                chunk_id=result.chunk_id,
                score=result.score,
                text=result.text,
            )
            for result in results
        ],
    )


@app.get("/documents")
def documents() -> dict:
    return {"documents": store.list_documents()}


@app.delete("/documents")
def clear_documents() -> dict:
    store.clear()
    return {"ok": True}
