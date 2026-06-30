from __future__ import annotations

from typing import Any

import requests


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: str, chat_model: str, embed_model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.chat_model = chat_model
        self.embed_model = embed_model

    def health(self) -> dict[str, Any]:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            return {"ok": True, "models": response.json().get("models", [])}
        except requests.RequestException as exc:
            return {"ok": False, "error": str(exc)}

    def embed(self, text: str) -> list[float]:
        payload = {"model": self.embed_model, "prompt": text}
        try:
            response = requests.post(f"{self.base_url}/api/embeddings", json=payload, timeout=60)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise OllamaError(f"Ollama embedding request failed: {exc}") from exc

        data = response.json()
        embedding = data.get("embedding")
        if not isinstance(embedding, list):
            raise OllamaError("Ollama did not return an embedding.")
        return [float(value) for value in embedding]

    def chat(self, message: str, context: str) -> str:
        system_prompt = (
            "You are a helpful RAG assistant. Answer using only the provided context. "
            "If the context does not contain the answer, say you do not know. "
            "When possible, mention the source filename in your answer."
        )
        prompt = f"Context:\n{context}\n\nQuestion:\n{message}"
        payload = {
            "model": self.chat_model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        }
        try:
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=180)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise OllamaError(f"Ollama chat request failed: {exc}") from exc

        data = response.json()
        content = data.get("message", {}).get("content")
        if not isinstance(content, str):
            raise OllamaError("Ollama did not return a chat message.")
        return content

