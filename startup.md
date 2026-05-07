# 🚀 WakeBot v2.1.0 — Quick Start Guide

Welcome to the new **WakeBot**. The architecture has been completely overhauled for **decoupled, event-driven performance**. Triggers (Audio/Vision) now communicate via a central **EventBus**, making the system faster and more stable.

---

## 🛠️ 1. Installation & Environment

1.  **Run the Setup**:
    ```powershell
    .\setup.bat
    ```
    *This will create the `wakebot_env`, upgrade pip, and install all modular dependencies.*

2.  **Activate Environment**:
    ```powershell
    .\wakebot_env\Scripts\activate
    ```

---

## 🏃 2. How to Run

### 🌟 Unified Engine (Recommended)
This starts the full awareness suite (Audio + Vision + Dashboard).
```powershell
python -m wakebot run vision
```

### 🎧 Audio-Only Mode
Lightweight mode for background detection.
```powershell
python -m wakebot run audio
```

---

## 🎮 3. Control Center (Dashboard)

The Dashboard now features:
- **🎧 Audio System Toggle**: Enable/Disable mic detection instantly.
- **👤 Presence Toggle**: Stop the camera from watching you.
- **🖥️ Screen Monitor Toggle**: Privacy mode for your desktop.
- **🧠 AI VLM Toggle**: Control cloud-based AI analysis.
- **📡 API Status**: Real-time monitoring of **Ollama** and **Gemini** connectivity.

---

## 🧩 4. Modular TTS (Kokoro)

To enable high-quality local speech:
1.  Navigate to `models/tts/kokoro/`.
2.  Download and place:
    - `kokoro-v0_19.onnx`
    - `voices.bin`
3.  The system will automatically detect them and enable local voice responses!

---

## 🧪 5. Testing & Verification

- **Help Command**: `python -m wakebot --help`
- **Audio Calibration**: `python -m wakebot calibrate` (Run this first to set your clap threshold!)
- **Event Monitoring**: Watch the terminal logs to see `Event Triggered: USER_ARRIVED` when you walk up to your PC.

---

## 🐛 Troubleshooting

- **Ollama Inactive?** Ensure Ollama is running on your PC (port 11434).
- **Gemini failing?** Check your `.env` file for a valid `GEMINI_API_KEY`.
- **VS Code not opening?** Ensure VS Code is installed. The bot now uses a more robust search method to find it!

---
*Stay modular, stay scalable.* 👏
