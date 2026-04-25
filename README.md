# Doc2Action AI Workspace

[![CI](https://github.com/Richer211/DOC2ACTION/actions/workflows/ci.yml/badge.svg)](https://github.com/Richer211/DOC2ACTION/actions)

**持续集成（CI）**：向 `main` / `master` **推送代码**或开 **Pull Request** 时，GitHub Actions 工作流 [**CI**](https://github.com/Richer211/DOC2ACTION/actions) 会自动跑 **后端**（`ruff`、`pytest`）与 **前端**（`tsc --noEmit`、`eslint`）。上方徽章为绿色表示**当前默认分支上最近一次流水线已通过**；点徽章可打开 Actions 查看每次运行的日志与耗时。

---

Doc2Action 把非结构化文档转为可执行的结构化信息（Summary / Action Items / Risks / Open Questions），并支持引用原文 chunk、人工编辑与导出。当前实现覆盖 **MVP 主链路 + 鉴权 + 异步队列 + RAG + 知识库（P2）**。

## 当前能力一览

### 前端（Next.js + TypeScript + Tailwind）

- **全站顶栏**：导航（工作台 / 知识库 / 评测摘要）+ 登录状态与退出
- **`/` 工作台**：文本与 `.txt` / `.md` 上传、文档类型与推理模式、**启用 RAG**、可选 **知识库集合**、可选 **异步任务**轮询、`POST /analyze` 或 Jobs API
- **`/login`**：JWT 登录，成功后进入首页（token 存 `sessionStorage`）
- **`/kb` 知识库**：集合 CRUD（文档标题 + 正文）；与 RAG 联用时向分析提示注入 top‑k 片段
- **`/eval-summary`**：离线评测报告摘要（需与后端相同鉴权）

### 后端（FastAPI）

- **`GET /health`**：健康检查
- **`POST /analyze`**：同步分析（清洗、切块、结构化输出；LLM 失败时可降级规则抽取）
- **`POST /api/v1/jobs/analyze`** + **`GET /api/v1/jobs/{id}`**：可选异步任务（Redis + RQ + worker）
- **`POST /api/v1/auth/token`**：可选 JWT
- **知识库**：`POST/GET /api/v1/kb/collections`，`POST/GET .../collections/{id}/documents`
- **分析记录**：SQLite（默认 `backend/.cache/analyses.sqlite`，见 `.gitignore`）
- **RAG**：语义切块与向量检索（需配置 `OPENAI_API_KEY` 等）；可选附加知识库片段进入 prompt

### 其它资产

- **Phase 6**：`samples/`、`scripts/run_sample_checks.py`、演示材料与 `docs/demo-script.md`
- **评估流水线**：`ml/eval/evaluate.py` 等（报告默认路径见 `backend/.env.example`）

## 目录结构（节选）

```text
Doc2Action/
├── backend/
│   ├── app/
│   │   ├── main.py          # API、分析、KB、Jobs
│   │   ├── kb_store.py      # 知识库 SQLite
│   │   ├── rag.py           # 切块与检索
│   │   └── ...
│   ├── requirements.txt
│   ├── Dockerfile           # Railway / 容器部署
│   ├── railway.toml         # Railway：强制 Dockerfile，避免 Railpack
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/             # page.tsx, login/, kb/, eval-summary/, layout.tsx
│   │   ├── components/      # SiteHeader 等
│   │   └── lib/             # doc2action-api.ts（鉴权头、错误解析）
│   ├── .env.example
│   └── package.json
├── docker-compose.yml       # 可选：仅 Redis（RQ）
├── docs/
│   └── deploy-vercel-railway.md
├── learning/
├── ml/
└── samples/
```

## 环境要求

- Python >= 3.10  
- Node >= 18.17  

## 密钥与安全（必读）

- **永远不要**将真实 `OPENAI_API_KEY`、`DOC2ACTION_API_KEY`、`DOC2ACTION_JWT_SECRET` 或前端 `NEXT_PUBLIC_DOC2ACTION_API_KEY` **提交到 Git**。  
- 本地配置：后端复制 `backend/.env.example` 为 `backend/.env`；前端复制 `frontend/.env.example` 为 `frontend/.env.local`。二者已在 `.gitignore` 中忽略。  
- 若历史提交中曾泄露密钥，请**立即在各平台轮换密钥**。  
- 更细的说明见 `docs/security-secrets.md`。

## 本地运行

### 1) 启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # 再编辑 .env 填入密钥
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- 健康检查：[http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)  
- OpenAPI：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

分析示例：

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text":"会议结论：下周发布v1。需要完成登录页联调。","document_type":"meeting_notes"}'
```

### 2) 启动前端

```bash
cd frontend
npm install
cp .env.example .env.local   # 按需修改 API 地址与可选 API Key
npm run dev
```

打开 [http://localhost:3000](http://localhost:3000)。登录页：[http://localhost:3000/login](http://localhost:3000/login)。

### 3) 异步任务：Redis + RQ（可选）

仓库根目录仅提供 **Redis** 服务（尚无前后端一体化生产镜像）：

```bash
docker compose up -d redis
```

在 `backend/.env` 中设置 `DOC2ACTION_REDIS_URL=redis://127.0.0.1:6379/0`，然后：

- 终端 A：`uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`  
- 终端 B：`cd backend && python -m app.rq_worker`  

**macOS** 上请使用 `python -m app.rq_worker`（已用 SimpleWorker 避免 fork 相关问题），不要仅依赖可能仍 fork 的 `rq worker` CLI。

未配置 Redis 时，jobs 仍在当前 uvicorn 进程内执行。前端勾选 **异步任务** 即走 Jobs API。

自检：`bash scripts/verify_rq_jobs.sh`（若启用 API Key，先 `export DOC2ACTION_API_KEY=...`）。详见 `docs/demo-script.md`。

### 4) JWT 与受保护接口

配置 `DOC2ACTION_JWT_SECRET`（及可选 `DOC2ACTION_DEMO_USER` / `DOC2ACTION_DEMO_PASSWORD`）后，使用 `/login` 或 `POST /api/v1/auth/token` 获取 Bearer；可与 `X-API-Key` 并存。详见 `docs/security-secrets.md`。

### 5) 知识库与 RAG

1. 在 **`/kb`** 创建集合并添加文档。  
2. 在 **`/`** 勾选 **启用 RAG**，并可选择知识库集合；分析请求会携带 `kb_collection_id`（可选）。  
3. RAG / Embedding 依赖后端 `OPENAI_API_KEY` 等配置。

## 部署说明（现状与简历建议）

### 「部署」一般指什么？和 CI 有什么区别？

| | **CI（持续集成）** | **部署 / CD（持续交付）** |
|---|-------------------|---------------------------|
| **做什么** | 每次改代码自动 **跑测试和静态检查**，保证仓库质量 | 把可运行的 **前端 / 后端** 放到公网服务器，用户用 **HTTPS 域名** 访问 |
| **本仓库** | 已在 GitHub Actions 里配置（见上方徽章） | **最小演示**：按 [`docs/deploy-vercel-railway.md`](docs/deploy-vercel-railway.md) 在 **Vercel + Railway** 手动连接仓库即可；未接 GitHub Actions 自动发布 |

**部署一套全栈应用通常要管这些：**

1. **前端（Next.js）**：在 **Vercel**（或 Netlify、Cloudflare Pages 等）连接 GitHub 仓库，平台负责 `npm run build`、CDN、HTTPS；你要配置 **`NEXT_PUBLIC_API_BASE_URL`** 指向线上后端地址（以及按需配置 `NEXT_PUBLIC_DOC2ACTION_API_KEY`）。  
2. **后端（FastAPI）**：在 **Fly.io**、Render、Railway 等跑 **Python 进程**（常见方式是 Docker 镜像或平台提供的 Python 构建）；你要配置 **`OPENAI_API_KEY`**、可选 **`DOC2ACTION_*`**（JWT、API Key、Redis URL、`DOC2ACTION_ANALYSIS_DB` 路径等）。  
3. **数据与队列**：SQLite 文件在云上需 **持久卷** 或改用托管数据库；异步任务需要 **Redis**（如 Upstash）并在 Fly 上**额外跑** `python -m app.rq_worker` 或等价进程。  
4. **安全**：密钥只放在平台「环境变量」里，不要写进仓库；生产环境建议强制 HTTPS、限制 CORS、按需开鉴权。

**Vercel + Fly** 常被一起提起，是因为分工清晰：**Vercel 擅长托管前端**，**Fly（或同类 PaaS）擅长跑长时间运行的 API 容器**；并不是说必须选这两家，同类平台可以替换。

| 项目 | 说明 |
|------|------|
| **仓库内现有什么** | `backend/Dockerfile` + `backend/.dockerignore`（API 容器）；根目录 `docker-compose.yml` **仅 Redis**。一步步上线说明见 **`docs/deploy-vercel-railway.md`**。 |
| **算「有部署经验」吗** | 若你**自己**在云平台把前后端跑通：配置构建命令、环境变量、域名与 HTTPS，并完成一次完整 Analyze——可写进简历。 |
| **建议补强的故事** | 同一镜像可迁 **AWS（ECS/ECR）** 或 **阿里云（ACK/容器镜像服务）**；替换的是托管平台与网络，应用与环境变量模型不变。 |

结论：**代码库侧重可演示的全栈与 AI 管线**；**生产级一键部署需按目标平台补一层封装**；面试时能讲清「CI 验质量、部署管运行环境与密钥」即可。

## Phase 6 快速验证

```bash
cd backend
source .venv/bin/activate
python ../scripts/run_sample_checks.py
```

输出见 `learning/报告与演示材料/demo/`。

## Phase B（数据与评估）快速开始

```bash
cd backend
source .venv/bin/activate
python ../ml/eval/evaluate.py
```

输出默认：

- `learning/报告与演示材料/reports/baseline-eval.json`
- `learning/报告与演示材料/reports/baseline-eval.md`

数据与规范见 `ml/data/schema.json`、`learning/数据与标注规范/` 等。

低成本 LLM 对比基线：

```bash
cd backend
source .venv/bin/activate
python ../ml/eval/compare_baselines.py --llm-model gpt-4o-mini
```

## 升级规划文档

- `项目升级目标与路线图.md`：阶段目标与能力映射  
- `PRD.md` / `MVP.md`：产品与第一版边界  

## 下一步（可选）

- 按样本与评估结果继续优化 prompt 与规则。  
- 按需补充 **Dockerfile / CI / 部署文档**，与招聘岗位的「部署、运维」关键词对齐。

## 提交 GitHub 前（仓库卫生）

推送前建议在仓库根目录执行 `git status`，确认**未纳入**：

- 任何 `.env`、`.env.local`、真实密钥  
- `node_modules/`、`backend/.venv/`、`backend/.cache/`  
- `ml/train/artifacts/`（LoRA  checkpoint，体积大，已在 `.gitignore`）  
- `ml/data/external/` 下原始语料（若本地有下载，一般由 `.gitignore` 按子路径忽略）  

**非运行必需、但可保留的目录**（体积不大或便于讲故事）：`learning/`（学习笔记与报告）、`scripts/`（数据与评测辅助）、`ml/eval/`、`ml/data` 中已跟踪的小型 `jsonl` / `schema.json`。若希望仓库更「产品向」，可日后将 `learning/` 迁出或单独分支；**不建议删除** `backend/`、`frontend/`、`samples/`、`docs/`、`tests/` 等业务与文档主干。
