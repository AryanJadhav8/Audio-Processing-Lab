"""
Unit Tests for Audio Effects.

Covers every effect with mono, stereo, and edge-case inputs.
Run with:  python -m pytest backend/tests/test_effects.py -v
"""

from __future__ import annotations

import numpy as np
import pytest

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

SR = 22050  # sample rate used in tests


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mono_signal(duration: float = 1.0) -> np.ndarray:
    """Generate a 440 Hz sine wave (mono)."""
    t = np.linspace(0, duration, int(SR * duration), endpoint=False)
    return (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)


def _stereo_signal(duration: float = 1.0) -> np.ndarray:
    """Generate a stereo signal (2, samples)."""
    mono = _mono_signal(duration)
    return np.stack([mono, mono * 0.8], axis=0)


# ---------------------------------------------------------------------------
# Tests: peak_normalize
# ---------------------------------------------------------------------------

class TestPeakNormalize:
    def test_normalizes_to_target(self) -> None:
        sig = np.array([0.25, -0.5, 0.1], dtype=np.float32)
        out = peak_normalize(sig, target_peak=1.0)
        assert np.isclose(np.max(np.abs(out)), 1.0, atol=1e-6)

    def test_silent_signal_unchanged(self) -> None:
        sig = np.zeros(100, dtype=np.float32)
        out = peak_normalize(sig)
        np.testing.assert_array_equal(out, sig)


# ---------------------------------------------------------------------------
# Tests: reverse_audio
# ---------------------------------------------------------------------------

class TestReverseAudio:
    def test_mono_reverse(self) -> None:
        sig = _mono_signal(0.5)
        out = reverse_audio(sig, SR)
        np.testing.assert_array_almost_equal(out, sig[::-1])

    def test_stereo_reverse(self) -> None:
        sig = _stereo_signal(0.5)
        out = reverse_audio(sig, SR)
        np.testing.assert_array_almost_equal(out, sig[:, ::-1])

    def test_double_reverse_identity(self) -> None:
        sig = _mono_signal(0.2)
        out = reverse_audio(reverse_audio(sig, SR), SR)
        np.testing.assert_array_almost_equal(out, sig)


# ---------------------------------------------------------------------------
# Tests: pitch_shift
# ---------------------------------------------------------------------------

class TestPitchShift:
    def test_zero_shift_preserves_length(self) -> None:
        sig = _mono_signal(0.5)
        out = pitch_shift(sig, SR, semitones=0)
        assert len(out) == len(sig)

    def test_shift_returns_same_shape(self) -> None:
        sig = _mono_signal(0.5)
        out = pitch_shift(sig, SR, semitones=3)
        assert out.shape == sig.shape

    def test_stereo_shift(self) -> None:
        sig = _stereo_signal(0.5)
        out = pitch_shift(sig, SR, semitones=-2)
        assert out.shape == sig.shape


# ---------------------------------------------------------------------------
# Tests: reverb
# ---------------------------------------------------------------------------

class TestReverb:
    def test_output_longer_than_input(self) -> None:
        sig = _mono_signal(0.5)
        out = reverb(sig, SR, decay=0.5, delay_ms=100)
        assert len(out) > len(sig)

    def test_stereo_reverb(self) -> None:
        sig = _stereo_signal(0.5)
        out = reverb(sig, SR, decay=0.3, delay_ms=50)
        assert out.shape[0] == 2
        assert out.shape[1] > sig.shape[1]


# ---------------------------------------------------------------------------
# Tests: stereo_widen
# ---------------------------------------------------------------------------

class TestStereoWiden:
    def test_mono_becomes_stereo(self) -> None:
        sig = _mono_signal(0.5)
        out = stereo_widen(sig, SR)
        assert out.ndim == 2
        assert out.shape[0] == 2

    def test_stereo_stays_stereo(self) -> None:
        sig = _stereo_signal(0.5)
        out = stereo_widen(sig, SR)
        assert out.shape[0] == 2

    def test_channels_differ(self) -> None:
        sig = _mono_signal(0.5)
        out = stereo_widen(sig, SR, delay_ms=15, gain_diff_db=3.0)
        # Channels should not be identical due to delay + gain diff
        assert not np.allclose(out[0], out[1])


