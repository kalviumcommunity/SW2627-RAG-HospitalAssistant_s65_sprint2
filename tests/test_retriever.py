from pathlib import Path

import pytest

from app.retrieval.retriever import Retriever
from app.vector_store.local_store import LocalVectorStore


class FakeEmbedder:
    def embed_text(self, text: str) -> list[float]:
        return [1.0, 0.0] if "drug" in text.lower() else [0.0, 1.0]


def test_retriever_returns_relevant_metadata_and_top_k(tmp_path: Path) -> None:
    store = LocalVectorStore(tmp_path / "vectors.json")
    store.insert_many(
        [
            {
                "vector": [1.0, 0.0],
                "text": "Drug interaction guidance",
                "metadata": {"document_name": "Drug Guidelines.pdf", "page_number": 8},
            },
            {
                "vector": [0.0, 1.0],
                "text": "Emergency response protocol",
                "metadata": {"document_name": "Protocol.pdf", "page_number": 2},
            },
        ]
    )

    results = Retriever(FakeEmbedder(), store).retrieve("drug interaction", top_k=1)

    assert len(results) == 1
    assert results[0]["document_name"] == "Drug Guidelines.pdf"
    assert results[0]["page_number"] == 8
    assert results[0]["score"] == 1.0


def test_retriever_supports_threshold_and_rejects_empty_question(tmp_path: Path) -> None:
    store = LocalVectorStore(tmp_path / "vectors.json")
    store.insert([1.0, 0.0], "guidance", {})
    retriever = Retriever(FakeEmbedder(), store)

    assert retriever.retrieve("protocol", threshold=1.0) == []
    with pytest.raises(ValueError):
        retriever.retrieve("   ")