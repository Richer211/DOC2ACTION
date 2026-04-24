from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EVAL_SCRIPT = ROOT / "ml" / "eval" / "evaluate.py"
REPORT_DIR = ROOT / "learning" / "reports"


def _rel_to_root(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score each checkpoint-* LoRA adapter with ml/eval/evaluate.py and pick the best by offline metrics."
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Training output dir containing checkpoint-* folders (each with adapter weights).",
    )
    parser.add_argument(
        "--eval-data",
        type=Path,
        default=ROOT / "ml" / "data" / "final_v2" / "val.jsonl",
        help="Held-out jsonl for scoring (default: final_v2 val).",
    )
    parser.add_argument("--lora-base-model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--lora-max-new-tokens", type=int, default=256)
    parser.add_argument(
        "--report-prefix",
        default="lora-ckpt-scan",
        help="Prefix for evaluate.py reports; checkpoint step is appended.",
    )
    return parser.parse_args()


def find_checkpoints(run_dir: Path) -> list[tuple[int, Path]]:
    run_dir = run_dir.expanduser().resolve()
    out: list[tuple[int, Path]] = []
    for child in sorted(run_dir.iterdir()):
        if not child.is_dir():
            continue
        m = re.match(r"^checkpoint-(\d+)$", child.name)
        if not m:
            continue
        step = int(m.group(1))
        if (child / "adapter_model.safetensors").exists() or (child / "adapter_model.bin").exists():
            out.append((step, child.resolve()))
    out.sort(key=lambda x: x[0])
    return out


def composite_score(agg: dict[str, Any]) -> float:
    return float(
        mean(
            [
                float(agg.get("action_f1", 0.0)),
                float(agg.get("risk_f1", 0.0)),
                float(agg.get("question_f1", 0.0)),
                float(agg.get("summary_jaccard", 0.0)),
            ]
        )
    )


def main() -> None:
    args = parse_args()
    run_dir = args.run_dir.expanduser().resolve()
    eval_data = args.eval_data.expanduser().resolve()
    checkpoints = find_checkpoints(run_dir)
    if not checkpoints:
        print(f"No checkpoint-* with adapter weights under: {run_dir}", file=sys.stderr)
        sys.exit(1)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    for step, ckpt_dir in checkpoints:
        prefix = f"{args.report_prefix}-step{step}"
        cmd = [
            sys.executable,
            str(EVAL_SCRIPT),
            "--data-path",
            str(eval_data),
            "--extractor-mode",
            "lora",
            "--lora-base-model",
            args.lora_base_model,
            "--lora-adapter-dir",
            str(ckpt_dir),
            "--lora-max-new-tokens",
            str(args.lora_max_new_tokens),
            "--report-prefix",
            prefix,
        ]
        subprocess.run(cmd, check=True, cwd=str(ROOT))
        report_path = REPORT_DIR / f"{prefix}.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        agg = report.get("aggregate", {})
        score = composite_score(agg)
        results.append(
            {
                "step": step,
                "checkpoint_dir": _rel_to_root(ckpt_dir),
                "composite": round(score, 4),
                "aggregate": agg,
                "report_json": _rel_to_root(report_path),
            }
        )

    best = max(results, key=lambda r: r["composite"])
    summary_path = run_dir / "best_checkpoint_by_eval.json"
    summary_path.write_text(
        json.dumps({"best": best, "all": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("--- LoRA checkpoint scan (composite = mean of action/risk/question F1 + summary_jaccard) ---")
    for r in sorted(results, key=lambda x: x["composite"], reverse=True):
        print(f"step {r['step']:>5}  composite={r['composite']:.4f}  dir={r['checkpoint_dir']}")
    print()
    print(f"Best: step {best['step']}  composite={best['composite']:.4f}")
    print(f"Wrote: {_rel_to_root(summary_path)}")


if __name__ == "__main__":
    main()
