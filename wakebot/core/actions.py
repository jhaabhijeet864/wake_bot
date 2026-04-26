"""
WakeBot Core Actions (v3.0 - Unified & Decoupled)
Features: Hardware wake, Threaded Edge-TTS, Robust Window Management, and Spotify Force-Play.
"""

import os
import ctypes
import time
import asyncio
import subprocess
import platform
import threading
from typing import List, Optional

# Windows-specific imports
if platform.system() == "Windows":
    try:
        import win32gui
        import win32con
        import win32com.client
        import pygame
        import edge_tts
    except ImportError:
        pass


class WakeBotActions:
    """
    Principal orchestrator for system-level actions.
    Optimized for non-blocking execution and hardware-level automation.
    """

    def __init__(self, logger=None):
        self.logger = logger
        self.system = platform.system()
        self.last_wake_time = 0
        self.wake_cooldown = 60  # 1-minute fail-safe
        self.voice = "en-GB-ThomasNeural" 
        
        if self.logger:
            self.logger.info("WakeBotActions v3.0 initialized (Threaded & Decoupled).")

    def _mouse_jiggle(self):
        """Perform a hardware-level mouse jiggle via ctypes to wake the monitor."""
        MOUSEEVENTF_MOVE = 0x0001
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, 1, 1, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, -1, -1, 0, 0)

    def _press_enter(self):
        """Simulate a hardware Enter key press to drop the lock screen."""
        VK_RETURN = 0x0D
        KEYEVENTF_KEYUP = 0x0002
        ctypes.windll.user32.keybd_event(VK_RETURN, 0, 0, 0)
        time.sleep(0.1)
        ctypes.windll.user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)

    def wake_and_unlock(self) -> bool:
        """Hardware wake sequence with cooldown fail-safe."""
        if self.system != "Windows":
            return False
            
        current_time = time.time()
        if current_time - self.last_wake_time < self.wake_cooldown:
            if self.logger:
                self.logger.info("Wake sequence skipped (Cooldown active)")
            return False

        if self.logger:
            self.logger.info("Initiating hardware wake sequence...")

        self._mouse_jiggle()
        time.sleep(1.5)
        self._press_enter()
        
        self.last_wake_time = current_time
        return True

    def launch_or_maximize(self, window_title_part: str, launch_cmd: str):
        """Finds a window by title and maximizes/focuses it, or launches the app."""
        if self.system != "Windows":
            subprocess.Popen(launch_cmd, shell=True)
            return

        hwnd_found = []

        def enum_callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if window_title_part.lower() in title.lower():
                    hwnd_found.append(hwnd)

        win32gui.EnumWindows(enum_callback, None)

        if hwnd_found:
            hwnd = hwnd_found[0]
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                try:
                    shell = win32com.client.Dispatch("WScript.Shell")
                    shell.SendKeys('%')
                    win32gui.SetForegroundWindow(hwnd)
                except Exception:
                    pass
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Window management error: {e}")
        else:
            subprocess.Popen(launch_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    async def _generate_voice(self, text: str, output_path: str):
        """Internal async method to generate the TTS file."""
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_path)

    def edge_greet_user(self, text: str = "Welcome back, sir. All systems initialized."):
        """Generates voice via Edge-TTS and plays it. Designed to run in a thread."""
        temp_file = "temp_greeting.mp3"
        try:
            asyncio.run(self._generate_voice(text, temp_file))
            pygame.mixer.init()
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()
            pygame.mixer.quit()
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as e:
            if self.logger:
                self.logger.error(f"TTS Thread Failure (Non-blocking): {e}")

    def play_startup_theme(self):
        """Launches Spotify and forces playback after a hardware-sync delay."""
        if self.logger:
            self.logger.info("Initializing Spotify sequence...")
        
        # 1. Launch/Maximize Spotify
        self.launch_or_maximize("Spotify", "start spotify")
        
        # 2. Hardware-sync delay for Spotify to initialize
        time.sleep(4.0)
        
        # 3. Simulate VK_MEDIA_PLAY_PAUSE (0xB3)
        VK_MEDIA_PLAY_PAUSE = 0xB3
        KEYEVENTF_KEYUP = 0x0002
        if self.logger:
            self.logger.info("Sending Play/Pause hardware command.")
        ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        time.sleep(0.1)
        ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0)

    def welcome_home(self):
        """
        Master Orchestration Flow: 
        1. Wake & Unlock
        2. VS Code Workspace
        3. Trigger Threaded TTS (Non-blocking)
        4. Trigger Spotify Playback
        """
        if self.system != "Windows":
            return

        # 1. Hardware Wake
        if not self.wake_and_unlock():
            return

        # 2. Desktop Sync Delay
        time.sleep(2.0)

        # 3. VS Code Workspace
        self.launch_or_maximize("Visual Studio Code", "code")

        # 4. Threaded AI Interaction (Decoupled to prevent blocking Spotify)
        threading.Thread(target=self.edge_greet_user, daemon=True).start()

        # 5. Spotify Sequence (Now starts immediately after TTS thread spawn)
        self.play_startup_theme()

    def lock_screen(self):
        """Locks the workstation instantly."""
        if self.system == "Windows":
            ctypes.windll.user32.LockWorkStation()

    def wake_system(self):
        """Standard trigger alias."""
        self.welcome_home()

if __name__ == "__main__":
    actions = WakeBotActions()
    actions.welcome_home()
