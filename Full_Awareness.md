# Wake_Bot: Comprehensive Spatial & Contextual Awareness Architecture

## 1. MACRO-ANALYSIS
Integrating Computer Vision (CV) into `Wake_Bot` shifts the application from a reactive script (waking up via hardware triggers/hotkeys) to a **proactive, context-aware environment orchestrator**. This impacts:
- **Main Thread & Event Bus**: CV tasks (especially frame processing or deep learning inference) are computationally heavy and blocking. They **must** run on dedicated background threads or separate processes to prevent lagging the Windows API interactions or audio triggers in `wakebot/core/actions.py`.
- **Hardware Constraints**: Continuous camera feeds and frame processing consume CPU/GPU and battery. We need a "sleep/wake" cycle for the camera itself to avoid 100% constant utilization.
- **Privacy & Permissions**: Windows requires explicit permissions for camera access, and background camera usage might trigger Windows privacy overlays. 

---

## 2. EDGE-CASE PREDICTION & MITIGATION
1. **Resource Starvation (Thread Blocking)**: If CV inference runs on the main thread, the bot will miss audio triggers or fail to execute the VS Code orchestration smoothly. 
   * **Mitigation**: Offload CV processing to an isolated daemon thread with a shared thread-safe queue. Use an Event Bus to broadcast state changes.
2. **Camera Locking / Device Conflicts**: If the bot holds an exclusive lock on the webcam, the user won't be able to use Zoom or Teams. 
   * **Mitigation**: The bot must gracefully release the camera hook when another application requests it, or use screen-capture as a fallback. Implement a `cv2.VideoCapture(0)` `try/except` loop to detect locks and sleep/retry.
3. **Lighting & False Positives**: In a dark room (during the `goodnight` sequence), facial recognition will fail or trigger erratically. 
   * **Mitigation**: Implement a dynamic threshold based on ambient screen brightness or time of day. Add debouncing (e.g., must be out of frame for > 2 minutes to trigger `goodnight`).

---

## 3. COMPLETE EXECUTION: Phased Implementation Plan
To achieve "Option 3: Ultimate Multi-Modal Awareness" safely, we will chain Options 1, 2, and 3 as stepping stones. This ensures modularity and stability.

### Phase 1: Foundation - Lightweight Presence & Posture (Option 1)
*Best for: Fast implementation, low CPU usage, testing thread safety.*
* **Concept**: The bot uses your webcam to detect if you are at your desk, if you are looking at the screen, and your basic posture (e.g., slumped over vs. actively working).
* **Triggers**:
  - *Walk-up Trigger*: Automatically fires `WakeBotActions.welcome_home()` when you sit down.
  - *Walk-away Trigger*: Automatically fires `WakeBotActions.goodnight()` when you leave the frame for > 2 minutes.
* **Tech Stack**: `opencv-python` (cv2) for video capture, `mediapipe` for ultra-fast face and body mesh detection.
* **Architecture**: A new module `wakebot/triggers/vision/presence.py` running a background `threading.Thread` sampling the camera at 5 FPS to save CPU.

### Phase 2: Contextual Expansion - Screen & OCR Awareness (Option 2)
*Best for: Making the bot aware of your digital surroundings and current tasks.*
* **Concept**: The bot continuously "reads" your screen to understand what you are working on. It knows if you are stuck on an error in VS Code, watching a YouTube video, or reading documentation.
* **Triggers**:
  - *Contextual Actions*: If it sees an error trace in VS Code, it can proactively offer a solution via TTS (if added later).
  - *Media Awareness*: If it detects a full-screen game or Netflix, it suspends its own notifications to avoid interrupting you.
* **Tech Stack**: `mss` (fastest python screen grabber), `easyocr` or `pytesseract` for reading text.
* **Architecture**: A module `wakebot/triggers/vision/screen.py` that takes a screenshot every 5-10 seconds, extracts text, and updates a global `WorkspaceState` dictionary.

### Phase 3: Ultimate Multi-Modal Awareness (Option 3)
*Best for: A true "JARVIS-like" intelligent assistant.*
* **Concept**: Combines Webcam feeds and Screen captures, sending them periodically to a Vision-Language Model (VLM). The bot can answer questions like "Where did I leave my phone?" (from camera) or "What line is my bug on?" (from screen).
* **Triggers**:
  - *Dynamic Interrogation*: You can ask "What am I holding?" and it uses the camera to identify the object.
  - *Behavioral Syncing*: The bot recognizes the state of the room (e.g., lights are off) and automatically adjusts system volume and screen brightness.
* **Tech Stack**: `cv2` + API integration to a local `Ollama` instance running LLaVA, or a cloud API like Gemini 1.5 Pro.
* **Architecture**: A dual-feed system `wakebot/triggers/vision/multimodal.py` capturing frames, converting them to base64, and pinging the VLM on a 15-second interval or via a hotword trigger from `audio/detector.py`.

---

## 4. STRUCTURAL & ARCHITECTURAL INTEGRATION
To maintain modularity for future improvements, the directory structure will be expanded exactly as follows. This fits perfectly adjacent to the existing `wakebot/triggers/audio/detector.py`.

```text
Wake_Bot/
├── wakebot/
│   ├── core/
│   │   ├── actions.py         # Modified to listen to EventBus
│   │   └── event_bus.py       # [NEW] Thread-safe Pub/Sub coordinator
│   ├── cli/
│   │   ├── main.py
│   │   └── audio_cmd.py
│   ├── triggers/
│   │   ├── audio/
│   │   │   └── detector.py    # Existing
│   │   └── vision/            # [NEW MODULES]
│   │       ├── __init__.py
│   │       ├── base_vision.py # Abstract base class for vision threads
│   │       ├── presence.py    # Phase 1 implementation
│   │       ├── screen.py      # Phase 2 implementation
│   │       └── multimodal.py  # Phase 3 implementation
```

## 5. SELF-VERIFICATION & NEXT STEPS
* **Thread Safety**: By using `event_bus.py`, the vision scripts will emit events (e.g., `EventBus.emit('USER_ARRIVED')`) rather than directly instantiating `WakeBotActions`. The main thread will listen for these events and execute `self.welcome_home()`.
* **Clean Code**: `actions.py` remains strictly focused on action execution (Windows API, Spotify, VS Code). It does not need to know *how* a trigger occurred, only that it *did*.
* **Step 1 to Execute**: Create `wakebot/core/event_bus.py` to establish the communication layer, then scaffold `wakebot/triggers/vision/presence.py`.
