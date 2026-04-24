from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import AnalyzeRequest, analyze  # noqa: E402


DEFAULT_INPUT = ROOT / "ml" / "data" / "curation" / "jira.curate.top30.v1.jsonl"
DEFAULT_OUTPUT = ROOT / "ml" / "data" / "curated" / "jira.curated.top30.draft.v1.jsonl"
DEFAULT_REPORT = ROOT / "learning" / "reports" / "jira-curation-draft-summary.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create LLM-assisted draft labels for Jira Top30 curation.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-input-chars", type=int, default=2200)
    parser.add_argument("--model", default="gpt-4o-mini")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    return text


def clean_summary(summary: str, input_text: str) -> str:
    s = normalize_text(summary)
    bad_prefix = ("Project:", "Issue Type:", "Status:")
    if s.startswith(bad_prefix):
        m = re.search(r"Summary:\s*(.+)", input_text)
        if m:
            return normalize_text(m.group(1))[:220]
    return s[:220]


def keep_quality_items(items: list[str], max_items: int = 4, max_len: int = 180) -> list[str]:
    results: list[str] = []
    seen: set[str] = set()
    for item in items:
        t = normalize_text(str(item))
        if not t:
            continue
        if t.startswith(("Project:", "Issue Type:", "Status:", "Description:")):
            continue
        if len(t) > max_len:
            continue
        key = t.lower()
        if key in seen:
            continue
        seen.add(key)
        results.append(t)
        if len(results) >= max_items:
            break
    return results


def main() -> None:
    args = parse_args()
    rows = read_jsonl(args.input)

    os.environ["DOC2ACTION_EXTRACTOR_MODE"] = "llm"
    os.environ["OPENAI_MODEL"] = args.model

    args.output.parent.mkdir(parents=True, exist_ok=True)

    converted = 0
    with args.output.open("w", encoding="utf-8") as out:
        for row in rows:
            original_text = str(row.get("input_text", ""))
            input_text = original_text[: args.max_input_chars]
            pred = analyze(AnalyzeRequest(text=input_text, document_type="general")).model_dump()

            expected = {
                "summary": clean_summary(str(pred.get("summary", "")), input_text),
                "action_items": keep_quality_items([x.get("title", "") for x in pred.get("action_items", [])], max_items=4),
                "risks": keep_quality_items([x.get("description", "") for x in pred.get("risks", [])], max_items=4),
                "open_questions": keep_quality_items([x.get("question", "") for x in pred.get("open_questions", [])], max_items=4),
            }

            row["expected"] = expected
            row.setdefault("meta", {})
            row["meta"]["curation_source"] = "jira"
            row["meta"]["human_review_required"] = True
            row["meta"]["curation_stage"] = "draft_llm_assisted"
            row["meta"]["draft_model"] = args.model
            row["meta"]["draft_input_truncated"] = len(original_text) > args.max_input_chars
            converted += 1
            out.write(json.dumps(row, ensure_ascii=False) + "\n")

    report_lines = [
        "# Jira Draft Curation Summary",
        "",
        f"- input_file: `{args.input}`",
        f"- output_file: `{args.output}`",
        f"- rows: {converted}",
        f"- draft_model: `{args.model}`",
        "- note: 这是 LLM 草稿标签，仍需人工复核后才能作为高质量 gold 数据。",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Draft curation file generated: {args.output}")
    print(f"Summary report generated: {args.report}")


if __name__ == "__main__":
    main()
