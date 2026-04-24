#!/usr/bin/env bash
# 验证「Redis + RQ」异步任务链路（需 Redis、backend 已设 DOC2ACTION_REDIS_URL、worker 已启动）。
# 用法（仓库根目录）：
#   export DOC2ACTION_API_KEY=...   # 与 backend/.env 中 DOC2ACTION_API_KEY 一致（若后端启用了 Key）
#   bash scripts/verify_rq_jobs.sh
# 可选：API_BASE=http://127.0.0.1:8000 bash scripts/verify_rq_jobs.sh

set -euo pipefail

API_BASE="${API_BASE:-http://127.0.0.1:8000}"
POST_HDR=(-H "Content-Type: application/json" -H "Accept: application/json")
GET_HDR=(-H "Accept: application/json")
if [[ -n "${DOC2ACTION_API_KEY:-}" ]]; then
  POST_HDR+=(-H "X-API-Key: ${DOC2ACTION_API_KEY}")
  GET_HDR+=(-H "X-API-Key: ${DOC2ACTION_API_KEY}")
fi

echo "==> POST ${API_BASE}/api/v1/jobs/analyze"
BODY='{"text":"RQ 自检短文本","document_type":"general"}'
TMP=$(mktemp)
HTTP=$(curl -sS -o "$TMP" -w "%{http_code}" -X POST "${API_BASE}/api/v1/jobs/analyze" "${POST_HDR[@]}" -d "$BODY")
RESP=$(cat "$TMP")
rm -f "$TMP"
echo "$RESP"

if [[ "$HTTP" != "200" ]]; then
  echo "" >&2
  echo "FAIL: HTTP ${HTTP}（提交任务失败）。" >&2
  if [[ "$HTTP" == "401" ]]; then
    echo "后端已启用 DOC2ACTION_API_KEY。请先导出与 backend/.env 相同的密钥后再运行本脚本，例如：" >&2
    echo "  export DOC2ACTION_API_KEY='你的密钥'" >&2
    echo "  bash scripts/verify_rq_jobs.sh" >&2
  fi
  exit 1
fi

JOB_ID=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['job_id'])" "$RESP")

echo "==> Poll GET ${API_BASE}/api/v1/jobs/${JOB_ID}"
for _ in $(seq 1 60); do
  TMP2=$(mktemp)
  H2=$(curl -sS -o "$TMP2" -w "%{http_code}" -X GET "${API_BASE}/api/v1/jobs/${JOB_ID}" "${GET_HDR[@]}")
  ST=$(cat "$TMP2")
  rm -f "$TMP2"
  echo "$ST"
  if [[ "$H2" != "200" ]]; then
    echo "FAIL: poll HTTP ${H2}" >&2
    exit 1
  fi
  STATUS=$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('status',''))" "$ST")
  if [[ "$STATUS" == "completed" ]]; then
    echo "OK: job completed"
    exit 0
  fi
  if [[ "$STATUS" == "failed" ]]; then
    echo "FAIL: job failed" >&2
    exit 1
  fi
  sleep 0.5
done

echo "FAIL: timeout waiting for job" >&2
exit 1
