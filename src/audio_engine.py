"""
WakeBot Audio Engine Module
Handles PyAudio stream initialization, reading, and error recovery
"""

import pyaudio
import numpy as np
import time
from typing import Optional


# Configuration Constants
CHUNK = 1024          # Frames per buffer
FORMAT = pyaudio.paInt16  # 16-bit audio
CHANNELS = 1          # Mono
RATE = 44100          # Sample rate


class AudioStream:
    """Manages PyAudio microphone stream with error recovery"""
    
    def __init__(self, chunk_size: int = CHUNK, sample_rate: int = RATE, 
                 channels: int = CHANNELS, format_type: int = FORMAT):
        """
        Initialize AudioStream
        
        Args:
            chunk_size: Frames per buffer
            sample_rate: Audio sample rate
            channels: Number of audio channels (1 = mono)
            format_type: Audio format (pyaudio.paInt16)
        """
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.channels = channels
        self.format_type = format_type
        
        self.pyaudio_instance: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        
    def start_stream(self) -> bool:
        """
        Open microphone stream
        
        Returns:
            True if stream opened successfully, False otherwise
        """
        try:
            # Initialize PyAudio if not already done
            if self.pyaudio_instance is None:
                self.pyaudio_instance = pyaudio.PyAudio()
            
            # Close existing stream if any
            if self.stream is not None:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except:
                    pass
            
            # Open new stream
            self.stream = self.pyaudio_instance.open(
                format=self.format_type,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            # Start the stream explicitly
            if not self.stream.is_active():
                self.stream.start_stream()
            
            # Give the stream a moment to initialize (read a dummy chunk to prime it)
            try:
                self.stream.read(self.chunk_size, exception_on_overflow=False)
            except:
                pass  # Ignore errors during initialization read
            
            return True
            
        except Exception as e:
            print(f"Failed to start audio stream: {e}")
            return False
    
    def read_chunk(self) -> np.ndarray:
        """
        Read audio chunk from microphone
        
        Returns:
            numpy array of audio data
            
        Raises:
            Exception: If stream read fails
        """
        if self.stream is None:
            raise Exception("Stream not initialized. Call start_stream() first.")
        
        try:
            # Read raw bytes from stream
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            
            # Convert to numpy array
            audio_array = np.frombuffer(data, dtype=np.int16)
            
            return audio_array
            
        except Exception as e:
            # Stream error - will trigger restart
            raise Exception(f"Stream read error: {e}")
    
    def calculate_rms(self, audio_data: np.ndarray) -> float:
        """
        Compute Root Mean Square of audio chunk
        
        Formula: rms = np.sqrt(np.mean(audio_data.astype(np.float64)**2))
        
        Args:
            audio_data: numpy array of audio samples
            
        Returns:
            RMS value as float
        """
        if len(audio_data) == 0:
            return 0.0
        
        # Convert to float64 to avoid overflow
        audio_float = audio_data.astype(np.float64)
        
        # Calculate RMS
        rms = np.sqrt(np.mean(audio_float ** 2))
        
        return rms
    
    def stop_stream(self):
        """Clean shutdown of stream and PyAudio"""
        try:
            if self.stream is not None:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
        except:
            pass
        
        try:
            if self.pyaudio_instance is not None:
                self.pyaudio_instance.terminate()
                self.pyaudio_instance = None
        except:
            pass
    
    def restart_stream(self) -> bool:
        """
        Auto-restart stream on failure
        Waits 1 second before attempting restart
        
        Returns:
            True if restart successful, False otherwise
        """
        time.sleep(1)  # Wait before restart
        
        try:
            # Clean up existing stream
            if self.stream is not None:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except:
                    pass
                self.stream = None
            
            # Try to restart
            return self.start_stream()
            
        except Exception as e:
            print(f"Failed to restart stream: {e}")
            return False
    
    def is_stream_active(self) -> bool:
        """
        Check if stream is currently active
        
        Returns:
            True if stream is open and active
        """
        return self.stream is not None and self.stream.is_active()
