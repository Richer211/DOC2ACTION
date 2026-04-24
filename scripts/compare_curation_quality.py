from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BEFORE = ROOT / "ml" / "data" / "curation" / "jira.curate.top30.v1.jsonl"
DEFAULT_AFTER = ROOT / "ml" / "data" / "curated" / "jira.curated.top30.draft.v1.jsonl"
DEFAULT_REPORT = ROOT / "learning" / "reports" / "jira-curation-quality-compare.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare curation quality before vs after.")
    parser.add_argument("--before", type=Path, default=DEFAULT_BEFORE)
    parser.add_argument("--after", type=Path, default=DEFAULT_AFTER)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def avg(values: list[float]) -> float:
    return round(mean(values), 4) if values else 0.0


def is_metadata_summary(summary: str) -> bool:
    s = summary.strip()
    return s.startswith("Project:") or s.startswith("Issue Type:") or re.match(r"^Project:\s*\w+\s*[；;]\s*Issue Type:", s) is not None


def stats(rows: list[dict[str, Any]]) -> dict[str, float]:
    action_counts: list[float] = []
    risk_counts: list[float] = []
    question_counts: list[float] = []
    long_action_flags: list[float] = []
    metadata_summary_flags: list[float] = []
    empty_risk_flags: list[float] = []
    empty_question_flags: list[float] = []

    for row in rows:
        expected = row.get("expected", {})
        actions = [str(x).strip() for x in expected.get("action_items", []) if str(x).strip()]
        risks = [str(x).strip() for x in expected.get("risks", []) if str(x).strip()]
        questions = [str(x).strip() for x in expected.get("open_questions", []) if str(x).strip()]
        summary = str(expected.get("summary", "")).strip()

        action_counts.append(float(len(actions)))
        risk_counts.append(float(len(risks)))
        question_counts.append(float(len(questions)))

        long_action_flags.append(1.0 if any(len(a) > 220 for a in actions) else 0.0)
        metadata_summary_flags.append(1.0 if is_metadata_summary(summary) else 0.0)
        empty_risk_flags.append(1.0 if not risks else 0.0)
        empty_question_flags.append(1.0 if not questions else 0.0)

    return {
        "rows": float(len(rows)),
        "avg_action_count": avg(action_counts),
        "avg_risk_count": avg(risk_counts),
        "avg_question_count": avg(question_counts),
        "long_action_rate": avg(long_action_flags),
        "metadata_summary_rate": avg(metadata_summary_flags),
        "empty_risk_rate": avg(empty_risk_flags),
        "empty_question_rate": avg(empty_question_flags),
    }


def main() -> None:
    args = parse_args()
    before_rows = read_jsonl(args.before)
    after_rows = read_jsonl(args.after)

    before = stats(before_rows)
    after = stats(after_rows)

    lines = [
        "# Jira Curation Quality Compare",
        "",
        f"- before: `{args.before}`",
        f"- after: `{args.after}`",
        "",
        "## Metrics",
        f"- rows: before={int(before['rows'])}, after={int(after['rows'])}",
        f"- avg_action_count: before={before['avg_action_count']}, after={after['avg_action_count']}",
        f"- avg_risk_count: before={before['avg_risk_count']}, after={after['avg_risk_count']}",
        f"- avg_question_count: before={before['avg_question_count']}, after={after['avg_question_count']}",
        f"- long_action_rate: before={before['long_action_rate']}, after={after['long_action_rate']}",
        f"- metadata_summary_rate: before={before['metadata_summary_rate']}, after={after['metadata_summary_rate']}",
        f"- empty_risk_rate: before={before['empty_risk_rate']}, after={after['empty_risk_rate']}",
        f"- empty_question_rate: before={before['empty_question_rate']}, after={after['empty_question_rate']}",
    ]

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Quality compare report generated: {args.report}")


if __name__ == "__main__":
    main()
