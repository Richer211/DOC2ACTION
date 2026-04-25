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
| `DOC2ACTION_ANALYSIS_DB` | 可选 | 不填则默认容器内 `backend/.cache/analyses.sqlite`（**无卷时重启可能丢库**） |

**持久化 SQLite（可选）**：在 Railway 为该服务 **Add Volume**，例如挂载到 `/data`，并设置：

`DOC2ACTION_ANALYSIS_DB=/data/analyses.sqlite`

### 1.3 验证

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

GitHub Actions 的 **CI** 仍只负责测试与静态检查；**不会**自动部署到 Vercel/Railway。若需「合并到 main 自动发布」，可在二版后期再加 **Deploy** 工作流（分别调用 Vercel CLI / Railway API 或使用平台自带的 Git 集成）。
