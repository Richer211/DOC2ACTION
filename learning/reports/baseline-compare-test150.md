# Baseline Compare Report

数据集：`ml/data/final/test.jsonl`
LLM 模型：`gpt-4o-mini`

## Aggregate
- rules.action_f1: 0.0119
- llm.action_f1: 0.2214
- rules.risk_f1: 0.3333
- llm.risk_f1: 0.3571
- rules.summary_jaccard: 0.2213
- llm.summary_jaccard: 0.5519
- rules.used_llm_rate: 0.0
- llm.used_llm_rate: 1.0

## Delta (llm - rules)
- delta.action_f1: 0.2095
- delta.risk_f1: 0.0238
- delta.summary_jaccard: 0.3306