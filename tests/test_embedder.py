from types import SimpleNamespace

import pytest

from app.embeddings.embedder import Embedder, EmbeddingError


class FakeEmbeddings:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def create(self, *, model: str, input: list[str]) -> SimpleNamespace:
        self.calls.append(input)
        return SimpleNamespace(
            data=[SimpleNamespace(embedding=[float(len(text)), 1.0]) for text in input]
        )


def test_embedder_batches_texts_and_preserves_order() -> None:
    embeddings = FakeEmbeddings()
    embedder = Embedder(client=SimpleNamespace(embeddings=embeddings), batch_size=2)

    result = embedder.embed_texts(["one", "two", "three"])

    assert result == [[3.0, 1.0], [3.0, 1.0], [5.0, 1.0]]
    assert embeddings.calls == [["one", "two"], ["three"]]


def test_embedder_rejects_empty_text() -> None:
    embedder = Embedder(client=SimpleNamespace(embeddings=FakeEmbeddings()))
    with pytest.raises(ValueError):
        embedder.embed_text("")


def test_embedder_wraps_provider_errors() -> None:
    class BrokenEmbeddings:
        def create(self, **_: object) -> None:
            raise RuntimeError("network failure")

    embedder = Embedder(client=SimpleNamespace(embeddings=BrokenEmbeddings()))
    with pytest.raises(EmbeddingError):
        embedder.embed_text("protocol")