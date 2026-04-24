# 密钥与安全（Phase 7 · 面试可讲）

## `DOC2ACTION_API_KEY`（应用接口密钥）

- **用途**：保护 `POST /analyze`、`POST /api/v1/analyze`、`POST /api/v1/jobs/analyze` 等；与 **OpenAI API Key** 分离（一个管「谁可调你的服务」，一个管「谁可调模型供应商」）。
- **本地开发**：可不设置；设置后未带 `X-API-Key` / `Bearer` 的请求会 **401**。
- **轮换**：在部署平台或密钥管理系统中生成新值 → 更新服务端环境变量 → 再更新合法客户端（前端仅本地 demo 可用 `NEXT_PUBLIC_*`，**生产勿把应用密钥打进浏览器包**）。
- **泄露处理**：若密钥出现在截图、仓库或日志，视为已泄露 → **立即换新**并检查调用日志。

## 为何不裸奔公网

- 抽取接口会消耗 **LLM / Embedding** 成本，且可能被滥用为「免费代调 OpenAI」。
- 至少使用 **API Key + 限流**；再上 **HTTPS**、**WAF**、**IP 允许列表** 等按环境递进。

## 部署时密钥注入

- 优先由 **K8s Secret / 云厂商 Secret / CI 注入**，而非写入镜像或代码库。
- `.env` 仅用于本地；**`.env` 与 `.env.local` 已列入 `.gitignore`**（按仓库配置）。
- **容器 / PaaS**：在平台控制台配置环境变量（如 `DOC2ACTION_API_KEY`、`OPENAI_API_KEY`、`DOC2ACTION_REDIS_URL`），构建镜像时不 `ARG` 传入生产密钥；同一镜像多环境靠不同部署配置区分。

## `DOC2ACTION_JWT_SECRET`（可选 · Demo JWT）

- **用途**：签发 **`POST /api/v1/auth/token`** 返回的 **Bearer JWT**（HS256），可与 **`DOC2ACTION_API_KEY`** 二选一或并存：受保护路由接受 **`X-API-Key`**、**Bearer 应用 Key** 或 **Bearer JWT**（见 `app/deps_auth.py`）。
- **演示账号**：`DOC2ACTION_DEMO_USER` / `DOC2ACTION_DEMO_PASSWORD`（默认 `demo` / `demo`），**生产请改掉或关闭该端点**。
- **与 OpenAI Key**：仍完全分离；JWT 只解决「谁调用你的 HTTP API」。
