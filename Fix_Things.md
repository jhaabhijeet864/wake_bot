# WakeBot Finalization & Optimization Plan

This document outlines the final steps to transition WakeBot from a restructured prototype to a fully finalized, modular, and scalable production-grade application.

## 1. 🏗️ Architectural Refinement
- [ ] **Consolidate Audio Orchestration**: Create `wakebot/core/audio_orchestrator.py`. Currently, `audio_cmd.py` and `vision_cmd.py` duplicate the 3-thread audio pipeline (Producer, DetectionWorker, VoiceWatcher).
- [ ] **Deepen EventBus Integration**: Update `vision_cmd.py` and `audio_cmd.py` to use `EventBus.emit()` for triggers instead of directly calling `actions` or setting shared `threading.Event` flags in the orchestrator.
- [ ] **Unified Action Dispatcher**: Ensure `WakeBotActions` is the sole listener for system-level events (USER_ARRIVED, USER_LEFT, CLAP_DETECTED).

## 2. 🧹 Phase 4: Final Cleanup (Restructuring Completion)
- [ ] **Relocate Scripts**: Move `setup.bat` and `setup.sh` from the root to the `scripts/` directory.
- [ ] **Remove Legacy Artifacts**:
    - Delete root-level `main.py`.
    - Remove the `src/` directory (all logic has been migrated to `wakebot/`).
    - Remove `camera_presence_bot.py` (if it still exists in some hidden corner, though not seen in tree).
- [ ] **Finalize `requirements.txt`**: Ensure the root `requirements.txt` is just a pointer or a consolidated version of `requirements/*.txt`.

## 3. 📝 Documentation & UX
- [ ] **Update README.md**: Reflect the unified CLI usage (`python -m wakebot run vision`) and the new modular structure.
- [ ] **Finalize CLI Help**: Ensure `python -m wakebot --help` is clean and informative.

## 4. 🧪 Validation & Testing
- [ ] **Manual Integration Test**: Verify Audio triggers (Claps/Voice) work in both `audio` and `vision` modes.
- [ ] **Vision Verification**: Confirm Presence, Screen, and VLM modules run concurrently without resource locks.
- [ ] **Dashboard Check**: Verify toggles (Audio/Vision) in the UI correctly pause/resume background threads.

---
*Buddy, let's get this done. We're making this bot truly "Big".*
