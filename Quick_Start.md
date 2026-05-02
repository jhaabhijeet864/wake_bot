# 🚀 WakeBot Quick Start Guide

Welcome to the **WakeBot** (Big Bot v2.1) startup guide! This bot turns your PC into an autonomous workspace by reacting to your voice, claps, and even your physical presence.

---

## 🛠️ 1. First-Time Setup

Before you start, make sure you have the environment ready.

1.  **Install Dependencies**:
    Run the automated setup script:
    ```powershell
    .\setup.bat
    ```
2.  **Activate Environment**:
    Whenever you want to run commands manually, activate the venv first:
    ```powershell
    .\wakebot_env\Scripts\activate
    ```

---

## 🎧 2. Audio Calibration (CRITICAL)

To make sure the bot hears your claps but ignores your keyboard/background noise:

```powershell
python -m wakebot calibrate
```
> [!TIP]
> Sit quietly for 5 seconds, then **clap loudly 5 times** when prompted. This updates your `wakebot_config.json` with the perfect threshold.

---

## 🏃 3. Running WakeBot

### 🌟 The Unified Mode (Recommended)
This starts **everything** at once: Claps, Voice, Face Detection, and Screen Awareness.

```powershell
python -m wakebot run vision
```
- **What it does**: Opens the **Control Center Dashboard**.
- **Features**: 🎧 Audio + 👤 Presence + 🖥️ Screen OCR + 🧠 AI VLM.
- **Toggles**: You can pause/resume any module directly from the Dashboard sidebar.

### 🎧 Audio-Only Mode (Lightweight)
Use this if you don't have a webcam or want to save CPU.

```powershell
python -m wakebot run audio
```
- **What it does**: Runs in the terminal.
- **Features**: Claps and Voice commands only.

### 📥 System Tray Mode
Run WakeBot quietly in the background.

```powershell
python -m wakebot tray
```
- **What it does**: Adds an icon to your Windows Taskbar (near the clock).
- **Control**: Right-click the icon to switch between Audio and Vision modes.

---

## 🎮 4. Triggers & Actions

| Trigger | Action ⚡ |
| :--- | :--- |
| **👏 Single Clap** | **Welcome Home**: Wakes PC, opens VS Code, plays Spotify. |
| **👏👏 Double Clap** | **Goodnight**: Pauses music, turns off the monitor. |
| **🗣️ "Wake up"** | Voice trigger for the Welcome Home sequence. |
| **👤 Walk-up** | (Vision) Detected face → Triggers Welcome Home. |
| **🚶 Walk-away** | (Vision) Absent for 2 mins → Triggers Goodnight. |

---

## 🧠 5. AI Vision (Gemini Setup)

To use the **AI Multi-Modal** features (where the bot "sees" what you're doing):

1.  Get a Gemini API Key from [Google AI Studio](https://aistudio.google.com/).
2.  Set it in WakeBot:
    ```powershell
    python -m wakebot credentials set GEMINI_API_KEY your_key_here
    ```
3.  Ensure `"vlm_provider": "gemini"` is set in `wakebot_config.json`.

---

## 🧪 6. Testing & Troubleshooting

- **Check API Keys**: `python -m wakebot credentials get GEMINI_API_KEY`
- **Check Startup Status**: `python -m wakebot startup status`
- **Microphone Issues**: Run `calibrate` again. Ensure "Allow apps to access your microphone" is ON in Windows Settings.
- **Camera Issues**: Ensure no other app (Zoom/Teams) is using the webcam.

---

## 📂 Project Structure At-a-Glance
- `wakebot/cli/` — Command handlers (where the magic starts).
- `wakebot/triggers/` — Audio and Vision sensors.
- `wakebot/core/` — Actions, Config, and Dashboard UI.
- `wakebot_config.json` — Your personal settings.

---
**👏 Happy Automating!**
*Built for the Principal Architect workflow.*
