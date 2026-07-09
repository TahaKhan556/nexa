"""Nexa Backend — FastAPI server for NotebookLM proxy."""
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from session import server_session
from hermes import refine_prompt
from browser import chat_with_notebooklm
from db import init_db, save_message, get_history

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await server_session.initialize()
    logger.info("Nexa backend ready (agent-browser)")
    yield


app = FastAPI(
    title="Nexa API",
    description="NotebookLM proxy — Hermes + agent-browser",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    refined_prompt: str = None


@app.get("/api/status")
async def status():
    valid = await server_session.is_session_valid()
    return {"session_valid": valid, "status": "connected" if valid else "disconnected"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    user_message = req.message
    logger.info(f"User: {user_message[:100]}...")

    save_message("user", user_message)

    hermes_result = await refine_prompt(user_message)
    notebook_id = hermes_result.get("notebook_id", "")
    query = hermes_result.get("query", user_message)
    logger.info(f"Notebook: {notebook_id[:8]}... Query: {query[:80]}...")

    try:
        response = await chat_with_notebooklm(query, notebook_id=notebook_id)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        response = f"Error: {e}"

    logger.info(f"Response: {response[:100]}...")
    save_message("assistant", response, query)

    return ChatResponse(response=response, refined_prompt=query)


@app.get("/api/history")
async def history(limit: int = 50):
    return {"messages": get_history(limit)}


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "nexa-backend", "engine": "agent-browser"}
