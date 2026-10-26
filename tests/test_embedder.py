from types import SimpleNamespace

import pytest

from app.embeddings.embedder import Embedder, EmbeddingError


class FakeEmbeddings:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def encode(
        self,
        texts: list[str],
        *,
        convert_to_numpy: bool,
        normalize_embeddings: bool,
    ) -> list[list[float]]:
        self.calls.append(texts)
        return [[float(len(text)), 1.0] for text in texts]


def test_embedder_batches_texts_and_preserves_order() -> None:
    embeddings = FakeEmbeddings()
    embedder = Embedder(client=embeddings, batch_size=2)

    result = embedder.embed_texts(["one", "two", "three"])

    assert result == [[3.0, 1.0], [3.0, 1.0], [5.0, 1.0]]
    assert embeddings.calls == [["one", "two"], ["three"]]


def test_embedder_rejects_empty_text() -> None:
    embedder = Embedder(client=FakeEmbeddings())
    with pytest.raises(ValueError):
        embedder.embed_text("")


def test_embedder_wraps_provider_errors() -> None:
    class BrokenEmbeddings:
        def encode(self, **_: object) -> None:
            raise RuntimeError("network failure")

    embedder = Embedder(client=BrokenEmbeddings())
    with pytest.raises(EmbeddingError):
        embedder.embed_text("protocol")