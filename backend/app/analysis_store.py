"""SQLite persistence for analysis runs (P0: task/result audit trail)."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_LOCK = threading.Lock()

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_DEFAULT_DB = _BACKEND_DIR / ".cache" / "analyses.sqlite"


def db_path() -> Path:
    raw = os.getenv("DOC2ACTION_ANALYSIS_DB", "").strip()
    return Path(raw) if raw else _DEFAULT_DB


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_schema() -> None:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        conn = sqlite3.connect(path, check_same_thread=False)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_runs (
                    run_id TEXT PRIMARY KEY,
                    run_kind TEXT NOT NULL,
                    user_sub TEXT,
                    status TEXT NOT NULL,
                    document_type TEXT,
                    extractor_mode TEXT,
                    text_preview TEXT,
                    result_json TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()


def insert_async_pending(
    run_id: str,
    user_sub: str | None,
    document_type: str,
    extractor_mode: str,
    text_preview: str,
) -> None:
    now = _now_iso()
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        conn = sqlite3.connect(path, check_same_thread=False)
        try:
            conn.execute(
                """
                INSERT INTO analysis_runs (
                    run_id, run_kind, user_sub, status, document_type, extractor_mode,
                    text_preview, result_json, error, created_at, updated_at
                ) VALUES (?, 'async', ?, 'pending', ?, ?, ?, NULL, NULL, ?, ?)
                """,
                (run_id, user_sub, document_type, extractor_mode, text_preview, now, now),
            )
            conn.commit()
        finally:
            conn.close()


def update_run(
    run_id: str,
    status: str,
    result: dict[str, Any] | None,
    error: str | None,
) -> None:
    now = _now_iso()
    payload = json.dumps(result, ensure_ascii=False) if result is not None else None
    path = db_path()
    with _LOCK:
        conn = sqlite3.connect(path, check_same_thread=False)
        try:
            conn.execute(
                """
                UPDATE analysis_runs
                SET status = ?, result_json = ?, error = ?, updated_at = ?
                WHERE run_id = ?
                """,
                (status, payload, error, now, run_id),
            )
            conn.commit()
        finally:
            conn.close()


def insert_sync_run(
    run_id: str,
    user_sub: str | None,
    document_type: str,
    extractor_mode: str,
    text_preview: str,
    status: str,
    result: dict[str, Any] | None,
    error: str | None,
) -> None:
    now = _now_iso()
    payload = json.dumps(result, ensure_ascii=False) if result is not None else None
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        conn = sqlite3.connect(path, check_same_thread=False)
        try:
            conn.execute(
                """
                INSERT INTO analysis_runs (
                    run_id, run_kind, user_sub, status, document_type, extractor_mode,
                    text_preview, result_json, error, created_at, updated_at
                ) VALUES (?, 'sync', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    user_sub,
                    status,
                    document_type,
                    extractor_mode,
                    text_preview,
                    payload,
                    error,
                    now,
                    now,
                ),
            )
            conn.commit()
        finally:
            conn.close()


def list_recent(limit: int = 20) -> list[dict[str, Any]]:
    path = db_path()
    if not path.exists():
        return []
    limit = max(1, min(limit, 200))
    with _LOCK:
        conn = sqlite3.connect(path, check_same_thread=False)
        try:
            cur = conn.execute(
                """
                SELECT run_id, run_kind, user_sub, status, document_type, extractor_mode,
                       text_preview, error, created_at, updated_at,
                       CASE WHEN result_json IS NOT NULL THEN length(result_json) ELSE 0 END AS result_bytes
                FROM analysis_runs
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
    keys = [
        "run_id",
        "run_kind",
        "user_sub",
        "status",
        "document_type",
        "extractor_mode",
        "text_preview",
        "error",
        "created_at",
        "updated_at",
        "result_bytes",
    ]
    return [dict(zip(keys, r, strict=True)) for r in rows]
