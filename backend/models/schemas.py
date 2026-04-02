from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    text: str


class InventoryItemBase(BaseModel):
    sku: str
    name: str
    description: str = ""
    quantity: int = 0
    reorder_point: int = 0
    supplier_id: int = 0
    unit_price: float = 0.0


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    quantity: int | None = None
    reorder_point: int | None = None
    supplier_id: int | None = None
    unit_price: float | None = None


class InventoryItem(InventoryItemBase):
    id: int


class StockChangeRequest(BaseModel):
    quantity_change: int
    reason: str


class ReportResponse(BaseModel):
    report_type: str
    text: str
