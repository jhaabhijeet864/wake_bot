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
from wakebot.triggers.vision.presence import PresenceMonitor
from wakebot.triggers.vision.screen import ScreenMonitor
from wakebot.triggers.vision.multimodal import MultiModalEngine
from wakebot.triggers.audio.engine import AudioStream
from wakebot.triggers.audio.detector import ClapDetector
from wakebot.triggers.audio.voice import VoiceDetector
from wakebot.core.dashboard import WakeBotDashboard
from colorama import Fore, Style


def run_vision():
    """Run the UNIFIED pipeline: Audio + Vision + Dashboard UI."""
    config = load_config()
    logger = WakeBotLogger(quiet=True)
    actions = WakeBotActions(logger=logger)

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
    # SHARED EVENTS — The critical link between audio and vision
    # Both subsystems write to the SAME wake/sleep events.
    # ================================================================
    wake_event = threading.Event()
    sleep_event = threading.Event()
    stop_all = threading.Event()

    # ================================================================
    # AUDIO SUBSYSTEM
    # ================================================================
    audio_engine = AudioStream(
        chunk_size=config.chunk_size,
        sample_rate=config.sample_rate,
        channels=config.channels
    )

    clap_detector = None
    if config.clap_enabled:
        clap_detector = ClapDetector(
            threshold=config.threshold,
            double_clap_window_ms=config.double_clap_window_ms
        )

    voice_detector = None
    if config.voice_enabled:
        try:
            voice_detector = VoiceDetector(
                model_path=config.model_path,
                sample_rate=config.sample_rate,
                wake_phrases=config.wake_phrases
            )
        except Exception as e:
            logger.error(f"Failed to initialize voice detector: {e}")

    audio_queue = queue.Queue(maxsize=20)
    audio_paused = threading.Event()  # Dashboard toggle control

    def audio_producer():
        """Producer thread: captures microphone stream and feeds the queue."""
        if not audio_engine.start_stream():
            logger.error("Audio stream failed to start. Check microphone permissions.")
            return
        logger.info("Audio Producer thread active — microphone streaming.")

        while not stop_all.is_set():
            if audio_paused.is_set():
                time.sleep(0.1)
                continue
            try:
                chunk = audio_engine.read_chunk()
                if not audio_queue.full():
                    audio_queue.put_nowait(chunk)
            except Exception:
                audio_engine.restart_stream()
                time.sleep(1)

    def detection_worker():
        """Worker thread: processes audio for claps and feeds voice detector."""
        while not stop_all.is_set():
            if audio_paused.is_set():
                time.sleep(0.1)
                continue
            try:
                chunk = audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                # Process Claps
                if clap_detector:
                    rms = audio_engine.calculate_rms(chunk)
                    clap_action = clap_detector.process(rms)

                    if clap_action == "SINGLE":
                        wake_event.set()
                    elif clap_action == "DOUBLE":
                        sleep_event.set()

                # Process Voice (Feed the model)
                if voice_detector:
                    voice_detector.add_audio(chunk)

                audio_queue.task_done()
            except Exception:
                pass

    def voice_watcher():
        """Watcher thread: monitors voice detector for keyword matches."""
        while not stop_all.is_set():
            if audio_paused.is_set():
                time.sleep(0.1)
                continue
            if voice_detector and voice_detector.check_and_reset():
                logger.info("Voice match detected: Triggering Welcome Home sequence.")
                wake_event.set()
            time.sleep(0.1)

    # ================================================================
    # VISION SUBSYSTEM
    # ================================================================

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
        presence_monitor=presence,  # Enable frame sharing
    )

    # ================================================================
    # MASTER ORCHESTRATION THREAD
    # Polls shared events and dispatches actions.
    # ================================================================
    def orchestrator():
        logger.info("Orchestration thread active — polling audio + vision events.")
        last_action_time = 0.0
        cooldown = config.action_cooldown_s
        while not stop_all.is_set():
            now = time.time()
            if wake_event.is_set():
                if now - last_action_time >= cooldown:
                    logger.action("UNIFIED TRIGGER: Welcome Home Sequence")
                    workspace_state.set("user_present", True)
                    actions.welcome_home()
                    last_action_time = time.time()
                else:
                    logger.info("Wake event ignored (cooldown active).")
                wake_event.clear()
                sleep_event.clear()

            if sleep_event.is_set():
                if now - last_action_time >= cooldown:
                    logger.action("UNIFIED TRIGGER: Goodnight Sequence")
                    workspace_state.set("user_present", False)
                    actions.goodnight()
                    last_action_time = time.time()
                else:
                    logger.info("Sleep event ignored (cooldown active).")
                wake_event.clear()
                sleep_event.clear()
            time.sleep(0.1)

    orch_thread = threading.Thread(target=orchestrator, daemon=True)

    # ================================================================
    # START ALL SUBSYSTEMS
    # ================================================================

    # Audio threads
    if voice_detector:
        voice_detector.start()

    audio_threads = [
        threading.Thread(target=audio_producer, name="AudioProducer", daemon=True),
        threading.Thread(target=detection_worker, name="DetectionWorker", daemon=True),
        threading.Thread(target=voice_watcher, name="VoiceWatcher", daemon=True),
    ]
    for t in audio_threads:
        t.start()
    logger.info("Audio subsystem started (clap + voice detection active).")

    # Vision threads
    presence.start()
    screen.start()
    multimodal.start()
    orch_thread.start()
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
            audio_engine=audio_engine,
            clap_detector=clap_detector,
            voice_detector=voice_detector,
            audio_paused=audio_paused,
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
        if voice_detector:
            voice_detector.stop()
        audio_engine.stop_stream()
        logger.info("All subsystems stopped. Cleanup complete.")
