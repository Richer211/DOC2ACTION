# Baseline Evaluation Report

数据集：`/Users/ganggang/Documents/Doc2Action/ml/data/train.sample.jsonl`
- extractor_mode: `auto`
- openai_model: `gpt-4o-mini`

## Aggregate Metrics
- sample_count: 10
- action_f1: 0.3467
- risk_f1: 0.5
- question_f1: 0.7
- summary_jaccard: 0.1171
- citation_hit_rate: 1.0
- duplication_rate: 0.0
- used_llm_rate: 1.0

## Per Sample
- train-001 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3421
- train-002 (prd): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.0
- train-003 (email_thread): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.0
- train-004 (sop): action_f1=0.5, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.14
- train-005 (general): action_f1=0.5, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1
- train-006 (meeting_notes): action_f1=0.8, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1707
- train-007 (prd): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.0635
- train-008 (email_thread): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.0
- train-009 (sop): action_f1=0.6667, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.15
- train-010 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.2045