# ---------------------------------------------------------------------------
# Tests: trim_audio
# ---------------------------------------------------------------------------

class TestTrimAudio:
    def test_trim_mono(self) -> None:
        sig = _mono_signal(2.0)
        out = trim_audio(sig, SR, start_time=0.5, end_time=1.5)
        expected_samples = int(1.0 * SR)
        assert abs(len(out) - expected_samples) <= 1

    def test_trim_stereo(self) -> None:
        sig = _stereo_signal(2.0)
        out = trim_audio(sig, SR, start_time=0.0, end_time=1.0)
        assert out.shape[0] == 2
        assert abs(out.shape[1] - SR) <= 1

    def test_invalid_range(self) -> None:
        sig = _mono_signal(1.0)
        with pytest.raises(ValueError, match="start_time must be less"):
            trim_audio(sig, SR, start_time=0.8, end_time=0.2)

    def test_end_exceeds_duration(self) -> None:
        sig = _mono_signal(1.0)
        with pytest.raises(ValueError, match="exceeds duration"):
            trim_audio(sig, SR, start_time=0.0, end_time=5.0)

    def test_short_audio(self) -> None:
        """Edge case: very short audio (50ms)."""
        sig = _mono_signal(0.05)
        out = trim_audio(sig, SR, start_time=0.0, end_time=0.03)
        expected = int(0.03 * SR)
        assert abs(len(out) - expected) <= 1


# ---------------------------------------------------------------------------
# Tests: eight_d_audio
# ---------------------------------------------------------------------------

class TestEightDAudio:
    def test_mono_becomes_stereo(self) -> None:
        sig = _mono_signal(0.5)
        out = eight_d_audio(sig, SR)
        assert out.ndim == 2
        assert out.shape[0] == 2

    def test_stereo_input(self) -> None:
        sig = _stereo_signal(0.5)
        out = eight_d_audio(sig, SR)
        assert out.shape[0] == 2

    def test_channels_differ_over_time(self) -> None:
        """8D panning should create different L/R content."""
        sig = _mono_signal(1.0)
        out = eight_d_audio(sig, SR, pan_speed_hz=0.5, intensity=1.0)
        # Channels should not be identical
        assert not np.allclose(out[0], out[1])

    def test_intensity_zero_is_centered(self) -> None:
        """With intensity=0.1 (near zero), channels should be very similar."""
        sig = _mono_signal(0.5)
        out = eight_d_audio(sig, SR, intensity=0.1, pan_speed_hz=0.1)
        # With low intensity, L and R should be very close
        diff = np.max(np.abs(out[0] - out[1]))
        assert diff < 0.3  # channels are nearly balanced


# ---------------------------------------------------------------------------
# Tests: equalizer
# ---------------------------------------------------------------------------

class TestEqualizer:
    def test_flat_eq_preserves_signal(self) -> None:
        """All bands at 0 dB should return essentially the same signal."""
        sig = _mono_signal(0.5)
        flat_gains = {"sub_bass": 0.0, "bass": 0.0, "low_mid": 0.0, "mid": 0.0,
                      "high_mid": 0.0, "presence": 0.0, "brilliance": 0.0}
        out = equalizer(sig, SR, band_gains_db=flat_gains)
        # Should be very close to original (just a copy)
        np.testing.assert_array_almost_equal(out / np.max(np.abs(out)),
                                              sig / np.max(np.abs(sig)),
                                              decimal=4)

    def test_boost_changes_signal(self) -> None:
        """A significant bass boost should change the signal."""
        sig = _mono_signal(0.5)
        out = equalizer(sig, SR, band_gains_db={"bass": 10.0})
        assert not np.allclose(out, sig)

    def test_stereo_eq(self) -> None:
        sig = _stereo_signal(0.5)
        out = equalizer(sig, SR, band_gains_db={"mid": 6.0, "presence": -4.0})
        assert out.shape[0] == 2
        assert out.shape[1] == sig.shape[1]
