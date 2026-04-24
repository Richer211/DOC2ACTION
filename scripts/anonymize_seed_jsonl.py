from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?\d[\d\s\-()]{6,}\d)\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Anonymize sensitive values in Doc2Action seed jsonl.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def mask_text(text: str) -> str:
    masked = EMAIL_PATTERN.sub("xxx@example.com", text)
    masked = PHONE_PATTERN.sub("138****0000", masked)
    return masked


def mask_list(values: list[str]) -> list[str]:
    return [mask_text(v) for v in values]


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with args.input.open("r", encoding="utf-8") as inp, args.output.open("w", encoding="utf-8") as out:
        for line in inp:
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)

            row["input_text"] = mask_text(row.get("input_text", ""))
            expected = row.get("expected", {})
            expected["summary"] = mask_text(expected.get("summary", ""))
            expected["action_items"] = mask_list(expected.get("action_items", []))
            expected["risks"] = mask_list(expected.get("risks", []))
            expected["open_questions"] = mask_list(expected.get("open_questions", []))
            row["expected"] = expected

            meta = row.get("meta", {})
            meta["anonymized"] = True
            row["meta"] = meta

            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1

    print(f"Anonymized {count} rows -> {args.output}")


if __name__ == "__main__":
    main()
