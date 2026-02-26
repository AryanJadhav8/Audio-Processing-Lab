"""
File Manager — handles UUID naming, path resolution, validation,
and automatic cleanup of stale temporary files.
"""

from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path

from backend.config import (
    ALLOWED_EXTENSIONS,
    FILE_TTL_MINUTES,
    MAX_FILE_SIZE_BYTES,
    PROCESSED_DIR,
    UPLOAD_DIR,
    VISUALIZATION_DIR,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def generate_file_id() -> str:
    """Return a new UUID-4 string for file naming."""
    return uuid.uuid4().hex


def uploaded_path(file_id: str, ext: str = ".mp3") -> Path:
    """Return the canonical path for an uploaded file."""
    return UPLOAD_DIR / f"{file_id}{ext}"


def processed_path(file_id: str, ext: str = ".mp3") -> Path:
    """Return the canonical path for a processed file."""
    return PROCESSED_DIR / f"{file_id}{ext}"


def wav_path_for(file_id: str, directory: Path = UPLOAD_DIR) -> Path:
    """Return the WAV working-copy path inside *directory*."""
    return directory / f"{file_id}.wav"


def visualization_path(file_id: str, kind: str) -> Path:
    """Return path for a visualisation image (kind = 'waveform' | 'spectrogram')."""
    return VISUALIZATION_DIR / f"{file_id}_{kind}.png"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_extension(filename: str) -> str:
    """
    Check that *filename* has an allowed extension.

    Returns:
        The normalised extension (e.g. ``'.mp3'``).

    Raises:
        ValueError: If extension is not allowed.
    """
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return ext


def validate_file_size(size: int) -> None:
    """
    Raise ``ValueError`` if *size* exceeds the upload limit.
    """
    if size > MAX_FILE_SIZE_BYTES:
        mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
        raise ValueError(f"File size exceeds the {mb:.0f} MB limit.")


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def cleanup_old_files() -> int:
    """
    Delete files older than ``FILE_TTL_MINUTES`` from temp dirs.

    Returns:
        Number of files deleted.
    """
    cutoff = time.time() - FILE_TTL_MINUTES * 60
    deleted = 0
    for directory in (UPLOAD_DIR, PROCESSED_DIR, VISUALIZATION_DIR):
        for path in directory.iterdir():
            try:
                if path.is_file() and path.stat().st_mtime < cutoff:
                    path.unlink()
                    deleted += 1
                    logger.debug("Cleaned up: %s", path)
            except OSError as exc:
                logger.warning("Cleanup failed for %s: %s", path, exc)
    if deleted:
        logger.info("Cleaned up %d stale file(s).", deleted)
    return deleted
