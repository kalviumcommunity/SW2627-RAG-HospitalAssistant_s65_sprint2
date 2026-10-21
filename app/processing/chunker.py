"""Split cleaned pages into overlapping retrieval chunks."""

from __future__ import annotations

import hashlib

from app.loaders.document_loader import DocumentPage


def _chunk_id(document_id: str, page_number: int, chunk_index: int) -> str:
    value = f"{document_id}:{page_number}:{chunk_index}".encode("utf-8")
    return hashlib.sha1(value).hexdigest()[:16]


def chunk_page(
    page: DocumentPage,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> list[dict[str, object]]:
    """Return JSON-friendly chunks with source metadata."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be between zero and chunk_size")
    if not page.text.strip():
        return []

    step = chunk_size - chunk_overlap
    chunks: list[dict[str, object]] = []
    for chunk_index, start in enumerate(range(0, len(page.text), step)):
        text = page.text[start : start + chunk_size].strip()
        if not text:
            continue
        chunks.append(
            {
                "chunk_id": _chunk_id(page.document_id, page.page_number, chunk_index),
                "document_id": page.document_id,
                "document_name": page.document_name,
                "source_path": page.source_path,
                "page_number": page.page_number,
                "chunk_index": chunk_index,
                "text": text,
            }
        )
    return chunks


def chunk_pages(
    pages: list[DocumentPage], chunk_size: int = 800, chunk_overlap: int = 100
) -> list[dict[str, object]]:
    chunks: list[dict[str, object]] = []
    for page in pages:
        chunks.extend(chunk_page(page, chunk_size, chunk_overlap))
    return chunks