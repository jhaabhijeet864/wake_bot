"""
WakeBot Vision Command — Unified Orchestrator (v2.1.0)
Entry point for full Multi-Modal Awareness mode.
Uses EventBus for decoupled communication.
"""

import time
import queue
import threading
from wakebot.core import load_config, WakeBotLogger, WorkspaceState
from wakebot.core.event_bus import EventBus
from wakebot.core.audio_orchestrator import AudioOrchestrator
from wakebot.core.actions import WakeBotActions
from wakebot.triggers.vision.presence import PresenceMonitor
from wakebot.triggers.vision.screen import ScreenMonitor
from wakebot.triggers.vision.multimodal import MultiModalEngine
from wakebot.core.dashboard import WakeBotDashboard
from colorama import Fore, Style

def run_vision():
    """Start the unified automation suite."""
    config = load_config()
    logger = WakeBotLogger(quiet=True)
    
    # Core Infrastructure
    event_bus = EventBus()
    workspace_state = WorkspaceState()
    
    # Dispatcher (Automatically subscribes to events)
    actions = WakeBotActions(logger=logger)

    print(f"""
{Fore.CYAN}{Style.BRIGHT}    W A K E B O T  |  U N I F I E D  E N G I N E  (v2.1.0){Style.RESET_ALL}
{Fore.WHITE}    -------------------------------------------------------
    [ STATUS ] EventBus Active
    [ ENGINE ] Decoupled Orchestration
    [ CTRL+C ] Graceful Shutdown
    -------------------------------------------------------
    {Style.RESET_ALL}""")

    # 1. Start Audio Subsystem
    audio = AudioOrchestrator(config)
    audio.start()

    # 2. Start Vision Subsystems
    frame_queue = queue.Queue(maxsize=1)
    
    presence = PresenceMonitor(
        camera_index=config.camera_index,
        target_fps=config.vision_fps,
        absence_threshold=config.absence_threshold,
        logger=logger
    )
    presence.frame_queue = frame_queue

    screen = ScreenMonitor(
        workspace_state=workspace_state,
        interval=config.screen_interval,
        sensitive_apps=config.sensitive_apps,
        logger=logger
    )

    multimodal = MultiModalEngine(
        workspace_state=workspace_state,
        camera_index=config.camera_index,
        vlm_provider=config.vlm_provider,
        interval=config.vlm_interval,
        privacy_mode=config.privacy_mode,
        sensitive_apps=config.sensitive_apps,
        logger=logger,
        presence_monitor=presence
    )

    presence.start()
    screen.start()
    multimodal.start()

    # 3. Launch Dashboard (Blocks Main Thread)
    try:
        dashboard = WakeBotDashboard(
            workspace_state=workspace_state,
            frame_queue=frame_queue,
            presence_monitor=presence,
            screen_monitor=screen,
            vlm_engine=multimodal,
            audio_orchestrator=audio,
            logger=logger
        )
        dashboard.start_dashboard()
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down subsystems...")
        audio.stop()
        presence.stop()
        screen.stop()
        multimodal.stop()
        logger.info("Shutdown complete.")
