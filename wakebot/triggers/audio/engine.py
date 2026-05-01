"""
WakeBot Audio Engine
Handles microphone stream initialization and audio capture.
"""

import pyaudio
import numpy as np
import time
from typing import Optional

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


class AudioStream:
    """Manages PyAudio microphone stream with error recovery and GPU acceleration."""
    
    def __init__(self, chunk_size: int = 1024, sample_rate: int = 44100, 
                 channels: int = 1, format_type: int = pyaudio.paInt16):
        """
        Initialize AudioStream
        """
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.channels = channels
        self.format_type = format_type
        
        self.pyaudio_instance: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        
        # GPU State
        self._device = "cuda" if (HAS_TORCH and torch.cuda.is_available()) else "cpu"
        
    def start_stream(self) -> bool:
        """Open microphone stream"""
        try:
            if self.pyaudio_instance is None:
                self.pyaudio_instance = pyaudio.PyAudio()
            
            if self.stream is not None:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except:
                    pass
            
            self.stream = self.pyaudio_instance.open(
                format=self.format_type,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            if not self.stream.is_active():
                self.stream.start_stream()
            
            # Prime the stream
            try:
                self.stream.read(self.chunk_size, exception_on_overflow=False)
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"Failed to start audio stream: {e}")
            return False
    
    def read_chunk(self) -> np.ndarray:
        """Read audio chunk from microphone as numpy array"""
        if self.stream is None:
            raise Exception("Stream not initialized.")
        
        try:
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            return np.frombuffer(data, dtype=np.int16)
        except Exception as e:
            raise Exception(f"Stream read error: {e}")
    
    def calculate_rms(self, audio_data: np.ndarray) -> float:
        """Compute Root Mean Square of audio chunk. GPU accelerated if possible."""
        if len(audio_data) == 0:
            return 0.0
            
        try:
            if self._device == "cuda":
                # Move to GPU
                t_audio = torch.from_numpy(audio_data.astype(np.float32)).to(self._device)
                # Compute RMS: sqrt(mean(x^2))
                rms = torch.sqrt(torch.mean(t_audio ** 2)).item()
                return float(rms)
        except Exception:
            # Fallback to CPU if GPU fails
            pass
            
        # CPU Fallback (NumPy)
        audio_float = audio_data.astype(np.float64)
        return np.sqrt(np.mean(audio_float ** 2))
    
    def stop_stream(self):
        """Clean shutdown"""
        try:
            if self.stream is not None:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            if self.pyaudio_instance is not None:
                self.pyaudio_instance.terminate()
                self.pyaudio_instance = None
        except:
            pass
    
    def restart_stream(self) -> bool:
        """Auto-restart stream on failure"""
        time.sleep(1)
        self.stop_stream()
        return self.start_stream()

    def is_stream_active(self) -> bool:
        """Check if stream is active"""
        return self.stream is not None and self.stream.is_active()
