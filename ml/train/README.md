# LoRA 最小可跑指南

这个目录提供 Doc2Action 的本地 LoRA 微调最小链路：

- `train_lora.py`: 用 `ml/data/final/train.jsonl` + `val.jsonl` 训练 LoRA 适配器
- `infer_lora.py`: 加载底座模型 + LoRA 适配器做单条推理
- `select_best_lora_checkpoint.py`: 对同一 `output_dir` 下每个 `checkpoint-*` 跑离线 `evaluate.py`，按综合分选最优 checkpoint（见下文）

### 标签与 `eval_loss`

训练时对 **prompt 部分 mask 掉（label=-100）**，只对 **JSON 目标**算 loss。若整段序列被截断后只剩 prompt、没有目标 token，验证集上会出现 **`eval_loss` 为 nan**。当前 `train_lora.py` 已改为：**先分别 tokenize prompt 与 target，再仅在过长时对 prompt 做左侧截断**，保证窗口内始终包含可监督的 target token。

### 用离线指标选 checkpoint

`Trainer` 仍会按 `eval_loss` 做 `load_best_model_at_end`，但在小数据上你也可以用业务指标二次确认：

```bash
cd /Users/ganggang/Documents/Doc2Action
. .venv/bin/activate
python ml/train/select_best_lora_checkpoint.py \
  --run-dir ml/train/artifacts/doc2action-lora-v2 \
  --eval-data ml/data/final_v2/val.jsonl
```

会在 `--run-dir` 下生成 `best_checkpoint_by_eval.json`，并打印每个 `checkpoint-*` 的综合分（action/risk/question 的 F1 与 `summary_jaccard` 的平均）。

## 1) 安装依赖

```bash
cd /Users/ganggang/Documents/Doc2Action
. .venv/bin/activate
pip install -U transformers datasets peft accelerate bitsandbytes
```

> 说明：`bitsandbytes` 主要用于 CUDA 机器的 4-bit 训练。若本机不支持，可在训练命令里加 `--no-use-4bit`。

## 2) 启动训练（最小配置）

```bash
cd /Users/ganggang/Documents/Doc2Action
. .venv/bin/activate
python ml/train/train_lora.py \
  --model-name Qwen/Qwen2.5-1.5B-Instruct \
  --train-file ml/data/final/train.jsonl \
  --val-file ml/data/final/val.jsonl \
  --output-dir ml/train/artifacts/doc2action-lora \
  --max-length 2048 \
  --epochs 3 \
  --batch-size 1 \
  --grad-accum 8
```

训练完成后，LoRA 适配器默认输出到：

- `ml/train/artifacts/doc2action-lora/adapter`
- `ml/train/artifacts/doc2action-lora/run_config.json`

## 3) 单条推理验证

```bash
cd /Users/ganggang/Documents/Doc2Action
. .venv/bin/activate
python ml/train/infer_lora.py \
  --base-model Qwen/Qwen2.5-1.5B-Instruct \
  --adapter-dir ml/train/artifacts/doc2action-lora/adapter \
  --document-type meeting_notes \
  --text "会议决定下周发布v1，张三负责联调，风险是接口不稳定。"
```

## 4) 训练参数建议（先跑通再调优）

- 显存紧张：减小 `--max-length` 或增大 `--grad-accum`
- 无 CUDA：加 `--no-use-4bit`，可先小步验证链路
- 对齐更稳：训练时建议固定 `--seed`，每次只改 1-2 个参数
