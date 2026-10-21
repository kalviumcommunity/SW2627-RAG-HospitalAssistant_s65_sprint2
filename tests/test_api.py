from fastapi.testclient import TestClient

from app.api.main import create_app
from app.retrieval.service import RetrievalServiceError


def test_health_and_ask_return_answer_with_sources() -> None:
    app = create_app(
        retrieve=lambda question, top_k: [{"text": "Use the guide.", "document_name": "Guide.pdf", "page_number": 2, "score": 0.9}],
        generate=lambda question, chunks: "Use the guide.",
    )
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    response = client.post("/ask", json={"question": "What should I use?", "top_k": 1})
    assert response.status_code == 200
    assert response.json()["sources"][0]["document_name"] == "Guide.pdf"


def test_ask_rejects_empty_question_and_handles_no_results() -> None:
    client = TestClient(create_app(retrieve=lambda question, top_k: [], generate=lambda q, c: "never"))
    assert client.post("/ask", json={"question": ""}).status_code == 422
    response = client.post("/ask", json={"question": "Unknown"})
    assert response.status_code == 200
    assert "not contain enough information" in response.json()["answer"]


def test_ask_maps_retrieval_failure_to_service_error() -> None:
    def broken(question: str, top_k: int) -> list[dict[str, object]]:
        raise RetrievalServiceError("internal detail")

    response = TestClient(create_app(retrieve=broken)).post("/ask", json={"question": "Question"})
    assert response.status_code == 503
    assert response.json() == {"detail": "retrieval is temporarily unavailable"}