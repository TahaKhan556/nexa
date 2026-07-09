"""Nexa Backend — FastAPI server for NotebookLM proxy."""
import logging
import uuid
import asyncio
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional

from session import server_session
from hermes import refine_prompt
from browser import chat_with_notebooklm
from db import init_db, save_message, get_history
from studio import (
    FeatureType, GenerationStatus, _start_browser, navigate_to_notebook,
    check_notebook_has_sources, add_text_source,
    click_studio_tab, click_audio_overview, dismiss_add_sources_dialog,
    wait_for_audio_player, create_job, update_job, get_job, _jobs
)

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
    notebook_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    refined_prompt: str = None
    feature_type: Optional[str] = None
    content_url: Optional[str] = None
    job_id: Optional[str] = None


class StudioRequest(BaseModel):
    notebook_id: str
    feature_type: str  # briefing, audio, mindmap, video
    custom_prompt: Optional[str] = ""
    format_type: Optional[str] = "brief"  # For audio: brief, deep_dive
    language: Optional[str] = "en"


@app.get("/api/status")
async def status():
    valid = await server_session.is_session_valid()
    return {"session_valid": valid, "status": "connected" if valid else "disconnected"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    user_message = req.message
    logger.info(f"User: {user_message[:100]}...")

    # Check for slash commands
    if user_message.startswith("/"):
        return await handle_slash_command(user_message, req.notebook_id)

    save_message("user", user_message)

    hermes_result = await refine_prompt(user_message)
    notebook_id = req.notebook_id or hermes_result.get("notebook_id", "")
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


async def handle_slash_command(message: str, notebook_id: Optional[str] = None) -> ChatResponse:
    """Handle slash commands like /briefing, /audio, /mindmap, /video."""
    parts = message.split(" ", 1)
    command = parts[0].lower()
    custom_prompt = parts[1] if len(parts) > 1 else ""

    # Parse notebook ID from command if provided
    if not notebook_id and len(parts) > 1:
        # Try to extract notebook ID from the message
        for word in parts[1].split():
            if len(word) > 30 and "-" in word:
                notebook_id = word
                custom_prompt = ""
                break

    if not notebook_id:
        return ChatResponse(
            response="Please specify a notebook. Use /briefing [notebook_id] or select a notebook first.",
            feature_type="error"
        )

    # Map commands to feature types
    command_map = {
        "/briefing": (FeatureType.BRIEFING, "brief"),
        "/audio": (FeatureType.AUDIO, "deep_dive"),
        "/mindmap": (FeatureType.MINDMAP, ""),
        "/video": (FeatureType.VIDEO, "explainer"),
    }

    if command not in command_map:
        return ChatResponse(
            response=f"Unknown command: {command}. Available: /briefing, /audio, /mindmap, /video",
            feature_type="error"
        )

    feature_type, format_type = command_map[command]

    # Create job
    job_id = str(uuid.uuid4())
    job = create_job(job_id, notebook_id, feature_type)

    # Start generation in background
    asyncio.create_task(
        generate_studio_feature(job_id, notebook_id, feature_type, format_type, custom_prompt)
    )

    return ChatResponse(
        response=f"Starting {feature_type.value} generation... This may take a while.",
        feature_type=feature_type.value,
        job_id=job_id
    )


async def generate_studio_feature(
    job_id: str,
    notebook_id: str,
    feature_type: FeatureType,
    format_type: str,
    custom_prompt: str
):
    """Generate a studio feature in the background."""
    try:
        update_job(job_id, status=GenerationStatus.GENERATING.value)
        logger.info(f"Starting {feature_type.value} generation for notebook {notebook_id[:8]}...")

        _start_browser()

        if not await navigate_to_notebook(notebook_id):
            update_job(job_id, status=GenerationStatus.FAILED.value, error="Failed to navigate to notebook")
            return

        if feature_type in [FeatureType.BRIEFING, FeatureType.AUDIO]:
            # Check if notebook has sources
            try:
                has_sources = await check_notebook_has_sources()
            except Exception as e:
                update_job(job_id, status=GenerationStatus.FAILED.value, error=str(e))
                return

            if not has_sources:
                logger.info("Notebook has no sources, adding text source...")
                source_text = custom_prompt or "General knowledge overview"
                await add_text_source(source_text)
                time.sleep(3)

            # Click Studio tab
            await click_studio_tab()
            time.sleep(2)

            # Click Audio Overview button
            await click_audio_overview()
            time.sleep(3)

            # Check if an Add Sources dialog appeared (means notebook was still empty)
            dialog_dismissed = await dismiss_add_sources_dialog()
            if dialog_dismissed:
                logger.info("Add Sources dialog was open — notebook had no sources, adding one now...")
                source_text = custom_prompt or "General knowledge overview"
                await add_text_source(source_text)
                time.sleep(3)
                # Re-click Studio tab and Audio Overview
                await click_studio_tab()
                time.sleep(2)
                await click_audio_overview()
                time.sleep(3)

            # Wait for audio
            audio_url = await wait_for_audio_player(timeout=600, job_id=job_id)
            if audio_url:
                if audio_url == 'audio_generated':
                    update_job(job_id, status=GenerationStatus.READY.value, content_url='audio_generated')
                else:
                    update_job(job_id, status=GenerationStatus.READY.value, content_url=audio_url)
            else:
                update_job(job_id, status=GenerationStatus.FAILED.value, error="Audio generation timed out")

        elif feature_type == FeatureType.VIDEO:
            await click_studio_tab()
            time.sleep(2)
            # Click Video Overview
            result = await _cdp_eval("""
                (function() {
                    var btn = document.querySelector("div[role='button'][aria-label='Video Overview']");
                    if (btn) { btn.click(); return "clicked"; }
                    return "not found";
                })()
            """)
            logger.info(f"Video Overview: {result}")
            time.sleep(2)

            video_url = await wait_for_audio_player(timeout=1800)
            if video_url:
                update_job(job_id, status=GenerationStatus.READY.value, content_url=video_url)
            else:
                update_job(job_id, status=GenerationStatus.FAILED.value, error="Video generation timed out")

    except Exception as e:
        logger.error(f"Studio generation error: {e}")
        update_job(job_id, status=GenerationStatus.FAILED.value, error=str(e))


@app.get("/api/studio/status/{job_id}")
async def studio_status(job_id: str):
    """Check the status of a studio generation job."""
    job = get_job(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    return job


@app.get("/api/studio/audio/{job_id}")
async def serve_audio(job_id: str):
    """Serve a generated audio file."""
    from studio import STUDIO_STORAGE
    # Look for the file with any audio extension
    for ext in [".m4a", ".mp3", ".wav", ".webm"]:
        filepath = STUDIO_STORAGE / f"{job_id}{ext}"
        if filepath.exists():
            media_type = "audio/mp4" if ext == ".m4a" else "audio/mpeg"
            return FileResponse(
                path=str(filepath),
                media_type=media_type,
                filename=f"audio_overview_{job_id[:8]}{ext}",
            )
    return JSONResponse(status_code=404, content={"error": "Audio file not found"})


@app.post("/api/studio/generate")
async def studio_generate(req: StudioRequest):
    """Generate a studio feature."""
    job_id = str(uuid.uuid4())
    job = create_job(job_id, req.notebook_id, FeatureType(req.feature_type))

    asyncio.create_task(
        generate_studio_feature(
            job_id,
            req.notebook_id,
            FeatureType(req.feature_type),
            req.format_type or "brief",
            req.custom_prompt or ""
        )
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "feature_type": req.feature_type,
        "message": f"Starting {req.feature_type} generation..."
    }


@app.get("/api/history")
async def history(limit: int = 50):
    return {"messages": get_history(limit)}


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "nexa-backend", "engine": "agent-browser"}
