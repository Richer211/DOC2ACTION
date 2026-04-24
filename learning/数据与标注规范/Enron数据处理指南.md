# Enron 数据处理指南

> 目标：把本地 Enron 邮件语料转换成 Doc2Action 可用的 seed 数据（弱标注），用于后续人工修订与微调。

---

## 1. 放置位置（你已经完成）

- 压缩包：`ml/data/external/enron/raw/`
- 解压目录：`ml/data/external/enron/extracted/maildir/`

---

## 2. 为什么先“处理再标注”

Enron 原始邮件存在：

- 大量历史引用和转发噪声
- 编码和头信息格式不统一
- 与项目目标字段不直接对应

所以流程应是：

1. 清洗抽样
2. 自动弱标注（可当草稿）
3. 人工复核修订（高质量训练样本）

---

## 3. 一键执行流程

在 `backend` 虚拟环境中执行：

```bash
cd backend
source .venv/bin/activate
python ../scripts/process_enron_pipeline.py
```

将生成：

- `ml/data/external/enron/processed/enron.sample.jsonl`
- `ml/data/external/enron/processed/enron.seed.auto.jsonl`

如需脱敏版 seed（推荐用于共享/训练）：

```bash
python ../scripts/anonymize_seed_jsonl.py \
  --input ../ml/data/external/enron/processed/enron.seed.auto.jsonl \
  --output ../ml/data/external/enron/processed/enron.seed.auto.anonymized.jsonl
```

---

## 4. 脚本说明

- `scripts/sample_enron.py`
  - 从 `maildir` 抽样并清洗邮件正文
  - 输出标准化邮件记录
- `scripts/build_seed_from_enron.py`
  - 基于当前分析器自动生成弱标注 seed
  - 生成结构：summary/action/risk/question
- `scripts/process_enron_pipeline.py`
  - 串联上述两个步骤，方便批处理
- `scripts/anonymize_seed_jsonl.py`
  - 对 seed 数据中的邮箱/电话做统一脱敏

---

## 5. 哪些步骤必须人工标注

自动 seed 只能作为草稿，以下必须人工确认：

- action_items 是否可执行
- risks 是否真实风险而非背景描述
- open_questions 是否为“未决问题”
- summary 是否表达业务结论（而非复述）

建议抽检比例：

- 首轮至少抽检 30%
- 对误差高的类型（如 risks）可提高到 50%

建议人工修订优先级：

1. 先修 `summary`（保证结论清晰）
2. 再修 `action_items`（保证可执行）
3. 最后补 `risks/open_questions`（提升完整度）

---

## 6. 下一步建议

1. 先跑 200 条样本，检查弱标注质量
2. 选 50 条做人工修订，形成第一批高质量训练集
3. 接入 `ml/eval/evaluate.py` 做前后对比
