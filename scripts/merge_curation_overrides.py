from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = ROOT / "ml" / "data" / "curation" / "curation.batch.v1.jsonl"
DEFAULT_OVERRIDE = ROOT / "ml" / "data" / "curated" / "jira.curated.top30.draft.v1.jsonl"
DEFAULT_OUTPUT = ROOT / "ml" / "data" / "curation" / "curation.batch.v2.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge curated overrides into curation batch.")
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--override", type=Path, default=DEFAULT_OVERRIDE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    base_rows = read_jsonl(args.base)
    override_rows = read_jsonl(args.override)

    override_by_id = {row.get("id"): row for row in override_rows if row.get("id")}

    replaced = 0
    merged: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for row in base_rows:
        row_id = row.get("id", "")
        if row_id in override_by_id:
            merged.append(override_by_id[row_id])
            replaced += 1
            seen_ids.add(row_id)
        else:
            merged.append(row)

    appended = 0
    for row_id, row in override_by_id.items():
        if row_id and row_id not in seen_ids:
            merged.append(row)
            appended += 1

    write_jsonl(args.output, merged)
    print(f"Merged file written: {args.output}")
    print(f"base_rows={len(base_rows)}, override_rows={len(override_rows)}, replaced={replaced}, appended={appended}, output_rows={len(merged)}")


if __name__ == "__main__":
    main()
