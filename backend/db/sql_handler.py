import sqlite3
from datetime import datetime
from pathlib import Path

from db.path_utils import find_data_path


class SQLHandler:
    def __init__(self, db_path="data/inventory.db"):
        default_db = find_data_path("inventory.db")
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

    def list_products(self) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "SELECT id, sku, name, description, quantity, reorder_point, supplier_id, unit_price FROM products ORDER BY id"
        )
        rows = c.fetchall()
        conn.close()
        return [
            {
                "id": row[0],
                "sku": row[1],
                "name": row[2],
                "description": row[3],
                "quantity": row[4],
                "reorder_point": row[5],
                "supplier_id": row[6],
                "unit_price": row[7],
            }
            for row in rows
        ]

    def get_product(self, sku: str) -> dict | None:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "SELECT id, sku, name, description, quantity, reorder_point, supplier_id, unit_price FROM products WHERE sku = ?",
            (sku,),
        )
        row = c.fetchone()
        conn.close()
        if row is None:
            return None
        return {
            "id": row[0],
            "sku": row[1],
            "name": row[2],
            "description": row[3],
            "quantity": row[4],
            "reorder_point": row[5],
            "supplier_id": row[6],
            "unit_price": row[7],
        }

    def create_product(self, product: dict) -> dict:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO products (sku, name, description, quantity, reorder_point, supplier_id, unit_price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product["sku"],
                product["name"],
                product.get("description", ""),
                int(product.get("quantity", 0)),
                int(product.get("reorder_point", 0)),
                int(product.get("supplier_id", 0)),
                float(product.get("unit_price", 0.0)),
            ),
        )
        conn.commit()
        created = self.get_product(product["sku"])
        conn.close()
        if created is None:
            raise ValueError(f"Failed to create product: {product['sku']}")
        return created

    def update_product(self, sku: str, updates: dict) -> dict | None:
        current = self.get_product(sku)
        if current is None:
            return None

        merged = {**current, **{key: value for key, value in updates.items() if value is not None}}
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """
            UPDATE products
            SET name = ?, description = ?, quantity = ?, reorder_point = ?, supplier_id = ?, unit_price = ?
            WHERE sku = ?
            """,
            (
                merged["name"],
                merged.get("description", ""),
                int(merged.get("quantity", 0)),
                int(merged.get("reorder_point", 0)),
                int(merged.get("supplier_id", 0)),
                float(merged.get("unit_price", 0.0)),
                sku,
            ),
        )
        conn.commit()
        conn.close()
        return self.get_product(sku)

    def delete_product(self, sku: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM products WHERE sku = ?", (sku,))
        deleted = c.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def update_stock(self, sku: str, change: int, reason: str) -> int:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT quantity FROM products WHERE sku = ?", (sku,))
        current_row = c.fetchone()
        if current_row is None:
            conn.close()
            raise ValueError(f"SKU not found: {sku}")
        c.execute("UPDATE products SET quantity = quantity + ? WHERE sku = ?", (change, sku))
        c.execute(
            "INSERT INTO transactions (sku, change, reason, timestamp) VALUES (?, ?, ?, ?)",
            (sku, change, reason, datetime.now().isoformat()),
        )
        c.execute("SELECT quantity FROM products WHERE sku = ?", (sku,))
        row = c.fetchone()
        conn.commit()
        conn.close()
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
