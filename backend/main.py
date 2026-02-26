"""
FastAPI Application Entry-Point.

Wires together all routers, sets up CORS, logging, and a background
task for periodic file cleanup.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import FILE_TTL_MINUTES
from backend.routers import download, process, upload, visualize
from backend.utils.file_manager import cleanup_old_files

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("audio_lab")

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title="🎧 Audio Processing Lab",
    description=(
        "A production-ready audio manipulation API inspired by AudioAlter. "
        "Upload MP3s, apply DSP effects, visualise results, and download."
    ),
    version="1.0.0",
)

# CORS — allow Streamlit frontend (typically on port 8501)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(upload.router)
app.include_router(process.router)
app.include_router(download.router)
app.include_router(visualize.router)


# ---------------------------------------------------------------------------
# Health-check
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
async def health() -> dict:
    """Simple liveness probe."""
    return {"status": "ok", "service": "Audio Processing Lab"}


# ---------------------------------------------------------------------------
# Background cleanup task
# ---------------------------------------------------------------------------
async def _periodic_cleanup() -> None:
    """Delete stale temp files every ``FILE_TTL_MINUTES / 2`` minutes."""
    interval = FILE_TTL_MINUTES * 30  # seconds (half of TTL)
    while True:
        await asyncio.sleep(interval)
        try:
            cleanup_old_files()
        except Exception:
            logger.exception("Cleanup task error")


@app.on_event("startup")
async def _on_startup() -> None:
    logger.info("🚀  Audio Processing Lab API is starting …")
    asyncio.create_task(_periodic_cleanup())


@app.on_event("shutdown")
async def _on_shutdown() -> None:
    logger.info("👋  Shutting down …")
