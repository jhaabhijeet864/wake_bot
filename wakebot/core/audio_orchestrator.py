"""
WakeBot Audio Orchestrator
Centralized management for the 3-thread audio pipeline:
1. Producer (Microphone Stream)
2. Worker (Clap Detection)
3. Watcher (Voice Recognition)
"""

import time
import threading
import queue
from typing import Optional
from wakebot.core.logger import WakeBotLogger
from wakebot.core.event_bus import EventBus
from wakebot.triggers.audio.engine import AudioStream
from wakebot.triggers.audio.detector import ClapDetector
from wakebot.triggers.audio.voice import VoiceDetector

class AudioOrchestrator:
    """
    Manages audio detection threads and emits events via EventBus.
    """
    def __init__(self, config):
        self.config = config
        self.logger = WakeBotLogger()
        self.event_bus = EventBus()
        self.stop_event = threading.Event()
        self.paused = threading.Event()
        
        # Components
        self.audio_engine = AudioStream(
            chunk_size=config.chunk_size,
            sample_rate=config.sample_rate,
            channels=config.channels
        )
        
        self.clap_detector = None
        if getattr(config, 'clap_enabled', True):
            self.clap_detector = ClapDetector(
                threshold=config.threshold,
                double_clap_window_ms=config.double_clap_window_ms
            )
            
        self.voice_detector = None
        if getattr(config, 'voice_enabled', True):
            try:
                self.voice_detector = VoiceDetector(
                    model_path=config.model_path,
                    sample_rate=config.sample_rate,
                    wake_phrases=config.wake_phrases
                )
            except Exception as e:
                self.logger.error(f"Voice Detector failed to init: {e}")

        self.audio_queue = queue.Queue(maxsize=20)
        self.threads = []

    def _producer_loop(self):
        """Microphone capture loop."""
        if not self.audio_engine.start_stream():
            self.logger.error("Audio stream failed to start.")
            return
        
        while not self.stop_event.is_set():
            if self.paused.is_set():
                time.sleep(0.1)
                continue
            try:
                chunk = self.audio_engine.read_chunk()
                if not self.audio_queue.full():
                    self.audio_queue.put_nowait(chunk)
            except Exception:
                self.audio_engine.restart_stream()
                time.sleep(1)

    def _worker_loop(self):
        """Clap processing loop."""
        while not self.stop_event.is_set():
            if self.paused.is_set():
                time.sleep(0.1)
                continue
            try:
                chunk = self.audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                if self.clap_detector:
                    rms = self.audio_engine.calculate_rms(chunk)
                    action = self.clap_detector.process(rms)
                    if action == "SINGLE":
                        self.event_bus.emit("USER_ARRIVED", {"source": "clap"})
                    elif action == "DOUBLE":
                        self.event_bus.emit("USER_LEFT", {"source": "clap"})
                
                if self.voice_detector:
                    self.voice_detector.add_audio(chunk)
                
                self.audio_queue.task_done()
            except Exception:
                pass

    def _watcher_loop(self):
        """Voice recognition loop."""
        while not self.stop_event.is_set():
            if self.paused.is_set():
                time.sleep(0.1)
                continue
            if self.voice_detector and self.voice_detector.check_and_reset():
                self.logger.info("Voice hotword detected.")
                self.event_bus.emit("USER_ARRIVED", {"source": "voice"})
            time.sleep(0.1)

    def start(self):
        """Start all audio threads."""
        self.stop_event.clear()
        if self.voice_detector:
            self.voice_detector.start()
            
        self.threads = [
            threading.Thread(target=self._producer_loop, name="AudioProducer", daemon=True),
            threading.Thread(target=self._worker_loop, name="AudioWorker", daemon=True),
            threading.Thread(target=self._watcher_loop, name="VoiceWatcher", daemon=True)
        ]
        for t in self.threads:
            t.start()
        self.logger.info("Audio Orchestrator started.")

    def stop(self):
        """Stop all audio threads."""
        self.stop_event.set()
        if self.voice_detector:
            self.voice_detector.stop()
        self.audio_engine.stop_stream()
        for t in self.threads:
            t.join(timeout=1.0)
        self.logger.info("Audio Orchestrator stopped.")

    def pause(self):
        """Pause processing."""
        self.paused.set()

    def resume(self):
        """Resume processing."""
        self.paused.clear()
