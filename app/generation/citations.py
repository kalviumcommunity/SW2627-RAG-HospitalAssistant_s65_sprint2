"""Source citation helpers for retrieved context."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Citation:
    document_name: str
    page_number: int | None
    score: float | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def citations_from_chunks(chunks: list[dict[str, Any]]) -> list[Citation]:
    """Extract stable, duplicate-free citations from retrieval records."""
    citations: list[Citation] = []
    seen: set[tuple[str, int | None]] = set()
    for chunk in chunks:
        document_name = str(chunk.get("document_name") or "Unknown document")
        raw_page = chunk.get("page_number")
        page_number = raw_page if isinstance(raw_page, int) else None
        key = (document_name, page_number)
        if key in seen:
            continue
        seen.add(key)
        raw_score = chunk.get("score")
        score = float(raw_score) if isinstance(raw_score, (int, float)) else None
        citations.append(Citation(document_name, page_number, score))
    return citations


def attach_citations(answer: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Return an answer payload with source records for verification."""
    return {"answer": answer, "sources": [citation.as_dict() for citation in citations_from_chunks(chunks)]}