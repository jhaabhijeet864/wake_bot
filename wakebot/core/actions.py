"""
WakeBot Core Actions - Principal Architect Stable Baseline
- REMOVED: All TTS and Pygame dependencies for maximum stability.
- RETAINED: Hardware wake, VS Code orchestration, and Spotify Force-Play.
- SEQUENCE: Wake -> Workspace -> Spotify
"""

import os
import ctypes
import subprocess
import shutil
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
    Streamlined for baseline stability.
    """

    def __init__(self, logger=None, event_bus=None, workspace_state=None):
        self.logger = logger
        self.system = platform.system()
        self.song_url = "https://open.spotify.com/track/2iEGj7kAwH7HAa5epwYwLB?si=9d4ab6ee60ab46c1"
        self.event_bus = event_bus
        self.workspace_state = workspace_state
        self.last_action_time = 0.0
        self.cooldown = 2.0  # Minimum seconds between actions

        if self.event_bus:
            self.event_bus.subscribe("USER_ARRIVED", self._on_user_arrived)
            self.event_bus.subscribe("USER_LEFT", self._on_user_left)

    def _on_user_arrived(self, data=None):
        now = time.time()
        if now - self.last_action_time >= self.cooldown:
            if self.workspace_state:
                self.workspace_state.set("user_present", True)
            self.welcome_home()
            self.last_action_time = time.time()
        elif self.logger:
            self.logger.info("USER_ARRIVED event ignored (cooldown active).")

    def _on_user_left(self, data=None):
        now = time.time()
        if now - self.last_action_time >= self.cooldown:
            if self.workspace_state:
                self.workspace_state.set("user_present", False)
            self.goodnight()
            self.last_action_time = time.time()
        elif self.logger:
            self.logger.info("USER_LEFT event ignored (cooldown active).")

    def wake_system(self):
        """
        STAGE 1: Wake & Unlock Routine
        Jiggles mouse, waits for Victus display, and drops lock screen.
        """
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
            
            if self.logger:
                self.logger.action("System Wake & Unlock triggered")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Wake failed: {e}")
            return False

    def launch_or_maximize(self):
        """
        STAGE 2: Workspace Management
        Maximizes VS Code if open, otherwise launches it.
        """
        if self.system != "Windows" or not win32gui:
            if shutil.which('code'):
                subprocess.Popen(['code'])
            else:
                if self.logger:
                    self.logger.error("VS Code ('code') not found in PATH.")
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
                try:
                    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                    win32gui.SetForegroundWindow(hwnd)
                except Exception:
                    # Catching focus restrictions gracefully
                    pass
        else:
            if self.logger:
                self.logger.info("Launching VS Code...")
            if shutil.which('code'):
                subprocess.Popen(['code'])
            else:
                if self.logger:
                    self.logger.error("VS Code ('code') not found in PATH.")

    def play_startup_theme(self):
        """
        STAGE 3: Music Sequence (Force-Play)
        Launches Spotify URL. Auto-play is handled by the OS/App handshake.
        """
        try:
            if self.logger:
                self.logger.info("Firing Spotify startup theme...")
            
            # Start Spotify track - Most versions auto-play on URL open
            os.startfile(self.song_url)
            
            if self.logger:
                self.logger.action("Music sequence initiated via URL.")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Music sequence failed: {e}")

    def welcome_home(self):
        """
        Master Function: Sequential environment setup.
        Order: Wake -> Workspace (VS Code) -> Spotify
        """
        if self.logger:
            self.logger.action("WELCOME HOME SEQUENCE STARTED")
        
        self.wake_system()         # 1. Wake
        self.launch_or_maximize()  # 2. Workspace
        self.play_startup_theme()  # 3. Spotify

    def goodnight(self):
        """
        Sleep Command: Pauses music and turns monitor off.
        """
        if self.logger:
            self.logger.action("GOODNIGHT SEQUENCE TRIGGERED")
        
        try:
            # Pause Music
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0)
            
            # Turn off Monitor
            ctypes.windll.user32.SendMessageW(0xFFFF, WM_SYSCOMMAND, SC_MONITORPOWER, 2)
            
            if self.logger:
                self.logger.info("Monitor turned off, Music paused.")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Goodnight sequence failed: {e}")
