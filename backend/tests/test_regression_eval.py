from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient


def test_known_question_answer_regressions(client: TestClient) -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "qa_regression.json"
    cases = json.loads(fixture_path.read_text(encoding="utf-8"))

    for case in cases:
        client.delete("/documents")
        client.post(
            "/ingest",
            files={"files": (f"{case['name']}.txt", case["document"].encode("utf-8"), "text/plain")},
        )

        response = client.post("/chat", json={"message": case["question"], "top_k": 3})
        payload = response.json()

        assert response.status_code == 200
        assert case["expected_answer_contains"].lower() in payload["answer"].lower()
        assert any(
            case["expected_source_contains"].lower() in source["text"].lower()
            for source in payload["sources"]
        )

