from pathlib import Path

from app.vector_store.local_store import LocalVectorStore


def test_store_persists_vectors_and_metadata(tmp_path: Path) -> None:
    path = tmp_path / "vectors.json"
    store = LocalVectorStore(path)
    store.insert([1.0, 0.0], "drug interaction guidance", {"page_number": 8})

    reopened = LocalVectorStore(path)
    results = reopened.search([1.0, 0.0], top_k=1)

    assert reopened.count() == 1
    assert results[0]["text"] == "drug interaction guidance"
    assert results[0]["metadata"]["page_number"] == 8
    assert results[0]["score"] == 1.0


def test_store_orders_and_limits_results(tmp_path: Path) -> None:
    store = LocalVectorStore(tmp_path / "vectors.json")
    store.insert_many(
        [
            {"vector": [1.0, 0.0], "text": "a", "metadata": {}},
            {"vector": [0.0, 1.0], "text": "b", "metadata": {}},
        ]
    )

    assert [item["text"] for item in store.search([1.0, 0.0], top_k=1)] == ["a"]
    assert store.search([1.0, 0.0], threshold=1.1) == []


def test_store_can_be_cleared(tmp_path: Path) -> None:
    store = LocalVectorStore(tmp_path / "vectors.json")
    store.insert([1.0], "text", {})
    store.clear()
    assert store.count() == 0