from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRAIN_FILE = ROOT / "ml" / "data" / "final" / "train.jsonl"
DEFAULT_VAL_FILE = ROOT / "ml" / "data" / "final" / "val.jsonl"
DEFAULT_OUTPUT_DIR = ROOT / "ml" / "train" / "artifacts" / "doc2action-lora"


def build_prompt(row: dict[str, Any]) -> str:
    document_type = row.get("document_type", "general")
    input_text = row.get("input_text", "")
    return (
        "You are an information extraction assistant.\n"
        "Extract structured results from the input document.\n"
        "Return strict JSON with keys: summary, action_items, risks, open_questions.\n\n"
        f"Document Type: {document_type}\n"
        "Input Document:\n"
        f"{input_text}\n\n"
        "Output JSON:\n"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a LoRA adapter for Doc2Action.")
    parser.add_argument("--model-name", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--train-file", type=Path, default=DEFAULT_TRAIN_FILE)
    parser.add_argument("--val-file", type=Path, default=DEFAULT_VAL_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--logging-steps", type=int, default=10)
    parser.add_argument("--save-steps", type=int, default=100)
    parser.add_argument("--eval-steps", type=int, default=100)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument(
        "--target-modules",
        default="q_proj,k_proj,v_proj,o_proj,up_proj,down_proj,gate_proj",
        help="Comma-separated module names for LoRA.",
    )
    parser.add_argument("--use-4bit", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--bf16", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--gradient-checkpointing", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument(
        "--save-total-limit",
        type=int,
        default=4,
        help="Keep only the last N checkpoints on disk (0 = keep all).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        import torch
        from datasets import load_dataset
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            DataCollatorForSeq2Seq,
            Trainer,
            TrainingArguments,
            set_seed,
        )
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Missing training dependencies. Install with: "
            "pip install -U transformers datasets peft accelerate bitsandbytes"
        ) from exc

    if not args.train_file.exists() or not args.val_file.exists():
        raise FileNotFoundError(f"Missing train/val files: {args.train_file} / {args.val_file}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    set_seed(args.seed)

    has_cuda = torch.cuda.is_available()
    has_mps = bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
    use_4bit = bool(args.use_4bit and has_cuda)

    quantization_config = None
    if use_4bit:
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16 if args.bf16 else torch.float16,
            bnb_4bit_use_double_quant=True,
        )

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if has_cuda:
        model_dtype = torch.bfloat16 if args.bf16 else torch.float16
    elif has_mps:
        # MPS typically needs fp16 to fit medium models.
        model_dtype = torch.float16
    else:
        model_dtype = torch.float32

    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        quantization_config=quantization_config,
        dtype=model_dtype,
        device_map="auto" if has_cuda else None,
    )
    model.config.use_cache = False
    if args.gradient_checkpointing:
        model.gradient_checkpointing_enable()
    if has_mps:
        model.to("mps")

    if use_4bit:
        model = prepare_model_for_kbit_training(model)

    target_modules = [name.strip() for name in args.target_modules.split(",") if name.strip()]
    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=target_modules,
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    data_files = {"train": str(args.train_file), "validation": str(args.val_file)}
    dataset = load_dataset("json", data_files=data_files)

    def preprocess(row: dict[str, Any]) -> dict[str, Any]:
        """
        Build (prompt + target) so that target tokens always remain in the window and get supervised.

        The previous approach (tokenize full text then mask by separate prompt tokenization) breaks when
        truncation cuts off the entire JSON target: all labels become -100 and eval_loss becomes nan.
        Here we tokenize prompt and target separately, then left-truncate the *prompt* only so the
        answer always has token-level supervision.
        """
        prompt = build_prompt(row)
        target = json.dumps(row["expected"], ensure_ascii=False)

        target_ids = tokenizer(target, add_special_tokens=False)["input_ids"]
        eos_id = tokenizer.eos_token_id
        if eos_id is not None:
            target_ids = target_ids + [eos_id]

        max_len = int(args.max_length)
        # Reserve at least one token for the prompt prefix; keep JSON target supervised.
        max_target = max_len - 1
        if len(target_ids) > max_target:
            target_ids = target_ids[:max_target]

        max_prompt = max_len - len(target_ids)
        if max_prompt < 1:
            raise ValueError("max_length too small to fit prompt and target")

        prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
        if len(prompt_ids) > max_prompt:
            # Keep the beginning of the document; many labels key off leading metadata/context.
            prompt_ids = prompt_ids[:max_prompt]

        input_ids = prompt_ids + target_ids
        labels = [-100] * len(prompt_ids) + list(target_ids)

        return {
            "input_ids": input_ids,
            "attention_mask": [1] * len(input_ids),
            "labels": labels,
        }

    tokenized = dataset.map(
        preprocess,
        remove_columns=dataset["train"].column_names,
        desc="Tokenizing dataset",
    )

    training_args = TrainingArguments(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        warmup_ratio=args.warmup_ratio,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        eval_steps=args.eval_steps,
        eval_strategy="steps",
        save_strategy="steps",
        save_total_limit=(args.save_total_limit if args.save_total_limit > 0 else None),
        bf16=bool(has_cuda and args.bf16),
        fp16=bool(has_cuda and not args.bf16),
        optim="adamw_torch",
        report_to="none",
        seed=args.seed,
        gradient_checkpointing=args.gradient_checkpointing,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        dataloader_pin_memory=bool(has_cuda),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, pad_to_multiple_of=8 if has_cuda else None),
    )

    try:
        trainer.train()
    except RuntimeError as exc:
        message = str(exc).lower()
        if "out of memory" in message:
            raise RuntimeError(
                "Training OOM. Try: lower --max-length (e.g. 512), "
                "keep --batch-size 1, increase --grad-accum, or switch to a smaller base model."
            ) from exc
        raise
    trainer.save_model(str(args.output_dir / "adapter"))
    tokenizer.save_pretrained(str(args.output_dir / "adapter"))

    run_config: dict[str, Any] = {}
    for key, value in vars(args).items():
        run_config[key] = str(value) if isinstance(value, Path) else value
    (args.output_dir / "run_config.json").write_text(
        json.dumps(run_config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Training finished. Adapter saved to: {args.output_dir / 'adapter'}")


if __name__ == "__main__":
    main()
