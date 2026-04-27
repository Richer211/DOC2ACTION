# Evaluation Report

This report summarizes how Doc2Action is evaluated today and what the current baseline results suggest. The goal is to keep evaluation lightweight, reproducible, and useful for product decisions rather than to claim benchmark-grade model quality.

## Scope

The evaluation focuses on structured document extraction:

- summary quality
- action item extraction
- risk extraction
- open question extraction
- source citation coverage
- duplicate output rate

Evaluation scripts live in `ml/eval/` and read JSONL samples from `ml/data/`.

## Dataset

The current evaluation set is a small curated sample covering:

- meeting notes
- PRD-style excerpts
- issue / support style text
- general unstructured operational notes

The dataset is intentionally small enough to run locally during development. It is not a production benchmark; it is a regression and comparison harness for prompt, rule, and retrieval changes.

## Metrics

| Metric | Meaning |
| --- | --- |
| `action_f1` | F1-style overlap between predicted and expected action items |
| `risk_f1` | F1-style overlap between predicted and expected risks |
| `question_f1` | F1-style overlap between predicted and expected open questions |
| `summary_jaccard` | Character n-gram similarity between predicted and expected summaries |
| `citation_hit_rate` | Share of extracted items that include source chunk references |
| `duplication_rate` | Share of repeated output items after normalization |

The matching logic is intentionally simple and transparent. It is useful for detecting regressions, but qualitative review is still required for final prompt and product decisions.

## Current Baselines

Latest available comparison report: `learning/reports/baseline-compare-all-test150-v2.md`.

| Mode | action_f1 | risk_f1 | question_f1 | summary_jaccard | citation_hit_rate | duplication_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| rules | 0.0119 | 0.3333 | 0.7143 | 0.2213 | 1.0000 | 0.0238 |
| llm_api | 0.2214 | 0.3571 | 0.4190 | 0.5519 | 1.0000 | 0.0000 |
| lora | 0.0000 | 0.3333 | 0.7143 | 0.2267 | 0.0476 | 0.0000 |

Interpretation:

- The OpenAI-backed LLM path improves action extraction and summary similarity over rules.
- The rules path still performs reasonably on template-like risks and questions, which makes it useful as a fallback.
- Citation coverage is strong for rules and LLM API output because the production response keeps source chunk IDs.
- The local LoRA path is not yet production-ready in this report; it needs better training data, output schema enforcement, and source citation alignment.

## How to Reproduce

Rules baseline:

```bash
cd backend
source .venv/bin/activate
python ../ml/eval/evaluate.py \
  --extractor-mode rules \
  --report-prefix baseline-rules-local
```

LLM baseline:

```bash
cd backend
source .venv/bin/activate
python ../ml/eval/evaluate.py \
  --extractor-mode auto \
  --openai-model gpt-4o-mini \
  --report-prefix baseline-llm-local
```

Rules vs LLM comparison:

```bash
cd backend
source .venv/bin/activate
python ../ml/eval/compare_baselines.py \
  --llm-model gpt-4o-mini
```

Reports are written to `learning/reports/` or `learning/报告与演示材料/reports/`, depending on the script.

## Known Limitations

- The sample set is small and should be expanded before making strong claims about model quality.
- Current metrics use fuzzy text overlap and do not fully capture semantic correctness.
- Summary similarity is approximate; human review is still needed for conciseness and factual accuracy.
- LLM runs depend on model version, prompt changes, and API availability.
- RAG evaluation is still early; future reports should compare no-RAG vs RAG with fixed retrieval settings.

## Next Evaluation Improvements

- Add 30-50 more labeled samples across meeting notes, PRDs, support threads, and email-style tasks.
- Track latency and token usage alongside quality metrics.
- Add a qualitative error taxonomy: missed owner/date, vague action item, hallucinated risk, duplicate question, unsupported claim.
- Add regression thresholds in CI for rules-only smoke tests.
- Introduce a small human review checklist for demo readiness.
