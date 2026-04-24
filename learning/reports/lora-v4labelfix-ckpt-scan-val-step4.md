# Baseline Evaluation Report

数据集：`/Users/ganggang/Documents/Doc2Action/ml/data/final_v2/val.jsonl`
- extractor_mode: `lora`
- openai_model: `default`
- lora_base_model: `Qwen/Qwen2.5-1.5B-Instruct`
- lora_adapter_dir: `/Users/ganggang/Documents/Doc2Action/ml/train/artifacts/doc2action-lora-v4-labelfix/checkpoint-4`

## Aggregate Metrics
- sample_count: 29
- action_f1: 0.1954
- risk_f1: 0.5862
- question_f1: 0.7931
- summary_jaccard: 0.2242
- citation_hit_rate: 0.6552
- duplication_rate: 0.0
- used_llm_rate: 0.0
- used_lora_rate: 1.0

## Per Sample
- Mindville-12304 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1184
- meetingbank-train-21 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.4172
- enron-00007 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3529
- meetingbank-train-10 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3691
- IntelDAOS-35246 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.2594
- Sonatype-836587 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.283
- Qt-329590 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.3291
- RedHat-13173920 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.2411
- Jira-1841594 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.125
- MongoDB-1955328 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.4766
- RedHat-13204448 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.2781
- JFrog-84478 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1333
- meetingbank-train-2 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0259
- EN2001e.E (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0345
- Spring-69854 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.2866
- enron-00024 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.1379
- EN2001b.A (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.0333
- Hyperledger-42432 (general): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3507
- EN2001d.E (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0323
- meetingbank-train-26 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.2278
- IntelDAOS-35242 (general): action_f1=0.6667, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0351
- EN2001e.D (meeting_notes): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.0267
- enron-00029 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.3441
- enron-00016 (email_thread): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.1892
- enron-00001 (email_thread): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.4388
- meetingbank-train-20 (meeting_notes): action_f1=1.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.466
- Sonatype-836611 (general): action_f1=0.0, risk_f1=0.0, question_f1=1.0, summary_jaccard=0.2812
- Sonatype-836625 (general): action_f1=0.0, risk_f1=0.0, question_f1=0.0, summary_jaccard=0.1751
- EN2002a.B (meeting_notes): action_f1=0.0, risk_f1=1.0, question_f1=1.0, summary_jaccard=0.0333