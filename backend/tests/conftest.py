from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main
from app.vector_store import VectorStore


class FakeOllama:
    def health(self) -> dict:
        return {"ok": True, "models": [{"name": "fake-chat"}, {"name": "fake-embed"}]}

    def embed(self, text: str) -> list[float]:
        lowered = text.lower()
        return [
            float(lowered.count("refund")),
            float(lowered.count("email") + lowered.count("@")),
            float(lowered.count("support")),
            float(lowered.count("premium")),
            float(lowered.count("30") + lowered.count("four")),
        ]

    def chat(self, message: str, context: str) -> str:
        lowered = context.lower()
        if "30 days" in lowered:
            return "Customers can request a refund within 30 days."
        if "four business hours" in lowered:
            return "Premium support has a target first response time of four business hours."
        if "@" in context:
            return "The email address is available in the retrieved source."
        return "I do not know."


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()

    monkeypatch.setattr(main, "ollama", FakeOllama())
    monkeypatch.setattr(main, "store", VectorStore(tmp_path / "test.sqlite3"))
    monkeypatch.setattr(main.settings, "upload_dir", upload_dir)
    monkeypatch.setattr(main.settings, "chunk_size", 300)
    monkeypatch.setattr(main.settings, "chunk_overlap", 50)

    with TestClient(main.app) as test_client:
        yield test_client

