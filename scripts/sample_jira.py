from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from pymongo import MongoClient


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "ml" / "data" / "external" / "jira" / "processed" / "jira.sample.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sample Jira issues from restored MongoDB dump.")
    parser.add_argument("--uri", default="mongodb://localhost:27017")
    parser.add_argument("--db", default="JiraReposAnon")
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--collections", nargs="*", default=[], help="Optional specific collections to sample.")
    return parser.parse_args()


def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_comments(doc: dict[str, Any], limit: int = 3) -> list[str]:
    comments_raw = doc.get("fields", {}).get("comments", [])
    if not isinstance(comments_raw, list):
        return []
    comments = []
    for item in comments_raw[:limit]:
        body = ""
        if isinstance(item, dict):
            body = item.get("body", "") or item.get("comment", "")
        body = clean_text(str(body))
        if body:
            comments.append(body[:400])
    return comments


def compose_issue_text(doc: dict[str, Any]) -> str:
    fields = doc.get("fields", {})
    summary = clean_text(str(fields.get("summary", "")))
    description = clean_text(str(fields.get("description", "")))
    status = str((fields.get("status") or {}).get("name", ""))
    issue_type = str((fields.get("issuetype") or {}).get("name", ""))
    project_key = str((fields.get("project") or {}).get("key", ""))

    parts = [
        f"Project: {project_key}" if project_key else "",
        f"Issue Type: {issue_type}" if issue_type else "",
        f"Status: {status}" if status else "",
        f"Summary: {summary}" if summary else "",
        f"Description: {description}" if description else "",
    ]

    comments = extract_comments(doc)
    if comments:
        parts.append("Comments:")
        for idx, c in enumerate(comments, start=1):
            parts.append(f"{idx}. {c}")

    joined = "\n".join([p for p in parts if p]).strip()
    return joined[:5000]


def main() -> None:
    args = parse_args()
    client = MongoClient(args.uri)
    db = client[args.db]

    collections = args.collections or db.list_collection_names()
    collections = [c for c in collections if c not in {"system.indexes"}]
    if not collections:
        raise RuntimeError("No collections found in Jira database.")

    args.output.parent.mkdir(parents=True, exist_ok=True)

    per_collection = max(1, args.count // len(collections))
    total_written = 0
    with args.output.open("w", encoding="utf-8") as f:
        for collection_name in collections:
            collection = db[collection_name]
            cursor = collection.find(
                {},
                {
                    "_id": 0,
                    "id": 1,
                    "key": 1,
                    "self": 1,
                    "fields.summary": 1,
                    "fields.description": 1,
                    "fields.status.name": 1,
                    "fields.issuetype.name": 1,
                    "fields.project.key": 1,
                    "fields.comments": 1,
                    "fields.created": 1,
                    "fields.updated": 1,
                },
            ).limit(per_collection)

            for doc in cursor:
                issue_text = compose_issue_text(doc)
                if len(issue_text) < 80:
                    continue
                row = {
                    "id": f"{collection_name}-{doc.get('id', '')}",
                    "source_dataset": "jira_public_dataset",
                    "collection": collection_name,
                    "issue_key": doc.get("key", ""),
                    "issue_url": doc.get("self", ""),
                    "issue_text": issue_text,
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                total_written += 1
                if total_written >= args.count:
                    break
            if total_written >= args.count:
                break

    print(f"Exported {total_written} Jira issue samples to {args.output}")


if __name__ == "__main__":
    main()
