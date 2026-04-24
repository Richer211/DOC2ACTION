from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES = [
    ROOT / "ml" / "data" / "external" / "meetingbank" / "processed" / "meetingbank.seed.auto.jsonl",
    ROOT / "ml" / "data" / "external" / "enron" / "processed" / "enron.seed.auto.anonymized.jsonl",
    ROOT / "ml" / "data" / "external" / "ami" / "processed" / "ami.seed.auto.jsonl",
    ROOT / "ml" / "data" / "external" / "jira" / "processed" / "jira.seed.auto.jsonl",
]
DEFAULT_OUTPUT = ROOT / "ml" / "data" / "curation" / "curation.batch.v1.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a balanced curation batch from weak-labeled sources.")
    parser.add_argument("--total", type=int, default=150, help="Total sample size.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--sources",
        nargs="*",
        default=[str(p) for p in DEFAULT_SOURCES],
        help="Source jsonl files.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def source_name_from_path(path: Path) -> str:
    # external/<source>/processed/...
    parts = path.parts
    if "external" in parts:
        idx = parts.index("external")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return path.stem


def main() -> None:
    args = parse_args()
    random.seed(args.seed)

    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for source_path_str in args.sources:
        source_path = Path(source_path_str)
        rows = read_jsonl(source_path)
        src = source_name_from_path(source_path)
        for row in rows:
            row.setdefault("meta", {})
            row["meta"]["curation_source"] = src
            by_source[src].append(row)

    available_sources = [src for src, rows in by_source.items() if rows]
    if not available_sources:
        raise RuntimeError("No source rows found. Please verify source jsonl files exist.")

    per_source = max(1, args.total // len(available_sources))
    selected: list[dict[str, Any]] = []

    for src in available_sources:
        rows = by_source[src]
        random.shuffle(rows)
        selected.extend(rows[: min(per_source, len(rows))])

    if len(selected) < args.total:
        remainder_pool = []
        for src in available_sources:
            remainder_pool.extend(by_source[src][per_source:])
        random.shuffle(remainder_pool)
        selected.extend(remainder_pool[: args.total - len(selected)])

    selected = selected[: args.total]
    random.shuffle(selected)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for row in selected:
            row.setdefault("meta", {})
            row["meta"]["needs_manual_curation"] = True
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Prepared {len(selected)} rows for manual curation: {args.output}")
    for src in available_sources:
        count = sum(1 for row in selected if row.get("meta", {}).get("curation_source") == src)
        print(f"- {src}: {count}")


if __name__ == "__main__":
    main()
