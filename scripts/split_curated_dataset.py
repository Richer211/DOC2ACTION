from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "ml" / "data" / "curation" / "curation.batch.v1.jsonl"
DEFAULT_OUTPUT_DIR = ROOT / "ml" / "data" / "final"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split curated dataset into train/val/test jsonl files.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--stratify",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether to stratify split by (curation_source, document_type).",
    )
    parser.add_argument(
        "--max-input-chars",
        type=int,
        default=0,
        help="Truncate input_text to this length in output files; <=0 disables truncation.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]], split_name: str, max_input_chars: int = 0) -> int:
    truncated_count = 0
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            if max_input_chars > 0:
                input_text = row.get("input_text", "")
                if isinstance(input_text, str) and len(input_text) > max_input_chars:
                    row["input_text"] = input_text[:max_input_chars]
                    row.setdefault("meta", {})
                    row["meta"]["input_truncated"] = True
                    row["meta"]["original_input_length"] = len(input_text)
                    truncated_count += 1
            row.setdefault("meta", {})
            row["meta"]["split"] = split_name
            row["meta"]["weak_label"] = False
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return truncated_count


def allocate_counts(size: int, train_ratio: float, val_ratio: float) -> tuple[int, int, int]:
    train_float = size * train_ratio
    val_float = size * val_ratio
    test_float = size - train_float - val_float

    train_count = int(train_float)
    val_count = int(val_float)
    test_count = int(test_float)

    remainder = size - (train_count + val_count + test_count)
    fractional_parts = [
        (train_float - train_count, "train"),
        (val_float - val_count, "val"),
        (test_float - test_count, "test"),
    ]
    fractional_parts.sort(reverse=True)

    for _, bucket in fractional_parts[:remainder]:
        if bucket == "train":
            train_count += 1
        elif bucket == "val":
            val_count += 1
        else:
            test_count += 1

    return train_count, val_count, test_count


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f"Curated input not found: {args.input}")
    if args.train_ratio <= 0 or args.val_ratio <= 0 or args.train_ratio + args.val_ratio >= 1:
        raise ValueError("train_ratio and val_ratio must be >0 and sum to <1.")

    rows = read_jsonl(args.input)
    rng = random.Random(args.seed)

    if args.stratify:
        grouped_rows: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            meta = row.get("meta", {})
            source = meta.get("curation_source") or meta.get("source") or "unknown"
            doc_type = row.get("document_type", "unknown")
            grouped_rows[(source, doc_type)].append(row)

        train_rows: list[dict[str, Any]] = []
        val_rows: list[dict[str, Any]] = []
        test_rows: list[dict[str, Any]] = []
        for group in grouped_rows.values():
            rng.shuffle(group)
            train_count, val_count, _ = allocate_counts(len(group), args.train_ratio, args.val_ratio)
            train_rows.extend(group[:train_count])
            val_rows.extend(group[train_count : train_count + val_count])
            test_rows.extend(group[train_count + val_count :])
    else:
        rng.shuffle(rows)
        total = len(rows)
        train_end = int(total * args.train_ratio)
        val_end = train_end + int(total * args.val_ratio)

        train_rows = rows[:train_end]
        val_rows = rows[train_end:val_end]
        test_rows = rows[val_end:]

    rng.shuffle(train_rows)
    rng.shuffle(val_rows)
    rng.shuffle(test_rows)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    train_truncated = write_jsonl(args.output_dir / "train.jsonl", train_rows, "train", args.max_input_chars)
    val_truncated = write_jsonl(args.output_dir / "val.jsonl", val_rows, "val", args.max_input_chars)
    test_truncated = write_jsonl(args.output_dir / "test.jsonl", test_rows, "test", args.max_input_chars)

    print("Split completed.")
    print(f"- train: {len(train_rows)}")
    print(f"- val: {len(val_rows)}")
    print(f"- test: {len(test_rows)}")
    print(f"- output_dir: {args.output_dir}")
    print(f"- stratify: {args.stratify}")
    print(f"- max_input_chars: {args.max_input_chars}")
    print(f"- truncated_rows: {train_truncated + val_truncated + test_truncated}")


if __name__ == "__main__":
    main()
