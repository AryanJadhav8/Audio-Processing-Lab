"""
Audio Effects Service — pure DSP functions.

Every function here is **pure**: it takes a numpy signal + sample rate,
returns a transformed numpy signal.  No file I/O, no HTTP, no side-effects.
"""

from __future__ import annotations

import logging

import librosa
import numpy as np
from scipy.signal import fftconvolve

logger = logging.getLogger(__name__)


# ==========================================================================
# Normalisation (shared utility)
# ==========================================================================

def peak_normalize(signal: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
    """
    Peak-normalise *signal* so its maximum absolute value equals *target_peak*.

    Prevents clipping while maximising loudness.
    """
    peak = np.max(np.abs(signal))
    if peak == 0:
        return signal
    return signal * (target_peak / peak)


# ==========================================================================
# 1. Reverse Audio
# ==========================================================================

def reverse_audio(signal: np.ndarray, sr: int) -> np.ndarray:
    """
    Reverse the audio signal along the time axis.

    Handles both mono ``(samples,)`` and stereo ``(2, samples)`` layouts.
    """
    logger.info("Applying: Reverse Audio")
    if signal.ndim == 1:
        return signal[::-1].copy()
    # Stereo — reverse along the samples axis (axis=1)
    return signal[:, ::-1].copy()


# ==========================================================================
# 2. Pitch Shift
# ==========================================================================

def pitch_shift(
    signal: np.ndarray,
    sr: int,
    semitones: float = 0.0,
) -> np.ndarray:
    """
    Shift pitch by *semitones* while preserving duration.

    Uses ``librosa.effects.pitch_shift``.
    """
    logger.info("Applying: Pitch Shift (%+.1f semitones)", semitones)
    if signal.ndim == 1:
        shifted = librosa.effects.pitch_shift(y=signal, sr=sr, n_steps=semitones)
    else:
        # Process each channel independently
        channels = [
            librosa.effects.pitch_shift(y=signal[ch], sr=sr, n_steps=semitones)
            for ch in range(signal.shape[0])
        ]
        shifted = np.stack(channels, axis=0)
    return peak_normalize(shifted)


# ==========================================================================
# 3. Reverb (Echo-based)
# ==========================================================================

def reverb(
    signal: np.ndarray,
    sr: int,
    decay: float = 0.5,
    delay_ms: int = 100,
) -> np.ndarray:
    """
    Simple echo-based reverb.

    Algorithm
    ---------
    1. Compute delay in samples.
    2. Create a delayed copy scaled by *decay*.
    3. Add multiple reflections (up to 5) with exponentially decreasing gain.
    4. Mix with original and peak-normalise.
    """
    logger.info("Applying: Reverb (decay=%.2f, delay=%dms)", decay, delay_ms)
    delay_samples = int(sr * delay_ms / 1000)
    num_reflections = 5

    if signal.ndim == 1:
        out_length = len(signal) + delay_samples * num_reflections
        output = np.zeros(out_length, dtype=np.float32)
        output[: len(signal)] = signal
        for i in range(1, num_reflections + 1):
            offset = delay_samples * i
            gain = decay ** i
            end = offset + len(signal)
            if end > out_length:
                end = out_length
            output[offset:end] += signal[: end - offset] * gain
    else:
        channels, length = signal.shape
        out_length = length + delay_samples * num_reflections
        output = np.zeros((channels, out_length), dtype=np.float32)
        output[:, :length] = signal
        for i in range(1, num_reflections + 1):
            offset = delay_samples * i
            gain = decay ** i
            end = offset + length
            if end > out_length:
                end = out_length
            output[:, offset:end] += signal[:, : end - offset] * gain

    return peak_normalize(output)


# ==========================================================================
# 4. 3-D Audio / Stereo Widening
# ==========================================================================

def stereo_widen(
    signal: np.ndarray,
    sr: int,
    delay_ms: int = 10,
    gain_diff_db: float = 1.5,
) -> np.ndarray:
    """
    Widen the stereo image using inter-channel delay and gain difference.

    Steps
    -----
    1. Convert mono to stereo if necessary.
    2. Apply a small delay (zero-padding) to the right channel.
    3. Apply a slight gain reduction to the right channel.
    4. Recombine and normalise.
    """
    logger.info(
        "Applying: Stereo Widen (delay=%dms, gain_diff=%.1fdB)",
        delay_ms, gain_diff_db,
    )
    # Ensure stereo
    if signal.ndim == 1:
        signal = np.stack([signal, signal.copy()], axis=0)

    delay_samples = int(sr * delay_ms / 1000)
    gain_factor = 10 ** (-gain_diff_db / 20)

    left = signal[0]
    right = signal[1]

    # Apply delay to right channel (prepend zeros)
    right_delayed = np.concatenate([np.zeros(delay_samples, dtype=np.float32), right])
    # Pad left to match length
    left_padded = np.concatenate([left, np.zeros(delay_samples, dtype=np.float32)])

    # Apply slight gain diff
    right_delayed *= gain_factor

    # Apply subtle phase inversion on a portion for widening feel
    mid = (left_padded + right_delayed) / 2
    side = (left_padded - right_delayed) / 2
    # Boost side signal slightly for wider image
    side *= 1.3

    new_left = mid + side
    new_right = mid - side

    output = np.stack([new_left, new_right], axis=0)
    return peak_normalize(output)


# ==========================================================================
# 5. Trim / Cut
# ==========================================================================

def trim_audio(
    signal: np.ndarray,
    sr: int,
    start_time: float = 0.0,
    end_time: float | None = None,
) -> np.ndarray:
    """
    Slice the audio between *start_time* and *end_time* (seconds).

    Validates that ``start_time < end_time`` and both are within duration.
    """
    if signal.ndim == 1:
        total_samples = len(signal)
    else:
        total_samples = signal.shape[1]

    duration = total_samples / sr

    if end_time is None:
        end_time = duration

    # Validation
    if start_time < 0:
        raise ValueError("start_time must be >= 0")
    if end_time > duration:
        raise ValueError(
            f"end_time ({end_time:.2f}s) exceeds duration ({duration:.2f}s)"
        )
    if start_time >= end_time:
        raise ValueError("start_time must be less than end_time")

    start_sample = int(start_time * sr)
    end_sample = int(end_time * sr)

    logger.info(
        "Applying: Trim [%.2fs – %.2fs] (samples %d–%d)",
        start_time, end_time, start_sample, end_sample,
    )

    if signal.ndim == 1:
        return signal[start_sample:end_sample].copy()
    return signal[:, start_sample:end_sample].copy()


# ==========================================================================
# 6. 8D Audio (Auto-Panning)
# ==========================================================================

def eight_d_audio(
    signal: np.ndarray,
    sr: int,
    pan_speed_hz: float = 0.15,
    intensity: float = 0.8,
    crossfeed: float = 0.3,
) -> np.ndarray:
    """
    Create an 8D audio effect that pans sound around the listener's head.

    Algorithm
    ---------
    1. Convert mono to stereo if needed.
    2. Generate a sinusoidal panning envelope at *pan_speed_hz*.
    3. Apply the panning curve to left and right channels.
    4. Add crossfeed so the pan isn't 100% hard (more natural).
    5. Peak-normalise.

    Parameters
    ----------
    pan_speed_hz : float
        How many full L→R→L rotations per second (0.05–1.0).
    intensity : float
        Depth of the panning effect (0.0 = none, 1.0 = full).
    crossfeed : float
        How much of each channel bleeds into the other (0.0–0.6).
    """
    logger.info(
        "Applying: 8D Audio (speed=%.2fHz, intensity=%.1f, crossfeed=%.1f)",
        pan_speed_hz, intensity, crossfeed,
    )

    # Ensure stereo
    if signal.ndim == 1:
        signal = np.stack([signal, signal.copy()], axis=0)

    num_samples = signal.shape[1]

    # Create sinusoidal panning envelope (0 = full left, 1 = full right)
    t = np.arange(num_samples, dtype=np.float32) / sr
    pan_curve = 0.5 + 0.5 * np.sin(2 * np.pi * pan_speed_hz * t)

    # Scale by intensity (1.0 = pan_curve as-is, 0.0 = stays at 0.5 center)
    pan_curve = 0.5 + intensity * (pan_curve - 0.5)

    # Compute per-channel gains using equal-power panning law
    right_gain = np.sqrt(pan_curve)
    left_gain = np.sqrt(1.0 - pan_curve)

    # Mix original stereo content (center it first)
    mono_mix = (signal[0] + signal[1]) / 2.0

    # Apply panning
    left_out = mono_mix * left_gain
    right_out = mono_mix * right_gain

    # Add crossfeed for more natural feel
    if crossfeed > 0:
        left_out = left_out * (1.0 - crossfeed) + right_out * crossfeed
        right_out = right_out * (1.0 - crossfeed) + left_out * crossfeed

    output = np.stack([left_out, right_out], axis=0)
    return peak_normalize(output)


# ==========================================================================
# 7. Equalizer (Parametric Biquad)
# ==========================================================================

def equalizer(
    signal: np.ndarray,
    sr: int,
    band_gains_db: dict[str, float] | None = None,
) -> np.ndarray:
    """
    7-band parametric equalizer using cascaded biquad filters.

    Each band is a peaking EQ filter centred at a standard frequency.
    Gain is specified in dB (-12 to +12).

    Bands
    -----
    - ``sub_bass``   : 60 Hz
    - ``bass``       : 170 Hz
    - ``low_mid``    : 500 Hz
    - ``mid``        : 1000 Hz
    - ``high_mid``   : 3000 Hz
    - ``presence``   : 6000 Hz
    - ``brilliance`` : 12000 Hz

    Parameters
    ----------
    band_gains_db : dict
        Mapping of band name → gain in dB.  Bands not specified
        default to 0 dB (no change).
    """
    from scipy.signal import sosfilt

    # Standard EQ band centre frequencies
    BANDS: dict[str, float] = {
        "sub_bass": 60.0,
        "bass": 170.0,
        "low_mid": 500.0,
        "mid": 1000.0,
        "high_mid": 3000.0,
        "presence": 6000.0,
        "brilliance": 12000.0,
    }

    if band_gains_db is None:
        band_gains_db = {}

    logger.info("Applying: Equalizer — gains=%s", band_gains_db)

    def _peaking_eq_sos(
        freq: float, gain_db: float, q: float, fs: int
    ) -> np.ndarray:
        """Design a peaking EQ second-order section."""
        A = 10 ** (gain_db / 40.0)
        w0 = 2 * np.pi * freq / fs
        alpha = np.sin(w0) / (2.0 * q)

        b0 = 1 + alpha * A
        b1 = -2 * np.cos(w0)
        b2 = 1 - alpha * A
        a0 = 1 + alpha / A
        a1 = -2 * np.cos(w0)
        a2 = 1 - alpha / A

        # Normalise
        return np.array([b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0])

    # Build cascaded SOS array
    sos_sections = []
    for band_name, centre_freq in BANDS.items():
        gain = band_gains_db.get(band_name, 0.0)
        if abs(gain) < 0.01:
            continue  # skip flat bands for efficiency
        # Clamp frequency to Nyquist
        if centre_freq >= sr / 2:
            continue
        sos = _peaking_eq_sos(centre_freq, gain, q=1.4, fs=sr)
        sos_sections.append(sos)

    if not sos_sections:
        logger.info("All EQ bands flat — returning original signal")
        return signal.copy()

    sos_array = np.array(sos_sections)

    # Apply to each channel
    if signal.ndim == 1:
        output = sosfilt(sos_array, signal).astype(np.float32)
    else:
        channels = []
        for ch in range(signal.shape[0]):
            filtered = sosfilt(sos_array, signal[ch]).astype(np.float32)
            channels.append(filtered)
        output = np.stack(channels, axis=0)

    return peak_normalize(output)
