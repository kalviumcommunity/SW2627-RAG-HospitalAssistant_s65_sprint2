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


def test_documents_upload_list_and_delete(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.main.index_uploaded_document",
        lambda content, filename: {"status": "indexed", "document": filename, "pages": 1, "chunks": 1, "replaced": False},
    )
    monkeypatch.setattr("app.api.main.list_indexed_documents", lambda: [{"name": "guide.pdf", "pages": 1, "chunks": 1}])
    monkeypatch.setattr(
        "app.api.main.remove_document",
        lambda name: {"status": "removed", "document": name, "chunks": 1},
    )
    client = TestClient(create_app(retrieve=lambda q, k: [], generate=lambda q, c: "unused"))

    upload = client.post("/documents/upload", files={"file": ("guide.pdf", b"%PDF", "application/pdf")})
    assert upload.status_code == 200
    assert upload.json()["document"] == "guide.pdf"
    assert client.get("/documents").json()["documents"][0]["name"] == "guide.pdf"
    assert client.delete("/documents/guide.pdf").json()["status"] == "removed"