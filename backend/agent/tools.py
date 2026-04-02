from langchain.tools import tool

from db.sql_handler import SQLHandler
from db.vector_handler import VectorHandler

sql = SQLHandler()
vec = VectorHandler()


@tool
def check_stock(product_name: str) -> str:
    """Check current stock level of a product by name or SKU."""
    result = sql.get_stock(product_name)
    if result:
        return (
            f"Product: {result['name']} | SKU: {result['sku']} | Stock: {result['quantity']} units "
            f"| Reorder Point: {result['reorder_point']}"
        )
    return f"No product found matching '{product_name}'"


@tool
def update_inventory(sku: str, quantity_change: int, reason: str) -> str:
    """Add or remove units from inventory. Use positive for additions, negative for removals."""
    new_qty = sql.update_stock(sku, quantity_change, reason)
    return f"Updated SKU {sku}: new quantity is {new_qty} units. Reason logged: {reason}"


@tool
def generate_report(report_type: str) -> str:
    """Generate reports. Types: 'low_stock', 'reorder_needed', 'full_summary', 'transaction_history'"""
    return sql.generate_report(report_type)


@tool
def semantic_search(query: str) -> str:
    """Search product manuals and descriptions using natural language. Use for compatibility queries."""
    results = vec.similarity_search(query, k=3)
    return "\n\n".join([f"[{r.metadata.get('source', 'unknown')}]: {r.page_content}" for r in results])
