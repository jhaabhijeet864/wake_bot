"""
WakeBot Vision Command — Full Awareness Mode
Orchestrates all vision subsystems: Presence, Screen, and Multi-Modal.
Follows the same threading.Event pattern established in audio_cmd.py.
"""

import time
import queue
import threading
from wakebot.core import load_config, WakeBotLogger, WakeBotActions, WorkspaceState
from wakebot.triggers.vision.presence import PresenceMonitor
from wakebot.triggers.vision.screen import ScreenMonitor
from wakebot.triggers.vision.multimodal import MultiModalEngine
from wakebot.core.dashboard import WakeBotDashboard
from colorama import Fore, Style


def run_vision():
    """Run the full vision awareness pipeline with Dashboard UI."""
    config = load_config()
    logger = WakeBotLogger(quiet=True)
    actions = WakeBotActions(logger=logger)

    # Resolve effective VLM provider (local_only overrides config)
    effective_vlm_provider = "ollama" if config.local_only else config.vlm_provider

    print(f"""
{Fore.CYAN}{Style.BRIGHT}    W A K E B O T  |  V I S I O N  E N G I N E{Style.RESET_ALL}
{Fore.WHITE}    ------------------------------------------
    [ STATUS ] Dashboard Active
    [ ENGINE ] Multi-Modal v2.0
    [ CTRL+C ] Graceful Shutdown
    ------------------------------------------
    {Style.RESET_ALL}""")

    # Shared state container (thread-safe)
    workspace_state = WorkspaceState()
    
    # Frame queue for UI preview
    frame_queue = queue.Queue(maxsize=1)

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
    presence._frame_queue = frame_queue

    # ---- Phase 2: Screen Monitor ----
    screen = ScreenMonitor(
        workspace_state=workspace_state,
        interval=config.screen_interval,
        sensitive_apps=config.sensitive_apps,
        logger=logger,
    )

    # ---- Phase 3: Multi-Modal Engine ----
    multimodal = MultiModalEngine(
        workspace_state=workspace_state,
        camera_index=config.camera_index,
        vlm_provider=effective_vlm_provider,
        interval=config.vlm_interval,
        privacy_mode=config.privacy_mode,
        sensitive_apps=config.sensitive_apps,
        logger=logger,
        presence_monitor=presence, # Enable frame sharing
    )

    # Orchestration logic in a separate thread (so UI can stay on main)
    def orchestrator():
        logger.info("Orchestration thread active.")
        last_action_time = 0.0
        cooldown = config.action_cooldown_s
        while not stop_all.is_set():
            now = time.time()
            if wake_event.is_set():
                if now - last_action_time >= cooldown:
                    logger.action("VISION TRIGGER: Welcome Home Sequence")
                    workspace_state.set("user_present", True)
                    actions.welcome_home()
                    last_action_time = time.time()
                else:
                    logger.info("Wake event ignored (cooldown active).")
                wake_event.clear()
                sleep_event.clear()

            if sleep_event.is_set():
                if now - last_action_time >= cooldown:
                    logger.action("VISION TRIGGER: Goodnight Sequence")
                    workspace_state.set("user_present", False)
                    actions.goodnight()
                    last_action_time = time.time()
                else:
                    logger.info("Sleep event ignored (cooldown active).")
                wake_event.clear()
                sleep_event.clear()
            time.sleep(0.1)

    stop_all = threading.Event()
    orch_thread = threading.Thread(target=orchestrator, daemon=True)

    # Start all subsystems
    presence.start()
    screen.start()
    multimodal.start()
    orch_thread.start()

    # Launch Dashboard (Blocks Main Thread)
    try:
        dashboard = WakeBotDashboard(
            workspace_state=workspace_state,
            frame_queue=frame_queue,
            presence_monitor=presence,
            screen_monitor=screen,
            vlm_engine=multimodal,
            logger=logger
        )
        dashboard.start_dashboard()
    except KeyboardInterrupt:
        pass
    finally:
        stop_all.set()
        presence.stop()
        screen.stop()
        multimodal.stop()
        logger.info("All vision subsystems stopped. Cleanup complete.")

