"""
WakeBot Clap Detector
Detects single and double clap patterns from audio RMS data.
"""

import time
from typing import Optional, Any
from wakebot.core.detector import BaseDetector


class ClapDetector(BaseDetector):
    """Detector for single and double claps"""
    
    def __init__(self, threshold: int = 3000, double_clap_window_ms: int = 500):
        """
        Initialize ClapDetector
        
        Args:
            threshold: RMS threshold for clap detection
            double_clap_window_ms: Time window to detect double clap
        """
        self.threshold = threshold
        self.double_clap_window = double_clap_window_ms / 1000.0
        self.min_clap_gap = 0.1
        self.action_cooldown = 1.5
        
        self.last_clap_time: Optional[float] = None
        self.last_action_time: float = 0
        self.is_above_threshold = False
        self.pending_single = False
    
    def process(self, rms: float) -> Optional[str]:
        """Process RMS value and detect single or double clap"""
        current_time = time.time()
        
        if (current_time - self.last_action_time) < self.action_cooldown:
            return None
        
        if self.pending_single and self.last_clap_time is not None:
            if (current_time - self.last_clap_time) > self.double_clap_window:
                self.pending_single = False
                self.last_action_time = current_time
                return "SINGLE"
        
        if rms > self.threshold:
            if not self.is_above_threshold:
                self.is_above_threshold = True
                
                if self.pending_single and self.last_clap_time is not None:
                    time_since_last = current_time - self.last_clap_time
                    if time_since_last >= self.min_clap_gap and time_since_last <= self.double_clap_window:
                        self.pending_single = False
                        self.last_clap_time = current_time
                        self.last_action_time = current_time
                        return "DOUBLE"
                
                self.last_clap_time = current_time
                self.pending_single = True
        else:
            self.is_above_threshold = False
        
        return None

    def start(self):
        """Startup (no-op)"""
        pass

    def stop(self):
        """Shutdown (no-op)"""
        pass

    def check_and_reset(self) -> bool:
        """Clap detector is synchronous"""
        return False
