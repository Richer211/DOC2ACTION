"""Load offline evaluate.py markdown report for P1 summary API."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


def default_report_path() -> Path:
    raw = os.getenv("DOC2ACTION_EVAL_REPORT_MD", "").strip()
    if raw:
        return Path(raw).expanduser()
    repo = Path(__file__).resolve().parents[2]
    return repo / "learning" / "报告与演示材料" / "reports" / "baseline-eval.md"


def load_eval_summary() -> dict[str, Any]:
    path = default_report_path()
    if not path.is_file():
        return {
            "exists": False,
            "source_file": str(path),
            "aggregate": {},
            "excerpt": "",
            "hint": "在仓库根目录运行 ml/eval/evaluate.py 生成 baseline-eval.md 后刷新本页。",
        }
    text = path.read_text(encoding="utf-8")
    aggregate: dict[str, Any] = {}
    in_agg = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "## Aggregate Metrics":
            in_agg = True
            continue
        if in_agg:
            if stripped.startswith("## ") and stripped != "## Aggregate Metrics":
                break
            m = re.match(r"-\s*([\w_]+):\s*(.+)", stripped)
            if m:
                k, v = m.group(1), m.group(2).strip()
                try:
                    aggregate[k] = float(v) if "." in v else int(v)
                except ValueError:
                    aggregate[k] = v
    return {
        "exists": True,
        "source_file": str(path.resolve()),
        "aggregate": aggregate,
        "excerpt": text[:2800],
        "hint": None,
    }
