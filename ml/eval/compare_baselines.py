from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVAL_SCRIPT = ROOT / "ml" / "eval" / "evaluate.py"
REPORT_DIR = ROOT / "learning" / "reports"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare rules baseline vs low-cost LLM baseline.")
    parser.add_argument("--data-path", type=Path, default=ROOT / "ml" / "data" / "train.sample.jsonl")
    parser.add_argument("--llm-model", default="gpt-4o-mini")
    parser.add_argument("--rules-prefix", default="baseline-rules")
    parser.add_argument("--llm-prefix", default="baseline-llm-cheap")
    parser.add_argument("--summary-md", type=Path, default=REPORT_DIR / "baseline-compare.md")
    parser.add_argument(
        "--reuse-rules-json",
        type=Path,
        default=None,
        help="Reuse an existing rules aggregate json and skip rerunning rules evaluation.",
    )
    return parser.parse_args()


def run_eval(data_path: Path, prefix: str, extractor_mode: str, llm_model: str = "") -> dict:
    cmd = [
        "python",
        str(EVAL_SCRIPT),
        "--data-path",
        str(data_path),
        "--report-prefix",
        prefix,
        "--extractor-mode",
        extractor_mode,
    ]
    if llm_model:
        cmd.extend(["--openai-model", llm_model])
    subprocess.run(cmd, check=True)
    json_path = REPORT_DIR / f"{prefix}.json"
    return json.loads(json_path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if args.reuse_rules_json:
        rules_result = json.loads(args.reuse_rules_json.read_text(encoding="utf-8"))
    else:
        rules_result = run_eval(args.data_path, args.rules_prefix, "rules")
    llm_result = run_eval(args.data_path, args.llm_prefix, "auto", llm_model=args.llm_model)

    r = rules_result["aggregate"]
    l = llm_result["aggregate"]

    lines = [
        "# Baseline Compare Report",
        "",
        f"数据集：`{args.data_path}`",
        f"LLM 模型：`{args.llm_model}`",
        "",
        "## Aggregate",
        f"- rules.action_f1: {r['action_f1']}",
        f"- llm.action_f1: {l['action_f1']}",
        f"- rules.risk_f1: {r['risk_f1']}",
        f"- llm.risk_f1: {l['risk_f1']}",
        f"- rules.summary_jaccard: {r['summary_jaccard']}",
        f"- llm.summary_jaccard: {l['summary_jaccard']}",
        f"- rules.used_llm_rate: {r['used_llm_rate']}",
        f"- llm.used_llm_rate: {l['used_llm_rate']}",
        "",
        "## Delta (llm - rules)",
        f"- delta.action_f1: {round(l['action_f1'] - r['action_f1'], 4)}",
        f"- delta.risk_f1: {round(l['risk_f1'] - r['risk_f1'], 4)}",
        f"- delta.summary_jaccard: {round(l['summary_jaccard'] - r['summary_jaccard'], 4)}",
        "",
        f"- rules_source: `{'reused ' + str(args.reuse_rules_json) if args.reuse_rules_json else 'recomputed in this run'}`",
    ]

    args.summary_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Comparison completed: {args.summary_md}")


if __name__ == "__main__":
    main()
