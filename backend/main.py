from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.agent import build_agent
from db.load_documents import ingest

app = FastAPI(title="Cloudstok Inventory Agent")

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
    return {"text": result["output"]}


@app.get("/health")
def health():
    return {"status": "ok"}
