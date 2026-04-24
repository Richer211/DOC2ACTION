# Baseline Evaluation Report

数据集：`ml/data/final_v2/test.jsonl`
- extractor_mode: `lora`
- openai_model: `default`
- lora_base_model: `Qwen/Qwen2.5-1.5B-Instruct`
- lora_adapter_dir: `ml/train/artifacts/doc2action-lora-v5-top30fix/checkpoint-16`

## Aggregate Metrics
- sample_count: 26
- action_f1: 0.1795
- risk_f1: 0.6923
- question_f1: 0.8846
- summary_jaccard: 0.257
- citation_hit_rate: 0.4231
- duplication_rate: 0.0
- used_llm_rate: 0.0
- used_lora_rate: 1.0

## Per Sample
- RedHat-14362245 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1656
- MongoDB-1957808 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.2904
- enron-00008 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.2793
- Mojang-493168 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.6476
- JiraEcosystem-80827 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1356
- enron-00025 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3986
- EN2001a.C (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0541
- SecondLife-200968 (general): action_f1=1.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.089
- meetingbank-train-12 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3874
- enron-00028 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1798
- Spring-77130 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.4394
- EN2001e.C (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0964
- EN2001b.C (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0641
- meetingbank-train-16 (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.2262
- Sonatype-836541 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.3806
- MongoDB-1956376 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.4148
- meetingbank-train-14 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.323
- enron-00013 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1429
- MariaDB-79880 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1089
- Sakai-17300 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.451
- MariaDB-78716 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.5287
- IntelDAOS-35229 (general): action_f1=0.6667, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1348
- Apache-13417501 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1772
- JiraEcosystem-276837 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1509
- meetingbank-train-8 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3423
- EN2001d.D (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0727