"""
Lightweight retrieval for long documents: embed chunks + query, cosine top-k.

Requires OPENAI_API_KEY for embeddings; otherwise selection falls back to "use all chunks".
"""
from __future__ import annotations

import os
import re
try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None  # type: ignore[assignment]

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]

from app.embed_cache import get_embed_cache

_SENT_SPLIT = re.compile(r"(?<=[。！？!?])\s*|(?<=[.!?])\s+")


def split_long_paragraph(para: str, max_chars: int) -> list[str]:
    """Split a long paragraph on sentence boundaries, then pack into <= max_chars pieces."""
    para = para.strip()
    if not para:
        return []
    if len(para) <= max_chars:
        return [para]

    raw_parts = [p.strip() for p in _SENT_SPLIT.split(para) if p and p.strip()]
    if len(raw_parts) <= 1:
        return [para[:max_chars]]

    packed: list[str] = []
    current = ""
    for part in raw_parts:
        if not current:
            current = part
            continue
        candidate = f"{current}{part}" if current[-1] in "。！？!?." else f"{current} {part}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            packed.append(current)
            current = part
    if current:
        packed.append(current)

    out: list[str] = []
    for piece in packed:
        if len(piece) <= max_chars:
            out.append(piece)
            continue
        for i in range(0, len(piece), max_chars):
            out.append(piece[i : i + max_chars])
    return out


def split_into_semantic_chunks(text: str, max_chars: int = 500) -> list[str]:
    """
    Paragraph-first packing; long paragraphs are split on sentence boundaries then packed.
    """
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    texts: list[str] = []
    for para in paragraphs:
        texts.extend(split_long_paragraph(para, max_chars))

    if not texts:
        return [text] if text.strip() else [""]

    merged: list[str] = []
    current = ""
    for t in texts:
        if not current:
            current = t
            continue
        candidate = f"{current}\n{t}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            merged.append(current)
            current = t
    if current:
        merged.append(current)
    return merged


def retrieval_query(document_type: str) -> str:
    return (
        f"Document type: {document_type}. "
        "Extract summary, action items, risks, and open questions. "
        "Prioritize actionable tasks, deadlines, blockers, dependencies, and unanswered questions."
    )


def _embed_openai_api(texts: list[str], model: str) -> list[list[float]] | None:
    """Call OpenAI embeddings API only (no cache)."""
    if not texts or OpenAI is None or np is None:
        return None
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    client = OpenAI(api_key=api_key)
    try:
        resp = client.embeddings.create(model=model, input=texts)
        return [item.embedding for item in resp.data]
    except Exception:
        return None


def _embed_openai(texts: list[str], model: str) -> list[list[float]] | None:
    """Resolve embeddings with optional disk cache (per-text), batching API for misses."""
    if not texts or OpenAI is None or np is None:
        return None
    cache = get_embed_cache()
    out: list[list[float] | None] = [None] * len(texts)
    miss_idx: list[int] = []
    for i, t in enumerate(texts):
        if cache is not None:
            hit = cache.get(model, t)
            if hit is not None:
                out[i] = hit
                continue
        miss_idx.append(i)
    if miss_idx:
        batch = [texts[i] for i in miss_idx]
        fresh = _embed_openai_api(batch, model)
        if fresh is None or len(fresh) != len(batch):
            return None
        for j, idx in enumerate(miss_idx):
            vec = fresh[j]
            out[idx] = vec
            if cache is not None:
                cache.set(model, texts[idx], vec)
    resolved = [x for x in out if x is not None]
    if len(resolved) != len(texts):
        return None
    return resolved


def _embed_openai_batched(texts: list[str], model: str) -> list[list[float]] | None:
    """Embed many chunks in batches (OpenAI input size / payload limits)."""
    if not texts:
        return []
    batch_size = max(1, int(os.getenv("DOC2ACTION_RAG_EMBED_BATCH", "64")))
    out: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        part = _embed_openai(batch, model)
        if part is None or len(part) != len(batch):
            return None
        out.extend(part)
    return out


def embed_query_and_chunks(query: str, chunk_texts: list[str], model: str) -> tuple[list[float], list[list[float]]] | None:
    """Returns (query_embedding, chunk_embeddings) or None on failure."""
    q = _embed_openai([query], model)
    if not q:
        return None
    chunk_embs = _embed_openai_batched(chunk_texts, model)
    if chunk_embs is None or len(chunk_embs) != len(chunk_texts):
        return None
    return q[0], chunk_embs


def _cosine_top_positions(query: list[float], matrix: list[list[float]], k: int) -> list[int]:
    if np is None or not query or not matrix:
        return list(range(min(k, len(matrix))))
    q = np.array(query, dtype=np.float64)
    q = q / (np.linalg.norm(q) + 1e-12)
    scores: list[tuple[float, int]] = []
    for i, row in enumerate(matrix):
        v = np.array(row, dtype=np.float64)
        v = v / (np.linalg.norm(v) + 1e-12)
        scores.append((float(np.dot(q, v)), i))
    scores.sort(key=lambda x: x[0], reverse=True)
    return [idx for _, idx in scores[:k]]


def select_chunk_positions_for_prompt(
    chunk_texts: list[str],
    document_type: str,
    *,
    top_k: int,
    max_chars_budget: int,
    query_override: str | None = None,
) -> tuple[list[int] | None, str | None]:
    """
    Return (positions, reason_if_skipped).

    positions: 0-based indices of chunks for the LLM prompt (relevance order), or None = use all.
    reason_if_skipped: e.g. why retrieval was skipped (short doc, no API key, embed error).
    query_override: when set (e.g. user document text for KB retrieval), used as embedding query instead of generic retrieval_query(document_type).
    """
    if not chunk_texts:
        return None, "empty_chunks"

    n = len(chunk_texts)
    total_chars = sum(len(t) for t in chunk_texts)
    if n <= top_k and total_chars <= max_chars_budget:
        return None, "short_doc_fits_budget"

    if OpenAI is None or np is None:
        return None, "missing_deps"

    model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    query = query_override if query_override is not None else retrieval_query(document_type)
    pair = embed_query_and_chunks(query, chunk_texts, model)
    if pair is None:
        return None, "embed_failed_or_no_api_key"

    q_emb, chunk_embs = pair
    positions = _cosine_top_positions(q_emb, chunk_embs, min(top_k, n))

    selected: list[int] = []
    used_chars = 0
    for pos in positions:
        t = chunk_texts[pos]
        if used_chars + len(t) > max_chars_budget and selected:
            break
        if pos not in selected:
            selected.append(pos)
            used_chars += len(t)
        if len(selected) >= top_k:
            break

    if not selected:
        return None, "selection_empty"
    return selected, None
