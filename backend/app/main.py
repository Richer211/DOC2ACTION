import json
import os
import re
import threading
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from pydantic import BaseModel, Field

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency at runtime
    OpenAI = None  # type: ignore[assignment]

# torch / transformers / peft：必须在首次使用 LoRA 时再 import。
# 若在模块顶层 import，RQ worker fork 子进程时（尤其 macOS）易 SIGABRT，即使用户只跑 LLM 也会加载它们。

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency at runtime
    load_dotenv = None  # type: ignore[assignment]

try:
    import jwt
except Exception:  # pragma: no cover
    jwt = None  # type: ignore[assignment]


BASE_DIR = Path(__file__).resolve().parents[1]
if load_dotenv is not None:
    # Load backend/.env when available for local development.
    load_dotenv(BASE_DIR / ".env", override=True)

import app.analysis_store as analysis_store  # noqa: E402
import app.kb_store as kb_store  # noqa: E402
from app.deps_auth import get_optional_user_sub, require_api_key_if_configured  # noqa: E402
from app.eval_summary import load_eval_summary  # noqa: E402
from app.embed_cache import embed_cache_enabled  # noqa: E402
from app.observability import (  # noqa: E402
    RequestContextMiddleware,
    configure_logging,
    log_analyze_completed,
)
from app.rag import (  # noqa: E402
    select_chunk_positions_for_prompt,
    split_into_semantic_chunks,
)
from app.rq_support import enqueue_analyze, fetch_job_row, redis_jobs_enabled  # noqa: E402

_LORA_RUNTIME: dict[str, Any] = {"ready": False, "base_model": "", "adapter_dir": ""}

# In-memory async jobs when DOC2ACTION_REDIS_URL is unset; otherwise RQ + Redis (see app.rq_support).
_JOBS: dict[str, dict[str, Any]] = {}
_JOBS_LOCK = threading.Lock()

configure_logging()
ANALYZE_RATE_LIMIT = os.getenv("DOC2ACTION_RATE_LIMIT", "60/minute")
limiter = Limiter(key_func=get_remote_address, default_limits=[])


def _cors_allow_origins() -> list[str]:
    """浏览器跨域：本地默认 localhost:3000；生产用 DOC2ACTION_CORS_ORIGINS（逗号分隔，勿尾斜杠）。"""
    raw = os.getenv("DOC2ACTION_CORS_ORIGINS", "").strip()
    if not raw:
        return ["http://localhost:3000"]
    return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]


@asynccontextmanager
async def _lifespan(_: FastAPI):
    analysis_store.init_schema()
    kb_store.init_kb_schema()
    yield


def _norm_extractor_mode(header_val: str | None) -> str:
    v = (header_val or os.getenv("DOC2ACTION_EXTRACTOR_MODE", "auto")).strip().lower()
    return v if v in {"auto", "rules", "llm", "lora"} else "auto"


app = FastAPI(
    title="Doc2Action Backend",
    version="0.1.0",
    lifespan=_lifespan,
    openapi_tags=[
        {"name": "health", "description": "Liveness / readiness"},
        {"name": "auth", "description": "Optional JWT (set DOC2ACTION_JWT_SECRET)"},
        {"name": "analyze", "description": "Document → structured extraction (v1 contract under /api/v1)"},
        {
            "name": "jobs",
            "description": "Async analyze (job_id; poll GET). Use DOC2ACTION_REDIS_URL + RQ worker for multi-process.",
        },
        {"name": "analyses", "description": "Persisted analysis runs (SQLite)"},
        {"name": "eval", "description": "Offline evaluation report summary"},
        {"name": "kb", "description": "Knowledge base collections (P2)"},
    ],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestContextMiddleware)


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    """公网根路径：避免只打开域名时像「没服务」；交互请用 /docs 或 /api/v1/*。"""
    return {"service": "doc2action-backend", "docs": "/docs", "health": "/health"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "doc2action-backend"}


@app.get("/api/v1/health", tags=["health"])
def health_check_v1() -> dict[str, str]:
    return health_check()


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    document_type: str = "general"
    # None = follow env / headers; True/False = per-request override
    use_rag: bool | None = None
    use_semantic_chunks: bool | None = None
    # P2: when set with use_rag, retrieve excerpts from this KB collection (OpenAI embeddings)
    kb_collection_id: str | None = None


class Chunk(BaseModel):
    id: int
    text: str


class ActionItem(BaseModel):
    title: str
    priority: str = "medium"
    source_chunk_ids: list[int] = Field(default_factory=list)


class RiskItem(BaseModel):
    description: str
    severity: str = "medium"
    source_chunk_ids: list[int] = Field(default_factory=list)


