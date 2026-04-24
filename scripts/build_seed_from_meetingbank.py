from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    ROOT / "ml" / "data" / "external" / "meetingbank" / "processed" / "meetingbank.sample.jsonl"
)
DEFAULT_OUTPUT = (
    ROOT / "ml" / "data" / "external" / "meetingbank" / "processed" / "meetingbank.seed.auto.jsonl"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert MeetingBank sampled data to Doc2Action weak-label seed format."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def normalize_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^\s*[-*]\s*", "", line)
    line = re.sub(r"^\s*\d+[.)]\s*", "", line)
    return line.strip()


def split_summary_items(summary_text: str) -> tuple[str, list[str]]:
    lines = [normalize_line(line) for line in summary_text.splitlines() if normalize_line(line)]
    if not lines:
        return "", []
    # Use first line as global summary and keep short bullet-like lines as weak action candidates.
    main_summary = lines[0]
    candidate_actions = [line for line in lines[1:] if len(line) >= 8][:5]
    return main_summary, candidate_actions


def main() -> None:
    args = parse_args()
    input_path: Path = args.input
    output_path: Path = args.output

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    converted = []
    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
            summary = row.get("summary", "")
            transcript = row.get("transcript", "")
            seed_summary, weak_actions = split_summary_items(summary)

            converted.append(
                {
                    "id": row.get("id", ""),
                    "document_type": "meeting_notes",
                    "input_text": transcript,
                    "expected": {
                        "summary": seed_summary or summary[:200],
                        "action_items": weak_actions,
                        "risks": [],
                        "open_questions": [],
                    },
                    "meta": {
                        "source": "meetingbank_weak_label",
                        "original_uid": row.get("uid", ""),
                        "split": "train",
                        "weak_label": True,
                    },
                }
            )

    with output_path.open("w", encoding="utf-8") as f:
        for row in converted:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Converted {len(converted)} rows to seed format: {output_path}")


if __name__ == "__main__":
    main()
