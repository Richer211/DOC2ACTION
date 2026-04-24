"""Request ID + structured HTTP logging (Phase 7)."""
from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

LOG = logging.getLogger("doc2action.http")
LOG_ANALYZE = logging.getLogger("doc2action.analyze")


def configure_logging() -> None:
    if logging.root.handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assign X-Request-ID (or pass through client header) and log one line per request."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        rid = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = rid
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        line = {
            "event": "http_request",
            "request_id": rid,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
        }
        LOG.info(json.dumps(line, ensure_ascii=False))
        return response


def log_analyze_completed(
    request_id: str | None,
    meta: dict[str, Any],
    *,
    job_id: str | None = None,
) -> None:
    """Structured business log after a successful analyze (sync or async job)."""
    line: dict[str, Any] = {
        "event": "analyze_completed",
        "request_id": request_id,
        "extractor_mode": meta.get("extractor_mode"),
        "rag_applied": meta.get("rag_applied"),
        "rag_enabled": meta.get("rag_enabled"),
        "chunk_count": meta.get("chunk_count"),
        "used_llm": meta.get("used_llm"),
        "used_lora": meta.get("used_lora"),
    }
    if job_id:
        line["job_id"] = job_id
    LOG_ANALYZE.info(json.dumps(line, ensure_ascii=False))
