from pathlib import Path

import pytest

from app.admin.document_indexing import index_uploaded_document
from app.admin.document_workflow import DocumentWorkflowError, index_approved_documents, validate_document_paths
from app.vector_store.local_store import LocalVectorStore


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


def test_uploaded_document_replaces_same_name_and_preserves_metadata(tmp_path: Path, monkeypatch) -> None:
    import app.admin.document_indexing as indexing

    def fake_build(path, document_name, file_hash, source_path=None):
        return [
            {
                "vector": [1.0, 0.0],
                "text": path.read_text(),
                "metadata": {
                    "document_name": document_name,
                    "source_path": str(source_path),
                    "file_hash": file_hash,
                    "page_number": 1,
                },
            }
        ], 1

    monkeypatch.setattr(indexing, "_build_records", fake_build)
    store_path = tmp_path / "vectors.json"
    first = index_uploaded_document(b"version one", "guide.pdf", tmp_path, store_path)
    second = index_uploaded_document(b"version two", "guide.pdf", tmp_path, store_path)

    assert first["replaced"] is False
    assert second["replaced"] is True
    store = LocalVectorStore(store_path)
    assert store.count() == 1
    assert store._records[0]["text"] == "version two"