class OpenQuestion(BaseModel):
    question: str
    source_chunk_ids: list[int] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    summary: str
    action_items: list[ActionItem]
    risks: list[RiskItem]
    open_questions: list[OpenQuestion]
    chunks: list[Chunk]
    meta: dict[str, Any]


class JobEnqueueResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: AnalyzeResponse | None = None
    error: str | None = None


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.post("/api/v1/auth/token", response_model=TokenResponse, tags=["auth"])
def issue_access_token(request: Request, body: LoginRequest) -> TokenResponse:
    """Demo JWT when DOC2ACTION_JWT_SECRET is set (HS256). Pair with DOC2ACTION_DEMO_USER / DOC2ACTION_DEMO_PASSWORD."""
    if jwt is None:
        raise HTTPException(status_code=503, detail="PyJWT not available")
    secret = os.getenv("DOC2ACTION_JWT_SECRET", "").strip()
    if not secret:
        rid = getattr(request.state, "request_id", None)
        raise HTTPException(
            status_code=503,
            detail={
                "error": "jwt_disabled",
                "message": "Set DOC2ACTION_JWT_SECRET to enable JWT issuance.",
                "request_id": rid,
            },
        )
    demo_user = os.getenv("DOC2ACTION_DEMO_USER", "demo")
    demo_pass = os.getenv("DOC2ACTION_DEMO_PASSWORD", "demo")
    if body.username != demo_user or body.password != demo_pass:
        rid = getattr(request.state, "request_id", None)
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_credentials",
                "message": "Invalid username or password.",
                "request_id": rid,
            },
        )
    hours = int(os.getenv("DOC2ACTION_JWT_EXPIRE_HOURS", "24"))
    exp = datetime.now(timezone.utc) + timedelta(hours=hours)
    token = jwt.encode(
        {"sub": body.username, "iss": "doc2action", "exp": exp},
        secret,
        algorithm="HS256",
    )
    return TokenResponse(access_token=token, token_type="bearer")


class AnalysisRecentResponse(BaseModel):
    items: list[dict[str, Any]]


@app.get(
    "/api/v1/analyses/recent",
    response_model=AnalysisRecentResponse,
    tags=["analyses"],
    dependencies=[Depends(require_api_key_if_configured)],
)
def analyses_recent(
    limit: int = 20,
    user_sub: str | None = Depends(get_optional_user_sub),
) -> AnalysisRecentResponse:
    """最近分析记录（SQLite）。若请求带 JWT，则只返回该 `sub` 的行。"""
    rows = analysis_store.list_recent(limit)
    if user_sub is not None:
        rows = [r for r in rows if r.get("user_sub") == user_sub]
    return AnalysisRecentResponse(items=rows)


@app.get(
    "/api/v1/eval/summary",
    tags=["eval"],
    dependencies=[Depends(require_api_key_if_configured)],
)
def eval_summary() -> dict[str, Any]:
    """离线评测报告摘要（默认 `learning/报告与演示材料/reports/baseline-eval.md`）。"""
    return load_eval_summary()


@app.get(
    "/api/v1/eval/report.md",
    tags=["eval"],
    dependencies=[Depends(require_api_key_if_configured)],
)
def eval_report_markdown() -> PlainTextResponse:
    data = load_eval_summary()
    path = Path(data["source_file"])
    if not path.is_file():
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "评测报告文件不存在"})
    body = path.read_text(encoding="utf-8")
    return PlainTextResponse(body, media_type="text/markdown; charset=utf-8")


class KbCollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class KbDocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)


@app.post(
    "/api/v1/kb/collections",
    tags=["kb"],
    dependencies=[Depends(require_api_key_if_configured)],
)
def kb_collections_create(
    body: KbCollectionCreate,
    user_sub: str | None = Depends(get_optional_user_sub),
) -> dict[str, Any]:
    return kb_store.create_collection(body.name, user_sub)


@app.get(
    "/api/v1/kb/collections",
    tags=["kb"],
    dependencies=[Depends(require_api_key_if_configured)],
)
def kb_collections_list(user_sub: str | None = Depends(get_optional_user_sub)) -> dict[str, Any]:
    return {"items": kb_store.list_collections(user_sub)}


@app.post(
    "/api/v1/kb/collections/{collection_id}/documents",
    tags=["kb"],
    dependencies=[Depends(require_api_key_if_configured)],
)
def kb_documents_create(collection_id: str, body: KbDocumentCreate) -> dict[str, Any]:
    try:
        return kb_store.add_document(collection_id, body.title, body.content)
    except KeyError:
        raise HTTPException(status_code=404, detail={"message": "collection not found"}) from None
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve)) from ve


