from __future__ import annotations

import json
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SearchResult:
    chunk_id: int
    document_id: int
    filename: str
    text: str
    score: float


class VectorStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    path TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
                """
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id)")

    def add_document(self, filename: str, path: Path, chunks: list[str], embeddings: list[list[float]]) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length.")

        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO documents (filename, path) VALUES (?, ?)",
                (filename, str(path)),
            )
            document_id = int(cursor.lastrowid)
            connection.executemany(
                """
                INSERT INTO chunks (document_id, chunk_index, text, embedding)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (document_id, index, chunk, json.dumps(embedding))
                    for index, (chunk, embedding) in enumerate(zip(chunks, embeddings))
                ],
            )
            return document_id

    def list_documents(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT documents.id, documents.filename, documents.path, documents.created_at,
                       COUNT(chunks.id) AS chunk_count
                FROM documents
                LEFT JOIN chunks ON chunks.document_id = documents.id
                GROUP BY documents.id
                ORDER BY documents.created_at DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def clear(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM chunks")
            connection.execute("DELETE FROM documents")

    def search(self, query_embedding: list[float], top_k: int, query_text: str = "") -> list[SearchResult]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT chunks.id AS chunk_id, chunks.document_id, documents.filename,
                       chunks.text, chunks.embedding
                FROM chunks
                JOIN documents ON documents.id = chunks.document_id
                """
            ).fetchall()

        results: list[SearchResult] = []
        query_terms = tokenize(query_text)
        for row in rows:
            embedding = [float(value) for value in json.loads(row["embedding"])]
            vector_score = cosine_similarity(query_embedding, embedding)
            keyword_score = keyword_overlap(query_terms, str(row["text"]))
            score = vector_score + keyword_score
            results.append(
                SearchResult(
                    chunk_id=int(row["chunk_id"]),
                    document_id=int(row["document_id"]),
                    filename=str(row["filename"]),
                    text=str(row["text"]),
                    score=score,
                )
            )

        results.sort(key=lambda result: result.score, reverse=True)
        return results[:top_k]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z0-9@._+-]+", text.lower()) if len(token) > 1}


def keyword_overlap(query_terms: set[str], text: str) -> float:
    if not query_terms:
        return 0.0
    text_terms = tokenize(text)
    matches = query_terms.intersection(text_terms)
    if not matches:
        return 0.0
    return min(0.35, 0.12 * len(matches))
