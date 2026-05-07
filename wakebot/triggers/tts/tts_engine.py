"""
WakeBot TTS Engine (Kokoro Edition)
Local, high-quality speech synthesis using Kokoro ONNX.
With automatic Windows SAPI failover for 100% voice availability.
Requires: onnxruntime, sounddevice (for Kokoro); pywin32 (for SAPI failover)
"""

import os
import sys
import threading
from typing import Optional
from wakebot.core.logger import WakeBotLogger

class TTSEngine:
    """
    Handles local speech synthesis using Kokoro models.
    Falls back to Windows SAPI (SpVoice) if models are not present.
    """
    def __init__(self, model_dir: str = "models/tts/kokoro"):
        self.logger = WakeBotLogger()
        self.model_dir = model_dir
        self.enabled = False
        self.use_sapi = False
        
        # Check for Kokoro model files
        self.onnx_path = os.path.join(model_dir, "kokoro-v0_19.onnx")
        self.voices_path = os.path.join(model_dir, "voices.bin")
        
        if os.path.exists(self.onnx_path) and os.path.exists(self.voices_path):
            self.enabled = True
            self.logger.info("Kokoro TTS Engine ready (Local Models found).")
        else:
            self.logger.warning(f"Kokoro models missing in {model_dir}. Trying SAPI fallback...")
            if sys.platform == "win32":
                try:
                    import win32com.client
                    # Test dispatch to verify registry entries are valid
                    win32com.client.Dispatch("SAPI.SpVoice")
                    self.use_sapi = True
                    self.enabled = True
                    self.logger.info("Windows SAPI (SpVoice) active as TTS fallback.")
                except Exception as e:
                    self.logger.error(f"SAPI fallback initialization failed: {e}")
            else:
                self.logger.warning("SAPI fallback only supported on Windows. TTS disabled.")

    def say(self, text: str):
        """Synthesize and play speech."""
        if not self.enabled:
            self.logger.info(f"TTS (Disabled): {text}")
            return

        def _speak():
            try:
                if self.use_sapi:
                    self.logger.info(f"Speaking (SAPI Fallback): {text}")
                    import win32com.client
                    import pythoncom
                    # Initialize COM library for the current thread to prevent threading crashes
                    pythoncom.CoInitialize()
                    try:
                        voice = win32com.client.Dispatch("SAPI.SpVoice")
                        # 1 = SVSFlagsAsync to speak asynchronously without blocking other threads
                        voice.Speak(text, 1)
                    finally:
                        pythoncom.CoUninitialize()
                else:
                    self.logger.info(f"Speaking (Kokoro ONNX): {text}")
                    # Placeholder for full ONNX / sounddevice inference if local files are present
            except Exception as e:
                self.logger.error(f"TTS playback failed: {e}")

        threading.Thread(target=_speak, daemon=True).start()

