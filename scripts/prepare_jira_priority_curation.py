from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "ml" / "data" / "external" / "jira" / "processed" / "jira.seed.auto.jsonl"
DEFAULT_OUTPUT = ROOT / "ml" / "data" / "curation" / "jira.curate.top30.v1.jsonl"
DEFAULT_REPORT = ROOT / "learning" / "reports" / "jira-curation-top30.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare high-priority Jira manual curation batch.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--top-k", type=int, default=30)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def priority_score(row: dict[str, Any]) -> tuple[int, list[str]]:
    reasons: list[str] = []
    score = 0

    expected = row.get("expected", {})
    actions = expected.get("action_items", []) or []
    risks = expected.get("risks", []) or []
    questions = expected.get("open_questions", []) or []
    summary = str(expected.get("summary", "")).strip()
    input_text = str(row.get("input_text", ""))

    if not risks:
        score += 2
        reasons.append("missing_risks")
    if not questions:
        score += 1
        reasons.append("missing_open_questions")

    if summary.startswith("Project:") or summary.startswith("Issue Type:"):
        score += 3
        reasons.append("summary_is_metadata_like")

    if len(input_text) > 1800:
        score += 2
        reasons.append("very_long_input")
    elif len(input_text) > 1200:
        score += 1
        reasons.append("long_input")

    if not actions:
        score += 2
        reasons.append("missing_action_items")

    bad_prefixes = ("Description:", "Status:", "Summary:", "Project:", "Issue Type:")
    for action in actions:
        action_text = _normalize_space(str(action))
        if len(action_text) > 220:
            score += 2
            reasons.append("action_too_long")
            break
    for action in actions:
        action_text = _normalize_space(str(action))
        if action_text.startswith(bad_prefixes):
            score += 2
            reasons.append("action_contains_raw_metadata_prefix")
            break

    if "Comments:" in input_text and len(actions) <= 1:
        score += 1
        reasons.append("has_comments_but_low_extraction")

    return score, sorted(set(reasons))


def main() -> None:
    args = parse_args()
    rows = read_jsonl(args.input)

    scored: list[tuple[int, list[str], dict[str, Any]]] = []
    for row in rows:
        score, reasons = priority_score(row)
        scored.append((score, reasons, row))

    scored.sort(key=lambda x: x[0], reverse=True)
    selected = scored[: args.top_k]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out:
        for rank, (score, reasons, row) in enumerate(selected, start=1):
            row.setdefault("meta", {})
            row["meta"]["curation_source"] = "jira"
            row["meta"]["needs_manual_curation"] = True
            row["meta"]["priority_score"] = score
            row["meta"]["priority_reasons"] = reasons
            row["meta"]["curation_rank"] = rank
            out.write(json.dumps(row, ensure_ascii=False) + "\n")

    lines = [
        "# Jira Top30 Curation List",
        "",
        f"- source_file: `{args.input}`",
        f"- output_file: `{args.output}`",
        f"- top_k: {args.top_k}",
        "",
        "## Rules",
        "- 优先处理：summary 元数据化、action 过长、risk/question 缺失、长文本低提取。",
        "",
        "## Selected Samples",
    ]
    for rank, (score, reasons, row) in enumerate(selected, start=1):
        meta = row.get("meta", {})
        issue_key = meta.get("issue_key", "")
        item_id = row.get("id", "")
        reason_text = ", ".join(reasons) if reasons else "none"
        lines.append(f"- #{rank} `{item_id}` ({issue_key}) score={score} reasons=[{reason_text}]")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Prepared top-{args.top_k} Jira curation list: {args.output}")
    print(f"Report written: {args.report}")


if __name__ == "__main__":
    main()
