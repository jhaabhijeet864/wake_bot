"""
WakeBot Core Actions - Unified Action Dispatcher (v2.1.0)
Subscribes to EventBus and manages system routines autonomously.
- Fixed: VS Code launch path issue on Windows.
- Integrated: Event-driven execution via EventBus.
- Optimized: Debounced (cooldown) execution.
"""

import os
import ctypes
import subprocess
import shutil
import platform
import time
import threading
from typing import List, Optional
from wakebot.core.logger import WakeBotLogger
from wakebot.core.event_bus import EventBus
from wakebot.core.workspace_state import WorkspaceState

# Windows Constants
MOUSEEVENTF_MOVE = 0x0001
VK_RETURN = 0x0D
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002
WM_SYSCOMMAND = 0x0112
SC_MONITORPOWER = 0xF170

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None

class WakeBotActions:
    """
    Subscribes to events and executes system automation routines.
    """
    def __init__(self, logger=None):
        self.logger = logger or WakeBotLogger()
        self.system = platform.system()
        self.workspace_state = WorkspaceState()
        self.event_bus = EventBus()
        
        # Cooldown management
        self._last_action_time = 0.0
        self._cooldown_s = 5.0 # Default cooldown
        
        # Subscriptions
        self.event_bus.subscribe("USER_ARRIVED", self.on_user_arrived)
        self.event_bus.subscribe("USER_LEFT", self.on_user_left)
        
        self.song_url = "https://open.spotify.com/track/2iEGj7kAwH7HAa5epwYwLB?si=9d4ab6ee60ab46c1"

    def on_user_arrived(self, data=None):
        """React to user arrival event."""
        now = time.time()
        if now - self._last_action_time < self._cooldown_s:
            return
        
        self.logger.action(f"Event Triggered: USER_ARRIVED (Source: {data.get('source', 'unknown') if data else 'unknown'})")
        self.workspace_state.set("user_present", True)
        self.welcome_home()
        self._last_action_time = time.time()

    def on_user_left(self, data=None):
        """React to user departure event."""
        now = time.time()
        if now - self._last_action_time < self._cooldown_s:
            return
            
        self.logger.action(f"Event Triggered: USER_LEFT (Source: {data.get('source', 'unknown') if data else 'unknown'})")
        self.workspace_state.set("user_present", False)
        self.goodnight()
        self._last_action_time = time.time()

    def welcome_home(self):
        """Sequential environment setup."""
        self.logger.action("INITIATING: Welcome Home Sequence")
        self.wake_system()
        self.launch_or_maximize_vscode()
        self.play_spotify()

    def wake_system(self):
        """Wake monitor and drop lock screen."""
        if self.system != "Windows": return
        try:
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, 1, 1, 0, 0)
            time.sleep(1.5)
            ctypes.windll.user32.keybd_event(VK_RETURN, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)
        except Exception as e:
            self.logger.error(f"Wake failed: {e}")

    def launch_or_maximize_vscode(self):
        """Maximize VS Code if open, otherwise launch it."""
        if self.system != "Windows": return
        
        def find_vscode(hwnd, results):
            if win32gui and win32gui.IsWindowVisible(hwnd):
                if "Visual Studio Code" in win32gui.GetWindowText(hwnd):
                    results.append(hwnd)

        vscode_hwnds = []
        if win32gui:
            win32gui.EnumWindows(find_vscode, vscode_hwnds)

        if vscode_hwnds:
            for hwnd in vscode_hwnds:
                try:
                    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                    win32gui.SetForegroundWindow(hwnd)
                except Exception: pass
        else:
            self.logger.info("Launching VS Code...")
            try:
                # Use shell=True to handle PATH resolution for 'code' command on Windows
                subprocess.Popen(['code'], shell=True)
            except Exception as e:
                self.logger.error(f"Failed to launch VS Code: {e}")

    def play_spotify(self):
        """Launch Spotify track."""
        try:
            os.startfile(self.song_url)
        except Exception as e:
            self.logger.error(f"Spotify failed: {e}")

    def goodnight(self):
        """Pause music and turn monitor off."""
        self.logger.action("INITIATING: Goodnight Sequence")
        try:
            # Media Key: Play/Pause
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0)
            
            # Monitor Power Off
            ctypes.windll.user32.SendMessageW(0xFFFF, WM_SYSCOMMAND, SC_MONITORPOWER, 2)
        except Exception as e:
            self.logger.error(f"Goodnight failed: {e}")
