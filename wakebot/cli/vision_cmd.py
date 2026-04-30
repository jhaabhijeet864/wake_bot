"""
WakeBot Vision Command — Full Awareness Mode
Orchestrates all vision subsystems: Presence, Screen, and Multi-Modal.
Follows the same threading.Event pattern established in audio_cmd.py.
"""

import time
import threading
from wakebot.core import load_config, WakeBotLogger, WakeBotActions, WorkspaceState
from wakebot.triggers.vision.presence import PresenceMonitor
from wakebot.triggers.vision.screen import ScreenMonitor
from wakebot.triggers.vision.multimodal import MultiModalEngine


def run_vision():
    """Run the full vision awareness pipeline."""
    config = load_config()
    logger = WakeBotLogger()
    actions = WakeBotActions(logger=logger)

    # Shared state container (thread-safe)
    workspace_state = WorkspaceState()

    # Shared threading events (same pattern as audio_cmd.py)
    wake_event = threading.Event()
    sleep_event = threading.Event()

    # ---- Phase 1: Presence Monitor ----
    presence = PresenceMonitor(
        wake_event=wake_event,
        sleep_event=sleep_event,
        camera_index=config.camera_index,
        target_fps=config.vision_fps,
        absence_threshold=config.absence_threshold,
        logger=logger,
    )

    # ---- Phase 2: Screen Monitor ----
    screen = ScreenMonitor(
        workspace_state=workspace_state,
        interval=config.screen_interval,
        logger=logger,
    )

    # ---- Phase 3: Multi-Modal Engine ----
    multimodal = MultiModalEngine(
        workspace_state=workspace_state,
        camera_index=config.camera_index,
        vlm_provider=config.vlm_provider,
        interval=config.vlm_interval,
        logger=logger,
    )

    print("""
    ╔═══════════════════════════════════════╗
    ║      WakeBot Full Awareness Mode      ║
    ║  Phase 1: Presence Detection          ║
    ║  Phase 2: Screen & OCR Awareness      ║
    ║  Phase 3: Multi-Modal VLM             ║
    ╚═══════════════════════════════════════╝

    Press Ctrl+C to exit
    """)

    # Start all subsystems
    presence.start()
    screen.start()
    multimodal.start()

    logger.info("Full Awareness Mode active. All vision subsystems running.")

    # Master Orchestration Loop (mirrors audio_cmd.py pattern)
    try:
        while True:
            if wake_event.is_set():
                logger.action("VISION TRIGGER: Welcome Home Sequence")
                workspace_state.set("user_present", True)
                actions.welcome_home()
                wake_event.clear()
                sleep_event.clear()

            if sleep_event.is_set():
                logger.action("VISION TRIGGER: Goodnight Sequence")
                workspace_state.set("user_present", False)
                actions.goodnight()
                wake_event.clear()
                sleep_event.clear()

            time.sleep(0.1)

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user.")
    finally:
        presence.stop()
        screen.stop()
        multimodal.stop()
        logger.info("All vision subsystems stopped. Cleanup complete.")
