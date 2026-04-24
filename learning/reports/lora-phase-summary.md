# LoRA 阶段小结（面试可用叙事）

## 目标与结论

- **目标**：在固定数据管线（`final_v2`）上，用 LoRA 让本地小模型学会输出与标注一致的 `summary / action_items / risks / open_questions`，并在 `evaluate.py` 上与规则基线、云端 LLM 可比。
- **当前结论**：在现有指标与数据规模下，**早期对齐较好的 adapter（如 v2）仍常优于后续仅调参、改截断策略的实验**；继续单纯刷分性价比低，更适合把 LoRA 当作「可复现的 Phase C 交付」，把精力转向 **Phase D（RAG）** 与产品化。

## 为什么「新跑未必 beat v2」

1. **数据量小**：几十到百余条级别时，验证/测试方差大，单次指标波动不足以证明模型优劣。
2. **标注风格 vs 指标**：`action_f1` / `summary_jaccard` 对措辞敏感；人工精修 Top30 后，若分布与测试集不一致，整体指标未必同步上涨。
3. **训练细节**：prompt 与推理侧截断（head vs tail）、`max_new_tokens`、label 构造（避免全 `-100` 导致 `eval_loss` 无效）都会影响可比性；需在相同协议下对比。
4. **任务本质**：抽取任务在长文档上更依赖 **检索与上下文裁剪**（RAG），仅靠 LoRA 记忆有限语料，边际收益会快速递减。

## 工程上已稳定交付的内容

- **训练**：`ml/train/train_lora.py`（prompt/target 分词与 label mask、校验 loss 可解释）。
- **选 checkpoint**：`ml/train/select_best_lora_checkpoint.py`（路径解析、相对工程根目录）。
- **评测**：`ml/eval/evaluate.py`（LoRA 路径 truncation、按生成段解码、与后端行为对齐的默认 token 长度）。
- **服务**：`backend/app/main.py` 中 `X-Extractor-Mode: lora` 与可选 RAG/语义切块（Phase D）。

## 建议表述（30 秒版）

「我们完成了端到端 LoRA 管线与小数据评测闭环；实验证明在数据规模与任务设定下，继续调 LoRA 的收益有限，因此将 **RAG（检索增强）** 作为下一阶段主战场，LoRA 作为可选本地抽取器保留。」
