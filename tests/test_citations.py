from app.generation.citations import attach_citations, citations_from_chunks


def test_citations_remove_duplicate_document_pages() -> None:
    citations = citations_from_chunks(
        [
            {"document_name": "Guide.pdf", "page_number": 8, "score": 0.87},
            {"document_name": "Guide.pdf", "page_number": 8, "score": 0.80},
        ]
    )
    assert len(citations) == 1
    assert citations[0].score == 0.87


def test_citations_support_multiple_documents_and_missing_metadata() -> None:
    payload = attach_citations(
        "Answer",
        [{"document_name": "A.pdf", "page_number": 1}, {"text": "No metadata"}],
    )
    assert payload["answer"] == "Answer"
    assert payload["sources"] == [
        {"document_name": "A.pdf", "page_number": 1, "score": None},
        {"document_name": "Unknown document", "page_number": None, "score": None},
    ]