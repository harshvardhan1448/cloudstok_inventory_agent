import json
from pathlib import Path


def build_sample_dataset(output_path: str = "dataset_sample.jsonl"):
    records = [
        {
            "instruction": "How many units of SKU-1001 are in stock?",
            "input": "",
            "output": "SELECT quantity FROM products WHERE sku = 'SKU-1001'",
        },
        {
            "instruction": "List all products below reorder point",
            "input": "",
            "output": "SELECT sku, name, quantity, reorder_point FROM products WHERE quantity <= reorder_point",
        },
        {
            "instruction": "Show transaction history for SKU-1004",
            "input": "",
            "output": "SELECT sku, change, reason, timestamp FROM transactions WHERE sku = 'SKU-1004' ORDER BY id DESC",
        },
    ]

    out = Path(output_path)
    with out.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    print(f"Wrote {len(records)} records to {out}")


if __name__ == "__main__":
    build_sample_dataset()
