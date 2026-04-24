"""RQ worker task: importable entrypoint for Redis queue workers."""
from __future__ import annotations

from typing import Any

import app.analysis_store as analysis_store
from rq import get_current_job

from app.observability import log_analyze_completed


def run_analyze_job(
    body_dict: dict[str, Any],
    x_extractor_mode: str | None,
    x_rag_enabled: str | None,
) -> dict[str, Any]:
    """Run the same pipeline as synchronous /analyze; return AnalyzeResponse as dict."""
    # Local import avoids loading heavy app graph until the worker runs the job.
    from app.main import AnalyzeRequest, _analyze_core

    job = get_current_job()
    jid = job.id if job else "unknown"
    try:
        body = AnalyzeRequest(**body_dict)
        resp = _analyze_core(body, x_extractor_mode, x_rag_enabled)
        log_analyze_completed(None, resp.meta, job_id=jid)
        analysis_store.update_run(jid, "completed", resp.model_dump(), None)
        return resp.model_dump()
    except Exception as exc:
        analysis_store.update_run(jid, "failed", None, str(exc))
        raise
