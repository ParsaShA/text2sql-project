"""FastAPI service exposing the LangGraph Text-to-SQL agent.

Run:  uvicorn app.main:app --reload
Docs: http://127.0.0.1:8000/docs
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from . import config
from .agent import build_graph, run_agent
from .db import get_schema_info
from .schemas import QueryRequest, QueryResponse

STATE: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not config.DB_PATH.exists():
        raise RuntimeError(f"{config.DB_PATH} not found. Run `python create_table.py` first.")
    STATE["graph"] = build_graph()          # compiled once, reused for every request
    yield
    STATE.clear()


app = FastAPI(title="Text-to-SQL Agent (LangChain + LangGraph)", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "model": config.LLM_MODEL, "db": str(config.DB_PATH.name)}


@app.get("/schema")
def schema():
    return {"schema": get_schema_info()}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    try:
        final = run_agent(STATE["graph"], req.question, req.max_syntactic_attempts)
    except Exception as exc:  # LLM/network/auth errors
        raise HTTPException(status_code=502, detail=f"Agent error: {type(exc).__name__}: {exc}")

    result = final.get("result") or {"columns": [], "rows": []}
    ok = final.get("status") == "success"
    return QueryResponse(
        status=final.get("status", "failed"),
        question=req.question,
        answer=final.get("answer"),
        sql=final.get("sql"),
        columns=result["columns"] if ok else [],
        rows=result["rows"] if ok else [],
        syntactic_attempts=final.get("attempts", 0),
        semantic_correction_applied=final.get("semantic_applied", False),
        trace=final.get("trace", []),
    )


_PAGE = Path(__file__).with_name("index.html")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index():
    return _PAGE.read_text(encoding="utf-8")
