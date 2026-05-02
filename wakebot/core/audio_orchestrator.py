"""
WakeBot Audio Orchestrator
Consolidates the 3-thread audio pipeline (Producer, Worker, Watcher)
to eliminate code duplication between audio and vision commands.
"""

import time
import queue
import threading
from typing import Optional

from wakebot.core.logger import WakeBotLogger
from wakebot.core.config import WakeBotConfig
from wakebot.triggers.audio.engine import AudioStream
from wakebot.triggers.audio.detector import ClapDetector
from wakebot.triggers.audio.voice import VoiceDetector


class AudioOrchestrator:
    """
    Manages the lifecycle of audio detection threads.
    Decouples audio processing from CLI command logic.
    """

    def __init__(
        self,
        config: WakeBotConfig,
        event_bus=None,
        wake_event: Optional[threading.Event] = None,
        sleep_event: Optional[threading.Event] = None,
        logger: Optional[WakeBotLogger] = None,
    ):
        self.config = config
        self.event_bus = event_bus
        self.wake_event = wake_event
        self.sleep_event = sleep_event
        self.logger = logger or WakeBotLogger()

        # Audio Components
        self.engine = AudioStream(
            chunk_size=config.chunk_size,
            sample_rate=config.sample_rate,
            channels=config.channels
        )

        self.clap_detector = None
        if config.clap_enabled:
            self.clap_detector = ClapDetector(
                threshold=config.threshold,
                double_clap_window_ms=config.double_clap_window_ms
            )

        self.voice_detector = None
        if config.voice_enabled:
            try:
                self.voice_detector = VoiceDetector(
                    model_path=config.model_path,
                    sample_rate=config.sample_rate,
                    wake_phrases=config.wake_phrases
                )
            except Exception as e:
                self.logger.error(f"Failed to initialize voice detector: {e}")

        # Threading infrastructure
        self.audio_queue = queue.Queue(maxsize=20)
        self.stop_all = threading.Event()
        self.paused = threading.Event()
        self.threads = []

    def start(self):
        """Initialize and start all audio threads."""
        if self.voice_detector:
            self.voice_detector.start()

        self.threads = [
            threading.Thread(target=self._producer_loop, name="AudioProducer", daemon=True),
            threading.Thread(target=self._worker_loop, name="DetectionWorker", daemon=True),
            threading.Thread(target=self._voice_watcher_loop, name="VoiceWatcher", daemon=True),
        ]

        for t in self.threads:
            t.start()
        
        self.logger.info("Audio Orchestrator active — threads started.")

    def stop(self):
        """Gracefully stop all audio threads."""
        self.stop_all.set()
        if self.voice_detector:
            self.voice_detector.stop()
        self.engine.stop_stream()
        self.logger.info("Audio Orchestrator stopped.")

    def pause(self):
        """Pause audio processing."""
        self.paused.set()

    def resume(self):
        """Resume audio processing."""
        self.paused.clear()

    # ------------------------------------------------------------------
    # Thread Loops
    # ------------------------------------------------------------------

    def _producer_loop(self):
        """Producer thread: captures microphone stream and feeds the queue."""
        if not self.engine.start_stream():
            self.logger.error("Audio stream failed to start. Check microphone permissions.")
            return

        while not self.stop_all.is_set():
            if self.paused.is_set():
                time.sleep(0.1)
                continue
            try:
                chunk = self.engine.read_chunk()
                if not self.audio_queue.full():
                    self.audio_queue.put_nowait(chunk)
            except Exception:
                self.engine.restart_stream()
                time.sleep(1)

    def _worker_loop(self):
        """Worker thread: processes audio for claps and feeds voice detector."""
        while not self.stop_all.is_set():
            if self.paused.is_set():
                time.sleep(0.1)
                continue
            try:
                chunk = self.audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                # Process Claps
                if self.clap_detector:
                    rms = self.engine.calculate_rms(chunk)
                    clap_action = self.clap_detector.process(rms)

                    if clap_action == "SINGLE":
                        self._trigger_wake()
                    elif clap_action == "DOUBLE":
                        self._trigger_sleep()

                # Process Voice (Feed the model)
                if self.voice_detector:
                    self.voice_detector.add_audio(chunk)

                self.audio_queue.task_done()
            except Exception as e:
                self.logger.error(f"Audio worker error: {e}")

    def _voice_watcher_loop(self):
        """Watcher thread: monitors voice detector for keyword matches."""
        while not self.stop_all.is_set():
            if self.paused.is_set():
                time.sleep(0.1)
                continue
            if self.voice_detector and self.voice_detector.check_and_reset():
                self.logger.info("Voice match detected.")
                self._trigger_wake()
            time.sleep(0.1)

    # ------------------------------------------------------------------
    # Trigger Helpers
    # ------------------------------------------------------------------

    def _trigger_wake(self):
        """Emit USER_ARRIVED to event bus."""
        if self.wake_event:
            self.wake_event.set()
        if self.event_bus:
            self.event_bus.emit("USER_ARRIVED", {"source": "audio"})

    def _trigger_sleep(self):
        """Emit USER_LEFT to event bus."""
        if self.sleep_event:
            self.sleep_event.set()
        if self.event_bus:
            self.event_bus.emit("USER_LEFT", {"source": "audio"})
