from pathlib import Path

import pytest
from pypdf import PdfWriter

from app.loaders.document_loader import load_pdf


def _write_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with path.open("wb") as handle:
        writer.write(handle)


def test_load_pdf_preserves_source_identity(tmp_path: Path) -> None:
    source = tmp_path / "Clinical Protocol.pdf"
    _write_pdf(source)

    pages = load_pdf(source)

    assert len(pages) == 1
    assert pages[0].document_id == "Clinical Protocol"
    assert pages[0].document_name == "Clinical Protocol.pdf"
    assert pages[0].source_path == str(source)
    assert pages[0].page_number == 1


def test_load_pdf_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_pdf(tmp_path / "missing.pdf")


def test_load_pdf_rejects_non_pdf_file(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("not a PDF", encoding="utf-8")

    with pytest.raises(ValueError):
        load_pdf(source)