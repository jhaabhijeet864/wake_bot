"""
WakeBot Voice Detector (Vosk Edition)
Offline keyword spotting using Vosk for low latency and privacy.
"""

import json
import os
import threading
import queue
import numpy as np
from typing import Optional, Any
from vosk import Model, KaldiRecognizer
from wakebot.core.logger import WakeBotLogger
from wakebot.core.detector import BaseDetector


class VoiceDetector(BaseDetector):
    """Detects specific voice phrases using offline Vosk engine"""
    
    def __init__(self, model_path: str = "model", 
                 sample_rate: int = 44100,
                 wake_phrases: list = None):
        """
        Initialize Vosk VoiceDetector
        """
        self.logger = WakeBotLogger()
        self.sample_rate = sample_rate
        self.wake_phrases = wake_phrases or ["wake up", "daddy's home", "wake up daddy's home"]
        
        # Initialize Vosk Model
        if not os.path.exists(model_path):
            self.logger.error(f"Vosk model not found at '{model_path}'.")
            self.model = None
            self.recognizer = None
        else:
            try:
                self.model = Model(model_path)
                # Ensure wake_phrases is a list before adding [unk]
                grammar_list = list(self.wake_phrases) + ["[unk]"]
                grammar = json.dumps(grammar_list)
                self.recognizer = KaldiRecognizer(self.model, self.sample_rate, grammar)
                self.logger.info("Vosk Voice Detector initialized with restricted grammar.")
            except Exception as e:
                self.logger.error(f"Failed to load Vosk model: {e}")
                self.model = None
                self.recognizer = None

        self.audio_queue = queue.Queue()
        self.is_running = False
        self.phrase_detected = False
        self._thread = None
        
    def add_audio(self, audio_data: np.ndarray):
        """Add raw audio data (int16) to the processing queue"""
        if self.is_running and self.recognizer:
            self.audio_queue.put(audio_data.tobytes())

    def process(self, data: Any) -> Optional[str]:
        """Process audio data and check for keyword detection"""
        if isinstance(data, np.ndarray):
            self.add_audio(data)
        
        if self.check_and_reset():
            return "VOICE"
        return None

    def _processing_loop(self):
        """Background thread for processing audio queue"""
        while self.is_running:
            try:
                try:
                    data = self.audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        self.logger.info(f"Vosk Final: '{text}'")
                        self._check_text(text)
                
                self.audio_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error in voice processing loop: {e}")

    def _check_text(self, text: str):
        """Match recognized text against wake phrases"""
        text = text.lower()
        for phrase in self.wake_phrases:
            if phrase in text:
                self.logger.info(f"KEYWORD MATCH: '{phrase}' detected!")
                self.phrase_detected = True
                break

    def start(self):
        """Start the background processing thread"""
        if self.recognizer and not self.is_running:
            self.is_running = True
            self.phrase_detected = False
            self._thread = threading.Thread(target=self._processing_loop, daemon=True)
            self._thread.start()
            self.logger.info("Voice Detector thread active.")

    def stop(self):
        """Stop the background processing thread"""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def check_and_reset(self) -> bool:
        """Check if phrase was detected and reset state"""
        if self.phrase_detected:
            self.phrase_detected = False
            return True
        return False