@app.get(
    "/api/v1/kb/collections/{collection_id}/documents",
    tags=["kb"],
    dependencies=[Depends(require_api_key_if_configured)],
)
def kb_documents_list(collection_id: str) -> dict[str, Any]:
    try:
        return {"items": kb_store.list_documents(collection_id)}
    except KeyError:
        raise HTTPException(status_code=404, detail={"message": "collection not found"}) from None


def clean_text(raw_text: str) -> str:
    lines = [line.strip() for line in raw_text.splitlines()]
    non_empty = [line for line in lines if line]
    return "\n".join(non_empty)


def split_into_chunks(text: str, max_chars: int = 500) -> list[Chunk]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[Chunk] = []
    current = ""

    for para in paragraphs:
        if not current:
            current = para
            continue

        candidate = f"{current}\n{para}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(Chunk(id=len(chunks) + 1, text=current))
            current = para

    if current:
        chunks.append(Chunk(id=len(chunks) + 1, text=current))

    if not chunks:
        chunks.append(Chunk(id=1, text=text))

    return chunks


def build_chunks_for_request(cleaned_text: str, use_semantic: bool) -> list[Chunk]:
    max_chars = int(os.getenv("DOC2ACTION_CHUNK_MAX_CHARS", "500"))
    if use_semantic:
        pieces = split_into_semantic_chunks(cleaned_text, max_chars=max_chars)
        return [Chunk(id=i + 1, text=t) for i, t in enumerate(pieces)]
    return split_into_chunks(cleaned_text, max_chars=max_chars)


def prompt_chunks_for_llm(
    chunks: list[Chunk],
    document_type: str,
    rag_enabled: bool,
) -> tuple[list[Chunk], dict[str, Any]]:
    """Subset of chunks for the OpenAI prompt when RAG is on; metadata for response.meta."""
    meta: dict[str, Any] = {
        "rag_enabled": rag_enabled,
        "rag_applied": False,
        "rag_top_k": int(os.getenv("DOC2ACTION_RAG_TOP_K", "8")),
        "rag_prompt_char_budget": int(os.getenv("DOC2ACTION_RAG_MAX_PROMPT_CHARS", "12000")),
        "rag_embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
    }
    if not rag_enabled or not chunks:
        return chunks, meta

    top_k = meta["rag_top_k"]
    budget = meta["rag_prompt_char_budget"]
    positions, rag_reason = select_chunk_positions_for_prompt(
        [c.text for c in chunks],
        document_type,
        top_k=top_k,
        max_chars_budget=budget,
    )
    if rag_reason:
        meta["rag_reason"] = rag_reason
    if positions is None:
        return chunks, meta

    meta["rag_applied"] = True
    meta["rag_selected_positions"] = positions
    return [chunks[i] for i in positions if 0 <= i < len(chunks)], meta


def llm_observability_meta(prompt_chunks: list[Chunk], llm_saw_prompt: bool) -> dict[str, Any]:
    """Chunks that were passed to build_prompt (subset when RAG applied; else full list)."""
    return {
        "llm_prompt_chunks": [{"id": c.id, "text": c.text} for c in prompt_chunks],
        "llm_prompt_chunk_count": len(prompt_chunks),
        "llm_prompt_char_count": sum(len(c.text) for c in prompt_chunks),
        "llm_saw_prompt_chunks": llm_saw_prompt,
    }


def chunk_ids_for_sentence(sentence: str, chunks: list[Chunk]) -> list[int]:
    sentence_lower = sentence.lower()
    matched = [chunk.id for chunk in chunks if sentence_lower in chunk.text.lower()]
    return matched[:3] if matched else []


def build_prompt(
    document_type: str,
    chunks: list[Chunk],
    kb_excerpt_block: str | None = None,
) -> str:
    chunk_text = "\n\n".join([f"[chunk_{c.id}]\n{c.text}" for c in chunks])
    kb_block = ""
    if kb_excerpt_block and kb_excerpt_block.strip():
        kb_block = (
            "The following excerpts were retrieved from the user's attached knowledge base "
            "(use together with user document chunks; prefer citing user chunk ids in source_chunk_ids).\n\n"
            f"{kb_excerpt_block.strip()}\n\n"
        )
    return (
        "You are an assistant for converting unstructured documents into executable outputs.\n"
        f"Document type: {document_type}\n\n"
        f"{kb_block}"
        "Return a valid JSON object with this exact shape:\n"
        "{\n"
        '  "summary": "string",\n'
        '  "action_items": [{"title":"string","priority":"high|medium|low","source_chunk_ids":[1]}],\n'
        '  "risks": [{"description":"string","severity":"high|medium|low","source_chunk_ids":[1]}],\n'
        '  "open_questions": [{"question":"string","source_chunk_ids":[1]}]\n'
        "}\n\n"
        "Rules:\n"
        "- Use only information grounded in chunks.\n"
        "- Keep action_items concise and executable.\n"
        "- Do not invent owners or due dates unless explicit.\n\n"
        f"Chunks:\n{chunk_text}"
    )


