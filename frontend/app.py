"""
🎧 Audio Processing Lab — Streamlit Frontend

A premium, AudioAlter-inspired UI for uploading, processing,
visualising, and downloading audio files.

Run:
    streamlit run frontend/app.py
"""

from __future__ import annotations

import io
import time
from pathlib import Path

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_BASE = "http://localhost:8000"

EFFECTS = {
    "🔄 Reverse Audio": {
        "value": "reverse",
        "description": "Flip the entire audio signal — plays backward.",
        "params": {},
    },
    "🎵 Pitch Shifter": {
        "value": "pitch_shift",
        "description": "Shift the pitch up or down while preserving duration.",
        "params": {"semitones": {"min": -12.0, "max": 12.0, "default": 0.0, "step": 0.5, "label": "Semitones"}},
    },
    "🌊 Reverb": {
        "value": "reverb",
        "description": "Add echo-based reverb for a spacious, ambient feel.",
        "params": {
            "decay": {"min": 0.1, "max": 0.9, "default": 0.5, "step": 0.05, "label": "Decay"},
            "delay_ms": {"min": 50, "max": 300, "default": 100, "step": 10, "label": "Delay (ms)"},
        },
    },
    "🎧 3D Audio (Stereo Widen)": {
        "value": "stereo_widen",
        "description": "Widen the stereo field for an immersive 3D feel.",
        "params": {
            "delay_ms": {"min": 5, "max": 20, "default": 10, "step": 1, "label": "Channel Delay (ms)"},
            "gain_diff_db": {"min": 0.0, "max": 6.0, "default": 1.5, "step": 0.5, "label": "Gain Diff (dB)"},
        },
    },
    "✂️ Trim / Cut": {
        "value": "trim",
        "description": "Extract a section of the audio by start and end time.",
        "params": {
            "start_time": {"min": 0.0, "max": 600.0, "default": 0.0, "step": 0.1, "label": "Start (sec)"},
            "end_time": {"min": 0.1, "max": 600.0, "default": 10.0, "step": 0.1, "label": "End (sec)"},
        },
    },
    "🎱 8D Audio": {
        "value": "eight_d_audio",
        "description": "Pans audio around your head for an immersive 8D experience. Use headphones!",
        "params": {
            "pan_speed_hz": {"min": 0.05, "max": 1.0, "default": 0.15, "step": 0.05, "label": "Pan Speed (Hz)"},
            "intensity": {"min": 0.1, "max": 1.0, "default": 0.8, "step": 0.05, "label": "Intensity"},
            "crossfeed": {"min": 0.0, "max": 0.6, "default": 0.3, "step": 0.05, "label": "Crossfeed"},
        },
    },
    "🎚️ Equalizer": {
        "value": "equalizer",
        "description": "7-band parametric EQ — shape your sound with precision.",
        "params": {},  # handled by custom UI
        "custom_ui": True,
    },
}


