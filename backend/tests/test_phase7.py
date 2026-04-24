"""Phase 7: request id, optional API key, v1 paths."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_health_has_request_id_header(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert "x-request-id" in r.headers


def test_health_v1_matches(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_analyze_without_key_when_not_configured(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOC2ACTION_API_KEY", raising=False)
    r = client.post("/analyze", json={"text": "hello world", "document_type": "general"})
    assert r.status_code == 200


def test_analyze_rejects_bad_key_when_configured(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOC2ACTION_API_KEY", "secret-test-key")
    # Dependency closure may cache old env in edge cases; require_api_key reads getenv each call
    r = client.post("/analyze", json={"text": "hello world", "document_type": "general"})
    assert r.status_code == 401
    r2 = client.post(
        "/analyze",
        json={"text": "hello world", "document_type": "general"},
        headers={"X-API-Key": "secret-test-key"},
    )
    assert r2.status_code == 200
