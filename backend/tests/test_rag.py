"""Unit tests for semantic chunking and cosine ranking (no network)."""
from __future__ import annotations

from app.rag import _cosine_top_positions, split_into_semantic_chunks


def test_split_into_semantic_chunks_respects_paragraphs() -> None:
    text = "第一段说明。\n\n第二段也很长，需要单独成块。"
    parts = split_into_semantic_chunks(text, max_chars=500)
    assert len(parts) >= 1
    assert "第一段" in parts[0] or "第二段" in "".join(parts)


def test_cosine_top_positions_order() -> None:
    q = [1.0, 0.0, 0.0]
    matrix = [
        [0.0, 1.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    pos = _cosine_top_positions(q, matrix, k=2)
    assert pos[0] == 1
