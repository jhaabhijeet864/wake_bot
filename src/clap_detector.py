"""
WakeBot Clap Detection Module
Single and double clap detection
"""

import time
from typing import Optional


class ClapDetector:
    """Detector for single and double claps"""
    
    def __init__(self, threshold: int = 3000, double_clap_window_ms: int = 500):
        """
        Initialize ClapDetector
        
        Args:
            threshold: RMS threshold for clap detection
            double_clap_window_ms: Time window to detect double clap
        """
        self.threshold = threshold
        self.double_clap_window = double_clap_window_ms / 1000.0  # Convert to seconds
        self.min_clap_gap = 0.1  # Minimum 100ms between claps
        self.action_cooldown = 1.5  # 1.5 second cooldown after action
        
        self.last_clap_time: Optional[float] = None
        self.last_action_time: float = 0
        self.is_above_threshold = False
        self.pending_single = False
    
    def process(self, rms: float) -> Optional[str]:
        """
        Process RMS value and detect single or double clap
        
        Args:
            rms: Current RMS value from audio stream
            
        Returns:
            "SINGLE" for single clap, "DOUBLE" for double clap, None otherwise
        """
        current_time = time.time()
        
        # Check if we're in action cooldown period
        if (current_time - self.last_action_time) < self.action_cooldown:
            return None
        
        # Check if pending single clap has timed out (no second clap came)
        if self.pending_single and self.last_clap_time is not None:
            if (current_time - self.last_clap_time) > self.double_clap_window:
                # Single clap confirmed - no second clap within window
                self.pending_single = False
                self.last_action_time = current_time
                return "SINGLE"
        
        # Detect clap: RMS must exceed threshold (rising edge only)
        if rms > self.threshold:
            if not self.is_above_threshold:
                # Rising edge - this is a new clap
                self.is_above_threshold = True
                
                if self.pending_single and self.last_clap_time is not None:
                    # Check if this is a valid second clap
                    time_since_last = current_time - self.last_clap_time
                    if time_since_last >= self.min_clap_gap and time_since_last <= self.double_clap_window:
                        # Double clap detected!
                        self.pending_single = False
                        self.last_clap_time = current_time
                        self.last_action_time = current_time
                        return "DOUBLE"
                
                # First clap - wait for potential second clap
                self.last_clap_time = current_time
                self.pending_single = True
        else:
            # Below threshold - reset for next detection
            self.is_above_threshold = False
        
        return None
