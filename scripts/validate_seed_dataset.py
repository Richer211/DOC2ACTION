from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "ml" / "data" / "curation" / "curation.batch.v1.jsonl"
DEFAULT_REPORT = ROOT / "learning" / "reports" / "curation-validation.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Doc2Action seed/curated jsonl dataset quality.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip().lower())
    text = re.sub(r"[。！？?!；;:：\.,]+$", "", text)
    return text


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f"Input dataset not found: {args.input}")

    rows = read_jsonl(args.input)
    total = len(rows)
    required_top = ["id", "document_type", "input_text", "expected", "meta"]
    required_expected = ["summary", "action_items", "risks", "open_questions"]

    missing_top = 0
    missing_expected = 0
    too_short = 0
    duplicate_items = 0
    source_counter: Counter[str] = Counter()
    type_counter: Counter[str] = Counter()

    seen_inputs: set[str] = set()
    input_duplicates = 0

    for row in rows:
        if any(field not in row for field in required_top):
            missing_top += 1
            continue

        expected = row.get("expected", {})
        if any(field not in expected for field in required_expected):
            missing_expected += 1

        input_text = row.get("input_text", "")
        if len(normalize_text(input_text)) < 80:
            too_short += 1

        normalized_input = normalize_text(input_text)
        if normalized_input in seen_inputs:
            input_duplicates += 1
        else:
            seen_inputs.add(normalized_input)

        items = []
        items.extend(expected.get("action_items", []))
        items.extend(expected.get("risks", []))
        items.extend(expected.get("open_questions", []))
        normalized_items = [normalize_text(item) for item in items if normalize_text(item)]
        if len(normalized_items) != len(set(normalized_items)):
            duplicate_items += 1

        source = row.get("meta", {}).get("curation_source", "unknown")
        source_counter[source] += 1
        type_counter[row.get("document_type", "unknown")] += 1

    valid_rows = total - missing_top
    completeness = 0.0 if total == 0 else (valid_rows - missing_expected) / total

    lines = [
        "# Curation Dataset Validation Report",
        "",
        f"- input_file: `{args.input}`",
        f"- total_rows: {total}",
        f"- missing_top_fields: {missing_top}",
        f"- missing_expected_fields: {missing_expected}",
        f"- short_input_rows(<80 chars): {too_short}",
        f"- duplicate_input_rows: {input_duplicates}",
        f"- rows_with_duplicate_items: {duplicate_items}",
        f"- completeness_score: {completeness:.4f}",
        "",
        "## Distribution by Source",
    ]
    for src, count in source_counter.most_common():
        lines.append(f"- {src}: {count}")

    lines.extend(["", "## Distribution by Document Type"])
    for doc_type, count in type_counter.most_common():
        lines.append(f"- {doc_type}: {count}")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Validation completed. Report: {args.report}")


if __name__ == "__main__":
    main()
