from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import AnalyzeRequest, analyze  # noqa: E402


DATA_PATH = ROOT / "ml" / "data" / "train.sample.jsonl"
REPORT_DIR = ROOT / "learning" / "reports"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Doc2Action offline evaluation.")
    parser.add_argument("--data-path", type=Path, default=DATA_PATH)
    parser.add_argument("--report-prefix", default="baseline-eval", help="Output report file prefix.")
    parser.add_argument("--extractor-mode", choices=["auto", "rules", "llm", "lora"], default="auto")
    parser.add_argument("--openai-model", default="", help="Optional OpenAI model override.")
    parser.add_argument("--lora-base-model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--lora-adapter-dir", type=Path, default=ROOT / "ml" / "train" / "artifacts" / "doc2action-lora-local" / "adapter")
    parser.add_argument(
        "--lora-max-new-tokens",
        type=int,
        default=256,
        help="Max new tokens to generate in lora mode (align with typical train/eval runs).",
    )
    parser.add_argument("--lora-temperature", type=float, default=0.0)
    parser.add_argument(
        "--rag-enabled",
        action="store_true",
        help="Set DOC2ACTION_RAG_ENABLED=1 for /analyze (semantic chunks + embedding top-k for LLM prompt).",
    )
    parser.add_argument(
        "--semantic-chunks",
        action="store_true",
        help="Set DOC2ACTION_SEMANTIC_CHUNKS=1 (paragraph/sentence-aware chunks without RAG retrieval).",
    )
    parser.add_argument(
        "--compare-llm-rag",
        action="store_true",
        help=(
            "Run evaluation twice (LLM): semantic chunks without RAG vs with RAG; "
            "writes a side-by-side markdown report. Requires --extractor-mode auto or llm."
        ),
    )
    return parser.parse_args()


def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[。！？?!；;:：\.,]+$", "", text)
    return text


def char_ngrams(text: str, n: int = 2) -> set[str]:
    normalized = normalize_text(text)
    if len(normalized) < n:
        return {normalized} if normalized else set()
    return {normalized[i : i + n] for i in range(len(normalized) - n + 1)}


def text_similarity(a: str, b: str) -> float:
    a_norm = normalize_text(a)
    b_norm = normalize_text(b)
    if not a_norm and not b_norm:
        return 1.0
    if not a_norm or not b_norm:
        return 0.0
    if a_norm in b_norm or b_norm in a_norm:
        return 1.0

    grams_a = char_ngrams(a_norm, 2)
    grams_b = char_ngrams(b_norm, 2)
    union = grams_a | grams_b
    if not union:
        return 0.0
    return len(grams_a & grams_b) / len(union)


def list_f1(pred: list[str], gold: list[str], match_threshold: float = 0.6) -> dict[str, float]:
    pred_list = [normalize_text(item) for item in pred if normalize_text(item)]
    gold_list = [normalize_text(item) for item in gold if normalize_text(item)]

    if not pred_list and not gold_list:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}

    matched_pred: set[int] = set()
    matched_gold: set[int] = set()

    for pi, pred_text in enumerate(pred_list):
        best_gi = None
        best_score = 0.0
        for gi, gold_text in enumerate(gold_list):
            if gi in matched_gold:
                continue
            score = text_similarity(pred_text, gold_text)
            if score > best_score:
                best_score = score
                best_gi = gi

        if best_gi is not None and best_score >= match_threshold:
            matched_pred.add(pi)
            matched_gold.add(best_gi)

    true_positive = len(matched_pred)
    precision = true_positive / len(pred_list) if pred_list else 0.0
    recall = true_positive / len(gold_list) if gold_list else 0.0
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {"precision": precision, "recall": recall, "f1": f1}


def jaccard_similarity(a: str, b: str) -> float:
    grams_a = char_ngrams(a, 2)
    grams_b = char_ngrams(b, 2)
    if not grams_a and not grams_b:
        return 1.0
    union = grams_a | grams_b
    if not union:
        return 0.0
    return len(grams_a & grams_b) / len(union)


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        rows.append(json.loads(stripped))
    return rows


