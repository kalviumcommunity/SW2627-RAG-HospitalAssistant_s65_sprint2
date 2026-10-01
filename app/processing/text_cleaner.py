"""Predictable, meaning-preserving text cleanup."""

from __future__ import annotations

import re
import unicodedata

from app.loaders.document_loader import DocumentPage


def clean_text(text: str) -> str:
    """Normalize extraction whitespace and harmless control noise."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFC", text).replace("\x00", "")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return "\n".join(line.strip() for line in normalized.splitlines()).strip()


def clean_page(page: DocumentPage) -> DocumentPage:
    """Return a cleaned page while preserving all source metadata."""
    return DocumentPage(
        document_id=page.document_id,
        document_name=page.document_name,
        source_path=page.source_path,
        page_number=page.page_number,
        text=clean_text(page.text),
    )