# Jira 数据处理指南

> 目标：将 The Public Jira Dataset 的 MongoDB dump 转换为 Doc2Action 可用的 seed 数据。

---

## 1. 数据目录

- 压缩包：`ml/data/external/jira/raw/`
- 解压目录：`ml/data/external/jira/extracted/ThePublicJiraDataset/`
- dump 文件：`.../3. DataDump/mongodump-JiraReposAnon.archive`

---

## 2. 环境准备

需要本地 MongoDB 运行环境：

```bash
brew tap mongodb/brew
brew install mongodb-database-tools mongosh mongodb-community
brew services start mongodb/brew/mongodb-community
```

---

## 3. 数据恢复

```bash
mongorestore --gzip \
  --archive="ml/data/external/jira/extracted/ThePublicJiraDataset/3. DataDump/mongodump-JiraReposAnon.archive" \
  --nsFrom "JiraReposAnon.*" \
  --nsTo "JiraReposAnon.*"
```

> 提示：跨版本 restore 会有警告（7.x -> 8.x），用于抽样建种子一般可接受。

---

## 4. 抽样与弱标注

在 `backend` 虚拟环境中执行：

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
python ../scripts/process_jira_pipeline.py
```

输出：

- `ml/data/external/jira/processed/jira.sample.jsonl`
- `ml/data/external/jira/processed/jira.seed.auto.jsonl`

---

## 5. 质量建议

Jira 数据噪声大（模板文本、HTML、历史字段），建议人工修订优先：

1. `summary` 是否抓到核心问题
2. `action_items` 是否可执行
3. `risks` 与 `open_questions` 是否被正确区分

---

## 6. 下一步

1. 将 Jira seed 合并到 curation 批次
2. 做人工修订抽检
3. 与 MeetingBank/Enron/AMI 一起进入 train/val/test 切分
