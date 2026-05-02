"""
WakeBot Vision Command — Full Awareness Mode (Unified)
Orchestrates ALL subsystems: Audio (Claps + Voice) AND Vision (Presence, Screen, VLM).
All subsystems share the same wake_event / sleep_event threading.Event instances.

Audio pipeline is embedded directly here to avoid the prior architectural disconnect
where 'run audio' and 'run vision' were completely separate, unconnectable code paths.
"""

import time
import queue
import threading
from wakebot.core import load_config, WakeBotLogger, WakeBotActions, WorkspaceState
from wakebot.core.event_bus import EventBus
from wakebot.core.audio_orchestrator import AudioOrchestrator
from wakebot.triggers.vision.presence import PresenceMonitor
from wakebot.triggers.vision.screen import ScreenMonitor
from wakebot.triggers.vision.multimodal import MultiModalEngine
from wakebot.core.dashboard import WakeBotDashboard
from colorama import Fore, Style


def run_vision():
    """Run the UNIFIED pipeline: Audio + Vision + Dashboard UI."""
    config = load_config()
    logger = WakeBotLogger(quiet=True)

    # Initialize Event Bus
    event_bus = EventBus()
    
    # WakeBotActions subscribes to EventBus automatically
    actions = WakeBotActions(logger=logger, event_bus=event_bus)

    # Resolve effective VLM provider (local_only overrides config)
    effective_vlm_provider = "ollama" if config.local_only else config.vlm_provider

    print(f"""
{Fore.CYAN}{Style.BRIGHT}    W A K E B O T  |  U N I F I E D  E N G I N E{Style.RESET_ALL}
{Fore.WHITE}    ------------------------------------------------
    [ STATUS ] Dashboard Active
    [ ENGINE ] Audio + Vision v2.1 (Unified)
    [ CTRL+C ] Graceful Shutdown
    ------------------------------------------------
    {Style.RESET_ALL}""")

    # Shared state container (thread-safe)
    workspace_state = WorkspaceState()
    
    # Frame queue for UI preview
    frame_queue = queue.Queue(maxsize=1)

    # ================================================================
    # AUDIO SUBSYSTEM (Consolidated)
    # ================================================================
    audio_orch = AudioOrchestrator(
        config=config,
        event_bus=event_bus,
        logger=logger
    )
    audio_paused = audio_orch.paused  # Linked to dashboard toggle

    # ================================================================
    # VISION SUBSYSTEM
    # ================================================================

    # ---- Phase 1: Presence Monitor ----
    presence = PresenceMonitor(
        event_bus=event_bus,
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
        presence_monitor=presence,  # Enable frame sharing
    )

    # ================================================================
    # SHARED CONTROL
    # ================================================================
    stop_all = threading.Event()

    # ================================================================
    # START ALL SUBSYSTEMS
    # ================================================================

    audio_orch.start()

    # Vision threads
    presence.start()
    screen.start()
    multimodal.start()
    logger.info("Vision subsystem started (presence + screen + VLM active).")

    # ================================================================
    # DASHBOARD UI (blocks main thread)
    # ================================================================
    try:
        dashboard = WakeBotDashboard(
            workspace_state=workspace_state,
            frame_queue=frame_queue,
            presence_monitor=presence,
            screen_monitor=screen,
            vlm_engine=multimodal,
            audio_engine=audio_orch.engine,
            clap_detector=audio_orch.clap_detector,
            voice_detector=audio_orch.voice_detector,
            audio_paused=audio_paused,
            logger=logger
        )
        dashboard.start_dashboard()
    except KeyboardInterrupt:
        pass
    finally:
        stop_all.set()
        audio_orch.stop()
        presence.stop()
        screen.stop()
        multimodal.stop()
        event_bus.stop()
        logger.info("All subsystems stopped. Cleanup complete.")
