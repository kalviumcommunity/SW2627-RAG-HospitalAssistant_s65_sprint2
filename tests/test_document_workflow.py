from pathlib import Path

import pytest

from app.admin.document_workflow import DocumentWorkflowError, index_approved_documents, validate_document_paths


def test_rejects_unsupported_files(tmp_path: Path) -> None:
    pdf = tmp_path / "guide.pdf"
    pdf.write_bytes(b"%PDF")
    txt = tmp_path / "notes.txt"
    txt.write_text("private notes")
    failures = validate_document_paths([pdf, txt])
    assert failures == [{"source": str(txt), "error": "only PDF documents are supported"}]


def test_reports_indexing_counts_and_failures(tmp_path: Path) -> None:
    (tmp_path / "guide.pdf").write_bytes(b"%PDF")
    result = index_approved_documents(
        tmp_path, lambda **kwargs: {"documents": 1, "chunks": 3, "failed_documents": []}
    )
    assert result["indexed"] is True
    assert result["chunks"] == 3


def test_wraps_indexer_failure(tmp_path: Path) -> None:
    (tmp_path / "guide.pdf").write_bytes(b"%PDF")
    with pytest.raises(DocumentWorkflowError):
        index_approved_documents(tmp_path, lambda **kwargs: (_ for _ in ()).throw(OSError("failed")))