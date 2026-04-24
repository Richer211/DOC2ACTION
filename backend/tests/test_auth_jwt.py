"""Optional JWT demo login + Bearer access to /analyze."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_jwt_token_and_analyze_rules(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOC2ACTION_API_KEY", raising=False)
    monkeypatch.delenv("DOC2ACTION_REDIS_URL", raising=False)
    monkeypatch.setenv("DOC2ACTION_JWT_SECRET", "unit-test-jwt-secret-at-least-32-chars!!")
    monkeypatch.setenv("DOC2ACTION_DEMO_USER", "demo_user")
    monkeypatch.setenv("DOC2ACTION_DEMO_PASSWORD", "demo_pass")

    r = client.post(
        "/api/v1/auth/token",
        json={"username": "demo_user", "password": "demo_pass"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    assert token

    r2 = client.post(
        "/analyze",
        json={"text": "hello from jwt", "document_type": "general"},
        headers={
            "Authorization": f"Bearer {token}",
            "X-Extractor-Mode": "rules",
        },
    )
    assert r2.status_code == 200
    assert r2.json()["summary"]


def test_jwt_disabled_returns_503(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOC2ACTION_JWT_SECRET", raising=False)
    r = client.post("/api/v1/auth/token", json={"username": "a", "password": "b"})
    assert r.status_code == 503
