# Baseline Compare All Report

## Aggregate Metrics

| mode | action_f1 | risk_f1 | question_f1 | summary_jaccard | citation_hit_rate | duplication_rate |
|---|---:|---:|---:|---:|---:|---:|
| rules | 0.0119 | 0.3333 | 0.7143 | 0.2213 | 1.0000 | 0.0238 |
| llm_api | 0.2214 | 0.3571 | 0.4190 | 0.5519 | 1.0000 | 0.0000 |
| lora | 0.1961 | 0.3333 | 0.7143 | 0.5700 | 0.0000 | 0.0000 |

## Delta vs Rules
- llm_api: action_f1 +0.2095, risk_f1 +0.0238, question_f1 -0.2953, summary_jaccard +0.3306
- lora: action_f1 +0.1842, risk_f1 +0.0000, question_f1 +0.0000, summary_jaccard +0.3487

## LoRA Error Analysis (Lowest Composite Samples)
- EN2001e.A (meeting_notes): action_f1=0.0000, risk_f1=0.0000, question_f1=0.0000, summary_jaccard=0.5047
- EN2002c.B (meeting_notes): action_f1=0.0000, risk_f1=0.0000, question_f1=0.0000, summary_jaccard=0.5357
- Mojang-490600 (general): action_f1=0.0000, risk_f1=0.0000, question_f1=0.0000, summary_jaccard=0.5574
- EN2001d.A (meeting_notes): action_f1=0.0000, risk_f1=0.0000, question_f1=0.0000, summary_jaccard=0.6386
- EN2001d.C (meeting_notes): action_f1=0.2857, risk_f1=0.0000, question_f1=0.0000, summary_jaccard=0.4848
- meetingbank-train-14 (meeting_notes): action_f1=0.3333, risk_f1=0.0000, question_f1=0.0000, summary_jaccard=0.5213
- meetingbank-train-5 (meeting_notes): action_f1=0.0000, risk_f1=0.0000, question_f1=1.0000, summary_jaccard=0.5143
- Jira-1841594 (general): action_f1=0.0000, risk_f1=0.0000, question_f1=1.0000, summary_jaccard=0.5372