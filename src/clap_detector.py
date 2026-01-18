"""
WakeBot Clap Detection Module
Simple single clap detection
"""

import time
from typing import Optional


class ClapDetector:
    """Simple detector for single claps"""
    
    def __init__(self, threshold: int = 3000, cooldown_ms: int = 300):
        """
        Initialize ClapDetector
        
        Args:
            threshold: RMS threshold for clap detection
            cooldown_ms: Minimum time between claps (prevents rapid repeats)
        """
        self.threshold = threshold
        self.cooldown_ms = cooldown_ms / 1000.0  # Convert to seconds
        
        self.last_clap_time: Optional[float] = None
    
    def process(self, rms: float) -> Optional[str]:
        """
        Process RMS value and detect single clap
        
        Args:
            rms: Current RMS value from audio stream
            
        Returns:
            "SINGLE" if clap detected, None otherwise
        """
        current_time = time.time()
        
        # Check if we're in cooldown period
        if self.last_clap_time is not None:
            if (current_time - self.last_clap_time) < self.cooldown_ms:
                return None  # Still in cooldown, ignore
        
        # Detect clap: RMS must exceed threshold
        if rms > self.threshold:
            self.last_clap_time = current_time
            return "SINGLE"
        
        return None
