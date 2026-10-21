"""Safe, development-only discovery and indexing workflow for approved PDFs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


class DocumentWorkflowError(RuntimeError):
    """Raised when an indexing workflow cannot be completed."""


def list_approved_documents(raw_dir: str | Path) -> list[Path]:
    """Return PDFs only; callers can show unsupported files separately."""
    return sorted(Path(raw_dir).glob("*.pdf"))


def validate_document_paths(paths: list[Path]) -> list[dict[str, str]]:
    """Report unsupported or missing inputs before indexing starts."""
    failures: list[dict[str, str]] = []
    for path in paths:
        if path.suffix.lower() != ".pdf":
            failures.append({"source": str(path), "error": "only PDF documents are supported"})
        elif not path.is_file():
            failures.append({"source": str(path), "error": "document does not exist"})
    return failures


def index_approved_documents(
    raw_dir: str | Path,
    indexer: Callable[..., dict[str, Any]],
    **indexer_options: Any,
) -> dict[str, Any]:
    """Run the existing indexer after reporting invalid files."""
    raw_path = Path(raw_dir)
    all_entries = sorted(path for path in raw_path.iterdir()) if raw_path.exists() else []
    invalid = validate_document_paths(all_entries)
    pdfs = list_approved_documents(raw_path)
    if invalid:
        return {"documents": len(pdfs), "indexed": False, "failed_documents": invalid}
    try:
        stats = indexer(raw_dir=raw_path, **indexer_options)
    except Exception as error:
        raise DocumentWorkflowError("approved document indexing failed") from error
    return {**stats, "indexed": True, "failed_documents": stats.get("failed_documents", [])}