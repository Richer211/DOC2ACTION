# Baseline Compare Report

数据集：`ml/data/final/test.jsonl`
LLM 模型：`gpt-4o-mini`

## Aggregate
- rules.action_f1: 0.0119
- llm.action_f1: 0.1986
- rules.risk_f1: 0.3333
- llm.risk_f1: 0.3524
- rules.summary_jaccard: 0.2213
- llm.summary_jaccard: 0.5198
- rules.used_llm_rate: 0.0
- llm.used_llm_rate: 1.0

## Delta (llm - rules)
- delta.action_f1: 0.1867
- delta.risk_f1: 0.0191
- delta.summary_jaccard: 0.2985

- rules_source: `reused learning/reports/baseline-rules-test150.json`