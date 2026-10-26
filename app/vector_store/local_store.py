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

    def replace_document(self, document_name: str, records: list[dict[str, Any]]) -> None:
        """Atomically replace all records belonging to one document."""
        for record in records:
            if not {"vector", "text", "metadata"}.issubset(record):
                raise ValueError("each record needs vector, text, and metadata")
        retained = [
            record
            for record in self._records
            if record.get("metadata", {}).get("document_name") != document_name
        ]
        self._records = retained + records
        self._save_atomic()

    def replace_all(self, records: list[dict[str, Any]]) -> None:
        """Atomically replace the complete vector store."""
        for record in records:
            if not {"vector", "text", "metadata"}.issubset(record):
                raise ValueError("each record needs vector, text, and metadata")
        self._records = list(records)
        self._save_atomic()

    def remove_document(self, document_name: str) -> int:
        """Remove one document and return the number of removed chunks."""
        retained = [
            record
            for record in self._records
            if record.get("metadata", {}).get("document_name") != document_name
        ]
        removed = len(self._records) - len(retained)
        self._records = retained
        if removed:
            self._save_atomic()
        return removed

    def list_documents(self) -> list[dict[str, Any]]:
        documents: dict[str, dict[str, Any]] = {}
        for record in self._records:
            metadata = record.get("metadata", {})
            name = metadata.get("document_name")
            if not name:
                continue
            item = documents.setdefault(
                name,
                {
                    "name": name,
                    "document_id": metadata.get("document_id"),
                    "source_path": metadata.get("source_path"),
                    "file_hash": metadata.get("file_hash"),
                    "pages": set(),
                    "chunks": 0,
                },
            )
            if metadata.get("page_number") is not None:
                item["pages"].add(metadata["page_number"])
            item["chunks"] += 1
        return [
            {**item, "pages": len(item["pages"])}
            for item in sorted(documents.values(), key=lambda value: value["name"])
        ]

    def _save_atomic(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump({"records": self._records}, handle, indent=2)
        temporary.replace(self.path)

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