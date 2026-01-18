"""
WakeBot Actions Module
System automation actions triggered by clap patterns
"""

import pyautogui
import webbrowser
from src.logger import WakeBotLogger


class WakeBotActions:
    """Handles system automation actions"""
    
    def __init__(self, youtube_url: str = "https://www.youtube.com", 
                 wake_key: str = "shift"):
        """
        Initialize WakeBotActions
        
        Args:
            youtube_url: URL to open on double clap
            wake_key: Key to press on single clap (wake screen)
        """
        self.youtube_url = youtube_url
        self.wake_key = wake_key
        self.logger = WakeBotLogger()
    
    def wake_screen(self):
        """Single clap action - wake display"""
        try:
            pyautogui.press(self.wake_key)  # Non-intrusive keypress
            self.logger.action("Wake Screen")
        except Exception as e:
            self.logger.error(f"Failed to wake screen: {e}")
    
