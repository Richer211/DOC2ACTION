# Baseline Evaluation Report

数据集：`ml/data/final_v2/test.jsonl`
- extractor_mode: `lora`
- openai_model: `default`
- lora_base_model: `Qwen/Qwen2.5-1.5B-Instruct`
- lora_adapter_dir: `ml/train/artifacts/doc2action-lora-v6-headtruncate/checkpoint-4`

## Aggregate Metrics
- sample_count: 26
- action_f1: 0.1923
- risk_f1: 0.6923
- question_f1: 0.8846
- summary_jaccard: 0.2388
- citation_hit_rate: 1.0
- duplication_rate: 0.0
- used_llm_rate: 0.0
- used_lora_rate: 1.0

## Per Sample
- RedHat-14362245 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.119
- MongoDB-1957808 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.21
- enron-00008 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1923
- Mojang-493168 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.4028
- JiraEcosystem-80827 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0746
- enron-00025 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3942
- EN2001a.C (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0278
- SecondLife-200968 (general): action_f1=1.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.089
- meetingbank-train-12 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3636
- enron-00028 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0909
- Spring-77130 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.3172
- EN2001e.C (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0936
- EN2001b.C (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0625
- meetingbank-train-16 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3598
- Sonatype-836541 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.3882
- MongoDB-1956376 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.3197
- meetingbank-train-14 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.5433
- enron-00013 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1232
- MariaDB-79880 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0899
- Sakai-17300 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.5612
- MariaDB-78716 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.4807
- IntelDAOS-35229 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1888
- Apache-13417501 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1838
- JiraEcosystem-276837 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0833
- meetingbank-train-8 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3877
- EN2001d.D (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0616