def normalize_lora_payload(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary")
    if not isinstance(summary, str):
        summary = "No summary generated."

    action_items = payload.get("action_items", [])
    risks = payload.get("risks", [])
    open_questions = payload.get("open_questions", [])

    if not isinstance(action_items, list):
        action_items = []
    if not isinstance(risks, list):
        risks = []
    if not isinstance(open_questions, list):
        open_questions = []

    action_items = [str(x).strip() for x in action_items if str(x).strip()]
    risks = [str(x).strip() for x in risks if str(x).strip()]
    open_questions = [str(x).strip() for x in open_questions if str(x).strip()]

    return {
        "summary": summary,
        "action_items": action_items,
        "risks": risks,
        "open_questions": open_questions,
    }


def build_lora_predictor(
    base_model: str,
    adapter_dir: Path,
    max_new_tokens: int,
    temperature: float,
):
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Missing LoRA inference dependencies. Install: pip install -U transformers peft accelerate"
        ) from exc

    if not adapter_dir.exists():
        raise FileNotFoundError(f"LoRA adapter directory not found: {adapter_dir}")

    tokenizer = AutoTokenizer.from_pretrained(base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    has_cuda = torch.cuda.is_available()
    has_mps = bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
    if has_cuda:
        dtype = torch.bfloat16
    elif has_mps:
        dtype = torch.float16
    else:
        dtype = torch.float32

    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        dtype=dtype,
        device_map="auto" if has_cuda else None,
    )
    model = PeftModel.from_pretrained(base, str(adapter_dir))
    if has_mps:
        model.to("mps")
    model.eval()

    def _predict(sample: dict[str, Any]) -> dict[str, Any]:
        document_type = sample.get("document_type", "general")
        text = sample.get("input_text", "")
        prompt = (
            "You are an information extraction assistant.\n"
            "Extract structured results from the input document.\n"
            "Return strict JSON with keys: summary, action_items, risks, open_questions.\n\n"
            f"Document Type: {document_type}\n"
            "Input Document:\n"
            f"{text}\n\n"
            "Output JSON:\n"
        )

        # Long documents can blow MPS/CUDA attention memory; keep context aligned with LoRA training defaults.
        encoded = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        if has_cuda:
            encoded = {k: v.cuda() for k, v in encoded.items()}
        elif has_mps:
            encoded = {k: v.to("mps") for k, v in encoded.items()}

        with torch.no_grad():
            generate_kwargs: dict[str, Any] = {
                "max_new_tokens": max_new_tokens,
                "do_sample": temperature > 0,
            }
            if temperature > 0:
                generate_kwargs["temperature"] = temperature
            output = model.generate(**encoded, **generate_kwargs)

        input_len = int(encoded["input_ids"].shape[1])
        answer = tokenizer.decode(output[0][input_len:], skip_special_tokens=True).strip()
        try:
            raw_payload = json.loads(answer)
        except json.JSONDecodeError:
            raw_payload = {
                "summary": answer[:400] if answer else "No summary generated.",
                "action_items": [],
                "risks": [],
                "open_questions": [],
            }

        payload = normalize_lora_payload(raw_payload)
        return {
            "summary": payload["summary"],
            "action_items": [
                {"title": item, "priority": "medium", "source_chunk_ids": []}
                for item in payload["action_items"]
            ],
            "risks": [
                {"description": item, "severity": "medium", "source_chunk_ids": []}
                for item in payload["risks"]
            ],
            "open_questions": [
                {"question": item, "source_chunk_ids": []}
                for item in payload["open_questions"]
            ],
            "meta": {"used_llm": False, "used_lora": True},
        }

    return _predict


