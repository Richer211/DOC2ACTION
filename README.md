# Doc2Action

[![CI](https://github.com/Richer211/DOC2ACTION/actions/workflows/ci.yml/badge.svg)](https://github.com/Richer211/DOC2ACTION/actions)

Doc2Action is a web application that turns unstructured documents into reviewable action-oriented summaries. It accepts meeting notes, PRDs, and email-style text, then extracts:

- summary
- action items
- risks
- open questions
- source chunks used by the extraction

The project is built as a small production-style LLM application: FastAPI backend, Next.js frontend, optional JWT/API-key auth, SQLite persistence, RAG-style context retrieval, Docker deployment, and CI checks.

## Links

- App: [https://doc-2-action.vercel.app](https://doc-2-action.vercel.app)
- API docs: [https://doc2action-production.up.railway.app/docs](https://doc2action-production.up.railway.app/docs)

## Features

- Document analysis with rules, LLM, and fallback modes.
- Source-grounded output: extracted items can be traced back to input chunks.
- Editable review workspace with Markdown export.
- File upload for `.txt` and `.md` inputs.
- Optional JWT login and API key access.
- Recent analysis history stored in SQLite.
- Knowledge-base collections for RAG-style retrieval.
- Optional Redis/RQ background jobs.
- Health checks, request logging, and OpenAPI documentation.

## Architecture

```text
Browser
  -> Vercel / Next.js frontend
  -> Railway / FastAPI backend
  -> SQLite, optional Redis, optional OpenAI APIs
```

```text
Doc2Action/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app and API routes
│   │   ├── rag.py           # Chunking and retrieval helpers
│   │   ├── kb_store.py      # Knowledge-base persistence
│   │   └── analysis_store.py
│   ├── tests/
│   ├── Dockerfile
│   ├── railway.toml
│   └── requirements.txt
├── frontend/
│   ├── src/app/
│   ├── src/components/
│   └── src/lib/
├── ml/
├── samples/
└── scripts/
```

## Tech Stack

- Backend: FastAPI, Pydantic, SQLite, Redis/RQ optional
- Frontend: Next.js, TypeScript, Tailwind CSS
- LLM/RAG: OpenAI API, semantic chunking, source-reference mapping
- Deployment: Docker, Railway, Vercel
- CI: GitHub Actions, Ruff, Pytest, TypeScript, ESLint

## Local Setup

Requirements:

- Python 3.10+
- Node.js 18+

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Useful endpoints:

- `GET http://127.0.0.1:8000/health`
- `GET http://127.0.0.1:8000/version`
- `GET http://127.0.0.1:8000/docs`

Example request:

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text":"Meeting decision: launch v1 next week. Alice owns login QA.","document_type":"meeting_notes"}'
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Configuration

Backend configuration is read from environment variables. Start from `backend/.env.example`.

Common variables:

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Enables LLM extraction, embeddings, and RAG features |
| `OPENAI_MODEL` | OpenAI chat model name |
| `DOC2ACTION_CORS_ORIGINS` | Allowed browser origins, comma-separated |
| `DOC2ACTION_JWT_SECRET` | Enables JWT login |
| `DOC2ACTION_DEMO_USER` / `DOC2ACTION_DEMO_PASSWORD` | Demo login credentials |
| `DOC2ACTION_API_KEY` | Optional API key gate |
| `DOC2ACTION_ANALYSIS_DB` | SQLite path, e.g. `/data/analyses.sqlite` in production |
| `DOC2ACTION_REDIS_URL` | Enables Redis/RQ jobs |

Frontend configuration is read from `frontend/.env.local`:

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | FastAPI base URL |
| `NEXT_PUBLIC_DOC2ACTION_API_KEY` | Optional client-side API key |

Do not commit real `.env` files or secrets.

## Optional Background Jobs

Run Redis:

```bash
docker compose up -d redis
```

Set `DOC2ACTION_REDIS_URL=redis://127.0.0.1:6379/0`, then run:

```bash
cd backend
python -m app.rq_worker
```

If Redis is not configured, job endpoints fall back to in-process execution for local/demo use.

## Tests and Checks

Backend:

```bash
cd backend
ruff check app tests
python -m pytest tests/ -q
```

Frontend:

```bash
cd frontend
npm run lint
npx tsc --noEmit
```

The same checks run in GitHub Actions on pull requests and pushes to `main`.

## Deployment

The current production setup uses:

- Vercel for `frontend/`
- Railway for `backend/`
- Dockerfile-based backend build
- GitHub Actions CI with protected `main`

Important production notes:

- Railway service root directory should be `backend`.
- Railway backend should run as a normal web service, not as a Cron service.
- Public domain target port must match the port reported by Uvicorn.
- `DOC2ACTION_CORS_ORIGINS` must include the Vercel origin.
- Use a Railway Volume or another persistent store for SQLite history.

## Evaluation Utilities

Sample and evaluation scripts live under `samples/`, `scripts/`, and `ml/`.

```bash
cd backend
source .venv/bin/activate
python ../scripts/run_sample_checks.py
python ../ml/eval/evaluate.py
```

Generated reports are intended for local review and are ignored from the public repository.

## Repository Hygiene

Before pushing changes, check:

- no `.env` or `.env.local` files
- no real API keys or JWT secrets
- no `node_modules/`, `.venv/`, or `.cache/`
- no large training artifacts or local datasets
