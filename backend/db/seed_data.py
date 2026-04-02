import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "inventory.db"
DATA_DIR.mkdir(parents=True, exist_ok=True)

products = [
    ("SKU-1001", "Power Supply 220V", "Industrial power supply", 45, 20, 1, 89.99),
    ("SKU-1002", "Industrial Motor 5HP", "Heavy duty motor", 8, 10, 2, 450.00),
    ("SKU-1003", "Heavy Duty Cable 50m", "Armored cable", 120, 30, 1, 34.50),
    ("SKU-1004", "Circuit Breaker 32A", "DIN rail breaker", 5, 15, 3, 22.00),
    ("SKU-1005", "Control Panel Box", "Weatherproof enclosure", 60, 25, 2, 115.00),
]

conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()
c.execute(
    """CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY, sku TEXT UNIQUE, name TEXT, description TEXT,
    quantity INTEGER, reorder_point INTEGER, supplier_id INTEGER, unit_price REAL)"""
)
c.execute(
    """CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY, sku TEXT, change INTEGER, reason TEXT, timestamp TEXT)"""
)
c.executemany(
    "INSERT OR IGNORE INTO products (sku, name, description, quantity, reorder_point, supplier_id, unit_price) VALUES (?,?,?,?,?,?,?)",
    products,
)
conn.commit()
conn.close()
print("Seeded inventory.db with", len(products), "products")
