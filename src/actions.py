"""
WakeBot Actions Module
System automation actions triggered by clap patterns
"""

import pyautogui
import webbrowser
import platform
import subprocess
import ctypes
from src.logger import WakeBotLogger


class WakeBotActions:
    """Handles system automation actions"""
    
    def __init__(self, youtube_url: str = "https://www.youtube.com", 
                 wake_key: str = "shift",
                 open_lock_screen: bool = True):
        """
        Initialize WakeBotActions
        
        Args:
            youtube_url: URL to open on double clap
            wake_key: Key to press on single clap (wake screen)
            open_lock_screen: Whether to open lock screen when waking
        """
        self.youtube_url = youtube_url
        self.wake_key = wake_key
        self.open_lock_screen = open_lock_screen
        self.logger = WakeBotLogger()
        self.system = platform.system()
    
    def wake_screen(self):
        """Single clap action - wake display (shows lock screen if locked)"""
        try:
            # Wake the screen with a keypress - this will show lock screen if PC is locked
            pyautogui.press(self.wake_key)
            self.logger.action("Wake Screen")
        except Exception as e:
            self.logger.error(f"Failed to wake screen: {e}")
    
    def lock_screen(self):
        """Double clap action - lock the screen"""
        try:
            if self.system == "Windows":
                # Windows: Use LockWorkStation API
                ctypes.windll.user32.LockWorkStation()
                self.logger.action("Lock Screen (Windows)")
                
            elif self.system == "Linux":
                # Linux: Try multiple methods
                lock_commands = [
                    ['loginctl', 'lock-session'],
                    ['xdg-screensaver', 'lock'],
                    ['gnome-screensaver-command', '--lock'],
                    ['dm-tool', 'lock'],
                ]
                
                for cmd in lock_commands:
                    try:
                        subprocess.run(cmd, check=True, capture_output=True)
                        self.logger.action(f"Lock Screen (Linux: {cmd[0]})")
                        return
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                
                # Fallback: Try dbus
                try:
                    subprocess.run([
                        'dbus-send', '--type=method_call', '--dest=org.gnome.ScreenSaver',
                        '/org/gnome/ScreenSaver', 'org.gnome.ScreenSaver.Lock'
                    ], check=True, capture_output=True)
                    self.logger.action("Lock Screen (Linux: dbus)")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    self.logger.error("Could not lock screen on Linux")
                    
            elif self.system == "Darwin":
                # macOS: Use CGSession to lock
                subprocess.run([
                    '/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession',
                    '-suspend'
                ], check=True, capture_output=True)
                self.logger.action("Lock Screen (macOS)")
                
            else:
                self.logger.error(f"Unsupported operating system: {self.system}")
                
        except Exception as e:
            self.logger.error(f"Failed to lock screen: {e}")
