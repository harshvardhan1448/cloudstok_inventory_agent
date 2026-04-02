# Fine-tuning Notes

This folder demonstrates a QLoRA fine-tuning pipeline for text-to-SQL tasks targeting the inventory schema.

## Files
- finetune_lora.py: CLI training script using PEFT LoRA + TRL SFTTrainer
- prepare_dataset.py: Helper to generate sample JSONL format examples
- dataset_sample.jsonl: Sample training dataset for inventory text-to-SQL
- requirements.txt: Dependencies for the finetuning environment
- training_logs.txt: JSONL training history written by the script
- cloudstok_finetune_lora.ipynb: Separate notebook version kept as a standalone reference

## Suggested Run Environment
Use Google Colab T4 GPU.

## Quick Pipeline

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. (Optional) Regenerate the sample dataset:

```bash
python prepare_dataset.py
```

3. Run LoRA fine-tuning:

```bash
python finetune_lora.py \
	--model-name meta-llama/Meta-Llama-3-8B-Instruct \
	--dataset dataset_sample.jsonl \
	--output-dir lora_output \
	--logs-file training_logs.txt \
	--use-4bit
```

4. Expected outputs:
- `lora_output/` (saved adapter)
- `training_logs.txt` (JSONL with trainer state and loss values)

## Notes
- Use an HF token with Llama access when loading Meta Llama models.
- For quick smoke tests, you can swap to a smaller open model via `--model-name`.
- The notebook in this folder is separate from the main training script and is not required to run finetuning.
- This pipeline is for demonstration and assignment submission evidence.

## Note
Full model training artifacts are not included in this repository due to hardware and storage constraints.