def run_evaluation(
    data_path: Path,
    extractor_mode: str,
    lora_base_model: str,
    lora_adapter_dir: Path,
    lora_max_new_tokens: int,
    lora_temperature: float,
    analyze_request_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    samples = parse_jsonl(data_path)
    per_sample: list[dict[str, Any]] = []

    action_f1_scores: list[float] = []
    risk_f1_scores: list[float] = []
    question_f1_scores: list[float] = []
    summary_scores: list[float] = []
    citation_hit_rates: list[float] = []
    duplication_rates: list[float] = []
    used_llm_flags: list[bool] = []
    used_lora_flags: list[bool] = []

    lora_predict = None
    if extractor_mode == "lora":
        lora_predict = build_lora_predictor(
            base_model=lora_base_model,
            adapter_dir=lora_adapter_dir,
            max_new_tokens=lora_max_new_tokens,
            temperature=lora_temperature,
        )

    req_extra = dict(analyze_request_fields or {})

    for sample in samples:
        if extractor_mode == "lora":
            if lora_predict is None:
                raise RuntimeError("LoRA predictor initialization failed.")
            prediction = lora_predict(sample)
        else:
            prediction = analyze(
                AnalyzeRequest(
                    text=sample["input_text"],
                    document_type=sample.get("document_type", "general"),
                    **req_extra,
                )
            ).model_dump()

        meta = prediction.get("meta", {})
        used_llm_flags.append(bool(meta.get("used_llm")))
        used_lora_flags.append(bool(meta.get("used_lora")))

        pred_actions = [item["title"] for item in prediction["action_items"]]
        pred_risks = [item["description"] for item in prediction["risks"]]
        pred_questions = [item["question"] for item in prediction["open_questions"]]

        gold_actions = sample["expected"]["action_items"]
        gold_risks = sample["expected"]["risks"]
        gold_questions = sample["expected"]["open_questions"]

        action_metrics = list_f1(pred_actions, gold_actions)
        risk_metrics = list_f1(pred_risks, gold_risks)
        question_metrics = list_f1(pred_questions, gold_questions)
        summary_sim = jaccard_similarity(prediction["summary"], sample["expected"]["summary"])

        citation_items = prediction["action_items"] + prediction["risks"] + prediction["open_questions"]
        if citation_items:
            citation_hit = sum(1 for item in citation_items if item.get("source_chunk_ids")) / len(citation_items)
        else:
            citation_hit = 1.0

        all_texts = [*pred_actions, *pred_risks, *pred_questions]
        deduped_size = len({normalize_text(text) for text in all_texts if normalize_text(text)})
        duplication_rate = 0.0 if not all_texts else 1 - (deduped_size / len(all_texts))

        action_f1_scores.append(action_metrics["f1"])
        risk_f1_scores.append(risk_metrics["f1"])
        question_f1_scores.append(question_metrics["f1"])
        summary_scores.append(summary_sim)
        citation_hit_rates.append(citation_hit)
        duplication_rates.append(duplication_rate)

        per_sample.append(
            {
                "id": sample["id"],
                "document_type": sample["document_type"],
                "action_f1": round(action_metrics["f1"], 4),
                "risk_f1": round(risk_metrics["f1"], 4),
                "question_f1": round(question_metrics["f1"], 4),
                "summary_jaccard": round(summary_sim, 4),
                "citation_hit_rate": round(citation_hit, 4),
                "duplication_rate": round(duplication_rate, 4),
                "used_llm": bool(meta.get("used_llm")),
                "used_lora": bool(meta.get("used_lora")),
                "rag_applied": meta.get("rag_applied"),
                "llm_prompt_chunk_count": meta.get("llm_prompt_chunk_count"),
            }
        )

    n = len(samples)
    rag_true = sum(1 for row in per_sample if row.get("rag_applied") is True)

    aggregate = {
        "sample_count": n,
        "action_f1": round(mean(action_f1_scores), 4),
        "risk_f1": round(mean(risk_f1_scores), 4),
        "question_f1": round(mean(question_f1_scores), 4),
        "summary_jaccard": round(mean(summary_scores), 4),
        "citation_hit_rate": round(mean(citation_hit_rates), 4),
        "duplication_rate": round(mean(duplication_rates), 4),
        "used_llm_rate": round(sum(1 for x in used_llm_flags if x) / len(used_llm_flags), 4) if used_llm_flags else 0.0,
        "used_lora_rate": round(sum(1 for x in used_lora_flags if x) / len(used_lora_flags), 4) if used_lora_flags else 0.0,
        "rag_applied_sample_rate": round(rag_true / n, 4) if n else 0.0,
    }

    return {"aggregate": aggregate, "per_sample": per_sample}


def write_reports(
    result: dict[str, Any],
    data_path: Path,
    report_prefix: str,
    extractor_mode: str,
    openai_model: str,
    lora_base_model: str,
    lora_adapter_dir: Path,
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORT_DIR / f"{report_prefix}.json"
    md_path = REPORT_DIR / f"{report_prefix}.md"

    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    agg = result["aggregate"]
    rag_note = ""
    if os.getenv("DOC2ACTION_RAG_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}:
        rag_note = "- DOC2ACTION_RAG_ENABLED: `1` (semantic chunks + embedding top-k for LLM prompt)\n"
    elif os.getenv("DOC2ACTION_SEMANTIC_CHUNKS", "").strip().lower() in {"1", "true", "yes", "on"}:
        rag_note = "- DOC2ACTION_SEMANTIC_CHUNKS: `1` (semantic chunking only)\n"

    lines = [
        "# Baseline Evaluation Report",
        "",
        f"数据集：`{data_path}`",
        f"- extractor_mode: `{extractor_mode}`",
        f"- openai_model: `{openai_model or 'default'}`",
    ]
    if rag_note:
        lines.append(rag_note.rstrip())
    if extractor_mode == "lora":
        lines.extend(
            [
                f"- lora_base_model: `{lora_base_model}`",
                f"- lora_adapter_dir: `{lora_adapter_dir}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Aggregate Metrics",
            f"- sample_count: {agg['sample_count']}",
            f"- action_f1: {agg['action_f1']}",
            f"- risk_f1: {agg['risk_f1']}",
            f"- question_f1: {agg['question_f1']}",
            f"- summary_jaccard: {agg['summary_jaccard']}",
            f"- citation_hit_rate: {agg['citation_hit_rate']}",
            f"- duplication_rate: {agg['duplication_rate']}",
            f"- used_llm_rate: {agg['used_llm_rate']}",
            f"- used_lora_rate: {agg.get('used_lora_rate', 0.0)}",
            "",
            "## Per Sample",
        ]
    )

    for row in result["per_sample"]:
        lines.append(
            f"- {row['id']} ({row['document_type']}): "
            f"action_f1={row['action_f1']}, risk_f1={row['risk_f1']}, "
            f"question_f1={row['question_f1']}, summary_jaccard={row['summary_jaccard']}"
        )

    md_path.write_text("\n".join(lines), encoding="utf-8")


def write_compare_llm_rag_report(
    result_no_rag: dict[str, Any],
    result_rag: dict[str, Any],
    data_path: Path,
    report_prefix: str,
    extractor_mode: str,
    openai_model: str,
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md_path = REPORT_DIR / f"{report_prefix}-compare-llm-rag.md"
    a = result_no_rag["aggregate"]
    b = result_rag["aggregate"]

    lines = [
        "# LLM 离线评测：语义切块（无 RAG 检索） vs 启用 RAG",
        "",
        f"数据集：`{data_path}`",
        f"- extractor_mode: `{extractor_mode}`",
        f"- openai_model: `{openai_model or 'default'}`",
        "",
        "Run A：请求体 `use_semantic_chunks=true`, `use_rag=false`（与 Run B 使用相同切块策略，但不裁 prompt）。",
        "Run B：请求体 `use_rag=true`（语义切块 + 向量检索子集）。",
        "",
        "## 汇总指标对比",
        "",
        "| 指标 | Run A 无检索 | Run B RAG |",
        "|------|-------------|-----------|",
        f"| sample_count | {a['sample_count']} | {b['sample_count']} |",
        f"| action_f1 | {a['action_f1']} | {b['action_f1']} |",
        f"| risk_f1 | {a['risk_f1']} | {b['risk_f1']} |",
        f"| question_f1 | {a['question_f1']} | {b['question_f1']} |",
        f"| summary_jaccard | {a['summary_jaccard']} | {b['summary_jaccard']} |",
        f"| citation_hit_rate | {a['citation_hit_rate']} | {b['citation_hit_rate']} |",
        f"| used_llm_rate | {a['used_llm_rate']} | {b['used_llm_rate']} |",
        f"| rag_applied_sample_rate | {a.get('rag_applied_sample_rate', 0.0)} | {b.get('rag_applied_sample_rate', 0.0)} |",
        "",
        "说明：`rag_applied_sample_rate` 为样本中 `meta.rag_applied=true` 的比例；Run A 通常为 0。",
        "",
        "## 逐条差异（仅列出 summary_jaccard 或 action_f1 任一不同）",
        "",
    ]

    by_id_a = {row["id"]: row for row in result_no_rag["per_sample"]}
    by_id_b = {row["id"]: row for row in result_rag["per_sample"]}
    for sid in sorted(set(by_id_a) & set(by_id_b)):
        ra, rb = by_id_a[sid], by_id_b[sid]
        if (
            ra["summary_jaccard"] == rb["summary_jaccard"]
            and ra["action_f1"] == rb["action_f1"]
            and ra["risk_f1"] == rb["risk_f1"]
            and ra["question_f1"] == rb["question_f1"]
        ):
            continue
        lines.append(
            f"- **{sid}**: A action_f1={ra['action_f1']} B={rb['action_f1']}; "
            f"A sum_j={ra['summary_jaccard']} B={rb['summary_jaccard']}; "
            f"A llm_chunks={ra.get('llm_prompt_chunk_count')} B={rb.get('llm_prompt_chunk_count')}"
        )

    json_a = REPORT_DIR / f"{report_prefix}-compare-A-no-rag.json"
    json_b = REPORT_DIR / f"{report_prefix}-compare-B-rag.json"
    json_a.write_text(json.dumps(result_no_rag, ensure_ascii=False, indent=2), encoding="utf-8")
    json_b.write_text(json.dumps(result_rag, ensure_ascii=False, indent=2), encoding="utf-8")
    lines.extend(["", f"完整 JSON： `{json_a.name}` ， `{json_b.name}`", ""])

    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.compare_llm_rag and args.extractor_mode not in {"auto", "llm"}:
        raise SystemExit("--compare-llm-rag requires --extractor-mode auto or llm")

    os.environ["DOC2ACTION_EXTRACTOR_MODE"] = args.extractor_mode
    if args.openai_model:
        os.environ["OPENAI_MODEL"] = args.openai_model
    if args.rag_enabled and not args.compare_llm_rag:
        os.environ["DOC2ACTION_RAG_ENABLED"] = "1"
    if args.semantic_chunks and not args.compare_llm_rag:
        os.environ["DOC2ACTION_SEMANTIC_CHUNKS"] = "1"

    if args.compare_llm_rag:
        result_a = run_evaluation(
            data_path=args.data_path,
            extractor_mode=args.extractor_mode,
            lora_base_model=args.lora_base_model,
            lora_adapter_dir=args.lora_adapter_dir,
            lora_max_new_tokens=args.lora_max_new_tokens,
            lora_temperature=args.lora_temperature,
            analyze_request_fields={"use_semantic_chunks": True, "use_rag": False},
        )
        result_b = run_evaluation(
            data_path=args.data_path,
            extractor_mode=args.extractor_mode,
            lora_base_model=args.lora_base_model,
            lora_adapter_dir=args.lora_adapter_dir,
            lora_max_new_tokens=args.lora_max_new_tokens,
            lora_temperature=args.lora_temperature,
            analyze_request_fields={"use_rag": True},
        )
        write_compare_llm_rag_report(
            result_no_rag=result_a,
            result_rag=result_b,
            data_path=args.data_path,
            report_prefix=args.report_prefix,
            extractor_mode=args.extractor_mode,
            openai_model=args.openai_model,
        )
        print(f"Compare report written to {REPORT_DIR / (args.report_prefix + '-compare-llm-rag.md')}")
        return

    result = run_evaluation(
        data_path=args.data_path,
        extractor_mode=args.extractor_mode,
        lora_base_model=args.lora_base_model,
        lora_adapter_dir=args.lora_adapter_dir,
        lora_max_new_tokens=args.lora_max_new_tokens,
        lora_temperature=args.lora_temperature,
    )
    write_reports(
        result=result,
        data_path=args.data_path,
        report_prefix=args.report_prefix,
        extractor_mode=args.extractor_mode,
        openai_model=args.openai_model,
        lora_base_model=args.lora_base_model,
        lora_adapter_dir=args.lora_adapter_dir,
    )
    print("Baseline evaluation completed.")


if __name__ == "__main__":
    main()