# ---------------------------------------------------------------------------
# Custom CSS — premium dark AudioAlter-inspired theme
# ---------------------------------------------------------------------------
def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        /* ── Global ──────────────────────────────────────────────── */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        .stApp {
            background: linear-gradient(160deg, #0a0a10 0%, #0f0f1a 40%, #12101f 100%);
        }

        /* ── Header ──────────────────────────────────────────────── */
        .hero-title {
            font-size: 2.6rem;
            font-weight: 800;
            background: linear-gradient(135deg, #7c3aed 0%, #a855f7 50%, #c084fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0;
            letter-spacing: -0.5px;
        }
        .hero-subtitle {
            color: #8888aa;
            font-size: 1.05rem;
            font-weight: 300;
            margin-top: 4px;
            margin-bottom: 28px;
        }

        /* ── Cards ───────────────────────────────────────────────── */
        .glass-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(124,58,237,0.15);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            backdrop-filter: blur(12px);
            transition: border-color 0.3s;
        }
        .glass-card:hover {
            border-color: rgba(124,58,237,0.35);
        }

        /* ── Effect Badge ────────────────────────────────────────── */
        .effect-badge {
            display: inline-block;
            padding: 6px 16px;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            background: linear-gradient(135deg, #7c3aed, #6d28d9);
            color: #fff;
            margin-bottom: 10px;
        }

        /* ── Stat Pill ───────────────────────────────────────────── */
        .stat-row {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-top: 10px;
        }
        .stat-pill {
            background: rgba(124,58,237,0.12);
            border: 1px solid rgba(124,58,237,0.2);
            border-radius: 10px;
            padding: 8px 16px;
            font-size: 0.82rem;
            color: #c4b5fd;
        }
        .stat-pill b { color: #e0d4fc; }

        /* ── Dividers ────────────────────────────────────────────── */
        .section-divider {
            border: none;
            border-top: 1px solid rgba(124,58,237,0.15);
            margin: 28px 0;
        }

        /* ── Sidebar Styling ─────────────────────────────────────── */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0d0d18 0%, #111126 100%);
            border-right: 1px solid rgba(124,58,237,0.12);
        }

        /* ── Buttons ─────────────────────────────────────────────── */
        .stButton > button {
            background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 10px 28px !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(124,58,237,0.3) !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 25px rgba(124,58,237,0.45) !important;
        }

        /* ── Download Button ─────────────────────────────────────── */
        .stDownloadButton > button {
            background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 15px rgba(16,185,129,0.3) !important;
        }
        .stDownloadButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 25px rgba(16,185,129,0.45) !important;
        }

        /* ── Slider Labels ───────────────────────────────────────── */
        .stSlider label { color: #c4b5fd !important; font-weight: 500 !important; }

        /* ── Selectbox ───────────────────────────────────────────── */
        .stSelectbox label { color: #c4b5fd !important; font-weight: 500 !important; }

        /* ── File Uploader ───────────────────────────────────────── */
        [data-testid="stFileUploader"] {
            border: 2px dashed rgba(124,58,237,0.3) !important;
            border-radius: 14px !important;
            padding: 16px !important;
        }

        /* ── Processing timer ────────────────────────────────────── */
        .timer-text {
            font-size: 0.85rem;
            color: #a78bfa;
            font-weight: 500;
        }

        /* ── Scrollbar ───────────────────────────────────────────── */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0f0f14; }
        ::-webkit-scrollbar-thumb { background: #7c3aed44; border-radius: 6px; }
        ::-webkit-scrollbar-thumb:hover { background: #7c3aed88; }

        /* ── Image borders ───────────────────────────────────────── */
        img {
            border-radius: 12px;
        }

        /* ── Equalizer Band Columns ───────────────────────────────── */
        .eq-container {
            display: flex;
            justify-content: space-between;
            gap: 4px;
            padding: 16px 4px;
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(124,58,237,0.12);
            border-radius: 12px;
            margin-bottom: 16px;
        }
        .eq-band {
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
            min-width: 0;
        }
        .eq-band .eq-value {
            font-size: 0.72rem;
            font-weight: 700;
            color: #a78bfa;
            margin-bottom: 4px;
            font-variant-numeric: tabular-nums;
        }
        .eq-band .eq-freq {
            font-size: 0.62rem;
            font-weight: 600;
            color: #7c3aed;
            margin-top: 4px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .eq-band .eq-label {
            font-size: 0.58rem;
            color: #6b6b8a;
            margin-top: 1px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# API Helpers
# ---------------------------------------------------------------------------

def api_upload(file_bytes: bytes, filename: str) -> dict | None:
    """Upload audio to the backend. Returns response JSON or None."""
    try:
        resp = requests.post(
            f"{API_BASE}/upload",
            files={"file": (filename, file_bytes, "audio/mpeg")},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"❌ Upload failed: {e}")
        return None


def api_process(file_id: str, effect: str, params: dict) -> dict | None:
    """Send a processing request. Returns response JSON or None."""
    try:
        resp = requests.post(
            f"{API_BASE}/process",
            json={"file_id": file_id, "effect": effect, "parameters": params},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"❌ Processing failed: {e}")
        return None


def api_visualize(file_id: str, label: str = "") -> dict | None:
    """Request visualization generation. Returns URLs dict or None."""
    try:
        resp = requests.get(
            f"{API_BASE}/visualize/{file_id}",
            params={"label": label},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"❌ Visualization failed: {e}")
        return None


def api_get_image(url_path: str) -> bytes | None:
    """Fetch a visualization image from the backend."""
    try:
        resp = requests.get(f"{API_BASE}{url_path}", timeout=30)
        resp.raise_for_status()
        return resp.content
    except requests.RequestException:
        return None


def api_download(file_id: str) -> bytes | None:
    """Download processed MP3 bytes."""
    try:
        resp = requests.get(f"{API_BASE}/download/{file_id}", timeout=30)
        resp.raise_for_status()
        return resp.content
    except requests.RequestException as e:
        st.error(f"❌ Download failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Main UI
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="Audio Processing Lab",
        page_icon="🎧",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()

    # ── Hero ──────────────────────────────────────────────────────────────
    st.markdown('<p class="hero-title">🎧 Audio Processing Lab</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-subtitle">Upload · Transform · Visualise · Download — professional audio effects powered by DSP</p>',
        unsafe_allow_html=True,
    )

    # ── Session state init ────────────────────────────────────────────────
    for key in ("upload_info", "processed_info", "original_viz", "processed_viz"):
        if key not in st.session_state:
            st.session_state[key] = None

    # ══════════════════════════════════════════════════════════════════════
    # SIDEBAR
    # ══════════════════════════════════════════════════════════════════════
    with st.sidebar:
        st.markdown("### 📁 Upload Audio")
        uploaded_file = st.file_uploader(
            "Drag & drop or browse",
            type=["mp3", "wav", "ogg", "flac", "m4a"],
            help="Max 20 MB",
        )

        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()

            # Auto-upload on new file
            if (
                st.session_state.upload_info is None
                or st.session_state.upload_info.get("filename") != uploaded_file.name
            ):
                with st.spinner("Uploading…"):
                    info = api_upload(file_bytes, uploaded_file.name)
                if info:
                    st.session_state.upload_info = info
                    st.session_state.processed_info = None
                    st.session_state.original_viz = None
                    st.session_state.processed_viz = None

            upload_info = st.session_state.upload_info
            if upload_info:
                st.success(f"✅ **{upload_info['filename']}** uploaded")
                st.markdown(
                    f"""
                    <div class="stat-row">
                        <span class="stat-pill"><b>⏱</b> {upload_info['duration_seconds']:.1f}s</span>
                        <span class="stat-pill"><b>🎚</b> {upload_info['sample_rate']} Hz</span>
                        <span class="stat-pill"><b>🔊</b> {'Stereo' if upload_info['channels'] == 2 else 'Mono'}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # ── Effect Selection ──────────────────────────────────────────────
        st.markdown("### 🎛 Select Effect")
        effect_name = st.selectbox(
            "Effect",
            list(EFFECTS.keys()),
            label_visibility="collapsed",
        )
        effect_cfg = EFFECTS[effect_name]
        st.markdown(f"*{effect_cfg['description']}*")

        # ── Dynamic Parameters ────────────────────────────────────────────
        params: dict = {}
        is_eq = effect_cfg.get("custom_ui", False) and effect_cfg["value"] == "equalizer"
        is_trim = effect_cfg["value"] == "trim"

        if is_eq:
            # ── 7-Band Parametric Equalizer ──────────────────────────────
            st.markdown("#### 🎚️ 7-Band Equalizer")
            
            # Define the 7 EQ bands with frequencies
            eq_bands = [
                ("sub_bass", "Sub Bass", "60 Hz"),
                ("bass", "Bass", "170 Hz"),
                ("low_mid", "Low Mid", "500 Hz"),
                ("mid", "Mid", "1 kHz"),
                ("high_mid", "High Mid", "3 kHz"),
                ("presence", "Presence", "6 kHz"),
                ("brilliance", "Brilliance", "12 kHz"),
            ]
            
            # Create two columns for the sliders
            cols = st.columns(2)
            for idx, (band_key, band_label, band_freq) in enumerate(eq_bands):
                col = cols[idx % 2]
                with col:
                    params[band_key] = st.slider(
                        f"{band_label} ({band_freq})",
                        min_value=-12.0,
                        max_value=12.0,
                        value=0.0,
                        step=0.5,
                        key=f"eq_{band_key}",
                    )

        elif is_trim and st.session_state.upload_info:
            # ── Trim: duration-aware sliders ───────────────────────────────
            duration = st.session_state.upload_info["duration_seconds"]
            # Smart step: 0.1s for short audio, 0.5s for medium, 1s for long
            if duration <= 30:
                trim_step = 0.1
            elif duration <= 300:
                trim_step = 0.5
            else:
                trim_step = 1.0

            st.markdown("#### ✂️ Trim Range")
            st.markdown(
                f'<div class="stat-row"><span class="stat-pill"><b>⏱</b> '
                f'Duration: {duration:.1f}s</span></div>',
                unsafe_allow_html=True,
            )

            params["start_time"] = st.slider(
                "Start Time (sec)",
                min_value=0.0,
                max_value=max(duration - 0.1, 0.1),
                value=0.0,
                step=trim_step,
                key="trim_start",
            )
            # End slider min = start + step, max = duration, default = duration
            end_min = params["start_time"] + trim_step
            params["end_time"] = st.slider(
                "End Time (sec)",
                min_value=round(end_min, 2),
                max_value=round(duration, 2),
                value=round(duration, 2),
                step=trim_step,
                key="trim_end",
            )

            # Show selected range
            selected_dur = params["end_time"] - params["start_time"]
            st.markdown(
                f'<div class="stat-row">'
                f'<span class="stat-pill"><b>✂️</b> '
                f'{params["start_time"]:.1f}s → {params["end_time"]:.1f}s '
                f'({selected_dur:.1f}s)</span></div>',
                unsafe_allow_html=True,
            )

        elif is_trim and st.session_state.upload_info is None:
            st.warning("Upload an audio file first to set trim points.")

        elif effect_cfg["params"]:
            st.markdown("#### ⚙️ Parameters")
            for key, cfg in effect_cfg["params"].items():
                if isinstance(cfg["default"], float):
                    params[key] = st.slider(
                        cfg["label"],
                        min_value=cfg["min"],
                        max_value=cfg["max"],
                        value=cfg["default"],
                        step=cfg["step"],
                    )
                else:
                    params[key] = st.slider(
                        cfg["label"],
                        min_value=int(cfg["min"]),
                        max_value=int(cfg["max"]),
                        value=int(cfg["default"]),
                        step=int(cfg["step"]),
                    )

        # ── 8D Audio: headphone warning ────────────────────────────────────
        if effect_cfg["value"] == "eight_d_audio":
            st.warning("🎧 **Use headphones** for the best 8D experience!")

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # ── Process Button ────────────────────────────────────────────────
        process_disabled = st.session_state.upload_info is None
        if st.button(
            "🚀  Process Audio",
            use_container_width=True,
            disabled=process_disabled,
        ):
            with st.spinner("🔧 Processing…"):
                t0 = time.time()
                result = api_process(
                    st.session_state.upload_info["file_id"],
                    effect_cfg["value"],
                    params,
                )
                elapsed = time.time() - t0
            if result:
                st.session_state.processed_info = result
                st.session_state.processed_viz = None  # reset viz
                st.success(f"✅ Done in **{elapsed:.2f}s**")
                st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # MAIN PANEL
    # ══════════════════════════════════════════════════════════════════════

    if st.session_state.upload_info is None:
        # ── Empty state ───────────────────────────────────────────────────
        st.markdown(
            """
            <div class="glass-card" style="text-align:center; padding:60px 40px;">
                <p style="font-size:3.5rem; margin:0;">🎵</p>
                <p style="font-size:1.3rem; font-weight:600; color:#c4b5fd; margin:8px 0 4px;">
                    No audio loaded yet
                </p>
                <p style="color:#6b6b8a; font-size:0.95rem;">
                    Upload an MP3, WAV, OGG, FLAC or M4A file from the sidebar to get started.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ── Determine which effect is selected (for main-panel EQ) ────────────
    effect_name_selected = st.session_state.get("_effect_name_sel", None)

    upload_info = st.session_state.upload_info
    file_id = upload_info["file_id"]
    
    # Store EQ values in session state for visualization
    # This will be updated by the sidebar sliders
    from streamlit import session_state as ss
    # Note: The sidebar sliders will update these keys automatically

    # ── Generate original visualizations (once) ───────────────────────────
    if st.session_state.original_viz is None:
        with st.spinner("Generating visualizations for original…"):
            viz = api_visualize(file_id, label="Original")
        if viz:
            st.session_state.original_viz = viz

    # ── Original Audio Section ────────────────────────────────────────────
    st.markdown(
        '<div class="glass-card"><span class="effect-badge">ORIGINAL</span>',
        unsafe_allow_html=True,
    )
    col_a, col_b = st.columns(2)

    orig_viz = st.session_state.original_viz
    if orig_viz:
        wf_img = api_get_image(orig_viz["waveform_url"])
        sp_img = api_get_image(orig_viz["spectrogram_url"])
        with col_a:
            st.markdown("**Waveform**")
            if wf_img:
                st.image(wf_img, use_container_width=True)
        with col_b:
            st.markdown("**Spectrogram**")
            if sp_img:
                st.image(sp_img, use_container_width=True)

    # Original audio player
    orig_audio = api_download(file_id)
    if orig_audio:
        st.audio(orig_audio, format="audio/mp3")
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Equalizer Preview (if EQ is selected) ────────────────────────────
    # Get the current gains from session state (set by sidebar sliders)
    eq_gains = {
        "sub_bass": st.session_state.get("eq_sub_bass", 0.0),
        "bass": st.session_state.get("eq_bass", 0.0),
        "low_mid": st.session_state.get("eq_low_mid", 0.0),
        "mid": st.session_state.get("eq_mid", 0.0),
        "high_mid": st.session_state.get("eq_high_mid", 0.0),
        "presence": st.session_state.get("eq_presence", 0.0),
        "brilliance": st.session_state.get("eq_brilliance", 0.0),
    }
    
    # Only show if any EQ band has been adjusted (non-zero)
    if any(v != 0.0 for v in eq_gains.values()):
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown('<div class="glass-card"><span class="effect-badge">EQUALIZER PREVIEW</span>', unsafe_allow_html=True)
        
        eq_bands_data = [
            ("Sub Bass", "60 Hz", eq_gains["sub_bass"]),
            ("Bass", "170 Hz", eq_gains["bass"]),
            ("Low Mid", "500 Hz", eq_gains["low_mid"]),
            ("Mid", "1 kHz", eq_gains["mid"]),
            ("High Mid", "3 kHz", eq_gains["high_mid"]),
            ("Presence", "6 kHz", eq_gains["presence"]),
            ("Brilliance", "12 kHz", eq_gains["brilliance"]),
        ]
        
        # Build EQ container with proper HTML structure
        eq_html = '<div class="eq-container">'
        for label, freq, gain in eq_bands_data:
            bar_height = max(0, min(100, 50 + (gain / 12) * 50))
            if gain > 1:
                color = "#10b981"
            elif gain < -1:
                color = "#ef4444"
            else:
                color = "#7c3aed"
            
            eq_html += '<div class="eq-band">'
            eq_html += f'<div class="eq-value">{gain:+.1f}</div>'
            eq_html += f'<div style="width:100%;height:120px;background:rgba(255,255,255,0.05);border-radius:4px;position:relative;overflow:hidden;"><div style="position:absolute;bottom:0;left:2px;right:2px;height:{bar_height}%;background:linear-gradient(to top, {color}, {color}99);border-radius:2px;transition:all 0.2s ease;"></div></div>'
            eq_html += f'<div class="eq-freq">{freq}</div>'
            eq_html += f'<div class="eq-label">{label}</div>'
            eq_html += '</div>'
        eq_html += '</div>'
        
        st.markdown(eq_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Processed Audio Section ───────────────────────────────────────────
    proc_info = st.session_state.processed_info
    if proc_info:
        proc_id = proc_info["processed_file_id"]

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="glass-card"><span class="effect-badge">PROCESSED — {proc_info["effect"].upper()}</span>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="stat-row">
                <span class="stat-pill"><b>🎛</b> {proc_info['effect']}</span>
                <span class="stat-pill"><b>⚡</b> {proc_info['processing_time_seconds']:.3f}s</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Generate processed visualizations (once)
        if st.session_state.processed_viz is None:
            with st.spinner("Generating visualizations for processed…"):
                viz_p = api_visualize(proc_id, label="Processed")
            if viz_p:
                st.session_state.processed_viz = viz_p

        proc_viz = st.session_state.processed_viz
        col_c, col_d = st.columns(2)
        if proc_viz:
            wf_img_p = api_get_image(proc_viz["waveform_url"])
            sp_img_p = api_get_image(proc_viz["spectrogram_url"])
            with col_c:
                st.markdown("**Waveform**")
                if wf_img_p:
                    st.image(wf_img_p, use_container_width=True)
            with col_d:
                st.markdown("**Spectrogram**")
                if sp_img_p:
                    st.image(sp_img_p, use_container_width=True)

        # Processed audio player
        proc_audio = api_download(proc_id)
        if proc_audio:
            st.audio(proc_audio, format="audio/mp3")

            # Download button
            st.download_button(
                label="⬇️  Download Processed MP3",
                data=proc_audio,
                file_name=f"processed_{proc_id}.mp3",
                mime="audio/mpeg",
                use_container_width=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
