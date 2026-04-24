"""Async analyze jobs (Phase 7)."""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_job_analyze_completes(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOC2ACTION_API_KEY", raising=False)
    monkeypatch.delenv("DOC2ACTION_REDIS_URL", raising=False)
    r = client.post(
        "/api/v1/jobs/analyze",
        json={"text": "hello world for job", "document_type": "general"},
        headers={"X-Extractor-Mode": "rules"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "pending"
    jid = body["job_id"]

    status = "pending"
    data: dict = {}
    for _ in range(100):
        r2 = client.get(f"/api/v1/jobs/{jid}")
        assert r2.status_code == 200
        data = r2.json()
        status = data["status"]
        if status != "pending":
            break
        time.sleep(0.02)

    assert status == "completed"
    assert data.get("result") is not None
    assert data["result"]["summary"]


def test_job_unknown_404(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOC2ACTION_API_KEY", raising=False)
    monkeypatch.delenv("DOC2ACTION_REDIS_URL", raising=False)
    r = client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
