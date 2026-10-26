"""Public retrieval entry point for the later answer-generation phase."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import VECTOR_STORE_PATH
from app.embeddings.embedder import Embedder, EmbeddingError
from app.retrieval.retriever import Retriever
from app.vector_store.local_store import LocalVectorStore


class RetrievalServiceError(RuntimeError):
    """Raised when retrieval cannot be completed."""


@lru_cache(maxsize=1)
def _local_embedder() -> Embedder:
    """Load the local model once per API process instead of once per request."""
    return Embedder()


def retrieve_context(
    question: str,
    top_k: int = 5,
    retriever: Retriever | None = None,
    store_path: str | Path = VECTOR_STORE_PATH,
) -> list[dict[str, Any]]:
    """Validate a question and return source-backed retrieval results only."""
    if not question.strip():
        raise ValueError("question must not be empty")
    if top_k <= 0:
        return []

    active_retriever = retriever
    if active_retriever is None:
        active_retriever = Retriever(_local_embedder(), LocalVectorStore(store_path))
    try:
        return active_retriever.retrieve(question, top_k=top_k)
    except (EmbeddingError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise RetrievalServiceError("retrieval could not be completed") from error