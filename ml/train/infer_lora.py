from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ADAPTER_DIR = ROOT / "ml" / "train" / "artifacts" / "doc2action-lora" / "adapter"


def build_prompt(document_type: str, input_text: str) -> str:
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
    parser = argparse.ArgumentParser(description="Run local inference with a LoRA adapter.")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--adapter-dir", type=Path, default=DEFAULT_ADAPTER_DIR)
    parser.add_argument("--document-type", default="general")
    parser.add_argument("--text", default="")
    parser.add_argument("--input-file", type=Path, default=None, help="Optional text file path as input.")
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.adapter_dir.exists():
        raise FileNotFoundError(f"Adapter directory not found: {args.adapter_dir}")

    if args.input_file is not None:
        input_text = args.input_file.read_text(encoding="utf-8")
    else:
        input_text = args.text
    if not input_text.strip():
        raise ValueError("Please provide --text or --input-file.")

    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Missing inference dependencies. Install with: "
            "pip install -U transformers peft accelerate"
        ) from exc

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        dtype=torch.bfloat16 if torch.cuda.is_available() else None,
        device_map="auto" if torch.cuda.is_available() else None,
    )
    model = PeftModel.from_pretrained(base_model, str(args.adapter_dir))
    model.eval()

    prompt = build_prompt(args.document_type, input_text)
    encoded = tokenizer(prompt, return_tensors="pt")
    if torch.cuda.is_available():
        encoded = {k: v.cuda() for k, v in encoded.items()}

    with torch.no_grad():
        generate_kwargs = {
            "max_new_tokens": args.max_new_tokens,
            "do_sample": args.temperature > 0,
        }
        if args.temperature > 0:
            generate_kwargs["temperature"] = args.temperature
        output = model.generate(**encoded, **generate_kwargs)

    generated = tokenizer.decode(output[0], skip_special_tokens=True)
    answer = generated[len(prompt) :].strip() if generated.startswith(prompt) else generated.strip()

    print("=== Raw Output ===")
    print(answer)
    try:
        parsed = json.loads(answer)
        print("\n=== Parsed JSON ===")
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        print("\n(Output is not strict JSON yet. Consider tightening prompt or using lower temperature.)")


if __name__ == "__main__":
    main()
