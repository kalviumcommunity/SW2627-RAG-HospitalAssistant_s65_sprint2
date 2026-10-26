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