from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_reports_backend_and_fake_ollama(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["api"] == "ok"
    assert payload["ollama"]["ok"] is True


def test_documents_starts_empty(client: TestClient) -> None:
    response = client.get("/documents")

    assert response.status_code == 200
    assert response.json() == {"documents": []}


def test_ingest_document_and_list_documents(client: TestClient) -> None:
    response = client.post(
        "/ingest",
        files={"files": ("policy.txt", b"Refunds are available for 30 days.", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json()["ingested"][0]["filename"] == "policy.txt"

    documents_response = client.get("/documents")
    documents = documents_response.json()["documents"]
    assert len(documents) == 1
    assert documents[0]["filename"] == "policy.txt"
    assert documents[0]["chunk_count"] == 1


def test_chat_without_documents_returns_empty_knowledge_message(client: TestClient) -> None:
    response = client.post("/chat", json={"message": "What is the refund window?", "top_k": 3})

    assert response.status_code == 200
    assert response.json()["answer"] == "I do not have any ingested documents to search yet."
    assert response.json()["sources"] == []


def test_chat_answers_from_ingested_document(client: TestClient) -> None:
    client.post(
        "/ingest",
        files={"files": ("policy.txt", b"Customers can request a refund within 30 days.", "text/plain")},
    )

    response = client.post("/chat", json={"message": "What is the refund window?", "top_k": 2})

    assert response.status_code == 200
    payload = response.json()
    assert "30 days" in payload["answer"]
    assert payload["sources"][0]["filename"] == "policy.txt"


def test_clear_documents_endpoint(client: TestClient) -> None:
    client.post(
        "/ingest",
        files={"files": ("policy.txt", b"Refunds are available for 30 days.", "text/plain")},
    )

    response = client.delete("/documents")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert client.get("/documents").json() == {"documents": []}

