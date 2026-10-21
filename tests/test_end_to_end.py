from fastapi.testclient import TestClient

from app.api.main import create_app


def test_end_to_end_retrieval_generation_and_citations() -> None:
    retrieved = [{
        "text": "The approved guideline describes the process.",
        "document_name": "Approved Guide.pdf",
        "page_number": 8,
        "score": 0.87,
    }]
    app = create_app(
        retrieve=lambda question, top_k: retrieved,
        generate=lambda question, chunks: "The guideline describes the process.",
    )
    response = TestClient(app).post("/ask", json={"question": "What does the guide describe?"})
    assert response.status_code == 200
    assert response.json() == {
        "answer": "The guideline describes the process.",
        "sources": [{"document_name": "Approved Guide.pdf", "page_number": 8, "score": 0.87}],
    }