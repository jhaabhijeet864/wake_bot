"""
WakeBot System Tray Application
Provides a persistent system tray icon with context menu for controlling WakeBot.

Requires: pystray, Pillow
"""

import threading
from typing import Optional

from wakebot.core.logger import WakeBotLogger

try:
    import pystray
    from pystray import MenuItem as Item
    from PIL import Image, ImageDraw
except ImportError:
    pystray = None
    Item = None
    Image = None
    ImageDraw = None


class WakeBotTray:
    """
    System tray application for WakeBot.
    Provides Start/Stop controls and quick access to settings.
    """

    def __init__(self):
        self._logger = WakeBotLogger()
        self._engine_thread: Optional[threading.Thread] = None
        self._current_mode: Optional[str] = None
        self._icon = None

    def _create_icon_image(self, color: str = "#00C853") -> 'Image.Image':
        """Generate a simple colored circle icon for the tray."""
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Outer ring
        draw.ellipse([2, 2, size - 3, size - 3], fill=color, outline="#FFFFFF", width=2)
        # Inner "W" text approximation — a dot in the center
        center = size // 2
        r = 8
        draw.ellipse(
            [center - r, center - r, center + r, center + r],
            fill="#FFFFFF"
        )
        return img

    def _start_audio(self, icon, item):
        """Start audio detection engine in a background thread."""
        if self._engine_thread and self._engine_thread.is_alive():
            self._logger.warning("An engine is already running.")
            return

        self._current_mode = "audio"
        self._logger.info("Starting Audio Engine from System Tray...")

        def run():
            try:
                from wakebot.cli.audio_cmd import run_audio
                run_audio()
            except Exception as e:
                self._logger.error(f"Audio engine crashed: {e}")
            finally:
                self._current_mode = None

        self._engine_thread = threading.Thread(target=run, name="TrayAudioEngine", daemon=True)
        self._engine_thread.start()
        icon.icon = self._create_icon_image("#4FC3F7")  # Blue = audio active

    def _start_vision(self, icon, item):
        """Start vision detection engine in a background thread."""
        if self._engine_thread and self._engine_thread.is_alive():
            self._logger.warning("An engine is already running.")
            return

        self._current_mode = "vision"
        self._logger.info("Starting Vision Engine from System Tray...")

        def run():
            try:
                from wakebot.cli.vision_cmd import run_vision
                run_vision()
            except Exception as e:
                self._logger.error(f"Vision engine crashed: {e}")
            finally:
                self._current_mode = None

        self._engine_thread = threading.Thread(target=run, name="TrayVisionEngine", daemon=True)
        self._engine_thread.start()
        icon.icon = self._create_icon_image("#AB47BC")  # Purple = vision active

    def _open_settings(self, icon, item):
        """Open the config file in the default text editor."""
        import os
        import subprocess
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "wakebot_config.json"
        )
        if os.path.exists(config_path):
            os.startfile(config_path)
        else:
            self._logger.error(f"Config file not found: {config_path}")

    def _quit(self, icon, item):
        """Shut down the tray icon and all engines."""
        self._logger.info("System Tray: Shutting down...")
        icon.stop()

    def run(self):
        """Start the system tray application (blocks the calling thread)."""
        if not pystray or not Image:
            print(
                "[ERROR] pystray or Pillow is not installed.\n"
                "Install with: pip install pystray Pillow"
            )
            return

        menu = pystray.Menu(
            Item("🎧 Start Audio Mode", self._start_audio),
            Item("👁️ Start Vision Mode", self._start_vision),
            pystray.Menu.SEPARATOR,
            Item("⚙️ Open Settings", self._open_settings),
            pystray.Menu.SEPARATOR,
            Item("❌ Quit WakeBot", self._quit),
        )

        self._icon = pystray.Icon(
            name="WakeBot",
            icon=self._create_icon_image(),
            title="WakeBot — Idle",
            menu=menu,
        )

        self._logger.info("System Tray icon started. Right-click to access controls.")
        self._icon.run()


def run_tray():
    """Entry point for the system tray mode."""
    tray = WakeBotTray()
    tray.run()
