"""
Process Router — accepts effect + params, delegates to pipeline.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from backend.models.schemas import ProcessRequest, ProcessResponse
from backend.services.audio_pipeline import process_audio

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Process"])


@router.post("/process", response_model=ProcessResponse)
async def process_effect(request: ProcessRequest) -> ProcessResponse:
    """
    Apply an audio effect to a previously uploaded file.

    Accepts ``file_id``, ``effect`` name, and effect-specific ``parameters``.
    """
    logger.info(
        "Process request — file_id=%s, effect=%s",
        request.file_id, request.effect.value,
    )
    try:
        result = process_audio(
            file_id=request.file_id,
            effect=request.effect,
            parameters=request.parameters,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Processing failed")
        raise HTTPException(status_code=500, detail=f"Processing error: {exc}")

    return result
