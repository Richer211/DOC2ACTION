# 最小线上演示：Vercel（前端）+ Railway（后端）

面向 **Doc2Action 二版**：让浏览器能访问完整工作台（含登录、分析、知识库）。不涉及 AWS/阿里云；同一后端镜像日后可迁到其它容器平台。

## 架构

```text
用户浏览器
    → HTTPS → Vercel（Next.js）
    → HTTPS → Railway（FastAPI，`backend/Dockerfile`）
```

前端通过 `NEXT_PUBLIC_API_BASE_URL` 调用后端；后端通过 `DOC2ACTION_CORS_ORIGINS` 允许该前端源站跨域。

## 1. Railway：部署 API

### 1.1 新建服务（顺序很重要）

monorepo 若**不**先设子目录，Railway 会在**仓库根目录**用默认 **Railpack** 猜构建计划，容易报错：`Error creating build plan with Railpack`。

1. 登录 [Railway](https://railway.app)，**New Project** → **Deploy from GitHub repo**，选中 **DOC2ACTION**。
2. **立刻**打开该服务 **Settings**（齿轮）：
   - **Source → Root Directory**：填 **`backend`**（必须，与 `Dockerfile` / `requirements.txt` 同级）。
   - **Build**：**Builder** 选 **Dockerfile**（不要选 Railpack / Nixpacks）。若已提交本仓库里的 `backend/railway.toml`，也会写明 `builder = DOCKERFILE`，与界面一致即可。
3. 保存后 **Redeploy**（或 **Deployments → Redeploy**），再观察构建日志里应出现类似 **Using Dockerfile**。
4. **Networking → Generate Domain** 得到公网 URL。生成后**务必**在 **Settings → Networking** 里点开该 `*.up.railway.app` 域名，确认 **Target port（目标端口）** 与**进程监听端口**一致。Railway 会注入 `PORT`（Uvicorn 日志里常见为 **`...:8080`**）。若 Target port 被设成 **3000** 等错误值，会出现 **[Deploy Logs 里内部 /health=200，但公网与 HTTP Logs 全是 502](https://docs.railway.com/networking/troubleshooting/application-failed-to-respond)** 的现象。
5. **`Settings → Deploy` 里不要配置 Cron Schedule**（如 `0 0 * * *`）。在 Railway 中，[Cron 用于「到点执行、跑完就退出」的短任务](https://docs.railway.com/cron-jobs)；**Uvicorn / Web API 是长驻、不退出的进程**，与 Cron 语义冲突，容易出现 **HTTP 502、Deploy Logs 几乎为空、时间线里 Network 不启动、界面上写「Next in x hours」** 等。本仓库的后端**必须**作普通 Web 服务一直运行；需要定时任务请**另开服务**或在应用里用调度库。

若你**已经**在错误状态下部署失败：改完 Root Directory + Builder 后务必 **Redeploy**，不要只用旧失败记录。

### 1.2 环境变量（在 Railway Variables 中配置）

| 变量 | 必填 | 说明 |
|------|------|------|
| `OPENAI_API_KEY` | 若要 LLM/RAG | 与本地一致 |
| `OPENAI_MODEL` | 否 | 例如 `gpt-4o-mini` |
| `DOC2ACTION_CORS_ORIGINS` | **是**（有线上前端时） | 逗号分隔、**无尾斜杠**，例如 `https://你的项目.vercel.app`；本地调试可保留 `http://localhost:3000` 一并写上 |
| `DOC2ACTION_JWT_SECRET` | 建议 | 生产随机长字符串；配合 `/login` |
| `DOC2ACTION_DEMO_USER` / `DOC2ACTION_DEMO_PASSWORD` | 可选 | 与本地 demo 账号一致即可 |
| `DOC2ACTION_API_KEY` | 可选 | 与前端 `NEXT_PUBLIC_DOC2ACTION_API_KEY` 一致时，未登录也可用 API Key |
| `DOC2ACTION_REDIS_URL` | 可选 | 异步队列；演示可暂不配 |
| `DOC2ACTION_ANALYSIS_DB` | 推荐 | 不填则默认容器内 `backend/.cache/analyses.sqlite`（**无卷时重启会丢历史记录**） |

### 1.3 持久化 SQLite（推荐）

Doc2Action 的“最近分析”和知识库元数据默认写入 SQLite。若不挂载 Railway Volume，数据会存在容器文件系统里，**重新部署、横向扩容或容器迁移后可能丢失**。线上演示若希望保留历史记录，建议开启持久化：

1. Railway → `DOC2ACTION` 服务 → **Storage / Volumes** → **Add Volume**。
2. 将 Volume 挂载到容器路径，例如：`/data`。
3. Railway → **Variables** 新增：

`DOC2ACTION_ANALYSIS_DB=/data/analyses.sqlite`

4. **Redeploy** 后端。
5. 在线上跑一次 Analyze，刷新页面确认“最近分析”可见；再 Redeploy 一次后检查记录仍在。

> 当前 SQLite 适合 MVP / 单实例演示。若后续并发写入、多实例扩容或需要查询分析，应迁移到 Postgres，并把 `analysis_store` / `kb_store` 改为数据库连接池。

### 1.4 验证

```bash
curl -sS "https://<你的-railway-域名>/health"
```

应返回 JSON：`"status":"ok"`。

---

## 2. Vercel：部署前端

1. 登录 [Vercel](https://vercel.com)，**Add New…** → **Project**，导入同一 GitHub 仓库。
2. **Root Directory** 选：`frontend`（Framework Preset 一般为 **Next.js**）。
3. **Environment Variables**（Production，必要时 Preview 同步）：

| 变量 | 值 |
|------|-----|
| `NEXT_PUBLIC_API_BASE_URL` | Railway 公网 API 根 URL，**无尾斜杠**，例如 `https://doc2action-api-production-xxxx.up.railway.app` |
| `NEXT_PUBLIC_DOC2ACTION_API_KEY` | 若后端启用了 `DOC2ACTION_API_KEY`，与之一致；否则可不设 |

4. Deploy。记录前端域名，例如 `https://doc2action.vercel.app`。

5. **回到 Railway**，把 `DOC2ACTION_CORS_ORIGINS` 更新为上述 Vercel 域名（可多值逗号分隔），**Redeploy** 后端使 CORS 生效。

---

## 3. 本地 Docker 自测（可选）

在仓库内：

```bash
cd backend
docker build -t doc2action-api:local .
docker run --rm -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e DOC2ACTION_CORS_ORIGINS=http://localhost:3000 \
  doc2action-api:local
```

浏览器仍用本地 `npm run dev` 连 `http://127.0.0.1:8000` 即可。

---

## 4. 常见问题

- **Build：`Error creating build plan with Railpack`**：几乎都是因为 **Root Directory 仍是仓库根** 或未改为 **Dockerfile** 构建。按 **§1.1** 设 `backend` + Dockerfile 后 Redeploy。
- **浏览器里请求 API 报 CORS**：检查 `DOC2ACTION_CORS_ORIGINS` 是否**精确包含**前端 origin（协议 + 域名 + 端口，无路径、无尾斜杠）。
- **401**：生产建议开启 `DOC2ACTION_JWT_SECRET` 或 `DOC2ACTION_API_KEY`，并在前端登录或配置 `NEXT_PUBLIC_DOC2ACTION_API_KEY`。
- **迁 AWS / 阿里云**：同一 `backend/Dockerfile` 可推到 ECR/ACR，在 ECS/ACK 等上以相同环境变量运行；再配 ALB/SLB 与 HTTPS 证书即可，逻辑与 Railway 一致。
- **Deploy Logs 里 /health=200、但浏览器访问 /health 仍 502（HTTP Logs 也 502）**：**多为公网域名的 [Target port](https://docs.railway.com/networking/troubleshooting/application-failed-to-respond) 与容器内监听端口不一致**（例如边沿仍指向 **3000**、Uvicorn 实际在 **8080**）。到 **Settings → Networking** 里编辑 `*.up.railway.app`，把 **Target port** 改为与日志里 `Uvicorn running on` **同一端口**。
- **Deploy Logs 很空、时间线里「Network: Not started」、HTTP 全是 502**：**绝大多数是误开了 `Settings → Deploy → Cron Schedule`**。请**完全删除**该 Cron 表达式，保存后再 **Redeploy**（见上文 §1.1 第 5 点）。并确认 **Networking** 已 **Generate Domain**；**不要**在 Variables 里手填/覆盖 **`PORT`**。修复后 Deploy Logs 里应出现 `[doc2action] starting uvicorn...`；若仍全空，试 **Railway CLI** `railway logs` 或向官方带 deployment id 反馈。

---

## 5. 与 CI 的关系

GitHub Actions 的 **CI** 负责测试与静态检查；当前线上发布由 **Vercel / Railway 的 GitHub 集成**自动触发，而不是由 GitHub Actions 的 Deploy job 触发。

推荐发布链路：

1. 从 `main` 拉功能分支，例如 `feat/kb-search`、`fix/railway-health`。
2. 提交 PR 后，GitHub Actions 跑 CI，Vercel 自动生成 Preview Deployment。
3. CI 通过并人工检查 Preview 后，再 merge 到 `main`。
4. `main` 更新后：
   - Vercel 使用 `frontend/` 自动发布 Production。
   - Railway 使用 `backend/` 自动发布 Production。
5. Railway 建议开启 **Wait for CI**，避免 CI 失败时后端仍被部署。

若后续需要更严格的发布控制，可再增加 GitHub Actions Deploy workflow：在 CI 成功后调用 Vercel CLI / Railway API，并加入人工审批、版本标签、回滚记录等。

---

## 6. 分支保护建议

GitHub 上建议保护 `main`，避免本地直接 push 坏代码触发线上部署：

1. GitHub 仓库 → **Settings → Branches**。
2. **Add branch ruleset** 或 **Add branch protection rule**。
3. Branch name pattern 填：`main`。
4. 建议开启：
   - **Require a pull request before merging**。
   - **Require status checks to pass before merging**，并选择当前 CI workflow。
   - **Require branches to be up to date before merging**。
   - **Block force pushes**。
   - **Restrict deletions**。
5. 保存后，日常流程改为：功能分支 → PR → CI/Preview 验证 → merge `main` → 自动发布。

---

## 7. 本次部署排障复盘（面试可讲）

这次线上化的核心不是“把项目扔到平台上”，而是把 monorepo、容器端口、跨域、健康检查和发布门禁串成可复用的部署链路。

可以按下面思路讲：

- **现象 1：前端 Backend Health 显示 `Failed to fetch`**  
  先区分是 CORS、后端不可达还是认证问题。通过直接访问 Railway `/health` 发现后端公网 502，因此先排除前端页面逻辑，把问题收敛到 Railway 后端。

- **现象 2：Railway Build 成功，但 Deploy Logs 为空、HTTP Logs 全 502**  
  一开始容易误判为代码没启动。后来发现服务被配置了 **Cron Schedule**，而 Railway Cron 适合“到点执行并退出”的短任务，不适合 Uvicorn 这种长驻 Web 进程。修复方式是将 Schedule 改成 **No schedule**，让服务作为普通 Web API 常驻。

- **现象 3：Deploy Logs 里 `/health` 已经 200，但浏览器访问 `/health` 仍 502**  
  这说明容器内部已经健康，问题在 Railway Edge Proxy 到容器端口的映射。最终定位到 **Networking Target port** 与 Uvicorn 监听端口不一致；将 Target port 改为日志里的 `8080` 后公网恢复。

- **现象 4：Vercel 前端能打开，但浏览器请求 API 失败**  
  通过 CORS 原理定位：后端 `DOC2ACTION_CORS_ORIGINS` 必须填**前端页面 origin**，例如 `https://doc-2-action.vercel.app`，而不是 Railway 后端 URL。

- **现象 5：登录 401**  
  Demo 登录账号来自 Railway Variables：`DOC2ACTION_DEMO_USER` / `DOC2ACTION_DEMO_PASSWORD`。空字符串变量不会自动回退默认值；后端也做了 `.strip()` 以降低复制粘贴空格导致的误配。

这次沉淀出的工程化措施：

- `backend/Dockerfile` 显式使用 `uvicorn --host 0.0.0.0 --port ${PORT:-8000}`，并在启动时打印日志，便于云端排障。
- `backend/railway.toml` 固定 Dockerfile 构建，避免 monorepo 被 Railpack 误识别。
- 文档中补齐 Root Directory、Cron、Target port、CORS、Volume、CI 门禁等部署清单。
- 发布链路上建议启用 Railway **Wait for CI** 和 GitHub `main` 分支保护，避免 CI 未通过的代码自动上线。
