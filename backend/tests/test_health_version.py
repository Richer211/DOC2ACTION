from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("DOC2ACTION_ANALYSIS_DB", str(tmp_path / "health.sqlite"))
    monkeypatch.delenv("DOC2ACTION_API_KEY", raising=False)
    monkeypatch.delenv("DOC2ACTION_JWT_SECRET", raising=False)
    monkeypatch.delenv("DOC2ACTION_REDIS_URL", raising=False)
    with TestClient(app) as test_client:
        yield test_client


def test_health_includes_runtime_info(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "abcdef1234567890")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT_NAME", "production")

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "doc2action-backend"
    assert data["version"] == "0.1.0"
    assert data["commit_sha"] == "abcdef123456"
    assert data["environment"] == "production"


def test_version_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RAILWAY_GIT_COMMIT_SHA", raising=False)
    monkeypatch.delenv("VERCEL_GIT_COMMIT_SHA", raising=False)
    monkeypatch.delenv("GIT_COMMIT_SHA", raising=False)

    response = client.get("/version")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "doc2action-backend"
    assert data["version"] == "0.1.0"
    assert data["commit_sha"] == "unknown"
