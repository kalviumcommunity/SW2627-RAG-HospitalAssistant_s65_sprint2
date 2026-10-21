from pathlib import Path

import pytest

from app.retrieval.service import RetrievalServiceError, retrieve_context


class FakeRetriever:
    def retrieve(self, question: str, top_k: int = 5) -> list[dict[str, object]]:
        return [{"text": question, "score": 1.0}][:top_k]


def test_service_returns_retrieval_context() -> None:
    result = retrieve_context("drug interaction", top_k=1, retriever=FakeRetriever())
    assert result == [{"text": "drug interaction", "score": 1.0}]


def test_service_validates_empty_question() -> None:
    with pytest.raises(ValueError):
        retrieve_context(" ", retriever=FakeRetriever())


def test_service_wraps_store_or_embedding_failure(tmp_path: Path) -> None:
    class BrokenRetriever:
        def retrieve(self, question: str, top_k: int = 5) -> list[dict[str, object]]:
            raise OSError("store unavailable")

    with pytest.raises(RetrievalServiceError):
        retrieve_context("protocol", retriever=BrokenRetriever(), store_path=tmp_path / "unused.json")