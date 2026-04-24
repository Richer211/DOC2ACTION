# Jira Top30 Curation List

- source_file: `/Users/ganggang/Documents/Doc2Action/ml/data/external/jira/processed/jira.seed.auto.jsonl`
- output_file: `/Users/ganggang/Documents/Doc2Action/ml/data/curation/jira.curate.top30.v1.jsonl`
- top_k: 30

## Rules
- 优先处理：summary 元数据化、action 过长、risk/question 缺失、长文本低提取。

## Selected Samples
- #1 `RedHat-13173920` (XNIO-381) score=13 reasons=[action_contains_raw_metadata_prefix, action_too_long, has_comments_but_low_extraction, missing_open_questions, missing_risks, summary_is_metadata_like, very_long_input]
- #2 `Sakai-17339` (YAFT-53) score=13 reasons=[action_contains_raw_metadata_prefix, action_too_long, has_comments_but_low_extraction, missing_open_questions, missing_risks, summary_is_metadata_like, very_long_input]
- #3 `IntelDAOS-35246` (DAOS-9506) score=12 reasons=[action_contains_raw_metadata_prefix, action_too_long, missing_open_questions, missing_risks, summary_is_metadata_like, very_long_input]
- #4 `JiraEcosystem-356914` (WEBHOOKS-158) score=12 reasons=[action_contains_raw_metadata_prefix, action_too_long, missing_open_questions, missing_risks, summary_is_metadata_like, very_long_input]
- #5 `Qt-324572` (QTWEBSITE-999) score=12 reasons=[action_contains_raw_metadata_prefix, action_too_long, has_comments_but_low_extraction, long_input, missing_open_questions, missing_risks, summary_is_metadata_like]
- #6 `SecondLife-201205` (STORM-2147) score=12 reasons=[action_contains_raw_metadata_prefix, action_too_long, missing_open_questions, missing_risks, summary_is_metadata_like, very_long_input]
- #7 `SecondLife-200968` (STORM-2146) score=12 reasons=[action_contains_raw_metadata_prefix, action_too_long, missing_open_questions, missing_risks, summary_is_metadata_like, very_long_input]
- #8 `SecondLife-197623` (STORM-2138) score=12 reasons=[action_contains_raw_metadata_prefix, action_too_long, missing_open_questions, missing_risks, summary_is_metadata_like, very_long_input]
- #9 `Apache-13411703` (ZOOKEEPER-4415) score=12 reasons=[action_contains_raw_metadata_prefix, action_too_long, missing_open_questions, missing_risks, summary_is_metadata_like, very_long_input]
- #10 `JFrog-58017` (TFSAP-7) score=12 reasons=[action_contains_raw_metadata_prefix, action_too_long, missing_open_questions, missing_risks, summary_is_metadata_like, very_long_input]
- #11 `Spring-69854` (XD-3760) score=12 reasons=[action_contains_raw_metadata_prefix, action_too_long, has_comments_but_low_extraction, long_input, missing_open_questions, missing_risks, summary_is_metadata_like]
- #12 `MongoDB-1957815` (WT-8616) score=12 reasons=[action_contains_raw_metadata_prefix, action_too_long, missing_open_questions, missing_risks, summary_is_metadata_like, very_long_input]
- #13 `MongoDB-1957808` (WT-8613) score=12 reasons=[action_contains_raw_metadata_prefix, action_too_long, missing_open_questions, missing_risks, summary_is_metadata_like, very_long_input]
- #14 `MongoDB-1956702` (WT-8611) score=12 reasons=[action_contains_raw_metadata_prefix, action_too_long, has_comments_but_low_extraction, long_input, missing_open_questions, missing_risks, summary_is_metadata_like]
- #15 `MongoDB-1955328` (WT-8601) score=12 reasons=[action_contains_raw_metadata_prefix, action_too_long, missing_open_questions, missing_risks, summary_is_metadata_like, very_long_input]
- #16 `Jira-1836019` (SRCTREEWIN-13736) score=11 reasons=[action_contains_raw_metadata_prefix, action_too_long, long_input, missing_open_questions, missing_risks, summary_is_metadata_like]
- #17 `RedHat-14252155` (XNIO-387) score=11 reasons=[action_contains_raw_metadata_prefix, action_too_long, has_comments_but_low_extraction, missing_open_questions, missing_risks, summary_is_metadata_like]
- #18 `RedHat-13204448` (XNIO-382) score=11 reasons=[action_contains_raw_metadata_prefix, action_too_long, long_input, missing_open_questions, missing_risks, summary_is_metadata_like]
- #19 `JiraEcosystem-86832` (WLC-23) score=11 reasons=[action_contains_raw_metadata_prefix, action_too_long, has_comments_but_low_extraction, missing_open_questions, missing_risks, summary_is_metadata_like]
- #20 `JiraEcosystem-82726` (WLC-21) score=11 reasons=[action_contains_raw_metadata_prefix, action_too_long, has_comments_but_low_extraction, missing_open_questions, missing_risks, summary_is_metadata_like]
- #21 `Qt-329590` (QTWEBSITE-1017) score=11 reasons=[action_contains_raw_metadata_prefix, action_too_long, has_comments_but_low_extraction, missing_open_questions, missing_risks, summary_is_metadata_like]
- #22 `SecondLife-309817` (STORM-2151) score=11 reasons=[action_contains_raw_metadata_prefix, action_too_long, long_input, missing_open_questions, missing_risks, summary_is_metadata_like]
- #23 `SecondLife-200485` (STORM-2145) score=11 reasons=[action_contains_raw_metadata_prefix, action_too_long, long_input, missing_open_questions, missing_risks, summary_is_metadata_like]
- #24 `MariaDB-78716` (CONJ-729) score=11 reasons=[action_contains_raw_metadata_prefix, action_too_long, long_input, missing_open_questions, missing_risks, summary_is_metadata_like]
- #25 `MariaDB-78693` (CONJ-728) score=11 reasons=[action_contains_raw_metadata_prefix, action_too_long, long_input, missing_open_questions, missing_risks, summary_is_metadata_like]
- #26 `Sakai-17344` (YAFT-74) score=11 reasons=[action_contains_raw_metadata_prefix, action_too_long, has_comments_but_low_extraction, missing_open_questions, missing_risks, summary_is_metadata_like]
- #27 `Hyperledger-42432` (TX-54) score=11 reasons=[action_contains_raw_metadata_prefix, action_too_long, has_comments_but_low_extraction, missing_open_questions, missing_risks, summary_is_metadata_like]
- #28 `Sonatype-836541` (OSSRH-76881) score=11 reasons=[action_contains_raw_metadata_prefix, action_too_long, long_input, missing_open_questions, missing_risks, summary_is_metadata_like]
- #29 `JFrog-136478` (TFSAP-24) score=11 reasons=[action_too_long, has_comments_but_low_extraction, missing_open_questions, missing_risks, summary_is_metadata_like, very_long_input]
- #30 `JFrog-92265` (TFSAP-18) score=11 reasons=[action_contains_raw_metadata_prefix, action_too_long, has_comments_but_low_extraction, missing_open_questions, missing_risks, summary_is_metadata_like]