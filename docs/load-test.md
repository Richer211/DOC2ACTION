# Load Test Notes

Doc2Action includes a small standard-library load test script for smoke-level capacity checks. It is not a replacement for a full production load test, but it is useful for comparing basic latency, error rate, and deployment stability after changes.

Script:

```bash
python scripts/load_test.py --help
```

## Local Examples

Health check:

```bash
python scripts/load_test.py \
  --base-url http://127.0.0.1:8000 \
  --endpoint health \
  --requests 50 \
  --concurrency 5
```

Analyze endpoint:

```bash
python scripts/load_test.py \
  --base-url http://127.0.0.1:8000 \
  --endpoint analyze \
  --requests 20 \
  --concurrency 5
```

## Production Smoke Test

Run only small smoke tests against the public demo environment to avoid unnecessary API cost and platform throttling:

```bash
python scripts/load_test.py \
  --base-url https://doc2action-production.up.railway.app \
  --endpoint health \
  --requests 30 \
  --concurrency 5
```

If the backend requires an API key:

```bash
python scripts/load_test.py \
  --base-url https://doc2action-production.up.railway.app \
  --endpoint analyze \
  --requests 10 \
  --concurrency 2 \
  --api-key "$DOC2ACTION_API_KEY"
```

## Output

The script prints JSON:

```json
{
  "requests": 30,
  "ok": 30,
  "failed": 0,
  "success_rate": 1.0,
  "throughput_rps": 12.5,
  "latency_ms": {
    "min": 41.2,
    "avg": 53.8,
    "p50": 50.1,
    "p95": 79.4,
    "max": 91.3
  },
  "status_counts": {
    "200": 30
  },
  "sample_errors": []
}
```

You can also persist the summary:

```bash
python scripts/load_test.py \
  --base-url http://127.0.0.1:8000 \
  --endpoint health \
  --output-json learning/reports/load-health-local.json
```

## Suggested Baseline

For interview/demo readiness, keep a short note of:

- `/health` success rate under concurrency 5 and 10.
- `/analyze` success rate with a short input under concurrency 2 and 5.
- p50 and p95 latency.
- whether requests used rules mode, LLM mode, or API key/JWT auth.

## Limitations

- Uses Python threads and `urllib`, so it is intentionally simple.
- Does not measure browser rendering time.
- LLM latency varies with model provider availability and prompt size.
- Analyze tests may incur OpenAI API cost unless you force rules mode or use a small request count.
