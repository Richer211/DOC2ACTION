"""
Optional on-disk cache for OpenAI embedding vectors (SQLite).

Set DOC2ACTION_RAG_EMBED_CACHE_DIR to an absolute or relative directory path to enable.
Reduces repeated API calls for identical (model, text) pairs across requests.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any

_lock = threading.Lock()
_instance: Any = None


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class EmbeddingDiskCache:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()

    def _conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            conn.execute(
                "CREATE TABLE IF NOT EXISTS kv ("
                "model TEXT NOT NULL, h TEXT NOT NULL, emb TEXT NOT NULL, "
                "PRIMARY KEY (model, h))"
            )
            self._local.conn = conn
        return conn

    def get(self, model: str, text: str) -> list[float] | None:
        h = _text_hash(text)
        row = self._conn().execute("SELECT emb FROM kv WHERE model=? AND h=?", (model, h)).fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def set(self, model: str, text: str, emb: list[float]) -> None:
        h = _text_hash(text)
        blob = json.dumps(emb, separators=(",", ":"))
        with _lock:
            c = self._conn()
            c.execute(
                "INSERT OR REPLACE INTO kv (model, h, emb) VALUES (?,?,?)",
                (model, h, blob),
            )
            c.commit()


def get_embed_cache() -> EmbeddingDiskCache | None:
    global _instance
    raw = os.getenv("DOC2ACTION_RAG_EMBED_CACHE_DIR", "").strip()
    if not raw:
        return None
    if _instance is None:
        path = Path(raw).expanduser().resolve() / "openai_embeddings.sqlite"
        _instance = EmbeddingDiskCache(path)
    return _instance


def embed_cache_enabled() -> bool:
    return bool(os.getenv("DOC2ACTION_RAG_EMBED_CACHE_DIR", "").strip())
