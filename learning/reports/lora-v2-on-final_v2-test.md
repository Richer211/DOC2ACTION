# Baseline Evaluation Report

数据集：`ml/data/final_v2/test.jsonl`
- extractor_mode: `lora`
- openai_model: `default`
- lora_base_model: `Qwen/Qwen2.5-1.5B-Instruct`
- lora_adapter_dir: `ml/train/artifacts/doc2action-lora-v2/adapter`

## Aggregate Metrics
- sample_count: 26
- action_f1: 0.2308
- risk_f1: 0.6923
- question_f1: 0.8846
- summary_jaccard: 0.4164
- citation_hit_rate: 0.4231
- duplication_rate: 0.0
- used_llm_rate: 0.0
- used_lora_rate: 1.0

## Per Sample
- RedHat-14362245 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=1.0
- MongoDB-1957808 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.2886
- enron-00008 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1818
- Mojang-493168 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.0893
- JiraEcosystem-80827 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=1.0
- enron-00025 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3548
- EN2001a.C (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0278
- SecondLife-200968 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.0857
- meetingbank-train-12 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.4222
- enron-00028 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1414
- Spring-77130 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.0533
- EN2001e.C (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=1.0
- EN2001b.C (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0577
- meetingbank-train-16 (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3842
- Sonatype-836541 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.118
- MongoDB-1956376 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.4837
- meetingbank-train-14 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.4222
- enron-00013 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.027
- MariaDB-79880 (general): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=1.0
- Sakai-17300 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1722
- MariaDB-78716 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.0722
- IntelDAOS-35229 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=1.0
- Apache-13417501 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=1.0
- JiraEcosystem-276837 (general): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=1.0
- meetingbank-train-8 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3871
- EN2001d.D (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0563