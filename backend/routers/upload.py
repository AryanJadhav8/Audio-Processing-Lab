"""
Upload Router — handles file ingestion & validation.
"""

from __future__ import annotations

import logging
import shutil

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.models.schemas import UploadResponse
from backend.utils.audio_converter import get_audio_info
from backend.utils.file_manager import (
    generate_file_id,
    uploaded_path,
    validate_extension,
    validate_file_size,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_audio(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload an audio file (MP3, WAV, OGG, FLAC, M4A).

    - Validates extension and size.
    - Saves with a UUID filename.
    - Returns metadata about the uploaded audio.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    # --- validate extension --------------------------------------------------
    try:
        ext = validate_extension(file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # --- validate size -------------------------------------------------------
    contents = await file.read()
    try:
        validate_file_size(len(contents))
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc))

    # --- save ----------------------------------------------------------------
    file_id = generate_file_id()
    dest = uploaded_path(file_id, ext)
    dest.write_bytes(contents)
    logger.info("Uploaded %s → %s (%d bytes)", file.filename, dest.name, len(contents))

    # --- metadata ------------------------------------------------------------
    try:
        info = get_audio_info(dest)
    except Exception as exc:
        logger.error("Failed to read audio info: %s", exc)
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Cannot read audio file: {exc}")

    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        duration_seconds=round(info["duration"], 2),
        sample_rate=info["sample_rate"],
        channels=info["channels"],
    )
