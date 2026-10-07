import asyncio
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from app import main
from app.ollama_client import OllamaError


def assert_empty():
    assert main.store.list_documents() == []
    assert list(main.settings.upload_dir.iterdir()) == []


@pytest.mark.parametrize("message", ["", " \n\t ", "x" * 8001])
def test_invalid_chat_never_calls_model(client, monkeypatch, message):
    def forbidden(*args):
        pytest.fail("Invalid input reached Ollama")
    monkeypatch.setattr(main.ollama, "embed", forbidden)
    assert client.post("/chat", json={"message": message}).status_code == 422


def test_chat_trims_whitespace(client):
    assert main.ChatRequest(message="  hello  ").message == "hello"
    assert client.post("/chat", json={"message": "x" * 8000}).status_code == 200


@pytest.mark.parametrize("name,content,status", [
    ("script.exe", b"test", 400),
    ("empty.txt", b" \n ", 400),
    ("large.txt", b"a" * 17, 413),
])
def test_rejected_upload_leaves_no_files(client, monkeypatch, name, content, status):
    monkeypatch.setattr(main.settings, "max_upload_bytes", 16)
    response = client.post("/ingest", files={"files": (name, content)})
    assert response.status_code == status
    assert_empty()


def test_upload_exact_limit(client, monkeypatch):
    monkeypatch.setattr(main.settings, "max_upload_bytes", 16)
    assert client.post("/ingest", files={"files": ("policy.TXT", b"a" * 16)}).status_code == 200
    assert len(main.store.list_documents()) == 1


def test_batch_count_limit(client, monkeypatch):
    monkeypatch.setattr(main.settings, "max_upload_files", 1)
    response = client.post("/ingest", files=[("files", ("one.txt", b"one")), ("files", ("two.txt", b"two"))])
    assert response.status_code == 413
    assert_empty()


def test_model_failure_removes_uploaded_file(client, monkeypatch):
    def fail(*args):
        raise OllamaError("Model unavailable")
    monkeypatch.setattr(main.ollama, "embed", fail)
    assert client.post("/ingest", files={"files": ("one.txt", b"one")}).status_code == 400
    assert_empty()


def test_stream_limit_without_size_metadata(client, monkeypatch):
    monkeypatch.setattr(main.settings, "max_upload_bytes", 65536)
    upload = UploadFile(filename="large.txt", file=BytesIO(b"a" * 65537))
    with pytest.raises(HTTPException) as error:
        asyncio.run(main.ingest([upload]))
    assert error.value.status_code == 413
    assert upload.file.closed
    assert_empty()
