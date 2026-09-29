from secrets import compare_digest

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Security(api_key_header)) -> None:
    expected = get_settings().api_key.get_secret_value()
    if len(expected) < 32:
        raise HTTPException(status_code=503, detail="API authentication is not configured.")
    if api_key is None or not compare_digest(api_key.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
