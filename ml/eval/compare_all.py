from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "learning" / "reports"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare rules / llm / lora evaluation reports.")
    parser.add_argument("--rules-json", type=Path, default=REPORT_DIR / "baseline-rules-test150.json")
    parser.add_argument("--llm-json", type=Path, default=REPORT_DIR / "baseline-llm-test150.json")
    parser.add_argument("--lora-json", type=Path, default=REPORT_DIR / "baseline-lora-test150.json")
    parser.add_argument("--output-md", type=Path, default=REPORT_DIR / "baseline-compare-all-test150.md")
    parser.add_argument("--top-k", type=int, default=8, help="Top K low-score samples for error analysis.")
    return parser.parse_args()


def load_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Report not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def score_row(name: str, report: dict[str, Any]) -> dict[str, Any]:
    agg = report.get("aggregate", {})
    return {
        "name": name,
        "action_f1": float(agg.get("action_f1", 0.0)),
        "risk_f1": float(agg.get("risk_f1", 0.0)),
        "question_f1": float(agg.get("question_f1", 0.0)),
        "summary_jaccard": float(agg.get("summary_jaccard", 0.0)),
        "citation_hit_rate": float(agg.get("citation_hit_rate", 0.0)),
        "duplication_rate": float(agg.get("duplication_rate", 0.0)),
    }


def rank_low_samples(
    per_sample: list[dict[str, Any]],
    top_k: int,
) -> list[dict[str, Any]]:
    def sample_score(row: dict[str, Any]) -> float:
        return mean(
            [
                float(row.get("action_f1", 0.0)),
                float(row.get("risk_f1", 0.0)),
                float(row.get("question_f1", 0.0)),
                float(row.get("summary_jaccard", 0.0)),
            ]
        )

    ranked = sorted(per_sample, key=sample_score)
    return ranked[:top_k]


def main() -> None:
    args = parse_args()
    rules = load_report(args.rules_json)
    llm = load_report(args.llm_json)
    lora = load_report(args.lora_json)

    rows = [
        score_row("rules", rules),
        score_row("llm_api", llm),
        score_row("lora", lora),
    ]

    rules_row = rows[0]
    llm_row = rows[1]
    lora_row = rows[2]

    low_samples = rank_low_samples(lora.get("per_sample", []), args.top_k)

    lines = [
        "# Baseline Compare All Report",
        "",
        "## Aggregate Metrics",
        "",
        "| mode | action_f1 | risk_f1 | question_f1 | summary_jaccard | citation_hit_rate | duplication_rate |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for row in rows:
        lines.append(
            f"| {row['name']} | {row['action_f1']:.4f} | {row['risk_f1']:.4f} | "
            f"{row['question_f1']:.4f} | {row['summary_jaccard']:.4f} | "
            f"{row['citation_hit_rate']:.4f} | {row['duplication_rate']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Delta vs Rules",
            f"- llm_api: action_f1 {llm_row['action_f1'] - rules_row['action_f1']:+.4f}, "
            f"risk_f1 {llm_row['risk_f1'] - rules_row['risk_f1']:+.4f}, "
            f"question_f1 {llm_row['question_f1'] - rules_row['question_f1']:+.4f}, "
            f"summary_jaccard {llm_row['summary_jaccard'] - rules_row['summary_jaccard']:+.4f}",
            f"- lora: action_f1 {lora_row['action_f1'] - rules_row['action_f1']:+.4f}, "
            f"risk_f1 {lora_row['risk_f1'] - rules_row['risk_f1']:+.4f}, "
            f"question_f1 {lora_row['question_f1'] - rules_row['question_f1']:+.4f}, "
            f"summary_jaccard {lora_row['summary_jaccard'] - rules_row['summary_jaccard']:+.4f}",
            "",
            "## LoRA Error Analysis (Lowest Composite Samples)",
        ]
    )

    for row in low_samples:
        lines.append(
            f"- {row.get('id')} ({row.get('document_type')}): "
            f"action_f1={row.get('action_f1', 0):.4f}, "
            f"risk_f1={row.get('risk_f1', 0):.4f}, "
            f"question_f1={row.get('question_f1', 0):.4f}, "
            f"summary_jaccard={row.get('summary_jaccard', 0):.4f}"
        )

    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Comparison completed: {args.output_md}")


if __name__ == "__main__":
    main()
