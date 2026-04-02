import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
from db.sql_handler import SQLHandler

sql = SQLHandler()
print(sql.get_stock("Power Supply"))
print(sql.update_stock("SKU-1001", -5, "Test removal"))
print(sql.generate_report("low_stock"))
