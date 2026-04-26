"""
WakeBot Core Actions - Professional Automation
Optimized for HP Victus & Windows 11.
"""

import os
import ctypes
import subprocess
import platform
import time
from typing import List, Optional

# Constants for Windows API
MOUSEEVENTF_MOVE = 0x0001
VK_RETURN = 0x0D
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_STOP = 0xB2
KEYEVENTF_KEYUP = 0x0002
WM_SYSCOMMAND = 0x0112
SC_MONITORPOWER = 0xF170

# Optional imports for Window Management
try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None


class WakeBotActions:
    """
    Handles environment orchestration: Welcome Home and Goodnight routines.
    """

    def __init__(self, logger=None):
        self.logger = logger
        self.system = platform.system()
        self.last_execution_time = 0
        self.song_url = "https://open.spotify.com/track/2iEGj7kAwH7HAa5epwYwLB?si=9d4ab6ee60ab46c1"

    def wake_system(self):
        """
        1. Wake & Unlock Routine:
        Jiggles mouse, waits for Victus display, and drops lock screen.
        """
        current_time = time.time()
        if current_time - self.last_execution_time < 60:
            if self.logger:
                self.logger.info("Wake routine skipped: Cooldown active (60s)")
            return False

        if self.system != "Windows":
            return False

        try:
            # Jiggle mouse to wake hardware
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, 1, 1, 0, 0)
            
            # 1.5s hardware delay for Victus display to initialize
            time.sleep(1.5)
            
            # Press 'Enter' and release to drop lock screen
            ctypes.windll.user32.keybd_event(VK_RETURN, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)
            
            self.last_execution_time = current_time
            if self.logger:
                self.logger.action("System Wake & Unlock triggered")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Wake failed: {e}")
            return False

    def launch_or_maximize(self):
        """
        2. App Orchestrator:
        Maximizes VS Code if open, otherwise launches it.
        """
        if self.system != "Windows" or not win32gui:
            subprocess.Popen('code', shell=True)
            return

        def find_vscode(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                if "Visual Studio Code" in win32gui.GetWindowText(hwnd):
                    results.append(hwnd)

        vscode_hwnds = []
        win32gui.EnumWindows(find_vscode, vscode_hwnds)

        if vscode_hwnds:
            if self.logger:
                self.logger.info("Maximizing VS Code...")
            for hwnd in vscode_hwnds:
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                win32gui.SetForegroundWindow(hwnd)
        else:
            if self.logger:
                self.logger.info("Launching VS Code...")
            subprocess.Popen('code', shell=True)

    def play_startup_theme(self):
        """
        3. 'One Go' Music Sequence:
        Forces Spotify to open specific track and play.
        """
        try:
            # Force Windows to resolve link and open in Spotify
            os.startfile(self.song_url)
            
            # 2.5s delay to allow Spotify UI to load track data
            time.sleep(2.5)
            
            # Send VK_MEDIA_PLAY_PAUSE signal
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0)
            
            if self.logger:
                self.logger.action("Startup Theme playing")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Music sequence failed: {e}")

    def welcome_home(self):
        """
        4. Master Function: Sequential environment setup.
        """
        if self.logger:
            self.logger.action("Welcome Home Sequence Started")
        self.wake_system()
        self.launch_or_maximize()
        self.play_startup_theme()

    def goodnight(self):
        """
        Sleep Command: Pauses music and turns monitor off.
        """
        if self.logger:
            self.logger.action("GOODNIGHT SEQUENCE TRIGGERED")
        
        try:
            # 1. Pause Music
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0)
            
            # 2. Turn off Monitor (Power save)
            # 2 = off, 1 = standby, -1 = on
            ctypes.windll.user32.SendMessageW(0xFFFF, WM_SYSCOMMAND, SC_MONITORPOWER, 2)
            
            if self.logger:
                self.logger.info("Monitor turned off, Music paused.")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Goodnight sequence failed: {e}")

if __name__ == "__main__":
    actions = WakeBotActions()
    # To test: actions.welcome_home() or actions.goodnight()
    actions.welcome_home()
