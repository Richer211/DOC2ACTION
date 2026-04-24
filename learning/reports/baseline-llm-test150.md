# Baseline Evaluation Report

数据集：`ml/data/final/test.jsonl`
- extractor_mode: `auto`
- openai_model: `gpt-4o-mini`

## Aggregate Metrics
- sample_count: 21
- action_f1: 0.2214
- risk_f1: 0.3571
- question_f1: 0.419
- summary_jaccard: 0.5519
- citation_hit_rate: 1.0
- duplication_rate: 0.0
- used_llm_rate: 1.0

## Per Sample
- enron-00029 (email_thread): action_f1=0.6667, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.563
- meetingbank-train-14 (meeting_notes): action_f1=0.3333, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.6269
- EN2002c.B (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.4667
- EN2001e.A (meeting_notes): action_f1=0.3636, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.475
- JFrog-84478 (general): action_f1=0.0, risk_f1=1.0, question_f1=0.0, summary_jaccard=0.4715
- JiraEcosystem-276837 (general): action_f1=1.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.6375
- Jira-1838131 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.5299
- Mojang-490600 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.5
- meetingbank-train-5 (meeting_notes): action_f1=0.2857, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.6534
- JFrog-136478 (general): action_f1=0.0, risk_f1=0.5, question_f1=1.0, summary_jaccard=0.5409
- Mindville-10612 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.4706
- EN2001d.A (meeting_notes): action_f1=0.25, risk_f1=0.0, question_f1=0.4, summary_jaccard=0.5491
- meetingbank-train-6 (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.6303
- meetingbank-train-15 (meeting_notes): action_f1=0.5, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.4188
- enron-00006 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.6667
- RedHat-14362245 (general): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.7018
- enron-00011 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=0.0, summary_jaccard=0.6382
- SecondLife-309711 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.5148
- enron-00021 (email_thread): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.5867
- Jira-1841594 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.451
- EN2001d.C (meeting_notes): action_f1=0.25, risk_f1=0.0, question_f1=0.4, summary_jaccard=0.4969