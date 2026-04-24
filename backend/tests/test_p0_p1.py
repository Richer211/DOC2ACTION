"""P0/P1: SQLite analysis store + eval summary API."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DOC2ACTION_ANALYSIS_DB", str(tmp_path / "a.sqlite"))
    monkeypatch.delenv("DOC2ACTION_API_KEY", raising=False)
    monkeypatch.delenv("DOC2ACTION_JWT_SECRET", raising=False)
    monkeypatch.delenv("DOC2ACTION_REDIS_URL", raising=False)
    import app.analysis_store as store

    store.init_schema()
    return TestClient(app)


def test_analyses_recent_after_sync_rules(client: TestClient) -> None:
    r = client.post(
        "/analyze",
        json={"text": "hello persistence", "document_type": "general"},
        headers={"X-Extractor-Mode": "rules"},
    )
    assert r.status_code == 200
    r2 = client.get("/api/v1/analyses/recent?limit=5")
    assert r2.status_code == 200
    items = r2.json()["items"]
    assert len(items) >= 1
    assert items[0]["status"] == "completed"
    assert items[0]["run_kind"] == "sync"


def test_eval_summary_reads_baseline(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    monkeypatch.delenv("DOC2ACTION_API_KEY", raising=False)
    # client fixture already cleared auth; need client with eval route
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    md = repo / "learning" / "报告与演示材料" / "reports" / "baseline-eval.md"
    monkeypatch.setenv("DOC2ACTION_EVAL_REPORT_MD", str(md))
    r = client.get("/api/v1/eval/summary")
    assert r.status_code == 200
    data = r.json()
    assert data.get("exists") is True
    assert "aggregate" in data
    assert data["aggregate"].get("sample_count") == 10
