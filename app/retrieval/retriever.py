"""Semantic retrieval over the local vector store."""

from __future__ import annotations

from typing import Any

from app.embeddings.embedder import Embedder
from app.vector_store.local_store import LocalVectorStore


class Retriever:
    def __init__(self, embedder: Embedder, store: LocalVectorStore) -> None:
        self.embedder = embedder
        self.store = store

    def retrieve(
        self, question: str, top_k: int = 5, threshold: float | None = None
    ) -> list[dict[str, Any]]:
        if not question.strip():
            raise ValueError("question must not be empty")
        if top_k <= 0:
            return []
        query_vector = self.embedder.embed_text(question)
        matches = self.store.search(query_vector, top_k=top_k, threshold=threshold)
        return [
            {
                "text": match["text"],
                "score": match["score"],
                "document_name": match["metadata"].get("document_name"),
                "page_number": match["metadata"].get("page_number"),
                "metadata": match["metadata"],
            }
            for match in matches
        ]