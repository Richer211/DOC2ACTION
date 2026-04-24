# Baseline Evaluation Report

数据集：`ml/data/final/test.jsonl`
- extractor_mode: `auto`
- openai_model: `gpt-4o-mini`

## Aggregate Metrics
- sample_count: 21
- action_f1: 0.1986
- risk_f1: 0.3524
- question_f1: 0.3492
- summary_jaccard: 0.5198
- citation_hit_rate: 1.0
- duplication_rate: 0.0
- used_llm_rate: 1.0

## Per Sample
- enron-00029 (email_thread): action_f1=0.6667, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.563
- meetingbank-train-14 (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.6103
- EN2002c.B (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.4607
- EN2001e.A (meeting_notes): action_f1=0.1818, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.5025
- JFrog-84478 (general): action_f1=0.0, risk_f1=1.0, question_f1=0.0, summary_jaccard=0.3833
- JiraEcosystem-276837 (general): action_f1=1.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.6375
- Jira-1838131 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.5373
- Mojang-490600 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.5102
- meetingbank-train-5 (meeting_notes): action_f1=0.2857, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.6384
- JFrog-136478 (general): action_f1=0.0, risk_f1=0.4, question_f1=0.0, summary_jaccard=0.5032
- Mindville-10612 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.4706
- EN2001d.A (meeting_notes): action_f1=0.25, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.503
- meetingbank-train-6 (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.5932
- meetingbank-train-15 (meeting_notes): action_f1=0.5, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.4012
- enron-00006 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.6486
- RedHat-14362245 (general): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.6111
- enron-00011 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=0.0, summary_jaccard=0.5208
- SecondLife-309711 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.4944
- enron-00021 (email_thread): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.4161
- Jira-1841594 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.5033
- EN2001d.C (meeting_notes): action_f1=0.2857, risk_f1=0.0, question_f1=0.3333, summary_jaccard=0.4065