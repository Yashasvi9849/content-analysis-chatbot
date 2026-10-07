from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_key: SecretStr = SecretStr("")
    allowed_origins: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173"]
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.1"
    ollama_embed_model: str = "nomic-embed-text"
    database_path: Path = Path("./data/rag.sqlite3")
    upload_dir: Path = Path("./data/uploads")
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    max_upload_files: int = Field(default=10, gt=0)
    chunk_size: int = 900
    chunk_overlap: int = 150

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()

