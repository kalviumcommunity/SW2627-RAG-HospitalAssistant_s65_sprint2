"""Public retrieval entry point for the later answer-generation phase."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import VECTOR_STORE_PATH
from app.embeddings.embedder import Embedder, EmbeddingError
from app.retrieval.retriever import Retriever
from app.vector_store.local_store import LocalVectorStore


class RetrievalServiceError(RuntimeError):
    """Raised when retrieval cannot be completed."""


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
        active_retriever = Retriever(Embedder(), LocalVectorStore(store_path))
    try:
        return active_retriever.retrieve(question, top_k=top_k)
    except (EmbeddingError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise RetrievalServiceError("retrieval could not be completed") from error