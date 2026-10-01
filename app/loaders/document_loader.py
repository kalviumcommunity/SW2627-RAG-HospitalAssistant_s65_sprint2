"""Load approved PDF documents into page-level pipeline records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class DocumentPage:
    document_id: str
    document_name: str
    source_path: str
    page_number: int
    text: str


def load_pdf(path: str | Path) -> list[DocumentPage]:
    """Extract text from every page in a PDF, preserving source identity."""
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Document does not exist: {source}")
    if source.suffix.lower() != ".pdf":
        raise ValueError(f"Only PDF documents are supported: {source}")

    document_id = source.stem
    reader = PdfReader(str(source))
    return [
        DocumentPage(
            document_id=document_id,
            document_name=source.name,
            source_path=str(source),
            page_number=page_number,
            text=page.extract_text() or "",
        )
        for page_number, page in enumerate(reader.pages, start=1)
    ]


def load_documents(directory: str | Path) -> list[DocumentPage]:
    """Load all PDFs in a directory in stable filename order."""
    folder = Path(directory)
    if not folder.is_dir():
        raise FileNotFoundError(f"Document directory does not exist: {folder}")
    pages: list[DocumentPage] = []
    for path in sorted(folder.glob("*.pdf")):
        pages.extend(load_pdf(path))
    return pages