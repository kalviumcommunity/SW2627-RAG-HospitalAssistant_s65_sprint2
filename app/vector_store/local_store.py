"""Small persistent JSON vector store for local development."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def _cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have the same dimension")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


class LocalVectorStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._records: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            with self.path.open(encoding="utf-8") as handle:
                payload = json.load(handle)
            self._records = payload.get("records", [])

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump({"records": self._records}, handle, indent=2)

    def insert(
        self,
        vector: list[float],
        text: str,
        metadata: dict[str, Any],
    ) -> None:
        self._records.append({"vector": vector, "text": text, "metadata": metadata})
        self._save()

    def insert_many(self, records: list[dict[str, Any]]) -> None:
        for record in records:
            if not {"vector", "text", "metadata"}.issubset(record):
                raise ValueError("each record needs vector, text, and metadata")
        self._records.extend(records)
        self._save()

    def count(self) -> int:
        return len(self._records)

    def clear(self) -> None:
        self._records = []
        self._save()

    def search(
        self, query_vector: list[float], top_k: int = 5, threshold: float | None = None
    ) -> list[dict[str, Any]]:
        if top_k <= 0:
            return []
        results = []
        for record in self._records:
            score = _cosine(query_vector, record["vector"])
            if threshold is None or score >= threshold:
                results.append(
                    {
                        "text": record["text"],
                        "score": score,
                        "metadata": record["metadata"],
                    }
                )
        results.sort(key=lambda result: result["score"], reverse=True)
        return results[:top_k]