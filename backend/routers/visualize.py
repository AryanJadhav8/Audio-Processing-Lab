"""
Visualization Router — serves waveform & spectrogram images.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.services.audio_pipeline import generate_visualizations
from backend.utils.file_manager import visualization_path

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Visualization"])


@router.get("/visualize/{file_id}")
async def visualize(file_id: str, label: str = "") -> dict:
    """
    Generate and return URLs for waveform + spectrogram images.
    """
    try:
        paths = generate_visualizations(file_id, label=label)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("Visualization failed for %s", file_id)
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "file_id": file_id,
        "waveform_url": f"/visualize/image/{file_id}/waveform",
        "spectrogram_url": f"/visualize/image/{file_id}/spectrogram",
    }


@router.get("/visualize/image/{file_id}/{kind}")
async def get_visualization_image(file_id: str, kind: str) -> FileResponse:
    """
    Serve a generated visualization image.

    ``kind`` must be ``'waveform'`` or ``'spectrogram'``.
    """
    if kind not in ("waveform", "spectrogram"):
        raise HTTPException(status_code=400, detail="kind must be 'waveform' or 'spectrogram'")

    path = visualization_path(file_id, kind)
    if not path.exists():
        # Try generating on the fly
        try:
            generate_visualizations(file_id)
        except Exception:
            raise HTTPException(status_code=404, detail="Visualization not found")

    if not path.exists():
        raise HTTPException(status_code=404, detail="Visualization not found")

    return FileResponse(path=str(path), media_type="image/png")
