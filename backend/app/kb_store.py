"""P2: minimal knowledge base (collections + documents) in SQLite."""
from __future__ import annotations

import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.rag import split_into_semantic_chunks

_LOCK = threading.Lock()
_BACKEND_DIR = Path(__file__).resolve().parents[1]
_DEFAULT_DB = _BACKEND_DIR / ".cache" / "analyses.sqlite"


def db_path() -> Path:
    raw = os.getenv("DOC2ACTION_ANALYSIS_DB", "").strip()
    return Path(raw) if raw else _DEFAULT_DB


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_kb_schema() -> None:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        conn = sqlite3.connect(path, check_same_thread=False)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS kb_collections (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    user_sub TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS kb_documents (
                    id TEXT PRIMARY KEY,
                    collection_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (collection_id) REFERENCES kb_collections(id)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_kb_docs_collection ON kb_documents(collection_id)"
            )
            conn.commit()
        finally:
            conn.close()


def create_collection(name: str, user_sub: str | None) -> dict[str, Any]:
    cid = str(uuid.uuid4())
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        conn = sqlite3.connect(path, check_same_thread=False)
        try:
            conn.execute(
                "INSERT INTO kb_collections (id, name, user_sub, created_at) VALUES (?, ?, ?, ?)",
                (cid, name.strip() or "未命名", user_sub, _now()),
            )
            conn.commit()
        finally:
            conn.close()
    return {"id": cid, "name": name.strip() or "未命名", "user_sub": user_sub, "created_at": _now()}


def list_collections(user_sub: str | None) -> list[dict[str, Any]]:
    path = db_path()
    if not path.exists():
        return []
    with _LOCK:
        conn = sqlite3.connect(path, check_same_thread=False)
        try:
            if user_sub is not None:
                cur = conn.execute(
                    """
                    SELECT id, name, user_sub, created_at FROM kb_collections
                    WHERE user_sub = ?
                    ORDER BY created_at DESC
                    """,
                    (user_sub,),
                )
            else:
                cur = conn.execute(
                    "SELECT id, name, user_sub, created_at FROM kb_collections ORDER BY created_at DESC"
                )
            rows = cur.fetchall()
        finally:
            conn.close()
    return [
        {"id": r[0], "name": r[1], "user_sub": r[2], "created_at": r[3]}
        for r in rows
    ]


def collection_exists(collection_id: str) -> bool:
    path = db_path()
    if not path.exists():
        return False
    with _LOCK:
        conn = sqlite3.connect(path, check_same_thread=False)
        try:
            cur = conn.execute(
                "SELECT 1 FROM kb_collections WHERE id = ? LIMIT 1",
                (collection_id,),
            )
            return cur.fetchone() is not None
        finally:
            conn.close()


def add_document(collection_id: str, title: str, content: str) -> dict[str, Any]:
    if not collection_exists(collection_id):
        raise KeyError("collection_not_found")
    max_chars = int(os.getenv("DOC2ACTION_KB_MAX_DOC_CHARS", "500000"))
    if len(content) > max_chars:
        raise ValueError("document_too_large")
    did = str(uuid.uuid4())
    path = db_path()
    with _LOCK:
        conn = sqlite3.connect(path, check_same_thread=False)
        try:
            conn.execute(
                """
                INSERT INTO kb_documents (id, collection_id, title, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (did, collection_id, title.strip() or "未命名", content, _now()),
            )
            conn.commit()
        finally:
            conn.close()
    return {"id": did, "collection_id": collection_id, "title": title.strip() or "未命名"}


def list_documents(collection_id: str) -> list[dict[str, Any]]:
    if not collection_exists(collection_id):
        raise KeyError("collection_not_found")
    path = db_path()
    with _LOCK:
        conn = sqlite3.connect(path, check_same_thread=False)
        try:
            cur = conn.execute(
                """
                SELECT id, title, length(content), created_at FROM kb_documents
                WHERE collection_id = ? ORDER BY created_at DESC
                """,
                (collection_id,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
    return [
        {"id": r[0], "title": r[1], "content_length": r[2], "created_at": r[3]}
        for r in rows
    ]


def get_collection_chunk_strings(collection_id: str) -> list[str]:
    """Semantic chunks over all documents in collection (for KB-RAG)."""
    if not collection_exists(collection_id):
        raise KeyError("collection_not_found")
    path = db_path()
    with _LOCK:
        conn = sqlite3.connect(path, check_same_thread=False)
        try:
            cur = conn.execute(
                "SELECT title, content FROM kb_documents WHERE collection_id = ? ORDER BY created_at",
                (collection_id,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()
    if not rows:
        return []
    max_chars = int(os.getenv("DOC2ACTION_CHUNK_MAX_CHARS", "500"))
    pieces: list[str] = []
    for title, content in rows:
        header = f"## KB: {title}\n"
        blob = header + content
        pieces.extend(split_into_semantic_chunks(blob, max_chars=max_chars))
    return pieces
