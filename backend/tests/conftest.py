"""Shared pytest fixtures.

Starlette/FastAPI TestClient only runs application lifespan when used as a
context manager (`with TestClient(app) as c`). Without it, `init_schema()` in
lifespan never runs and SQLite tables (e.g. analysis_runs) are missing — CI
fails while a dirty local .cache may still pass.
"""
from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
