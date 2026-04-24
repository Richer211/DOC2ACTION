"""Redis + RQ helpers for async analyze (optional; see DOC2ACTION_REDIS_URL)."""
from __future__ import annotations

import os
from typing import Any

from redis import Redis
from rq import Queue
from rq.exceptions import NoSuchJobError
from rq.job import Job, JobStatus

from app.rq_tasks import run_analyze_job

_QUEUE_NAME = os.getenv("DOC2ACTION_RQ_QUEUE", "doc2action")


def redis_url() -> str:
    return os.getenv("DOC2ACTION_REDIS_URL", "").strip()


def redis_jobs_enabled() -> bool:
    return bool(redis_url())


def _connection() -> Redis:
    return Redis.from_url(redis_url())


def enqueue_analyze(
    body_dict: dict[str, Any],
    x_extractor_mode: str | None,
    x_rag_enabled: str | None,
) -> str:
    conn = _connection()
    q = Queue(_QUEUE_NAME, connection=conn)
    timeout_s = int(os.getenv("DOC2ACTION_RQ_JOB_TIMEOUT", "600"))
    ttl_s = int(os.getenv("DOC2ACTION_RQ_RESULT_TTL", "86400"))
    job = q.enqueue(
        run_analyze_job,
        body_dict,
        x_extractor_mode,
        x_rag_enabled,
        job_timeout=timeout_s,
        result_ttl=ttl_s,
    )
    return job.id


def fetch_job_row(job_id: str) -> dict[str, Any] | None:
    """Return internal row compatible with JobStatusResponse assembly, or None if unknown."""
    try:
        job = Job.fetch(job_id, connection=_connection())
    except NoSuchJobError:
        return None
    st = job.get_status()
    if st == JobStatus.FINISHED:
        return {"status": "completed", "result": job.result, "error": None}
    if st == JobStatus.FAILED:
        err = job.exc_info or "job failed"
        if isinstance(err, str) and len(err) > 4000:
            err = err[:4000] + "…"
        return {"status": "failed", "result": None, "error": err}
    if st == JobStatus.STARTED:
        return {"status": "running", "result": None, "error": None}
    return {"status": "pending", "result": None, "error": None}
