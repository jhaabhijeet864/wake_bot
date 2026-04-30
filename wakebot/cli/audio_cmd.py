"""
WakeBot Audio Command - Principal Architect Version
Threaded implementation of audio triggers (Claps & Voice) 
integrated with the "One Go" professional automation suite.
"""

import time
import threading
import queue
import os
from wakebot.core import load_config, WakeBotLogger, WakeBotActions
from wakebot.triggers.audio.engine import AudioStream
from wakebot.triggers.audio.detector import ClapDetector
from wakebot.triggers.audio.voice import VoiceDetector


def run_audio():
    """Run the audio automation loop using a threaded architecture"""
    # 1. Initialise configurations
    config = load_config()
    logger = WakeBotLogger()
    
    # Synchronization Events
    wake_event = threading.Event()
    sleep_event = threading.Event()
    
    # Initialize components
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
            config.voice_enabled = False

    actions = WakeBotActions(logger=logger)
    
    # Audio buffer for processing thread
    audio_queue = queue.Queue(maxsize=20)
    
    # 2. Thread Definitions
    
    def audio_producer():
        """Producer thread: captures microphone stream and feeds the queue"""
        if not audio_engine.start_stream():
            logger.error("Audio stream failed to start. Check microphone permissions.")
            return

        while True:
            try:
                chunk = audio_engine.read_chunk()
                if not audio_queue.full():
                    audio_queue.put_nowait(chunk)
            except Exception as e:
                # Robustness: Auto-restart stream on hardware disconnect
                audio_engine.restart_stream()
                time.sleep(1)

    def detection_worker():
        """Worker thread: processes audio for claps and feeds voice detector"""
        while True:
            try:
                chunk = audio_queue.get()
                
                # Process Claps
                if clap_detector:
                    rms = audio_engine.calculate_rms(chunk)
                    clap_action = clap_detector.process(rms)
                    
                    if clap_action == "SINGLE":
                        wake_event.set()
                    elif clap_action == "DOUBLE":
                        sleep_event.set() # Trigger the 'Goodnight' sequence
                
                # Process Voice (Feed the model)
                if voice_detector:
                    voice_detector.add_audio(chunk)
                
                audio_queue.task_done()
            except Exception as e:
                pass

    def voice_watcher():
        """Watcher thread: monitors voice detector for keyword matches"""
        while True:
            if voice_detector and voice_detector.check_and_reset():
                logger.info("Voice match detected: Triggering Welcome Home sequence.")
                wake_event.set()
            time.sleep(0.1)

    # Start detectors
    if voice_detector:
        voice_detector.start()

    # Launch daemon threads
    threads = [
        threading.Thread(target=audio_producer, name="AudioProducer", daemon=True),
        threading.Thread(target=detection_worker, name="DetectionWorker", daemon=True),
        threading.Thread(target=voice_watcher, name="VoiceWatcher", daemon=True)
    ]
    
    for t in threads:
        t.start()

    logger.info("WakeBot Audio system is active. Listening for triggers...")

    # 3. Master Orchestration Loop
    try:
        while True:
            # Check for Wake (Welcome Home)
            if wake_event.is_set():
                logger.action("INITIATING: Welcome Home Sequence")
                actions.welcome_home()
                # Clear BOTH events to ignore any false triggers caused by the music/noise during startup
                wake_event.clear()
                sleep_event.clear()
            
            # Check for Sleep (Goodnight)
            if sleep_event.is_set():
                logger.action("INITIATING: Goodnight Sequence")
                actions.goodnight()
                wake_event.clear()
                sleep_event.clear()
                
            time.sleep(0.1)

    except KeyboardInterrupt:
        logger.info("System shutdown requested by user.")
    finally:
        if voice_detector:
            voice_detector.stop()
        audio_engine.stop_stream()
        logger.info("Audio stream closed. Cleanup complete.")
