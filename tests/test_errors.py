from fastapi.testclient import TestClient

from app.api.main import create_app


def test_api_returns_request_identifier_without_exposing_details() -> None:
    response = TestClient(create_app(retrieve=lambda q, k: [])).get("/health")
    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_api_preserves_supplied_request_identifier() -> None:
    response = TestClient(create_app(retrieve=lambda q, k: [])).get(
        "/health", headers={"X-Request-ID": "test-request"}
    )
    assert response.headers["X-Request-ID"] == "test-request"


def test_api_returns_safe_response_for_unhandled_failure() -> None:
    def broken_retrieval(question: str, top_k: int) -> list[dict[str, object]]:
        raise RuntimeError("private internal detail")

    response = TestClient(create_app(retrieve=broken_retrieval)).post(
        "/ask", json={"question": "What is covered?"}
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "internal server error"}
    assert response.headers["X-Request-ID"]
    assert "private internal detail" not in response.text


def test_api_adds_basic_security_headers() -> None:
    response = TestClient(create_app(retrieve=lambda q, k: [])).get("/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"