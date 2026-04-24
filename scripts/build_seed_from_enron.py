from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import AnalyzeRequest, analyze  # noqa: E402


DEFAULT_INPUT = ROOT / "ml" / "data" / "external" / "enron" / "processed" / "enron.sample.jsonl"
DEFAULT_OUTPUT = ROOT / "ml" / "data" / "external" / "enron" / "processed" / "enron.seed.auto.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build weak-label seed dataset from sampled Enron emails.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def compose_input_text(row: dict[str, str]) -> str:
    subject = row.get("subject", "").strip()
    body = row.get("body", "").strip()
    text = f"Subject: {subject}\n\n{body}" if subject else body
    return text.strip()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    converted = 0

    with args.input.open("r", encoding="utf-8") as inp, args.output.open("w", encoding="utf-8") as out:
        for line in inp:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            input_text = compose_input_text(row)
            if len(input_text) < 80:
                continue

            prediction = analyze(AnalyzeRequest(text=input_text, document_type="email_thread")).model_dump()
            seed = {
                "id": row["id"],
                "document_type": "email_thread",
                "input_text": input_text,
                "expected": {
                    "summary": prediction.get("summary", ""),
                    "action_items": [item.get("title", "") for item in prediction.get("action_items", []) if item.get("title")],
                    "risks": [item.get("description", "") for item in prediction.get("risks", []) if item.get("description")],
                    "open_questions": [item.get("question", "") for item in prediction.get("open_questions", []) if item.get("question")],
                },
                "meta": {
                    "source": "enron_weak_label",
                    "source_file": row.get("source_file", ""),
                    "weak_label": True,
                    "split": "train",
                    "used_llm": prediction.get("meta", {}).get("used_llm", False),
                },
            }
            out.write(json.dumps(seed, ensure_ascii=False) + "\n")
            converted += 1

    print(f"Converted {converted} rows into weak-label seed file: {args.output}")


if __name__ == "__main__":
    main()
