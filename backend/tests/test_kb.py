"""Knowledge base REST API (P2)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_kb_collections_and_documents(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.delenv("DOC2ACTION_API_KEY", raising=False)
    monkeypatch.delenv("DOC2ACTION_JWT_SECRET", raising=False)
    db = tmp_path / "kb_api.sqlite"
    monkeypatch.setenv("DOC2ACTION_ANALYSIS_DB", str(db))

    import app.analysis_store as analysis_store
    import app.kb_store as kb_store

    analysis_store.init_schema()
    kb_store.init_kb_schema()

    r = client.post("/api/v1/kb/collections", json={"name": "Unit KB"})
    assert r.status_code == 200
    cid = r.json()["id"]
    assert cid

    r2 = client.get("/api/v1/kb/collections")
    assert r2.status_code == 200
    items = r2.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == cid

    r3 = client.post(
        f"/api/v1/kb/collections/{cid}/documents",
        json={"title": "Note A", "content": "Hello knowledge base content."},
    )
    assert r3.status_code == 200
    assert r3.json()["title"] == "Note A"

    r4 = client.get(f"/api/v1/kb/collections/{cid}/documents")
    assert r4.status_code == 200
    docs = r4.json()["items"]
    assert len(docs) == 1

    bad = client.get("/api/v1/kb/collections/00000000-0000-0000-0000-000000000000/documents")
    assert bad.status_code == 404
