import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.agent import build_agent
from db.load_documents import ingest
from db.sql_handler import SQLHandler
from models.schemas import (
    InventoryItemCreate,
    InventoryItemUpdate,
    StockChangeRequest,
)

app = FastAPI(title="Cloudstok Inventory Agent")
sql = SQLHandler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    ingest()


agent_executor = build_agent()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@app.get("/")
def root():
    return {
        "service": "Cloudstok Inventory Agent",
        "status": "running",
        "health": "/health",
        "chat": "/chat",
        "docs": "/docs",
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    result = agent_executor.invoke({"input": req.message})

    async def stream_response():
        yield f"data: {json.dumps({'text': result['output']})}\n\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")


@app.get("/inventory")
def list_inventory():
    return {"items": sql.list_products()}


@app.get("/inventory/{sku}")
def get_inventory_item(sku: str):
    item = sql.get_product(sku)
    if item is None:
        raise HTTPException(status_code=404, detail=f"SKU not found: {sku}")
    return item


@app.post("/inventory")
def create_inventory_item(item: InventoryItemCreate):
    try:
        created = sql.create_product(item.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return created


@app.put("/inventory/{sku}")
def update_inventory_item(sku: str, item: InventoryItemUpdate):
    try:
        updated = sql.update_product(sku, item.model_dump(exclude_unset=True))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail=f"SKU not found: {sku}")
    return updated


@app.delete("/inventory/{sku}")
def delete_inventory_item(sku: str):
    deleted = sql.delete_product(sku)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"SKU not found: {sku}")
    return {"deleted": True, "sku": sku}


@app.post("/inventory/{sku}/adjust")
def adjust_inventory_item(sku: str, request: StockChangeRequest):
    try:
        new_quantity = sql.update_stock(sku, request.quantity_change, request.reason)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"sku": sku, "new_quantity": new_quantity, "reason": request.reason}


@app.get("/reports")
def reports():
    return {
        "available_reports": ["low_stock", "reorder_needed", "full_summary", "transaction_history"],
    }


@app.get("/reports/{report_type}")
def report(report_type: str):
    text = sql.generate_report(report_type)
    if text == "Unknown report type.":
        raise HTTPException(status_code=404, detail=text)
    return {"report_type": report_type, "text": text}


@app.get("/health")
def health():
    return {"status": "ok"}
