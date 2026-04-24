# Baseline Evaluation Report

数据集：`ml/data/final/test.jsonl`
- extractor_mode: `rules`
- openai_model: `default`

## Aggregate Metrics
- sample_count: 21
- action_f1: 0.0119
- risk_f1: 0.3333
- question_f1: 0.7143
- summary_jaccard: 0.2213
- citation_hit_rate: 1.0
- duplication_rate: 0.0238
- used_llm_rate: 0.0

## Per Sample
- enron-00029 (email_thread): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.3571
- meetingbank-train-14 (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.4138
- EN2002c.B (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.0867
- EN2001e.A (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.0757
- JFrog-84478 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1311
- JiraEcosystem-276837 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1512
- Jira-1838131 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1655
- Mojang-490600 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.089
- meetingbank-train-5 (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.4208
- JFrog-136478 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1027
- Mindville-10612 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1799
- EN2001d.A (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.0814
- meetingbank-train-6 (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.5177
- meetingbank-train-15 (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.3882
- enron-00006 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.6296
- RedHat-14362245 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1441
- enron-00011 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.2159
- SecondLife-309711 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.0932
- enron-00021 (email_thread): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1916
- Jira-1841594 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1156
- EN2001d.C (meeting_notes): action_f1=0.25, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.0955