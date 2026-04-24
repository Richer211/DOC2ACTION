from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import AnalyzeRequest, analyze

SAMPLES_DIR = ROOT / "samples"
OUTPUT_DIR = ROOT / "learning" / "demo"


def infer_doc_type(name: str) -> str:
    if "meeting" in name:
        return "meeting_notes"
    if "prd" in name:
        return "prd"
    if "email" in name:
        return "email_thread"
    if "sop" in name:
        return "sop"
    return "general"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_rows: list[str] = []

    for sample_path in sorted(SAMPLES_DIR.glob("*.md")):
        text = sample_path.read_text(encoding="utf-8")
        request = AnalyzeRequest(text=text, document_type=infer_doc_type(sample_path.name))
        result = analyze(request).model_dump()

        output_json = OUTPUT_DIR / f"{sample_path.stem}.result.json"
        output_json.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        summary_rows.append(
            f"- `{sample_path.name}` -> "
            f"actions: {len(result['action_items'])}, "
            f"risks: {len(result['risks'])}, "
            f"questions: {len(result['open_questions'])}, "
            f"used_llm: {result['meta']['used_llm']}"
        )

    report = [
        "# Phase 6 样本检查结果",
        "",
        "本报告由 `scripts/run_sample_checks.py` 自动生成。",
        "",
        "## 结果摘要",
        *summary_rows,
        "",
        "## 说明",
        "- 结果明细 JSON 存放在本目录下。",
        "- 当前无有效 OpenAI key 时，会走本地规则降级路径。",
    ]
    (OUTPUT_DIR / "phase6-sample-report.md").write_text("\n".join(report), encoding="utf-8")
    print("Phase 6 sample checks completed.")


if __name__ == "__main__":
    main()
