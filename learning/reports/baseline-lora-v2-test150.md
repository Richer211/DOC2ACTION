# Baseline Evaluation Report

数据集：`ml/data/final/test.jsonl`
- extractor_mode: `lora`
- openai_model: `default`
- lora_base_model: `Qwen/Qwen2.5-1.5B-Instruct`
- lora_adapter_dir: `ml/train/artifacts/doc2action-lora-v2/adapter`

## Aggregate Metrics
- sample_count: 21
- action_f1: 0.0
- risk_f1: 0.3333
- question_f1: 0.7143
- summary_jaccard: 0.2267
- citation_hit_rate: 0.0476
- duplication_rate: 0.0
- used_llm_rate: 0.0
- used_lora_rate: 1.0

## Per Sample
- enron-00029 (email_thread): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1534
- meetingbank-train-14 (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.3467
- EN2002c.B (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.3179
- EN2001e.A (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.4044
- JFrog-84478 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1311
- JiraEcosystem-276837 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1512
- Jira-1838131 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1655
- Mojang-490600 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.089
- meetingbank-train-5 (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.3966
- JFrog-136478 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1027
- Mindville-10612 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1799
- EN2001d.A (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.0814
- meetingbank-train-6 (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.405
- meetingbank-train-15 (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.3462
- enron-00006 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.2093
- RedHat-14362245 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1441
- enron-00011 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.2164
- SecondLife-309711 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.0932
- enron-00021 (email_thread): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.2628
- Jira-1841594 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1156
- EN2001d.C (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.4487