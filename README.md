# 🎧 Audio Processing Lab

A production-ready, full-stack audio processing web application inspired by [AudioAlter](https://audioalter.com). Upload MP3 files, apply professional DSP effects, visualise waveforms & spectrograms, and download processed audio — all through a sleek, dark-themed UI.

---

## ✨ Features

| Effect | Description |
|---|---|
| 🔄 **Reverse** | Play audio backwards |
| 🎵 **Pitch Shift** | Shift pitch ±12 semitones without changing speed |
| 🌊 **Reverb** | Echo-based reverb with configurable decay & delay |
| 🎧 **3D Audio** | Stereo widening via inter-channel delay & gain diff |
| ✂️ **Trim** | Cut a section by start/end time |

Plus:
- **Waveform** & **Spectrogram** visualisation (before & after)
- In-browser **audio playback**
- One-click **MP3 download**
- Automatic peak **normalisation** (no clipping)
- Background **file cleanup** (TTL-based)

---

## 🏗 Architecture

```
miniproject/
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Centralised settings
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── routers/
│   │   ├── upload.py            # POST /upload
│   │   ├── process.py           # POST /process
│   │   ├── download.py          # GET  /download/{file_id}
│   │   └── visualize.py         # GET  /visualize/{file_id}
│   ├── services/
│   │   ├── audio_effects.py     # Pure DSP functions
│   │   ├── audio_pipeline.py    # Orchestrates the full pipeline
│   │   └── visualization.py     # Waveform & spectrogram generation
│   ├── utils/
│   │   ├── audio_converter.py   # MP3 ↔ WAV conversion
│   │   └── file_manager.py      # UUID naming, validation, cleanup
│   └── tests/
│       └── test_effects.py      # Unit tests for all effects
├── frontend/
│   └── app.py                   # Streamlit UI
├── .streamlit/
│   └── config.toml              # Dark theme config
├── requirements.txt
└── README.md
```

**Layered separation:**
- **Routers** → HTTP only (no DSP logic)
- **Services** → pure DSP & visualisation
- **Utils** → file I/O & conversion
- **Models** → Pydantic schemas

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **ffmpeg** installed and on your `PATH`
  - Windows: `winget install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html)
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

### 1. Clone & Install

```bash
cd miniproject
pip install -r requirements.txt
```

### 2. Start the Backend (FastAPI)

```bash
# From the project root (miniproject/)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API docs are available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Start the Frontend (Streamlit)

Open a **second terminal**:

```bash
# From the project root (miniproject/)
streamlit run frontend/app.py
```

The UI opens at: [http://localhost:8501](http://localhost:8501)

---

## 📖 Usage

1. **Upload** an MP3 (or WAV/OGG/FLAC/M4A) via the sidebar — max 20 MB.
2. **Select** an effect from the dropdown.
3. **Adjust** parameters with the sliders.
4. Click **🚀 Process Audio**.
5. **View** waveform & spectrogram (original vs processed).
6. **Play** the processed audio in the browser.
7. **Download** the result as MP3.

---

## 🧪 Running Tests

```bash
python -m pytest backend/tests/test_effects.py -v
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload` | Upload audio file → returns `file_id` |
| `POST` | `/process` | Apply effect → returns `processed_file_id` |
| `GET` | `/download/{file_id}` | Download MP3 |
| `GET` | `/visualize/{file_id}` | Generate & return viz URLs |
| `GET` | `/visualize/image/{file_id}/{kind}` | Serve PNG image |

Full interactive docs: `http://localhost:8000/docs`

---

## ⚙️ Configuration

All tuneable values live in `backend/config.py`:

| Setting | Default | Purpose |
|---|---|---|
| `MAX_FILE_SIZE_MB` | 20 | Upload limit |
| `FILE_TTL_MINUTES` | 30 | Auto-delete after N minutes |
| `DEFAULT_SAMPLE_RATE` | 44100 | Fallback sample rate |

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Uvicorn, Pydantic |
| Frontend | Streamlit |
| Audio DSP | librosa, NumPy, SciPy, soundfile, pydub |
| Visualisation | matplotlib, librosa.display |
| Conversion | ffmpeg (via pydub) |

---

## 📝 License

MIT — use freely for academic and personal projects.
