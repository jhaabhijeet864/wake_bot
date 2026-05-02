"""
WakeBot Audio Command - Consolidated Version
Uses AudioOrchestrator and EventBus for clean, decoupled audio triggering.
"""

import time
from wakebot.core import load_config, WakeBotLogger, WakeBotActions
from wakebot.core.event_bus import EventBus
from wakebot.core.audio_orchestrator import AudioOrchestrator


def run_audio():
    """Run the audio automation loop using a threaded architecture"""
    # 1. Initialise configurations
    config = load_config()
    logger = WakeBotLogger()
    
    # Initialize Event Bus
    event_bus = EventBus()
    
    # WakeBotActions subscribes to EventBus automatically for USER_ARRIVED and USER_LEFT
    actions = WakeBotActions(logger=logger, event_bus=event_bus)
    
    # ================================================================
    # AUDIO SUBSYSTEM (Consolidated)
    # ================================================================
    audio_orch = AudioOrchestrator(
        config=config,
        event_bus=event_bus,
        logger=logger
    )
    
    # Launch audio threads
    audio_orch.start()

    logger.info("WakeBot Audio system is active. Listening for triggers...")

    # 3. Master Orchestration Loop (Idle wait while EventBus handles actions)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("System shutdown requested by user.")
    finally:
        audio_orch.stop()
        event_bus.stop()
        logger.info("Audio stream closed. Cleanup complete.")
