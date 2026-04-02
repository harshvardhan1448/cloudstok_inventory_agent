# Fine-tuning Notes

This folder demonstrates a QLoRA fine-tuning pipeline for text-to-SQL tasks targeting the inventory schema.

## Files
- finetune_lora.py: Training script using PEFT LoRA + TRL SFTTrainer
- prepare_dataset.py: Helper to generate sample JSONL format examples
- dataset_sample.jsonl: Small sample dataset
- training_logs.txt: Place training loss logs after Colab run

## Suggested Run Environment
Use Google Colab T4 GPU.

## Note
Full model training artifacts are not included in this repository due to hardware and storage constraints.
