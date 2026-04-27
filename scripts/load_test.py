from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path


DEFAULT_TEXT = (
    "Meeting decision: launch v1 next week. Alice owns login QA. "
    "Risk: payment callback may be delayed. Question: who approves the release?"
)


@dataclass(frozen=True)
class Result:
    ok: bool
    status_code: int
    latency_ms: float
    error: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Small HTTP load test for Doc2Action.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL without trailing slash.")
    parser.add_argument("--endpoint", choices=["health", "analyze"], default="health")
    parser.add_argument("--requests", type=int, default=50, help="Total number of HTTP requests.")
    parser.add_argument("--concurrency", type=int, default=5, help="Number of concurrent workers.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Per-request timeout in seconds.")
    parser.add_argument("--document-type", default="meeting_notes")
    parser.add_argument("--text", default=DEFAULT_TEXT)
    parser.add_argument("--api-key", default="", help="Optional X-API-Key value.")
    parser.add_argument("--jwt", default="", help="Optional Bearer token.")
    parser.add_argument("--output-json", type=Path, default=None, help="Optional path for machine-readable results.")
    return parser.parse_args()


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, round((pct / 100) * (len(ordered) - 1))))
    return ordered[idx]


def build_request(args: argparse.Namespace) -> urllib.request.Request:
    base_url = args.base_url.rstrip("/")
    headers = {"Accept": "application/json"}
    if args.api_key:
        headers["X-API-Key"] = args.api_key
    if args.jwt:
        headers["Authorization"] = f"Bearer {args.jwt}"

    if args.endpoint == "health":
        return urllib.request.Request(f"{base_url}/health", headers=headers, method="GET")

    payload = json.dumps(
        {"text": args.text, "document_type": args.document_type},
        ensure_ascii=False,
    ).encode("utf-8")
    headers["Content-Type"] = "application/json"
    return urllib.request.Request(f"{base_url}/analyze", data=payload, headers=headers, method="POST")


def send_once(args: argparse.Namespace) -> Result:
    request = build_request(args)
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            response.read()
            latency_ms = (time.perf_counter() - started) * 1000
            status_code = int(response.status)
            return Result(ok=200 <= status_code < 300, status_code=status_code, latency_ms=latency_ms)
    except urllib.error.HTTPError as exc:
        latency_ms = (time.perf_counter() - started) * 1000
        body = exc.read().decode("utf-8", errors="replace")[:200]
        return Result(ok=False, status_code=int(exc.code), latency_ms=latency_ms, error=body)
    except Exception as exc:
        latency_ms = (time.perf_counter() - started) * 1000
        return Result(ok=False, status_code=0, latency_ms=latency_ms, error=str(exc))


def summarize(results: list[Result], total_elapsed_ms: float) -> dict[str, object]:
    latencies = [r.latency_ms for r in results]
    ok_count = sum(1 for r in results if r.ok)
    status_counts: dict[str, int] = {}
    for result in results:
        key = str(result.status_code)
        status_counts[key] = status_counts.get(key, 0) + 1

    return {
        "requests": len(results),
        "ok": ok_count,
        "failed": len(results) - ok_count,
        "success_rate": round(ok_count / len(results), 4) if results else 0.0,
        "total_elapsed_ms": round(total_elapsed_ms, 2),
        "throughput_rps": round((len(results) / total_elapsed_ms) * 1000, 2) if total_elapsed_ms else 0.0,
        "latency_ms": {
            "min": round(min(latencies), 2) if latencies else 0.0,
            "avg": round(statistics.mean(latencies), 2) if latencies else 0.0,
            "p50": round(percentile(latencies, 50), 2),
            "p95": round(percentile(latencies, 95), 2),
            "max": round(max(latencies), 2) if latencies else 0.0,
        },
        "status_counts": status_counts,
        "sample_errors": [r.error for r in results if r.error][:5],
    }


def main() -> None:
    args = parse_args()
    if args.requests <= 0:
        raise SystemExit("--requests must be positive")
    if args.concurrency <= 0:
        raise SystemExit("--concurrency must be positive")

    started = time.perf_counter()
    results: list[Result] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(send_once, args) for _ in range(args.requests)]
        for future in as_completed(futures):
            results.append(future.result())
    total_elapsed_ms = (time.perf_counter() - started) * 1000

    summary = summarize(results, total_elapsed_ms)
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
