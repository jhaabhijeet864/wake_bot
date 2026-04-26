"""
WakeBot Abstract Base Classes
Defines the interface for all detection triggers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any


class BaseDetector(ABC):
    """
    Abstract Base Class for all detectors (Clap, Voice, Camera, etc.)
    Ensures a consistent interface for the main application loop.
    """
    
    @abstractmethod
    def process(self, data: Any) -> Optional[str]:
        """
        Process incoming sensor data and return an action string if triggered.
        
        Args:
            data: The sensor data (e.g., RMS value, audio chunk, or video frame)
            
        Returns:
            A string identifying the detected action (e.g., "WAKE", "LOCK"), 
            or None if no action is triggered.
        """
        pass

    @abstractmethod
    def start(self):
        """Initialize and start the detector."""
        pass

    @abstractmethod
    def stop(self):
        """Cleanly stop the detector."""
        pass

    @abstractmethod
    def check_and_reset(self) -> bool:
        """
        Check if a trigger occurred since the last call and reset the state.
        Useful for async/background detectors.
        """
        pass
