"""
Visualization Service — waveform & spectrogram generation.

Produces publication-quality PNG images using matplotlib + librosa.
Every function is pure: signal in, image path out.
"""

from __future__ import annotations

import logging
from pathlib import Path

import librosa
import librosa.display
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — safe for servers
import matplotlib.pyplot as plt
import numpy as np

from backend.utils.file_manager import visualization_path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------
_FIG_WIDTH = 12
_FIG_HEIGHT = 3.5
_DPI = 120
_BG_COLOR = "#0f0f14"
_WAVEFORM_COLOR = "#7c3aed"
_SPEC_CMAP = "magma"


def _setup_axes(ax: plt.Axes) -> None:
    """Apply dark-theme styling to an axes object."""
    ax.set_facecolor(_BG_COLOR)
    ax.tick_params(colors="#aaa", labelsize=8)
    ax.xaxis.label.set_color("#ccc")
    ax.yaxis.label.set_color("#ccc")
    ax.title.set_color("#eee")
    for spine in ax.spines.values():
        spine.set_color("#333")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_waveform(
    signal: np.ndarray,
    sr: int,
    file_id: str,
    title: str = "Waveform",
) -> Path:
    """
    Render a waveform plot and save it as PNG.

    Args:
        signal: Audio signal (mono or first channel of stereo).
        sr: Sample rate.
        file_id: UUID used for the output filename.
        title: Plot title.

    Returns:
        Path to the saved PNG.
    """
    # Use mono for display
    if signal.ndim == 2:
        display_signal = signal[0]
    else:
        display_signal = signal

    fig, ax = plt.subplots(figsize=(_FIG_WIDTH, _FIG_HEIGHT), dpi=_DPI)
    fig.patch.set_facecolor(_BG_COLOR)
    _setup_axes(ax)

    times = np.linspace(0, len(display_signal) / sr, num=len(display_signal))
    ax.plot(times, display_signal, color=_WAVEFORM_COLOR, linewidth=0.4, alpha=0.9)
    ax.fill_between(times, display_signal, alpha=0.15, color=_WAVEFORM_COLOR)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_xlim(0, times[-1])

    out = visualization_path(file_id, "waveform")
    fig.savefig(str(out), bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.debug("Waveform saved → %s", out.name)
    return out


def generate_spectrogram(
    signal: np.ndarray,
    sr: int,
    file_id: str,
    title: str = "Spectrogram",
) -> Path:
    """
    Render a spectrogram and save it as PNG.

    Uses ``librosa.stft`` → dB scale → ``librosa.display.specshow``.

    Returns:
        Path to the saved PNG.
    """
    if signal.ndim == 2:
        display_signal = signal[0]
    else:
        display_signal = signal

    S = librosa.stft(display_signal)
    S_db = librosa.amplitude_to_db(np.abs(S), ref=np.max)

    fig, ax = plt.subplots(figsize=(_FIG_WIDTH, _FIG_HEIGHT), dpi=_DPI)
    fig.patch.set_facecolor(_BG_COLOR)
    _setup_axes(ax)

    img = librosa.display.specshow(
        S_db, sr=sr, x_axis="time", y_axis="hz",
        ax=ax, cmap=_SPEC_CMAP,
    )
    cbar = fig.colorbar(img, ax=ax, format="%+2.0f dB")
    cbar.ax.tick_params(colors="#aaa", labelsize=8)
    cbar.outline.set_edgecolor("#333")
    ax.set_title(title, fontsize=11, fontweight="bold")

    out = visualization_path(file_id, "spectrogram")
    fig.savefig(str(out), bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.debug("Spectrogram saved → %s", out.name)
    return out
