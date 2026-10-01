"""Simple source-level retrieval evaluation metrics."""

from __future__ import annotations

from typing import Any, Protocol


class RetrievalLike(Protocol):
    def retrieve(self, question: str, top_k: int = 5) -> list[dict[str, Any]]: ...


def evaluate_retrieval(
    retriever: RetrievalLike, cases: list[dict[str, Any]], top_k: int = 5
) -> dict[str, Any]:
    """Measure whether each expected document appears in the top-k results."""
    successful = 0
    details = []
    for case in cases:
        results = retriever.retrieve(case["query"], top_k=top_k)
        documents = {result.get("document_name") for result in results}
        hit = case["expected_document"] in documents
        successful += int(hit)
        details.append({"query": case["query"], "hit": hit, "results": results})
    total = len(cases)
    return {
        "total_queries": total,
        "successful_retrievals": successful,
        "hit_rate": successful / total if total else 0.0,
        "details": details,
    }