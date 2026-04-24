from __future__ import annotations

import argparse
import json
from pathlib import Path

from datasets import load_dataset


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT / "ml" / "data" / "external" / "meetingbank" / "processed" / "meetingbank.sample.jsonl"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sample records from MeetingBank dataset.")
    parser.add_argument("--split", default="train", choices=["train", "validation", "test"])
    parser.add_argument("--count", type=int, default=50, help="Number of samples to export.")
    parser.add_argument("--offset", type=int, default=0, help="Offset in selected split.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = load_dataset("huuuyeah/meetingbank", split=args.split)

    output_path: Path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    start = max(args.offset, 0)
    end = min(start + max(args.count, 1), len(dataset))

    rows = []
    for idx in range(start, end):
        sample = dataset[idx]
        rows.append(
            {
                "id": f"meetingbank-{args.split}-{idx}",
                "uid": sample.get("uid", f"{args.split}-{idx}"),
                "source_dataset": "huuuyeah/meetingbank",
                "split": args.split,
                "transcript": sample.get("transcript", ""),
                "summary": sample.get("summary", ""),
            }
        )

    with output_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Exported {len(rows)} samples to {output_path}")


if __name__ == "__main__":
    main()
