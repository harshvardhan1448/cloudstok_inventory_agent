import sqlite3
from datetime import datetime
from pathlib import Path


class SQLHandler:
    def __init__(self, db_path="data/inventory.db"):
        default_db = Path(__file__).resolve().parents[2] / "data" / "inventory.db"
        if db_path == "data/inventory.db":
            self.db_path = str(default_db)
        else:
            self.db_path = db_path
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                sku TEXT UNIQUE,
                name TEXT,
                description TEXT,
                quantity INTEGER,
                reorder_point INTEGER,
                supplier_id INTEGER,
                unit_price REAL
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                sku TEXT,
                change INTEGER,
                reason TEXT,
                timestamp TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    def get_stock(self, query: str) -> dict | None:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "SELECT * FROM products WHERE name LIKE ? OR sku = ?",
            (f"%{query}%", query),
        )
        row = c.fetchone()
        conn.close()
        if row:
            return {
                "id": row[0],
                "sku": row[1],
                "name": row[2],
                "quantity": row[4],
                "reorder_point": row[5],
            }
        return None

    def update_stock(self, sku: str, change: int, reason: str) -> int:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE products SET quantity = quantity + ? WHERE sku = ?", (change, sku))
        c.execute(
            "INSERT INTO transactions (sku, change, reason, timestamp) VALUES (?, ?, ?, ?)",
            (sku, change, reason, datetime.now().isoformat()),
        )
        c.execute("SELECT quantity FROM products WHERE sku = ?", (sku,))
        row = c.fetchone()
        conn.commit()
        conn.close()
        if row is None:
            raise ValueError(f"SKU not found: {sku}")
        return int(row[0])

    def generate_report(self, report_type: str) -> str:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if report_type in {"low_stock", "reorder_needed"}:
            c.execute("SELECT sku, name, quantity, reorder_point FROM products WHERE quantity <= reorder_point")
            rows = c.fetchall()
            conn.close()
            if not rows:
                return "No products below reorder point."
            return "LOW STOCK ALERT:\n" + "\n".join(
                [f"SKU: {r[0]} | {r[1]} | Stock: {r[2]} | Reorder Point: {r[3]}" for r in rows]
            )
        if report_type == "full_summary":
            c.execute("SELECT sku, name, quantity, unit_price FROM products")
            rows = c.fetchall()
            conn.close()
            return "FULL INVENTORY:\n" + "\n".join(
                [f"{r[0]} | {r[1]} | Qty: {r[2]} | Price: ${r[3]}" for r in rows]
            )
        if report_type == "transaction_history":
            c.execute("SELECT sku, change, reason, timestamp FROM transactions ORDER BY id DESC LIMIT 50")
            rows = c.fetchall()
            conn.close()
            if not rows:
                return "No transactions found."
            return "TRANSACTIONS:\n" + "\n".join(
                [f"SKU: {r[0]} | Change: {r[1]} | Reason: {r[2]} | Time: {r[3]}" for r in rows]
            )
        conn.close()
        return "Unknown report type."
