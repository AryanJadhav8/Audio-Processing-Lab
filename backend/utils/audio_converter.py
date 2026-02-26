"""
Audio Converter — MP3 ↔ WAV conversion using pydub + ffmpeg.

All DSP in the project operates on WAV arrays; this module bridges
the gap between user-facing MP3s and the internal representation.
"""

from __future__ import annotations

import logging
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from pydub import AudioSegment

from backend.config import DEFAULT_SAMPLE_RATE

logger = logging.getLogger(__name__)


def mp3_to_wav(mp3_path: Path, wav_path: Path) -> Path:
    """
    Convert an MP3 file to WAV using pydub (ffmpeg under the hood).

    Args:
        mp3_path: Source MP3 file.
        wav_path: Destination WAV file.

    Returns:
        The *wav_path* for convenience.
    """
    logger.info("Converting MP3 → WAV: %s", mp3_path.name)
    audio = AudioSegment.from_mp3(str(mp3_path))
    audio.export(str(wav_path), format="wav")
    return wav_path


def wav_to_mp3(wav_path: Path, mp3_path: Path, bitrate: str = "192k") -> Path:
    """
    Convert a WAV file back to MP3.

    Args:
        wav_path: Source WAV.
        mp3_path: Destination MP3.
        bitrate: Target bitrate (default 192 kbps).

    Returns:
        The *mp3_path*.
    """
    logger.info("Converting WAV → MP3: %s", wav_path.name)
    audio = AudioSegment.from_wav(str(wav_path))
    audio.export(str(mp3_path), format="mp3", bitrate=bitrate)
    return mp3_path


def load_audio(wav_path: Path, sr: int | None = None, mono: bool = False) -> tuple[np.ndarray, int]:
    """
    Load a WAV file via librosa.

    Args:
        wav_path: Path to WAV file.
        sr: Target sample rate (``None`` = native).
        mono: Force mono downmix.

    Returns:
        ``(signal, sample_rate)`` — signal shape is ``(samples,)``
        for mono or ``(channels, samples)`` for stereo.
    """
    y, sr_out = librosa.load(str(wav_path), sr=sr, mono=mono)
    logger.debug(
        "Loaded %s — shape=%s, sr=%d",
        wav_path.name, y.shape, sr_out,
    )
    return y, sr_out


def save_audio(signal: np.ndarray, sr: int, wav_path: Path) -> Path:
    """
    Write a numpy signal to a WAV file.

    Handles both mono ``(samples,)`` and stereo ``(2, samples)``
    layouts.  soundfile expects ``(samples, channels)`` for multichannel,
    so we transpose when necessary.

    Returns:
        The *wav_path*.
    """
    if signal.ndim == 2:
        # librosa uses (channels, samples); soundfile wants (samples, channels)
        signal = signal.T
    sf.write(str(wav_path), signal, sr)
    logger.debug("Saved audio to %s", wav_path.name)
    return wav_path


def get_audio_info(file_path: Path) -> dict:
    """
    Return basic metadata for an audio file.

    Returns:
        dict with keys ``duration``, ``sample_rate``, ``channels``.
    """
    audio = AudioSegment.from_file(str(file_path))
    return {
        "duration": audio.duration_seconds,
        "sample_rate": audio.frame_rate,
        "channels": audio.channels,
    }
