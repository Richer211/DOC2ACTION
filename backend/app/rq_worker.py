"""Run an RQ worker: processes queue DOC2ACTION_RQ_QUEUE (default doc2action).

Usage (from repo root, after `pip install -r backend/requirements.txt`):

  cd backend
  export DOC2ACTION_REDIS_URL=redis://127.0.0.1:6379/0
  python -m app.rq_worker

On macOS the default RQ Worker uses fork(); ObjC + fork causes SIGABRT
(``NSMutableString initialize...``). This module uses SimpleWorker on darwin
(same process, no fork). On Linux the default is fork-based Worker unless
DOC2ACTION_RQ_SIMPLE_WORKER=1.

Or: rq worker -u "$DOC2ACTION_REDIS_URL" doc2action  (CLI still forks on Mac — prefer python -m app.rq_worker)
"""
from __future__ import annotations

import os
import sys

import app.analysis_store as analysis_store
import app.kb_store as kb_store
from redis import Redis
from rq import SimpleWorker, Worker

from app.rq_support import _QUEUE_NAME, redis_url


def _worker_class() -> type[Worker]:
    if sys.platform == "darwin":
        return SimpleWorker
    if os.getenv("DOC2ACTION_RQ_SIMPLE_WORKER", "").strip().lower() in {"1", "true", "yes", "on"}:
        return SimpleWorker
    return Worker


def main() -> None:
    analysis_store.init_schema()
    kb_store.init_kb_schema()
    url = redis_url() or "redis://127.0.0.1:6379/0"
    conn = Redis.from_url(url)
    _worker_class()([_QUEUE_NAME], connection=conn).work()


if __name__ == "__main__":
    main()
