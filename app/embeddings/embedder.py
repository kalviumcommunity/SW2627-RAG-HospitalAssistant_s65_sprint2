"""Embedding adapter with batching and dependency injection for tests."""

from __future__ import annotations

from collections.abc import Sequence
import hashlib
import math
from typing import Any

from app.config import EMBEDDING_MODEL


class EmbeddingError(RuntimeError):
    """Raised when the embedding provider cannot create vectors."""


class _HashingClient:
    def __init__(self, dimensions: int) -> None:
        if dimensions <= 0:
            raise ValueError("hashing dimensions must be positive")
        self.dimensions = dimensions

    def encode(
        self,
        texts: Sequence[str],
        *,
        convert_to_numpy: bool,
        normalize_embeddings: bool,
    ) -> list[list[float]]:
        vectors = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for token in text.lower().split():
                digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
                index = int.from_bytes(digest[:4], "big") % self.dimensions
                sign = 1.0 if digest[4] & 1 else -1.0
                vector[index] += sign
            if normalize_embeddings:
                norm = math.sqrt(sum(value * value for value in vector))
                if norm:
                    vector = [value / norm for value in vector]
            vectors.append(vector)
        return vectors


class Embedder:
    def __init__(
        self,
        model: str = EMBEDDING_MODEL,
        client: Any | None = None,
        batch_size: int = 100,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self.model = model
        self.batch_size = batch_size
        if client:
            self.client = client
        elif model.startswith("hash-"):
            try:
                dimensions = int(model.removeprefix("hash-"))
            except ValueError as error:
                raise ValueError("hash embedding model must use the format hash-N") from error
            self.client = _HashingClient(dimensions)
        else:
            from sentence_transformers import SentenceTransformer

            self.client = SentenceTransformer(model)

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
                response = self.client.encode(
                    batch,
                    convert_to_numpy=False,
                    normalize_embeddings=True,
                )
                vectors.extend([[float(value) for value in vector] for vector in response])
        except Exception as error:
            raise EmbeddingError("embedding provider request failed") from error
        if len(vectors) != len(texts):
            raise EmbeddingError("embedding provider returned an unexpected count")
        return vectors