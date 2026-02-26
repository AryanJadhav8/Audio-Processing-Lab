"""
Application Configuration Module.

Centralizes all configuration constants and settings for the
Audio Processing Lab backend. No hardcoded paths — everything
is derived from environment variables or computed at runtime.
"""

from pathlib import Path
from tempfile import gettempdir

# ---------------------------------------------------------------------------
# Directory Configuration
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent.parent
TEMP_DIR: Path = Path(gettempdir()) / "audio_processing_lab"
UPLOAD_DIR: Path = TEMP_DIR / "uploads"
PROCESSED_DIR: Path = TEMP_DIR / "processed"
VISUALIZATION_DIR: Path = TEMP_DIR / "visualizations"

# Ensure directories exist at import time
for _dir in (UPLOAD_DIR, PROCESSED_DIR, VISUALIZATION_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Upload Constraints
# ---------------------------------------------------------------------------
MAX_FILE_SIZE_MB: int = 20
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS: set[str] = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}

# ---------------------------------------------------------------------------
# Audio Processing Defaults
# ---------------------------------------------------------------------------
DEFAULT_SAMPLE_RATE: int = 44100

# ---------------------------------------------------------------------------
# File Cleanup
# ---------------------------------------------------------------------------
FILE_TTL_MINUTES: int = 30  # Auto-delete files older than this

# ---------------------------------------------------------------------------
# Effect Parameter Bounds
# ---------------------------------------------------------------------------
PITCH_SHIFT_MIN: float = -12.0
PITCH_SHIFT_MAX: float = 12.0

REVERB_DECAY_MIN: float = 0.1
REVERB_DECAY_MAX: float = 0.9
REVERB_DELAY_MS_MIN: int = 50
REVERB_DELAY_MS_MAX: int = 300

STEREO_DELAY_MS_MIN: int = 5
STEREO_DELAY_MS_MAX: int = 20

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
API_HOST: str = "0.0.0.0"
API_PORT: int = 8000
