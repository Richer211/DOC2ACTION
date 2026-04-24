# Baseline Evaluation Report

数据集：`ml/data/final/test.jsonl`
- extractor_mode: `lora`
- openai_model: `default`
- lora_base_model: `Qwen/Qwen2.5-1.5B-Instruct`
- lora_adapter_dir: `ml/train/artifacts/doc2action-lora-local/adapter`

## Aggregate Metrics
- sample_count: 21
- action_f1: 0.1961
- risk_f1: 0.3333
- question_f1: 0.7143
- summary_jaccard: 0.57
- citation_hit_rate: 0.0
- duplication_rate: 0.0
- used_llm_rate: 0.0
- used_lora_rate: 1.0

## Per Sample
- enron-00029 (email_thread): action_f1=0.5, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.6098
- meetingbank-train-14 (meeting_notes): action_f1=0.3333, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.5213
- EN2002c.B (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.5357
- EN2001e.A (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.5047
- JFrog-84478 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.5205
- JiraEcosystem-276837 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.7113
- Jira-1838131 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.5035
- Mojang-490600 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.5574
- meetingbank-train-5 (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.5143
- JFrog-136478 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.6207
- Mindville-10612 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.5174
- EN2001d.A (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.6386
- meetingbank-train-6 (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.5705
- meetingbank-train-15 (meeting_notes): action_f1=1.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.4093
- enron-00006 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.6714
- RedHat-14362245 (general): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.8447
- enron-00011 (email_thread): action_f1=0.6667, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.58
- SecondLife-309711 (general): action_f1=0.3333, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.5654
- enron-00021 (email_thread): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.5515
- Jira-1841594 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.5372
- EN2001d.C (meeting_notes): action_f1=0.2857, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.4848