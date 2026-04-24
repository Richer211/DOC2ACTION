# Baseline Evaluation Report

数据集：`ml/data/final_v2/test.jsonl`
- extractor_mode: `lora`
- openai_model: `default`
- lora_base_model: `Qwen/Qwen2.5-1.5B-Instruct`
- lora_adapter_dir: `ml/train/artifacts/doc2action-lora-local/adapter`

## Aggregate Metrics
- sample_count: 26
- action_f1: 0.1346
- risk_f1: 0.6154
- question_f1: 0.8846
- summary_jaccard: 0.273
- citation_hit_rate: 0.4231
- duplication_rate: 0.0
- used_llm_rate: 0.0
- used_lora_rate: 1.0

## Per Sample
- RedHat-14362245 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1391
- MongoDB-1957808 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.4635
- enron-00008 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.196
- Mojang-493168 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.563
- JiraEcosystem-80827 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0807
- enron-00025 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3143
- EN2001a.C (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0278
- SecondLife-200968 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.0865
- meetingbank-train-12 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3654
- enron-00028 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.2013
- Spring-77130 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.6149
- EN2001e.C (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0844
- EN2001b.C (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0667
- meetingbank-train-16 (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.4223
- Sonatype-836541 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.4481
- MongoDB-1956376 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.3796
- meetingbank-train-14 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.4103
- enron-00013 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1512
- MariaDB-79880 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1057
- Sakai-17300 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.5759
- MariaDB-78716 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.5284
- IntelDAOS-35229 (general): action_f1=0.5, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1415
- Apache-13417501 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1585
- JiraEcosystem-276837 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1226
- meetingbank-train-8 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3805
- EN2001d.D (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0706