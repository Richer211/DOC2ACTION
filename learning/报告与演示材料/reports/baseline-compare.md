# Baseline Compare Report

数据集：`/Users/ganggang/Documents/Doc2Action/ml/data/train.sample.jsonl`
LLM 模型：`gpt-4o-mini`

## Aggregate
- rules.action_f1: 0.15
- llm.action_f1: 0.3467
- rules.risk_f1: 0.1667
- llm.risk_f1: 0.5
- rules.summary_jaccard: 0.171
- llm.summary_jaccard: 0.1171
- rules.used_llm_rate: 0.0
- llm.used_llm_rate: 1.0

## Delta (llm - rules)
- delta.action_f1: 0.1967
- delta.risk_f1: 0.3333
- delta.summary_jaccard: -0.0539