import argparse
import json
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from trl import SFTTrainer


def build_prompt(example: dict) -> dict:
    prompt = (
        "### Instruction\n"
        f"{example['instruction']}\n\n"
        "### Input\n"
        f"{example.get('input', '')}\n\n"
        "### Response\n"
        f"{example['output']}"
    )
    return {"text": prompt}


def parse_args():
    parser = argparse.ArgumentParser(description="QLoRA fine-tuning pipeline for inventory text-to-SQL")
    parser.add_argument("--model-name", default="meta-llama/Meta-Llama-3-8B-Instruct")
    parser.add_argument("--dataset", default="dataset_sample.jsonl")
    parser.add_argument("--output-dir", default="./lora_output")
    parser.add_argument("--logs-file", default="training_logs.txt")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max-seq-len", type=int, default=512)
    parser.add_argument("--use-4bit", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model_kwargs = {"trust_remote_code": True}
    if args.use_4bit:
        model_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )
        model_kwargs["device_map"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(args.model_name, **model_kwargs)

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)

    dataset = load_dataset("json", data_files=str(dataset_path), split="train")
    dataset = dataset.map(build_prompt)

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        logging_steps=10,
        save_strategy="epoch",
        report_to="none",
        fp16=torch.cuda.is_available(),
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=args.max_seq_len,
        tokenizer=tokenizer,
    )

    trainer.train()
    trainer.save_model(args.output_dir)

    logs_path = Path(args.logs_file)
    with logs_path.open("w", encoding="utf-8") as f:
        for row in trainer.state.log_history:
            f.write(json.dumps(row) + "\n")

    print(f"Saved adapter to: {args.output_dir}")
    print(f"Saved training logs to: {logs_path}")


if __name__ == "__main__":
    main()
