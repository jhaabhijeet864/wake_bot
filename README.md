<p align="center">
  <h1 align="center">🤖 WakeBot — Big Bot</h1>
  <p align="center">
    <em>An autonomous, multi-modal environment orchestrator for your desktop.</em><br>
    <strong>Audio Triggers • Computer Vision • AI-Powered Awareness</strong>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" />
  <img src="https://img.shields.io/badge/status-Active%20Development-00C853?style=for-the-badge" />
  <img src="https://img.shields.io/badge/version-2.0.0-blueviolet?style=for-the-badge" />
</p>

---

## 🧠 What is WakeBot?

WakeBot (codename: **Big Bot**) is a Python-powered desktop automation daemon that reacts to **audio cues** (claps, voice commands) and **visual context** (webcam presence, screen content, AI vision models) to orchestrate your workspace — waking your PC, launching VS Code, playing Spotify, detecting errors on screen, and more.

It is designed with a **Principal Architect philosophy**: every module runs on its own daemon thread, communicates via thread-safe events, and never blocks the main execution loop.

---

## ✨ Features at a Glance

| Feature | Trigger | Module |
|---|---|---|
| 👏 **Single Clap** → Wake PC + VS Code + Spotify | Audio | `audio_cmd.py` |
| 👏👏 **Double Clap** → Goodnight (Pause Music + Screen Off) | Audio | `audio_cmd.py` |
| 🗣️ **Voice Command** → "Wake up daddy's home" | Audio (Vosk) | `audio_cmd.py` |
| 👤 **Walk-up Detection** → Auto Welcome Home | Vision (Phase 1) | `presence.py` |
| 🚶 **Walk-away Detection** → Auto Goodnight (2 min) | Vision (Phase 1) | `presence.py` |
| 🖥️ **Screen OCR** → Detect errors, media, active apps | Vision (Phase 2) | `screen.py` |
| 🧠 **AI Vision Analysis** → "What am I doing?" via VLM | Vision (Phase 3) | `multimodal.py` |

---

## 🚀 Quick Start

### 1️⃣ Clone & Install

```bash
git clone https://github.com/your-username/Wake_Bot.git
cd Wake_Bot

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# Install all dependencies
pip install -r requirements.txt
```

### 2️⃣ Setup Voice Model (Optional)

WakeBot uses **Vosk** for offline voice recognition.

