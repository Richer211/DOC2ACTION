# 约 5 分钟演示脚本（Doc2Action）

## 准备

1. 后端：`cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
2. 前端：`cd frontend && npm run dev`
3. 浏览器打开 `http://localhost:3000`

可选：若启用 **`DOC2ACTION_API_KEY`**，在 `frontend/.env.local` 配置 **`NEXT_PUBLIC_DOC2ACTION_API_KEY`**（勿提交）。

## 流程（可按口述精简）

1. **健康检查**：页面顶部 Backend Health 为绿色 `status: ok`。
2. **同步分析**：`samples/meeting_notes.md` 粘贴或上传 → 选文档类型 → **Analyze** → 展示 Summary / Action Items / Risks / Open Questions。
3. **引用**：点击某条「查看引用」→ 右侧依据面板展示 chunk 原文。
4. **编辑与导出**：改一条 action → **导出 Markdown**。
5. **异步队列（可选）**：勾选 **异步任务（后台队列）** → 再 Analyze → 观察「已提交任务，轮询中…」→ 结果与同步一致。  
   - 若配置了 **`DOC2ACTION_REDIS_URL`**，需另开终端：`cd backend && python -m app.rq_worker`（并 `docker compose up -d redis` 或自备 Redis）。**macOS** 请用该命令而非 `rq worker` CLI：后者仍会 fork，易触发 ObjC 与 `fork` 不兼容而崩溃；`app.rq_worker` 在 darwin 上已改用 **SimpleWorker**（同进程执行作业）。
6. **工程化（口头）**：`request_id`（响应头）、限流（`DOC2ACTION_RATE_LIMIT`）、`docs/security-secrets.md`、CI（`.github/workflows/ci.yml`）。
7. **Swagger**：`http://127.0.0.1:8000/docs` → **jobs** 下 `POST` + `GET` 轮询；**auth** 下 JWT（需 `DOC2ACTION_JWT_SECRET`）。

## 故意演示（可选）

- **401**：后端启用 Key 但前端未配置 / 请求未带头。
- **429**：短时间连续点击 Analyze 触发限流。

## 怎么确认「新增功能」没问题

| 检查项 | 做法 |
|--------|------|
| 后端 + JWT + 内存任务（不启 Redis） | 仓库根目录：`cd backend && python -m pytest tests/ -q`（应全部通过）。 |
| Redis + RQ 整条链路 | 1）`docker compose up -d redis`；2）`backend/.env` 设 `DOC2ACTION_REDIS_URL=redis://127.0.0.1:6379/0`；3）终端 A：`uvicorn`；4）终端 B：`cd backend && python -m app.rq_worker`；5）仓库根目录：`bash scripts/verify_rq_jobs.sh`（若启用 API Key 则先 `export DOC2ACTION_API_KEY=...`）。脚本以 `completed` 退出即表示 **入队 + Worker 消费 + GET 取回结果** 正常。 |
| 页面异步勾选 | 同上启动 Redis + worker 后，前端勾选「异步任务」点 Analyze，应出现结果（与脚本等价）。 |

**三个终端各自干什么**：终端 A 提供 HTTP API；终端 B 的 worker 只负责从 Redis 拉任务并执行 `_analyze_core`（没有 B，任务会永远停在 `pending`）；Docker 里的 Redis 存队列与 RQ 任务状态。
