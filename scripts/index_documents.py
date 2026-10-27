"""Index approved PDFs through loading, processing, embedding, and storage."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow this file to be executed directly from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import (
    INDEX_CHUNK_OVERLAP,
    INDEX_CHUNK_SIZE,
    MAX_DOCUMENTS,
    MAX_PAGES,
    RAW_DATA_DIR,
    VECTOR_STORE_PATH,
)
from app.embeddings.embedder import Embedder
from app.loaders.document_loader import load_pdf
from app.processing.chunker import chunk_pages
from app.processing.text_cleaner import clean_page
from app.vector_store.local_store import LocalVectorStore


def index_documents(
    raw_dir: str | Path = RAW_DATA_DIR,
    store_path: str | Path = VECTOR_STORE_PATH,
    embedder: Embedder | None = None,
    chunk_size: int = INDEX_CHUNK_SIZE,
    chunk_overlap: int = INDEX_CHUNK_OVERLAP,
    max_documents: int = MAX_DOCUMENTS,
    max_pages: int = MAX_PAGES,
) -> dict[str, object]:
    """Index a small, configurable number of PDFs for the demo."""
    raw_path = Path(raw_dir)
    paths = sorted(raw_path.glob("*.pdf"))
    if max_documents <= 0:
        raise ValueError("max_documents must be positive")
    if max_pages < 0:
        raise ValueError("max_pages must not be negative")
    paths = paths[:max_documents]
    print("Loading documents...")
    pages = []
    failures: list[dict[str, str]] = []
    for path in paths:
        try:
            pages.extend(load_pdf(path))
        except Exception as error:
            failures.append({"source": str(path), "error": str(error)})

    print("Cleaning documents...")
    if max_pages:
        pages = pages[:max_pages]
    cleaned_pages = [clean_page(page) for page in pages]
    print("Creating chunks...")
    chunks = chunk_pages(cleaned_pages, chunk_size, chunk_overlap)
    print("Generating embeddings...")
    active_embedder = embedder or Embedder()
    vectors = active_embedder.embed_texts([str(chunk["text"]) for chunk in chunks])
    print("Indexing vectors...")
    store = LocalVectorStore(store_path)
    store.clear()
    store.insert_many(
        [
            {"vector": vector, "text": chunk["text"], "metadata": chunk}
            for vector, chunk in zip(vectors, chunks)
        ]
    )
    stats = {
        "documents": len(paths),
        "pages": len(pages),
        "chunks": len(chunks),
        "indexed_vectors": store.count(),
        "failed_documents": failures,
    }
    print(f"Indexing complete: {stats}")
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--store", type=Path, default=VECTOR_STORE_PATH)
    args = parser.parse_args()
    index_documents(args.raw_dir, args.store)


if __name__ == "__main__":
    main()