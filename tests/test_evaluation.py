from app.evaluation.metrics import evaluate_retrieval


class FakeRetriever:
    def retrieve(self, question: str, top_k: int = 5) -> list[dict[str, object]]:
        document = "Drug Guidelines.pdf" if "drug" in question else "Protocol.pdf"
        return [{"document_name": document}][:top_k]


def test_evaluation_reports_hit_rate_without_fabricating_results() -> None:
    cases = [
        {"query": "drug question", "expected_document": "Drug Guidelines.pdf"},
        {"query": "protocol question", "expected_document": "Missing.pdf"},
    ]

    result = evaluate_retrieval(FakeRetriever(), cases, top_k=1)

    assert result["total_queries"] == 2
    assert result["successful_retrievals"] == 1
    assert result["hit_rate"] == 0.5
    assert [detail["hit"] for detail in result["details"]] == [True, False]