def is_metadata_or_heading(sentence: str) -> bool:
    stripped = sentence.strip()
    if not stripped:
        return True

    if re.match(r"^#{1,6}\s*", stripped):
        return True

    if re.match(r"^(from|to|date|subject)\s*:", stripped, re.IGNORECASE):
        return True

    heading_like = {
        "会议结论",
        "待办事项",
        "风险点",
        "待确认问题",
        "背景",
        "目标",
        "范围",
        "非目标",
        "验收标准",
        "风险与依赖",
        "开放问题",
        "操作步骤",
        "场景",
    }
    if stripped in heading_like:
        return True

    return False


def normalize_sentence(sentence: str) -> str:
    # Strip common markdown list markers and repeated spaces.
    normalized = re.sub(r"^\s*[-*]\s*", "", sentence.strip())
    normalized = re.sub(r"^\s*\d+[.)]\s*", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def dedupe_dict_items(items: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        value = str(item.get(key, "")).strip().lower()
        value = normalize_sentence(value)
        value = re.sub(r"[。！？?!；;:：\.\s]+$", "", value)
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(item)
    return deduped


def extract_markdown_section_items(text: str, section_keywords: list[str]) -> list[str]:
    lines = text.splitlines()
    in_section = False
    items: list[str] = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if re.match(r"^#{1,6}\s*", line):
            heading = re.sub(r"^#{1,6}\s*", "", line).strip()
            if any(keyword in heading for keyword in section_keywords):
                in_section = True
                continue
            if in_section:
                in_section = False

        if in_section:
            normalized = normalize_sentence(line)
            if normalized and not is_metadata_or_heading(normalized):
                items.append(normalized)

    return items


def extract_with_rules(cleaned_text: str, chunks: list[Chunk]) -> dict[str, Any]:
    sentence_candidates = re.split(r"[。！？!?;\n]", cleaned_text)
    sentences = [normalize_sentence(s) for s in sentence_candidates if normalize_sentence(s)]
    content_sentences = [s for s in sentences if not is_metadata_or_heading(s)]

    summary_priority_keywords = ["结论", "目标", "上线", "范围", "完成", "需要", "确认"]
    prioritized_summary = [
        s
        for s in content_sentences
        if any(keyword in s for keyword in summary_priority_keywords) and "是否" not in s and "?" not in s and "？" not in s
    ]
    summary_pool = prioritized_summary if prioritized_summary else content_sentences
    summary = "；".join(summary_pool[:2])[:220] if summary_pool else cleaned_text[:220]

    action_keywords = ["todo", "action", "need", "must", "should", "需要", "请", "跟进", "完成"]
    risk_keywords = ["risk", "blocker", "dependency", "delay", "风险", "阻塞", "依赖", "延期"]

    action_items: list[dict[str, Any]] = []
    risks: list[dict[str, Any]] = []
    open_questions: list[dict[str, Any]] = []

    section_action_items = extract_markdown_section_items(cleaned_text, ["待办事项", "操作步骤"])
    section_risk_items = extract_markdown_section_items(cleaned_text, ["风险"])
    section_question_items = extract_markdown_section_items(cleaned_text, ["待确认问题", "开放问题"])

    for sentence in content_sentences:
        lower = sentence.lower()
        is_question = "?" in sentence or "？" in sentence or "是否" in sentence
        if len(sentence) < 6:
            continue

        if any(keyword in lower for keyword in action_keywords) and not is_question and len(action_items) < 6:
            action_items.append(
                {
                    "title": sentence,
                    "priority": "medium",
                    "source_chunk_ids": chunk_ids_for_sentence(sentence, chunks),
                }
            )

        if any(keyword in lower for keyword in risk_keywords) and not is_metadata_or_heading(sentence) and len(risks) < 6:
            risks.append(
                {
                    "description": sentence,
                    "severity": "medium",
                    "source_chunk_ids": chunk_ids_for_sentence(sentence, chunks),
                }
            )

        if is_question and len(open_questions) < 6:
            open_questions.append(
                {
                    "question": sentence,
                    "source_chunk_ids": chunk_ids_for_sentence(sentence, chunks),
                }
            )

    for sentence in section_action_items:
        if len(action_items) >= 6:
            break
        action_items.append(
            {
                "title": sentence,
                "priority": "medium",
                "source_chunk_ids": chunk_ids_for_sentence(sentence, chunks),
            }
        )

    for sentence in section_risk_items:
        if len(risks) >= 6:
            break
        risks.append(
            {
                "description": sentence,
                "severity": "medium",
                "source_chunk_ids": chunk_ids_for_sentence(sentence, chunks),
            }
        )

    for sentence in section_question_items:
        if len(open_questions) >= 6:
            break
        open_questions.append(
            {
                "question": sentence,
                "source_chunk_ids": chunk_ids_for_sentence(sentence, chunks),
            }
        )

    action_items = dedupe_dict_items(action_items, "title")
    risks = dedupe_dict_items(risks, "description")
    open_questions = dedupe_dict_items(open_questions, "question")

    if not action_items and content_sentences:
        fallback = content_sentences[0]
        action_items.append(
            {
                "title": f"Review and follow up: {fallback}",
                "priority": "medium",
                "source_chunk_ids": chunk_ids_for_sentence(fallback, chunks),
            }
        )

    return {
        "summary": summary or "No summary generated.",
        "action_items": action_items,
        "risks": risks,
        "open_questions": open_questions,
    }


def extract_with_openai(prompt: str) -> dict[str, Any] | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You produce grounded structured JSON only."},
                {"role": "user", "content": prompt},
            ],
        )
        raw = response.choices[0].message.content or "{}"
        return json.loads(raw)
    except Exception:
        # Keep Phase 2 flow stable even when API key/model/network is unavailable.
        return None


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": payload.get("summary") or "No summary generated.",
        "action_items": payload.get("action_items") or [],
        "risks": payload.get("risks") or [],
        "open_questions": payload.get("open_questions") or [],
    }


