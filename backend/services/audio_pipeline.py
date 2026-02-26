"""
Audio Pipeline — orchestrates the full processing workflow.

    Upload MP3 → convert to WAV → load → apply effect → normalise
    → save WAV → convert to MP3 → return processed file_id.

This module is the **only** place where file I/O and DSP logic meet.
Routers call the pipeline; the pipeline calls services and utils.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import numpy as np

from backend.config import PROCESSED_DIR, UPLOAD_DIR
from backend.models.schemas import (
    EffectName,
    EightDAudioParams,
    EqualizerParams,
    PitchShiftParams,
    ProcessResponse,
    ReverbParams,
    StereoWidenParams,
    TrimParams,
)
from backend.services.audio_effects import (
    eight_d_audio,
    equalizer,
    peak_normalize,
    pitch_shift,
    reverb,
    reverse_audio,
    stereo_widen,
    trim_audio,
)
from backend.services.visualization import generate_spectrogram, generate_waveform
from backend.utils.audio_converter import (
    load_audio,
    mp3_to_wav,
    save_audio,
    wav_to_mp3,
)
from backend.utils.file_manager import (
    generate_file_id,
    processed_path,
    uploaded_path,
    wav_path_for,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Effect dispatcher
# ---------------------------------------------------------------------------

def _apply_effect(
    signal: np.ndarray,
    sr: int,
    effect: EffectName,
    params: dict,
) -> np.ndarray:
    """
    Dispatch to the correct effect function based on *effect* enum.

    Returns the processed signal (numpy array).
    """
    match effect:
        case EffectName.REVERSE:
            return reverse_audio(signal, sr)

        case EffectName.PITCH_SHIFT:
            validated = PitchShiftParams(**params)
            return pitch_shift(signal, sr, semitones=validated.semitones)

        case EffectName.REVERB:
            validated = ReverbParams(**params)
            return reverb(signal, sr, decay=validated.decay, delay_ms=validated.delay_ms)

        case EffectName.STEREO_WIDEN:
            validated = StereoWidenParams(**params)
            return stereo_widen(
                signal, sr,
                delay_ms=validated.delay_ms,
                gain_diff_db=validated.gain_diff_db,
            )

        case EffectName.TRIM:
            validated = TrimParams(**params)
            return trim_audio(signal, sr, start_time=validated.start_time, end_time=validated.end_time)

        case EffectName.EIGHT_D_AUDIO:
            validated = EightDAudioParams(**params)
            return eight_d_audio(
                signal, sr,
                pan_speed_hz=validated.pan_speed_hz,
                intensity=validated.intensity,
                crossfeed=validated.crossfeed,
            )

        case EffectName.EQUALIZER:
            validated = EqualizerParams(**params)
            band_gains = {
                "sub_bass": validated.sub_bass,
                "bass": validated.bass,
                "low_mid": validated.low_mid,
                "mid": validated.mid,
                "high_mid": validated.high_mid,
                "presence": validated.presence,
                "brilliance": validated.brilliance,
            }
            return equalizer(signal, sr, band_gains_db=band_gains)

        case _:
            raise ValueError(f"Unknown effect: {effect}")


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def process_audio(
    file_id: str,
    effect: EffectName,
    parameters: dict,
) -> ProcessResponse:
    """
    Execute the full audio processing pipeline.

    Steps
    -----
    1. Locate uploaded MP3.
    2. Convert to WAV.
    3. Load with librosa (preserving native sample rate).
    4. Apply the requested effect.
    5. Peak-normalise.
    6. Save processed WAV.
    7. Convert processed WAV back to MP3.
    8. Return ``ProcessResponse``.
    """
    t0 = time.perf_counter()

    # 1. Locate source
    source_mp3 = uploaded_path(file_id, ".mp3")
    if not source_mp3.exists():
        raise FileNotFoundError(f"Uploaded file not found: {file_id}")

    # 2. Convert MP3 → WAV
    source_wav = wav_path_for(file_id, UPLOAD_DIR)
    if not source_wav.exists():
        mp3_to_wav(source_mp3, source_wav)

    # 3. Load audio
    signal, sr = load_audio(source_wav, sr=None, mono=False)

    # 4. Apply effect
    processed_signal = _apply_effect(signal, sr, effect, parameters)

    # 5. Normalise
    processed_signal = peak_normalize(processed_signal)

    # 6. Save processed WAV
    proc_id = generate_file_id()
    proc_wav = wav_path_for(proc_id, PROCESSED_DIR)
    save_audio(processed_signal, sr, proc_wav)

    # 7. Convert WAV → MP3
    proc_mp3 = processed_path(proc_id, ".mp3")
    wav_to_mp3(proc_wav, proc_mp3)

    elapsed = time.perf_counter() - t0
    logger.info(
        "Pipeline complete — effect=%s, time=%.2fs, output=%s",
        effect.value, elapsed, proc_id,
    )

    return ProcessResponse(
        file_id=file_id,
        processed_file_id=proc_id,
        effect=effect.value,
        processing_time_seconds=round(elapsed, 3),
    )


def generate_visualizations(file_id: str, label: str = "") -> dict[str, Path]:
    """
    Generate waveform + spectrogram for a given file_id.

    Looks in both upload and processed directories.

    Returns:
        ``{"waveform": Path, "spectrogram": Path}``
    """
    # Try to find the WAV (prefer processed, fall back to upload)
    wav = wav_path_for(file_id, PROCESSED_DIR)
    if not wav.exists():
        wav = wav_path_for(file_id, UPLOAD_DIR)
    if not wav.exists():
        # Might need conversion from mp3
        mp3_up = uploaded_path(file_id, ".mp3")
        mp3_proc = processed_path(file_id, ".mp3")
        source = mp3_proc if mp3_proc.exists() else mp3_up
        if not source.exists():
            raise FileNotFoundError(f"No audio found for file_id={file_id}")
        wav = wav_path_for(file_id, source.parent)
        mp3_to_wav(source, wav)

    signal, sr = load_audio(wav, sr=None, mono=False)

    waveform_title = f"Waveform{' — ' + label if label else ''}"
    spec_title = f"Spectrogram{' — ' + label if label else ''}"

    return {
        "waveform": generate_waveform(signal, sr, file_id, title=waveform_title),
        "spectrogram": generate_spectrogram(signal, sr, file_id, title=spec_title),
    }
