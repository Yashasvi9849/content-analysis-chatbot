from __future__ import annotations

from pathlib import Path

from app.vector_store import VectorStore, cosine_similarity, keyword_overlap, tokenize


def test_cosine_similarity_scores_identical_vectors_highest() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_keyword_overlap_boosts_exact_terms() -> None:
    query_terms = tokenize("refund window")

    assert keyword_overlap(query_terms, "The refund window is 30 days.") > 0
    assert keyword_overlap(query_terms, "This is about support hours.") == 0


def test_vector_store_adds_lists_and_searches_documents(tmp_path: Path) -> None:
    store = VectorStore(tmp_path / "rag.sqlite3")
    document_id = store.add_document(
        filename="policy.txt",
        path=tmp_path / "policy.txt",
        chunks=["refund policy", "email support"],
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
    )

    documents = store.list_documents()
    results = store.search([1.0, 0.0], top_k=1, query_text="refund")

    assert document_id == 1
    assert documents[0]["filename"] == "policy.txt"
    assert documents[0]["chunk_count"] == 2
    assert results[0].text == "refund policy"


def test_vector_store_clear_removes_documents_and_chunks(tmp_path: Path) -> None:
    store = VectorStore(tmp_path / "rag.sqlite3")
    store.add_document("policy.txt", tmp_path / "policy.txt", ["refund policy"], [[1.0]])

    store.clear()

    assert store.list_documents() == []
    assert store.search([1.0], top_k=3, query_text="refund") == []