def extract_first_json_object(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    candidate = stripped[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def detect_output_language_hint(input_text: str) -> str:
    # Simple heuristic: if Chinese chars exist, enforce Chinese output.
    if re.search(r"[\u4e00-\u9fff]", input_text):
        return "Chinese"
    return "Same as input"


def contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def chinese_char_ratio(text: str) -> float:
    if not text:
        return 0.0
    chinese_count = len(re.findall(r"[\u4e00-\u9fff]", text))
    visible_count = len(re.findall(r"\S", text))
    if visible_count == 0:
        return 0.0
    return chinese_count / visible_count


def _normalize_lora_payload(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary")
    if not isinstance(summary, str):
        summary = "No summary generated."

    action_items = payload.get("action_items", [])
    risks = payload.get("risks", [])
    open_questions = payload.get("open_questions", [])

    if not isinstance(action_items, list):
        action_items = []
    if not isinstance(risks, list):
        risks = []
    if not isinstance(open_questions, list):
        open_questions = []

    return {
        "summary": summary,
        "action_items": [str(x).strip() for x in action_items if str(x).strip()],
        "risks": [str(x).strip() for x in risks if str(x).strip()],
        "open_questions": [str(x).strip() for x in open_questions if str(x).strip()],
    }


def _load_lora_runtime(base_model: str, adapter_dir: str) -> bool:
    if (
        _LORA_RUNTIME.get("ready")
        and _LORA_RUNTIME.get("base_model") == base_model
        and _LORA_RUNTIME.get("adapter_dir") == adapter_dir
    ):
        return True

    if not adapter_dir:
        return False
    if not Path(adapter_dir).exists():
        return False

    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception:
        return False

    has_cuda = bool(torch.cuda.is_available())
    has_mps = bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
    if has_cuda:
        dtype = torch.bfloat16
    elif has_mps:
        dtype = torch.float16
    else:
        dtype = torch.float32

    tokenizer = AutoTokenizer.from_pretrained(base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        dtype=dtype,
        device_map="auto" if has_cuda else None,
    )
    model = PeftModel.from_pretrained(base, adapter_dir)
    if has_mps:
        model.to("mps")
    model.eval()

    _LORA_RUNTIME.update(
        {
            "ready": True,
            "base_model": base_model,
            "adapter_dir": adapter_dir,
            "tokenizer": tokenizer,
            "model": model,
            "has_cuda": has_cuda,
            "has_mps": has_mps,
        }
    )
    return True


def extract_with_lora(document_type: str, input_text: str, chunks: list[Chunk]) -> dict[str, Any] | None:
    base_model = os.getenv("DOC2ACTION_LORA_BASE_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
    adapter_dir = os.getenv(
        "DOC2ACTION_LORA_ADAPTER_DIR",
        str(BASE_DIR.parent / "ml" / "train" / "artifacts" / "doc2action-lora-local" / "adapter"),
    )
    if not _load_lora_runtime(base_model, adapter_dir):
        return None

    import torch

    tokenizer = _LORA_RUNTIME["tokenizer"]
    model = _LORA_RUNTIME["model"]
    has_cuda = bool(_LORA_RUNTIME.get("has_cuda"))
    has_mps = bool(_LORA_RUNTIME.get("has_mps"))
    max_new_tokens = int(os.getenv("DOC2ACTION_LORA_MAX_NEW_TOKENS", "256"))
    temperature = float(os.getenv("DOC2ACTION_LORA_TEMPERATURE", "0"))
    output_language = detect_output_language_hint(input_text)

    prompt = (
        "You are an information extraction assistant.\n"
        "Extract structured results from the input document.\n"
        "Return strict JSON with keys: summary, action_items, risks, open_questions.\n\n"
        f"Output language: {output_language}\n"
        "Keep all output fields in the requested output language.\n\n"
        f"Document Type: {document_type}\n"
        "Input Document:\n"
        f"{input_text}\n\n"
        "Output JSON:\n"
    )
    encoded = tokenizer(prompt, return_tensors="pt")
    if has_cuda:
        encoded = {k: v.cuda() for k, v in encoded.items()}
    elif has_mps:
        encoded = {k: v.to("mps") for k, v in encoded.items()}

    try:
        with torch.no_grad():
            generate_kwargs: dict[str, Any] = {
                "max_new_tokens": max_new_tokens,
                "do_sample": temperature > 0,
            }
            if temperature > 0:
                generate_kwargs["temperature"] = temperature
            output = model.generate(**encoded, **generate_kwargs)

        generated = tokenizer.decode(output[0], skip_special_tokens=True)
        answer = generated[len(prompt) :].strip() if generated.startswith(prompt) else generated.strip()
        parsed = extract_first_json_object(answer)
        if parsed is None:
            return None
    except Exception:
        return None

    payload = _normalize_lora_payload(parsed)
    if contains_chinese(input_text):
        joined_text = " ".join(
            [
                payload.get("summary", ""),
                *payload.get("action_items", []),
                *payload.get("risks", []),
                *payload.get("open_questions", []),
            ]
        )
        # If Chinese input produced mostly non-Chinese output, fallback for UX consistency.
        if chinese_char_ratio(joined_text) < 0.1:
            return None

    action_items = [
        {"title": text, "priority": "medium", "source_chunk_ids": chunk_ids_for_sentence(text, chunks)}
        for text in payload["action_items"]
    ]
    risks = [
        {"description": text, "severity": "medium", "source_chunk_ids": chunk_ids_for_sentence(text, chunks)}
        for text in payload["risks"]
    ]
    open_questions = [
        {"question": text, "source_chunk_ids": chunk_ids_for_sentence(text, chunks)}
        for text in payload["open_questions"]
    ]

    return {
        "summary": payload["summary"] or "No summary generated.",
        "action_items": action_items,
        "risks": risks,
        "open_questions": open_questions,
    }


def _truthy_env(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _optional_header_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return None


def _analyze_core(
    analyze_body: AnalyzeRequest,
    x_extractor_mode: str | None,
    x_rag_enabled: str | None,
) -> AnalyzeResponse:
    cleaned_text = clean_text(analyze_body.text)
    rag_env = _truthy_env(os.getenv("DOC2ACTION_RAG_ENABLED"))
    hdr_rag = _truthy_env(_optional_header_str(x_rag_enabled))
    if analyze_body.use_rag is True:
        rag_enabled = True
    elif analyze_body.use_rag is False:
        rag_enabled = False
    else:
        rag_enabled = rag_env or hdr_rag

    if analyze_body.use_semantic_chunks is True:
        use_semantic = True
    elif analyze_body.use_semantic_chunks is False:
        use_semantic = False
    else:
        use_semantic = rag_enabled or _truthy_env(os.getenv("DOC2ACTION_SEMANTIC_CHUNKS"))

    if analyze_body.kb_collection_id and not kb_store.collection_exists(analyze_body.kb_collection_id):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_kb_collection",
                "message": "Unknown kb_collection_id",
            },
        )

    chunks = build_chunks_for_request(cleaned_text, use_semantic=use_semantic)

    kb_excerpt_block: str | None = None
    kb_meta_extra: dict[str, Any] = {}
    if analyze_body.kb_collection_id:
        kb_meta_extra["kb_collection_id"] = analyze_body.kb_collection_id
        if not rag_enabled:
            kb_meta_extra["kb_note"] = "kb_retrieval_requires_rag"
        else:
            kb_texts = kb_store.get_collection_chunk_strings(analyze_body.kb_collection_id)
            kb_meta_extra["kb_segment_count"] = len(kb_texts)
            if not kb_texts:
                kb_meta_extra["kb_rag_reason"] = "empty_collection"
            else:
                top_k = int(os.getenv("DOC2ACTION_RAG_TOP_K", "8"))
                budget = int(os.getenv("DOC2ACTION_RAG_MAX_PROMPT_CHARS", "12000"))
                q_budget = int(os.getenv("DOC2ACTION_KB_QUERY_MAX_CHARS", "8000"))
                query_txt = f"{analyze_body.document_type}\n\n{cleaned_text}"[:q_budget]
                positions, kb_reason = select_chunk_positions_for_prompt(
                    kb_texts,
                    analyze_body.document_type,
                    top_k=top_k,
                    max_chars_budget=budget,
                    query_override=query_txt,
                )
                if kb_reason:
                    kb_meta_extra["kb_rag_reason"] = kb_reason
                if positions:
                    kb_meta_extra["kb_rag_applied"] = True
                    kb_meta_extra["kb_selected_positions"] = positions
                    selected_texts = [kb_texts[i] for i in positions if 0 <= i < len(kb_texts)]
                    kb_excerpt_block = "\n\n".join(
                        f"[kb_excerpt_{j}]\n{t}" for j, t in enumerate(selected_texts)
                    )
                else:
                    kb_meta_extra["kb_rag_applied"] = False

    llm_prompt_chunks, rag_meta = prompt_chunks_for_llm(
        chunks,
        analyze_body.document_type,
        rag_enabled=rag_enabled,
    )
    prompt = build_prompt(
        analyze_body.document_type,
        llm_prompt_chunks,
        kb_excerpt_block=kb_excerpt_block,
    )

    extractor_mode = (
        (_optional_header_str(x_extractor_mode) or os.getenv("DOC2ACTION_EXTRACTOR_MODE", "auto")).strip().lower()
    )
    if extractor_mode not in {"auto", "rules", "llm", "lora"}:
        extractor_mode = "auto"

    llm_payload: dict[str, Any] | None = None
    lora_payload: dict[str, Any] | None = None
    if extractor_mode in {"auto", "llm"}:
        llm_payload = extract_with_openai(prompt)
    lora_input = cleaned_text
    if extractor_mode == "lora" and rag_enabled and _truthy_env(os.getenv("DOC2ACTION_RAG_FOR_LORA")):
        rag_ctx = "\n\n".join(f"[chunk_{c.id}]\n{c.text}" for c in llm_prompt_chunks)
        if kb_excerpt_block:
            rag_ctx = f"{kb_excerpt_block}\n\n---\n\n{rag_ctx}"
        lora_input = f"Retrieved excerpts (most relevant chunks first):\n{rag_ctx}\n\nFull document:\n{cleaned_text}"
    if extractor_mode == "lora":
        lora_payload = extract_with_lora(analyze_body.document_type, lora_input, chunks)

    if extractor_mode == "rules":
        parsed_payload = extract_with_rules(cleaned_text, chunks)
    elif extractor_mode == "lora":
        parsed_payload = lora_payload if lora_payload else extract_with_rules(cleaned_text, chunks)
    else:
        parsed_payload = normalize_payload(llm_payload) if llm_payload else extract_with_rules(cleaned_text, chunks)

    used_llm = bool(llm_payload)
    return AnalyzeResponse(
        summary=parsed_payload["summary"],
        action_items=parsed_payload["action_items"],
        risks=parsed_payload["risks"],
        open_questions=parsed_payload["open_questions"],
        chunks=chunks,
        meta={
            "document_type": analyze_body.document_type,
            "chunk_count": len(chunks),
            "used_llm": used_llm,
            "used_lora": bool(lora_payload),
            "extractor_mode": extractor_mode,
            "llm_fallback": extractor_mode in {"auto", "llm"} and not used_llm,
            "lora_fallback": extractor_mode == "lora" and not bool(lora_payload),
            "semantic_chunks": use_semantic,
            "rag_embed_cache_enabled": embed_cache_enabled(),
            **rag_meta,
            **kb_meta_extra,
            **llm_observability_meta(llm_prompt_chunks, used_llm),
        },
    )


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    tags=["analyze"],
    dependencies=[Depends(require_api_key_if_configured)],
)
@limiter.limit(ANALYZE_RATE_LIMIT)
def analyze(
    request: Request,
    analyze_body: AnalyzeRequest,
    user_sub: str | None = Depends(get_optional_user_sub),
    x_extractor_mode: str | None = Header(default=None, alias="X-Extractor-Mode"),
    x_rag_enabled: str | None = Header(default=None, alias="X-RAG-Enabled"),
) -> AnalyzeResponse:
    run_id = str(uuid.uuid4())
    preview = analyze_body.text[:500]
    ext_mode = _norm_extractor_mode(x_extractor_mode)
    try:
        resp = _analyze_core(analyze_body, x_extractor_mode, x_rag_enabled)
        log_analyze_completed(getattr(request.state, "request_id", None), resp.meta)
        analysis_store.insert_sync_run(
            run_id,
            user_sub,
            analyze_body.document_type,
            ext_mode,
            preview,
            "completed",
            resp.model_dump(),
            None,
        )
        return resp
    except Exception as exc:
        analysis_store.insert_sync_run(
            run_id,
            user_sub,
            analyze_body.document_type,
            ext_mode,
            preview,
            "failed",
            None,
            str(exc),
        )
        raise


def _analyze_job_task(
    job_id: str,
    body_dict: dict[str, Any],
    x_extractor_mode: str | None,
    x_rag_enabled: str | None,
) -> None:
    try:
        body = AnalyzeRequest(**body_dict)
        resp = _analyze_core(body, x_extractor_mode, x_rag_enabled)
        log_analyze_completed(None, resp.meta, job_id=job_id)
        analysis_store.update_run(job_id, "completed", resp.model_dump(), None)
        with _JOBS_LOCK:
            _JOBS[job_id] = {"status": "completed", "result": resp.model_dump(), "error": None}
    except Exception as exc:  # pragma: no cover - defensive
        analysis_store.update_run(job_id, "failed", None, str(exc))
        with _JOBS_LOCK:
            _JOBS[job_id] = {"status": "failed", "result": None, "error": str(exc)}


@app.post(
    "/api/v1/jobs/analyze",
    response_model=JobEnqueueResponse,
    tags=["jobs"],
    dependencies=[Depends(require_api_key_if_configured)],
)
@limiter.limit(ANALYZE_RATE_LIMIT)
def submit_analyze_job(
    request: Request,
    background_tasks: BackgroundTasks,
    analyze_body: AnalyzeRequest,
    user_sub: str | None = Depends(get_optional_user_sub),
    x_extractor_mode: str | None = Header(default=None, alias="X-Extractor-Mode"),
    x_rag_enabled: str | None = Header(default=None, alias="X-RAG-Enabled"),
) -> JobEnqueueResponse:
    preview = analyze_body.text[:500]
    ext_mode = _norm_extractor_mode(x_extractor_mode)
    if redis_jobs_enabled():
        try:
            job_id = enqueue_analyze(
                analyze_body.model_dump(),
                x_extractor_mode,
                x_rag_enabled,
            )
        except Exception as exc:
            rid = getattr(request.state, "request_id", None)
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "queue_unavailable",
                    "message": f"Could not enqueue job: {exc!s}",
                    "request_id": rid,
                },
            ) from exc
        analysis_store.insert_async_pending(
            job_id, user_sub, analyze_body.document_type, ext_mode, preview
        )
        return JobEnqueueResponse(job_id=job_id, status="pending")

    job_id = str(uuid.uuid4())
    analysis_store.insert_async_pending(job_id, user_sub, analyze_body.document_type, ext_mode, preview)
    with _JOBS_LOCK:
        _JOBS[job_id] = {"status": "pending", "result": None, "error": None}
    background_tasks.add_task(
        _analyze_job_task,
        job_id,
        analyze_body.model_dump(),
        x_extractor_mode,
        x_rag_enabled,
    )
    return JobEnqueueResponse(job_id=job_id, status="pending")


@app.get(
    "/api/v1/jobs/{job_id}",
    response_model=JobStatusResponse,
    tags=["jobs"],
    dependencies=[Depends(require_api_key_if_configured)],
)
def get_analyze_job(request: Request, job_id: str) -> JobStatusResponse:
    if redis_jobs_enabled():
        row = fetch_job_row(job_id)
    else:
        with _JOBS_LOCK:
            row = _JOBS.get(job_id)
    if not row:
        rid = getattr(request.state, "request_id", None)
        raise HTTPException(
            status_code=404,
            detail={
                "error": "not_found",
                "message": "Unknown job_id",
                "request_id": rid,
            },
        )
    result: AnalyzeResponse | None = None
    if row["status"] == "completed" and row.get("result"):
        result = AnalyzeResponse.model_validate(row["result"])
    return JobStatusResponse(
        job_id=job_id,
        status=row["status"],
        result=result,
        error=row.get("error"),
    )


app.add_api_route(
    "/api/v1/analyze",
    analyze,
    methods=["POST"],
    response_model=AnalyzeResponse,
    tags=["analyze"],
    dependencies=[Depends(require_api_key_if_configured)],
)