1. Download a model from [Vosk Models](https://alphacephei.com/vosk/models) (recommended: `vosk-model-small-en-us-0.15`, ~40MB)
2. Extract into the `model/` directory in the project root
3. Directory should look like: `Wake_Bot/model/am/...`, `Wake_Bot/model/graph/...`

### 3️⃣ Calibrate Audio (First Time)

```bash
python -m wakebot calibrate
```

Follow the prompts: sit quietly for 5 seconds, then clap loudly 5 times. The tool will recommend a threshold value — update `wakebot_config.json` accordingly.

### 4️⃣ Run WakeBot

```bash
# 🎧 Audio Mode — Claps & Voice triggers
python -m wakebot run audio

# 👁️ Vision Mode — Full Awareness (Presence + Screen + AI)
python -m wakebot run vision
```

---

## 🎮 CLI Commands

WakeBot uses a unified CLI router. All commands are accessible via `python -m wakebot`.

| Command | Description |
|---|---|
| `python -m wakebot run audio` | 🎧 Start audio detection (claps + voice) |
| `python -m wakebot run vision` | 👁️ Start full vision awareness (all 3 phases) |
| `python -m wakebot audio` | 🎧 Direct audio mode (shorthand) |
| `python -m wakebot vision` | 👁️ Direct vision mode (shorthand) |
| `python -m wakebot calibrate` | 🔧 Run the audio calibration tool |

---

## 🏗️ Architecture

### 📁 Project Structure

```
Wake_Bot/
├── 📄 wakebot_config.json              # Runtime configuration (JSON)
├── 📄 requirements.txt                 # Python dependencies
├── 📄 Full_Awareness.md                # Vision architecture plan
│
├── 📂 model/                           # Vosk speech recognition model
├── 📂 scripts/                         # Environment setup scripts
│
├── 📂 wakebot/                         # Main package
│   ├── 📄 __init__.py                  # Package root (v2.1.0)
│   ├── 📄 __main__.py                  # python -m wakebot entrypoint
│   │
│   ├── 📂 core/                        # Core logic & shared infrastructure
│   │   ├── 📄 actions.py               # WakeBotActions (wake, VS Code, Spotify, goodnight)
│   │   ├── 📄 config.py                # WakeBotConfig dataclass + JSON loader
│   │   ├── 📄 audio_orchestrator.py    # 🆕 Consolidated audio pipeline
│   │   ├── 📄 event_bus.py             # 🆕 Thread-safe Pub/Sub coordinator
│   │   ├── 📄 logger.py                # WakeBotLogger (timestamped console output)
│   │   └── 📄 workspace_state.py       # Thread-safe global state (WorkspaceState)
│   │
│   ├── 📂 cli/                         # CLI routing & command handlers
│   │   ├── 📄 main.py                  # Unified CLI router (argparse)
│   │   ├── 📄 audio_cmd.py             # Threaded audio pipeline (3 daemon threads)
│   │   ├── 📄 vision_cmd.py            # 🆕 Full Awareness orchestrator (3 phases)
│   │   └── 📄 calibrate_cmd.py         # Audio threshold calibration tool
│   │
│   └── 📂 triggers/                    # Sensor modules (input only — no action logic)
│       ├── 📂 audio/
│       │   ├── 📄 engine.py            # AudioStream (PyAudio wrapper)
│       │   ├── 📄 detector.py          # ClapDetector (single/double clap FSM)
│       │   ├── 📄 voice.py             # VoiceDetector (Vosk-based)
│       │   └── 📄 model_downloader.py  # Vosk model auto-downloader
│       │
│       └── 📂 vision/
│           ├── 📄 engine.py            # CameraEngine (OpenCV VideoCapture wrapper)
│           ├── 📄 detector.py          # PersonDetector (legacy Haar Cascades)
│           ├── 📄 presence.py          # 🆕 Phase 1: MediaPipe presence monitor
│           ├── 📄 screen.py            # 🆕 Phase 2: Screen OCR (mss + EasyOCR)
│           └── 📄 multimodal.py        # 🆕 Phase 3: VLM engine (Ollama/Gemini)
│
└── 📂 src/                             # Legacy modules (audio engine, clap detector)
```

### 🧵 Threading Model

WakeBot uses a **producer/consumer + event-driven** threading model. No module directly calls `WakeBotActions` — they set `threading.Event` flags that the master orchestration loop polls at 10 Hz.

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│  Audio Producer  │     │  Presence Monitor │     │   Screen Monitor   │
│  (mic → queue)   │     │  (webcam @ 5 FPS) │     │  (OCR @ 10s)       │
└───────┬─────────┘     └────────┬─────────┘     └─────────┬──────────┘
        │                        │                          │
        ▼                        ▼                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│ Detection Worker │     │   wake_event ⚡   │     │  WorkspaceState 🔒 │
│ (clap + voice)   │     │   sleep_event ⚡  │     │  (thread-safe)     │
└───────┬─────────┘     └────────┬─────────┘     └────────────────────┘
        │                        │
        ▼                        ▼
   ┌─────────────────────────────────────┐
   │     Master Orchestration Loop       │
   │  (polls events → calls actions)     │
   │  wake_event → welcome_home()        │
   │  sleep_event → goodnight()          │
   └─────────────────────────────────────┘
```

---

## 👁️ Vision System — Full Awareness

The vision system is implemented in 3 progressive phases, each building on the last.

### Phase 1: 👤 Presence Detection (`presence.py`)
- **Tech**: OpenCV + MediaPipe FaceDetection (short-range model)
- **Behavior**: Samples webcam at 5 FPS. Detects face → sets `wake_event`. Face absent for >2 minutes → sets `sleep_event`.
- **CPU Impact**: ~2-5ms per frame inference. Under 3% total CPU at 5 FPS.

### Phase 2: 🖥️ Screen & OCR Awareness (`screen.py`)
- **Tech**: `mss` (screen capture) + `EasyOCR` (GPU-accelerated if CUDA available)
- **Behavior**: Captures the primary monitor every 10 seconds, extracts text, and detects:
  - 🎮 **Fullscreen Media/Games** (Netflix, Minecraft, GTA, etc.) → suppresses notifications
  - 🐛 **Error Traces** (Python tracebacks, npm errors, etc.) → flags for proactive assistance
- **Killswitch**: `screen.pause()` / `screen.resume()` to instantly halt OCR.

### Phase 3: 🧠 Multi-Modal VLM (`multimodal.py`)
- **Tech**: Webcam + Screen → base64 → Ollama (LLaVA) or Google Gemini 1.5 Pro
- **Behavior**: Periodically (every 60s) or on-demand (via hotword) sends combined frames to a Vision-Language Model.
- **Use Cases**:
  - "What am I working on?" → VLM reads screen
  - "What am I holding?" → VLM analyzes webcam
  - Autonomous state detection: working, relaxing, or away

### 🧠 VLM Backend Setup

**Option A: Ollama (Local, Free, Private)**
```bash
# Install Ollama: https://ollama.com
ollama pull llava
# WakeBot connects to http://localhost:11434 automatically
```

**Option B: Google Gemini (Cloud, Higher Quality)**
```bash
# Set your API key
set GEMINI_API_KEY=your_api_key_here

# Update config
# In wakebot_config.json: "vlm_provider": "gemini"
```

---

## ⚙️ Configuration

All configuration lives in `wakebot_config.json` (auto-generated on first run).

```json
{
    "chunk_size": 1024,
    "sample_rate": 16000,
    "channels": 1,
    "threshold": 3000,
    "cooldown_ms": 100,
    "double_clap_window_ms": 500,

    "voice_enabled": true,
    "wake_phrases": ["wake up", "daddy's home"],
    "model_path": "model",

    "vision_enabled": false,
    "camera_index": 0,
    "vision_fps": 5.0,
    "absence_threshold": 120.0,
    "screen_interval": 10.0,
    "vlm_provider": "ollama",
    "vlm_interval": 60.0,

    "wake_key": "shift",
    "open_lock_screen": true,
    "log_rms_values": false
}
```

| Key | Type | Default | Description |
|---|---|---|---|
| `threshold` | int | 3000 | RMS threshold for clap detection |
| `double_clap_window_ms` | int | 500 | Max gap between claps for double-clap |
| `voice_enabled` | bool | true | Enable Vosk voice recognition |
| `vision_enabled` | bool | false | Enable camera presence detection |
| `camera_index` | int | 0 | OpenCV camera device index |
| `vision_fps` | float | 5.0 | Presence monitor frame rate |
| `absence_threshold` | float | 120.0 | Seconds before walk-away triggers goodnight |
| `screen_interval` | float | 10.0 | Seconds between screen OCR captures |
| `vlm_provider` | str | "ollama" | VLM backend: `"ollama"` or `"gemini"` |
| `vlm_interval` | float | 60.0 | Seconds between periodic VLM analyses |

---

## 📦 Dependencies

### Core
| Package | Purpose |
|---|---|
| `pyaudio` | Microphone stream capture |
| `numpy` | Audio signal processing (RMS) |
| `pyautogui` | System automation (keypress) |
| `pywin32` | Windows API (window management) |
| `colorama` | Colored terminal output |

### Vision (Phase 1-3)
| Package | Purpose |
|---|---|
| `opencv-python` | Webcam video capture & frame processing |
| `mediapipe` | Ultra-fast face detection (Phase 1) |
| `mss` | High-speed screen capture (Phase 2) |
| `easyocr` | Optical character recognition (Phase 2) |
| `requests` | Ollama API communication (Phase 3) |
| `google-generativeai` | *(Optional)* Gemini API (Phase 3) |

---

## 🔧 Troubleshooting

<details>
<summary>🎤 Microphone Not Detected</summary>

- **Windows**: Settings → Privacy → Microphone → Allow apps
- Ensure no other app has exclusive microphone access
- Run `python -m wakebot calibrate` to test
</details>

<details>
<summary>👏 Claps Not Registering</summary>

1. Run `python -m wakebot calibrate`
2. Lower `threshold` in `wakebot_config.json` (try 70-80% of current)
3. Clap closer to the microphone
4. Ensure a quiet environment
</details>

<details>
<summary>📷 Camera Not Working (Vision Mode)</summary>

- Check Windows Privacy → Camera → Allow apps
- Ensure no other app (Zoom, Teams) is using the camera
- Try changing `camera_index` to `1` in config
- WakeBot auto-retries camera after 5s on failure
</details>

<details>
<summary>🧠 Ollama/VLM Not Responding</summary>

- Ensure Ollama is running: `ollama serve`
- Pull the model: `ollama pull llava`
- Check `http://localhost:11434` is accessible
</details>

---

## 🗺️ Roadmap & Future Growth

- [ ] 🎛️ **System Tray UI** — `pystray` widget with pause/resume toggles for each subsystem
- [ ] 🗣️ **TTS Responses** — Proactive voice feedback ("I see an error on line 42...")
- [ ] 🌙 **Ambient Awareness** — Auto-adjust brightness/volume based on room state
- [ ] 🔗 **Smart Home Integration** — IoT triggers (lights, plugs) via MQTT
- [ ] 📱 **Mobile Companion** — Push notifications via Pushover/Telegram
- [ ] 🧪 **Gesture Recognition** — MediaPipe hand tracking for custom gestures
- [ ] 🔐 **Face ID Lock** — Lock PC when an unrecognized face is detected

---

## 🤝 Contributing

Contributions are welcome! The architecture is designed for modularity:

1. **New Audio Triggers** → Add a detector in `wakebot/triggers/audio/` implementing `BaseDetector`
2. **New Vision Triggers** → Add a daemon thread in `wakebot/triggers/vision/` emitting to `threading.Event`
3. **New Actions** → Extend `WakeBotActions` in `wakebot/core/actions.py`

---

## 📄 License

MIT License — See LICENSE for details.

---

<p align="center">
  <strong>👏 Clap to wake. 👁️ See to understand. 🧠 Think to act.</strong><br>
  <em>Built with ❤️ by the Big Bot team.</em>
</p>
