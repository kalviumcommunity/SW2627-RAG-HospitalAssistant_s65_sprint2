"""Document upload, replacement, and local indexing services."""

from __future__ import annotations

import hashlib
import re
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.config import (
    INDEX_CHUNK_OVERLAP,
    INDEX_CHUNK_SIZE,
    MAX_DOCUMENTS,
    MAX_UPLOAD_BYTES,
    RAW_DATA_DIR,
    VECTOR_STORE_PATH,
)
from app.embeddings.embedder import Embedder
from app.loaders.document_loader import load_pdf
from app.processing.chunker import chunk_pages
from app.processing.text_cleaner import clean_page
from app.vector_store.local_store import LocalVectorStore


class DocumentIndexingError(RuntimeError):
    """Raised when a document cannot be safely indexed."""


def _safe_filename(filename: str) -> str:
    name = Path(filename).name
    if not name or Path(name).suffix.lower() != ".pdf":
        raise DocumentIndexingError("only PDF files are supported")
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    if safe in {"", ".", ".."} or not safe.lower().endswith(".pdf"):
        raise DocumentIndexingError("invalid PDF filename")
    return safe


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@lru_cache(maxsize=1)
def _embedder() -> Embedder:
    return Embedder()


def _build_records(
    path: Path, document_name: str, file_hash: str, source_path: Path | None = None
) -> tuple[list[dict[str, Any]], int]:
    pages = [clean_page(page) for page in load_pdf(path)]
    chunks = chunk_pages(pages, INDEX_CHUNK_SIZE, INDEX_CHUNK_OVERLAP)
    vectors = _embedder().embed_texts([str(chunk["text"]) for chunk in chunks])
    source = str(source_path or path)
    records = []
    for vector, chunk in zip(vectors, chunks):
        metadata = {
            **chunk,
            "document_id": Path(document_name).stem,
            "document_name": document_name,
            "source_path": source,
            "file_hash": file_hash,
        }
        records.append({"vector": vector, "text": chunk["text"], "metadata": metadata})
    return records, len(pages)


def list_indexed_documents(store_path: str | Path = VECTOR_STORE_PATH) -> list[dict[str, Any]]:
    return LocalVectorStore(store_path).list_documents()


def index_uploaded_document(
    content: bytes,
    filename: str,
    raw_dir: str | Path = RAW_DATA_DIR,
    store_path: str | Path = VECTOR_STORE_PATH,
) -> dict[str, Any]:
    """Validate, embed, and atomically replace one uploaded PDF."""
    document_name = _safe_filename(filename)
    if not content:
        raise DocumentIndexingError("uploaded PDF is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise DocumentIndexingError(f"PDF exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit")

    raw_path = Path(raw_dir)
    raw_path.mkdir(parents=True, exist_ok=True)
    final_path = raw_path / document_name
    temporary_path = raw_path / f".{uuid4().hex}-{document_name}"
    temporary_path.write_bytes(content)
    replaced = final_path.exists()
    previous_content = final_path.read_bytes() if final_path.exists() else None
    try:
        file_hash = _file_hash(temporary_path)
        existing = LocalVectorStore(store_path).list_documents()
        unchanged = next(
            (
                item
                for item in existing
                if item["name"] == document_name and item.get("file_hash") == file_hash
            ),
            None,
        )
        if unchanged:
            temporary_path.unlink()
            return {
                "status": "unchanged",
                "document": document_name,
                "pages": unchanged["pages"],
                "chunks": unchanged["chunks"],
                "replaced": False,
            }
        records, pages = _build_records(temporary_path, document_name, file_hash, final_path)
        if not records:
            raise DocumentIndexingError("PDF contains no extractable text")
        store = LocalVectorStore(store_path)
        temporary_path.replace(final_path)
        try:
            store.replace_document(document_name, records)
        except Exception:
            if previous_content is None:
                final_path.unlink(missing_ok=True)
            else:
                final_path.write_bytes(previous_content)
            raise
        return {
            "status": "indexed",
            "document": document_name,
            "pages": pages,
            "chunks": len(records),
            "replaced": replaced,
        }
    except DocumentIndexingError:
        temporary_path.unlink(missing_ok=True)
        raise
    except Exception as error:
        temporary_path.unlink(missing_ok=True)
        raise DocumentIndexingError("document indexing failed") from error


def remove_document(
    document_name: str,
    raw_dir: str | Path = RAW_DATA_DIR,
    store_path: str | Path = VECTOR_STORE_PATH,
) -> dict[str, Any]:
    safe_name = _safe_filename(document_name)
    removed_chunks = LocalVectorStore(store_path).remove_document(safe_name)
    path = Path(raw_dir) / safe_name
    path.unlink(missing_ok=True)
    return {"status": "removed", "document": safe_name, "chunks": removed_chunks}


def rebuild_documents(
    raw_dir: str | Path = RAW_DATA_DIR,
    store_path: str | Path = VECTOR_STORE_PATH,
) -> dict[str, Any]:
    paths = sorted(Path(raw_dir).glob("*.pdf"))[:MAX_DOCUMENTS]
    all_records: list[dict[str, Any]] = []
    pages = 0
    for path in paths:
        records, document_pages = _build_records(path, path.name, _file_hash(path))
        all_records.extend(records)
        pages += document_pages
    store = LocalVectorStore(store_path)
    store.replace_all(all_records)
    return {"status": "rebuilt", "documents": len(paths), "pages": pages, "chunks": len(all_records)}
