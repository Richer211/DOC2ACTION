# Baseline Evaluation Report

数据集：`/Users/ganggang/Documents/Doc2Action/ml/data/train.sample.jsonl`
- extractor_mode: `rules`
- openai_model: `default`

## Aggregate Metrics
- sample_count: 10
- action_f1: 0.15
- risk_f1: 0.1667
- question_f1: 1.0
- summary_jaccard: 0.171
- citation_hit_rate: 1.0
- duplication_rate: 0.025
- used_llm_rate: 0.0

## Per Sample
- train-001 (meeting_notes): action_f1=1.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.3
- train-002 (prd): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3889
- train-003 (email_thread): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1667
- train-004 (sop): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1296
- train-005 (general): action_f1=0.5, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.0612
- train-006 (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1429
- train-007 (prd): action_f1=0.0, risk_f1=0.6667, question_f1=1.0, summary_jaccard=0.06
- train-008 (email_thread): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1429
- train-009 (sop): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1404
- train-010 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1778