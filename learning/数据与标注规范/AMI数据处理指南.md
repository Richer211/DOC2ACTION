# AMI 数据处理指南

> 目标：把 AMI 会议转录语料（words XML）转换成 Doc2Action 可用的 seed 数据，用于后续人工修订与微调。

---

## 1. 数据目录约定

- 压缩包：`ml/data/external/ami/raw/`
- 解压目录：`ml/data/external/ami/extracted/ami_public_manual_1.6.2/`
- 关键源目录：`.../words/*.words.xml`

---

## 2. 执行流程

在 `backend` 虚拟环境中执行：

```bash
cd backend
source .venv/bin/activate
python ../scripts/process_ami_pipeline.py
```

生成文件：

- `ml/data/external/ami/processed/ami.sample.jsonl`
- `ml/data/external/ami/processed/ami.seed.auto.jsonl`

---

## 3. 脚本说明

- `scripts/sample_ami.py`
  - 解析 `words.xml`，重建可读 transcript
  - 输出 meeting_id、speaker、文本内容
- `scripts/build_seed_from_ami.py`
  - 调用当前分析器生成弱标注 seed
  - 目标字段：summary/action/risk/question
- `scripts/process_ami_pipeline.py`
  - 一键串联处理流程

---

## 4. 数据特性与注意事项

- AMI 是口语化会议语料，存在大量停顿词与口语重复
- 自动弱标注可快速起步，但精度有限
- 建议优先人工修订：
  1. summary 可读性
  2. action_items 执行性
  3. risks/open_questions 完整性

---

## 5. 推荐下一步

1. 先跑 200 条样本生成弱标注
2. 抽 50 条做人工修订，形成 `ami.curated.v1`
3. 与 Enron 修订集混合，构建第一版微调训练集
