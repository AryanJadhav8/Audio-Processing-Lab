"""
Download Router — serves processed (or original) audio files.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.utils.file_manager import processed_path, uploaded_path

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Download"])


@router.get("/download/{file_id}")
async def download_file(file_id: str) -> FileResponse:
    """
    Download an audio file by its ``file_id``.

    Checks processed directory first, then uploads.
    """
    # Prefer processed MP3
    mp3 = processed_path(file_id, ".mp3")
    if not mp3.exists():
        mp3 = uploaded_path(file_id, ".mp3")
    if not mp3.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")

    logger.info("Serving download: %s", mp3.name)
    return FileResponse(
        path=str(mp3),
        media_type="audio/mpeg",
        filename=f"{file_id}.mp3",
    )
