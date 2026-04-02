# Cloudstok Inventory Agent

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-FF4B4B)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

Cloudstok Inventory Agent is a natural-language inventory assistant for warehouse workflows. It combines a FastAPI backend, a Streamlit UI, SQLite inventory state, and Chroma-based semantic search over product manuals.

## Architecture

```text
USER (Streamlit UI) -> FastAPI backend -> LangChain agent -> SQL tools + Chroma semantic search
```

## Tech Stack
- LLM: Llama 3 8B via Groq API
- Agent Framework: LangChain OpenAI Tools Agent
- Vector DB: ChromaDB
- SQL DB: SQLite
- API: FastAPI
- UI: Streamlit
- Fine-tuning: QLoRA script (PEFT + TRL)

## Setup
1. Copy .env.example to .env and set GROQ_API_KEY.
2. Run: docker-compose up --build
3. Open: http://localhost:8501

## Local Dev (without Docker)
1. Install backend dependencies from backend/requirements.txt
2. Run seed: python backend/db/seed_data.py
3. Start backend from backend/: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
4. Install frontend dependencies from frontend/requirements.txt
5. Start frontend from frontend/: streamlit run app.py --server.port=8501 --server.address=0.0.0.0

## API
- POST /chat with JSON: {"message": "...", "session_id": "default"}
- GET /health

## Fine-tuning
See finetuning/README_finetune.md for dataset prep and training notes.

## Deviations
- /chat endpoint currently uses non-streaming invoke() response for simpler integration.
- Frontend uses standard JSON response parsing from /chat.

## Checklist
- Backend tools and agent wired
- Chroma ingestion script added
- FastAPI + Streamlit app added
- Docker compose stack added
- Fine-tuning pipeline files added
