"""Embedding adapter with batching and dependency injection for tests."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from openai import OpenAI

from app.config import EMBEDDING_API_KEY, EMBEDDING_MODEL


class EmbeddingError(RuntimeError):
    """Raised when the embedding provider cannot create vectors."""


class Embedder:
    def __init__(
        self,
        model: str = EMBEDDING_MODEL,
        api_key: str | None = EMBEDDING_API_KEY,
        client: Any | None = None,
        batch_size: int = 100,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self.model = model
        self.batch_size = batch_size
        self.client = client or OpenAI(api_key=api_key)

    def embed_text(self, text: str) -> list[float]:
        vectors = self.embed_texts([text])
        return vectors[0]

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        if any(not text.strip() for text in texts):
            raise ValueError("cannot embed empty text")

        vectors: list[list[float]] = []
        try:
            for start in range(0, len(texts), self.batch_size):
                batch = list(texts[start : start + self.batch_size])
                response = self.client.embeddings.create(model=self.model, input=batch)
                vectors.extend([list(item.embedding) for item in response.data])
        except Exception as error:
            raise EmbeddingError("embedding provider request failed") from error
        if len(vectors) != len(texts):
            raise EmbeddingError("embedding provider returned an unexpected count")
        return vectors