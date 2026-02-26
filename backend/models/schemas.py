"""
Pydantic Schemas for request / response validation.

Every API contract is defined here so that routers stay thin
and validation is centralised.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class EffectName(str, Enum):
    """Supported audio effects."""
    REVERSE = "reverse"
    PITCH_SHIFT = "pitch_shift"
    REVERB = "reverb"
    STEREO_WIDEN = "stereo_widen"
    TRIM = "trim"
    EIGHT_D_AUDIO = "eight_d_audio"
    EQUALIZER = "equalizer"


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------
class ProcessRequest(BaseModel):
    """Body of POST /process."""
    file_id: str = Field(..., description="UUID of the uploaded file")
    effect: EffectName = Field(..., description="Effect to apply")
    parameters: dict = Field(
        default_factory=dict,
        description="Effect-specific parameters",
    )


class TrimParams(BaseModel):
    """Validated trim parameters."""
    start_time: float = Field(..., ge=0, description="Start in seconds")
    end_time: float = Field(..., gt=0, description="End in seconds")


class PitchShiftParams(BaseModel):
    """Validated pitch-shift parameters."""
    semitones: float = Field(
        0.0, ge=-12.0, le=12.0,
        description="Semitones to shift (-12 to +12)",
    )


class ReverbParams(BaseModel):
    """Validated reverb parameters."""
    decay: float = Field(0.5, ge=0.1, le=0.9, description="Decay factor")
    delay_ms: int = Field(100, ge=50, le=300, description="Delay in ms")


class StereoWidenParams(BaseModel):
    """Validated 3-D / stereo-widening parameters."""
    delay_ms: int = Field(10, ge=5, le=20, description="Inter-channel delay ms")
    gain_diff_db: float = Field(1.5, ge=0.0, le=6.0, description="Gain diff dB")


class EightDAudioParams(BaseModel):
    """Validated 8D audio parameters."""
    pan_speed_hz: float = Field(0.15, ge=0.05, le=1.0, description="Panning speed in Hz")
    intensity: float = Field(0.8, ge=0.1, le=1.0, description="Pan intensity")
    crossfeed: float = Field(0.3, ge=0.0, le=0.6, description="Crossfeed amount")


class EqualizerParams(BaseModel):
    """Validated equalizer parameters — 7-band gains in dB."""
    sub_bass: float = Field(0.0, ge=-12.0, le=12.0, description="60 Hz gain dB")
    bass: float = Field(0.0, ge=-12.0, le=12.0, description="170 Hz gain dB")
    low_mid: float = Field(0.0, ge=-12.0, le=12.0, description="500 Hz gain dB")
    mid: float = Field(0.0, ge=-12.0, le=12.0, description="1 kHz gain dB")
    high_mid: float = Field(0.0, ge=-12.0, le=12.0, description="3 kHz gain dB")
    presence: float = Field(0.0, ge=-12.0, le=12.0, description="6 kHz gain dB")
    brilliance: float = Field(0.0, ge=-12.0, le=12.0, description="12 kHz gain dB")


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------
class UploadResponse(BaseModel):
    """Returned after a successful upload."""
    file_id: str
    filename: str
    duration_seconds: float
    sample_rate: int
    channels: int
    message: str = "Upload successful"


class ProcessResponse(BaseModel):
    """Returned after processing completes."""
    file_id: str
    processed_file_id: str
    effect: str
    processing_time_seconds: float
    message: str = "Processing complete"


class ErrorResponse(BaseModel):
    """Standard error envelope."""
    detail: str


class VisualizationResponse(BaseModel):
    """Returned visualization metadata."""
    file_id: str
    waveform_url: str
    spectrogram_url: str
