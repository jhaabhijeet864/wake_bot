# Background & Motivation
The current `Wake_Bot` project has grown organically, resulting in a mix of different domains (Audio/Clap detection vs. Camera/Presence detection) residing at the project root. The file structure is messy, with scattered entry points (`main.py`, `calibrate.py`, `camera_presence_bot.py`), duplicate system action logic (screen locking/waking in both bots), and mixed configuration/requirement files. To achieve an industry-grade, scalable software, we need a complete restructuring into a unified, modular architecture.

# Objective
Implement a **Unified Pluggable Architecture** for the Wake_Bot project. This will allow the software to be easily extended with new triggers (e.g., Bluetooth, Network) while sharing core system functionalities (logging, configuration, OS-level actions) and maintaining a clean, professional directory structure.

# Scope & Impact
- **Root Directory:** Cleaned up. Scripts, docs, and configs moved to dedicated folders.
- **Core Package (`wakebot/`):** A new unified Python package encapsulating all logic.
- **Unified CLI:** A single entry point (e.g., `python -m wakebot run audio` or `python -m wakebot calibrate`) replaces scattered top-level scripts.
- **Dependencies:** Requirements will be split into logical components (`base`, `audio`, `vision`, `dev`) for efficient installation.
- **Testing:** Test scaffolding will be introduced.

# Proposed Architecture

```text
Wake_Bot/
├── .gitignore
├── pyproject.toml              # Modern dependency & metadata management (or setup.py)
├── README.md                   # Unified project documentation
├── docs/                       # Detailed component documentation
│   ├── audio_bot.md
│   └── camera_bot.md
├── scripts/                    # Environment setup scripts
│   ├── setup.bat
│   └── setup.sh
├── requirements/               # Organized dependencies
│   ├── base.txt                # Common (pyautogui, colorama)
│   ├── audio.txt               # Audio specific (pyaudio)
│   ├── vision.txt              # Camera specific (opencv-python, torch)
│   └── dev.txt                 # Dev tools (pytest, etc.)
├── tests/                      # Unit and integration tests
│   ├── conftest.py
│   ├── test_core/
│   ├── test_triggers/
│   └── test_cli/
└── wakebot/                    # Main package source code
    ├── __init__.py
    ├── __main__.py             # Unified CLI entry point
    ├── core/                   # Shared business logic
    │   ├── __init__.py
    │   ├── actions.py          # Unified OS-level actions (lock, sleep, wake)
    │   ├── config.py           # Unified configuration management interface
    │   └── logger.py           # Centralized logging
    ├── triggers/               # Pluggable event triggers
    │   ├── __init__.py
    │   ├── audio/              # Audio processing & clap detection
    │   │   ├── __init__.py
    │   │   ├── engine.py       # Stream management (from audio_engine.py)
    │   │   ├── detector.py     # Clap logic (from clap_detector.py)
    │   │   └── voice.py        # [NEW] Vosk-based offline voice recognition
    │   └── vision/             # Camera processing & person detection
    │       ├── __init__.py
    │       ├── engine.py       # Camera setup (from camera_presence_bot.py)
    │       └── detector.py     # Person/Face detection logic
    └── cli/                    # Command Line Interface routing
        ├── __init__.py
        ├── main.py             # Argument parser (argparse)
        ├── audio_cmd.py        # Logic for running audio bot
        ├── vision_cmd.py       # Logic for running camera bot
        └── calibrate_cmd.py    # Logic for running calibration
```

# Implementation Plan

### Phase 1: Directory Setup & Core Consolidation
1. Create the new directory skeleton (`wakebot/`, `docs/`, `scripts/`, `requirements/`, `tests/`).
2. Move `setup.bat` and `setup.sh` to `scripts/`.
3. Create the `requirements/` folder and split the current `requirements.txt` and `camera_requirements.txt` into `base.txt`, `audio.txt`, `vision.txt`, and `dev.txt`. Add a `pyproject.toml` (or `setup.py`) for package metadata.
4. Refactor `src/actions.py` and `camera_presence_bot.py`'s action logic (lock, sleep, wake) into a unified `wakebot/core/actions.py`.
5. Move and refactor `src/logger.py` to `wakebot/core/logger.py`.
6. Create `wakebot/core/config.py` to handle dynamic loading of module-specific configurations.

### Phase 2: Refactoring Triggers
1. **Audio Trigger:** Move `src/audio_engine.py` to `wakebot/triggers/audio/engine.py` and `src/clap_detector.py` to `wakebot/triggers/audio/detector.py`.
2. **Offline Voice Trigger:** Integrate `src/voice_detector.py` into `wakebot/triggers/audio/voice.py`. Ensure Vosk model paths and restricted grammar settings are handled via the unified config.
3. **Vision Trigger:** Break down `camera_presence_bot.py` into modular components: `wakebot/triggers/vision/engine.py` (camera handling) and `wakebot/triggers/vision/detector.py` (OpenCV/YOLO logic).

### Phase 3: Unified CLI & Entry Points
1. Build a robust CLI in `wakebot/cli/main.py` using `argparse`.
2. Migrate `main.py` (audio loop) into `wakebot/cli/audio_cmd.py`.
3. Migrate `camera_presence_bot.py` (main loop) into `wakebot/cli/vision_cmd.py`.
4. Migrate `calibrate.py` into `wakebot/cli/calibrate_cmd.py`.
5. Set up `wakebot/__main__.py` to route to the CLI.

### Phase 4: Cleanup & Documentation
1. Delete the old root-level scripts (`main.py`, `calibrate.py`, `camera_presence_bot.py`, `src/`).
2. Move `CAMERA_BOT_README.md` to `docs/vision_bot.md` and rewrite `README.md` to reflect the new unified architecture and usage instructions.
3. Setup basic test files in `tests/` to ensure the core actions can be tested.

# Verification & Testing
- Run `python -m wakebot run audio` to verify the clap detection works.
- Run `python -m wakebot run vision` to verify the camera detection works.
- Run `python -m wakebot calibrate` to ensure calibration still functions correctly.
- Verify that OS-level actions (lock/wake) trigger correctly for both modules using the unified `actions.py`.

# Migration & Rollback
- Ensure all existing configuration files (`wakebot_config.json`, `camera_bot_config.json`) are supported by the new unified config loader or migrated gracefully.
- The `src/` directory and root scripts will be deleted only in Phase 4, ensuring the new code is written side-by-side before the final swap. If severe issues occur during migration, we can checkout the previous git state.
