import pytest
from pydantic import SecretStr

from app import main


@pytest.mark.parametrize("method,path,kwargs", [
    ("get", "/health", {}),
    ("get", "/documents", {}),
    ("delete", "/documents", {}),
    ("post", "/chat", {"json": {"message": "private data?"}}),
    ("post", "/ingest", {"files": {"files": ("private.txt", b"secret", "text/plain")}}),
])
@pytest.mark.parametrize("key", [None, "incorrect", "x" * 40])
def test_unauthorized_requests_have_no_side_effects(client, monkeypatch, method, path, kwargs, key):
    def forbidden(*args, **kwargs):
        pytest.fail("Unauthorized request reached data or model operations")

    for target, names in [(main.ollama, ["health", "embed", "chat"]),
                          (main.store, ["search", "list_documents", "clear", "add_document"])]:
        for name in names:
            monkeypatch.setattr(target, name, forbidden)
    client.headers.pop("X-API-Key", None)
    if key is not None:
        client.headers["X-API-Key"] = key
    response = client.request(method, path, **kwargs)
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key."}
    assert not list(main.settings.upload_dir.iterdir())


@pytest.mark.parametrize("configured_key", ["", "short"])
def test_unconfigured_auth_fails_closed(client, monkeypatch, configured_key):
    monkeypatch.setattr(main.settings, "api_key", SecretStr(configured_key))
    assert client.get("/documents").status_code == 503


def test_key_rotation_rejects_old_key(client, monkeypatch):
    monkeypatch.setattr(main.settings, "api_key", SecretStr("new-key-" + "b" * 32))
    assert client.get("/documents").status_code == 401
    assert client.get("/documents", headers={"X-API-Key": "new-key-" + "b" * 32}).status_code == 200


@pytest.mark.parametrize("origin,expected", [
    ("http://127.0.0.1:5173", 200),
    ("http://localhost:5173", 200),
    ("https://untrusted.example", 400),
    ("null", 400),
])
def test_cors_preflight(client, origin, expected):
    client.headers.pop("X-API-Key")
    response = client.options("/documents", headers={
        "Origin": origin,
        "Access-Control-Request-Method": "DELETE",
        "Access-Control-Request-Headers": "X-API-Key",
    })
    assert response.status_code == expected
    assert response.headers.get("access-control-allow-origin") == (origin if expected == 200 else None)


def test_swagger_describes_api_key_requirement(client):
    operation = client.get("/openapi.json").json()["paths"]["/chat"]["post"]
    assert operation["security"] == [{"APIKeyHeader": []}]
