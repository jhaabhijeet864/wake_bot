"""
WakeBot Screen Monitor — Phase 2
Background daemon thread for screen capture and OCR text extraction.

Updates WorkspaceState with:
  - Active window title
  - Extracted screen text (capped at 2000 chars)
  - Fullscreen media detection flag
  - Error pattern detection flag + context

Supports pause/resume via a killswitch (threading.Event).
"""

import re
import time
import threading
from typing import Optional, List

from wakebot.core.logger import WakeBotLogger

try:
    import mss
    import mss.tools
except ImportError:
    mss = None

try:
    import easyocr
except ImportError:
    easyocr = None

try:
    import win32gui
except ImportError:
    win32gui = None

# ---------------------------------------------------------------
# Pattern databases
# ---------------------------------------------------------------
MEDIA_PATTERNS: List[str] = [
    "netflix", "youtube", "disney+", "prime video", "hulu",
    "vlc media player", "windows media player", "spotify",
    "grand theft auto", "minecraft", "steam", "epic games",
]

ERROR_PATTERNS: List[str] = [
    r"Traceback \(most recent call last\)",
    r"Error:|Exception:|FAILED|error\[",
    r"SyntaxError:|TypeError:|ValueError:|KeyError:|ImportError:",
    r"ENOENT|EACCES|EPERM",
    r"npm ERR!|ModuleNotFoundError",
]


class ScreenMonitor(threading.Thread):
    """
    Daemon thread that captures the screen periodically and extracts
    text via OCR.  Updates a shared WorkspaceState dictionary.
    """

    def __init__(
        self,
        workspace_state,
        interval: float = 10.0,
        logger: Optional[WakeBotLogger] = None,
    ):
        super().__init__(name="ScreenMonitor", daemon=True)

        self._workspace_state = workspace_state
        self._interval = interval
        self._stop_event = threading.Event()

        # Killswitch: set = running, clear = paused
        self._pause_event = threading.Event()
        self._pause_event.set()

        self._logger = logger or WakeBotLogger()
        self._reader = None  # Lazy-init EasyOCR
        self._error_res = [
            re.compile(p, re.IGNORECASE) for p in ERROR_PATTERNS
        ]

    # ------------------------------------------------------------------
    # Thread entry
    # ------------------------------------------------------------------
    def run(self):
        """Main screen reading loop."""
        if not mss:
            self._logger.error("mss not installed. Screen monitoring disabled.")
            return

        if not easyocr:
            self._logger.error(
                f"easyocr initialization failed: {import_error}. "
                "Screen monitoring (OCR) disabled."
            )
            return

        # Initialize OCR reader (may download model on first run)
        cuda_available = False
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                self._logger.info(
                    f"CUDA detected: {torch.cuda.get_device_name(0)} — EasyOCR will use GPU."
                )
            else:
                self._logger.warning("CUDA not available. EasyOCR will use CPU (slower).")
        except ImportError:
            self._logger.warning("PyTorch not installed. EasyOCR will use CPU.")

        try:
            self._logger.info(
                "Initializing EasyOCR reader (this may take a moment)..."
            )
            self._reader = easyocr.Reader(["en"], gpu=cuda_available, verbose=False)
            self._logger.info(
                f"EasyOCR reader initialized ({'GPU' if cuda_available else 'CPU'})."
            )
        except Exception as e:
            self._logger.error(f"EasyOCR init failed: {e}")
            return

        self._logger.info(
            f"Screen Monitor started: {self._interval}s interval"
        )

        while not self._stop_event.is_set():
            # Block here while paused (killswitch)
            self._pause_event.wait()
            if self._stop_event.is_set():
                break

            try:
                self._capture_and_analyze()
            except Exception as e:
                self._logger.error(f"Screen capture cycle error: {e}")

            self._stop_event.wait(self._interval)

        self._logger.info("Screen Monitor stopped.")

    # ------------------------------------------------------------------
    # Core analysis
    # ------------------------------------------------------------------
    def _capture_and_analyze(self):
        """Capture screen, run OCR, update WorkspaceState."""
        active_window = self._get_active_window()

        # Fullscreen media check (cheap — string compare only)
        is_media = any(
            p in active_window.lower() for p in MEDIA_PATTERNS
        )

        # Screen capture
        import numpy as np

        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)[:, :, :3]  # Drop alpha channel

        # OCR
        results = self._reader.readtext(img, detail=0)
        extracted = " ".join(results)

        # Error pattern matching
        is_error = False
        error_ctx = ""
        for pattern in self._error_res:
            match = pattern.search(extracted)
            if match:
                is_error = True
                start = max(0, match.start() - 50)
                end = min(len(extracted), match.end() + 50)
                error_ctx = extracted[start:end]
                break

        # Atomic batch update (thread-safe via WorkspaceState._lock)
        self._workspace_state.update({
            "active_window": active_window,
            "extracted_text": extracted[:2000],
            "is_fullscreen_media": is_media,
            "is_error_detected": is_error,
            "error_context": error_ctx,
        })

        if is_media:
            self._logger.info(f"Media detected: {active_window}")
        if is_error:
            self._logger.info("Error pattern detected in screen text.")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _get_active_window() -> str:
        """Get the title of the currently focused window."""
        if win32gui:
            try:
                hwnd = win32gui.GetForegroundWindow()
                return win32gui.GetWindowText(hwnd)
            except Exception:
                pass
        return ""

    # ------------------------------------------------------------------
    # Public API — Killswitch
    # ------------------------------------------------------------------
    def pause(self):
        """Pause screen reading (killswitch ON)."""
        self._pause_event.clear()
        self._workspace_state.set("screen_reading_active", False)
        self._logger.info("Screen Monitor PAUSED by user.")

    def resume(self):
        """Resume screen reading (killswitch OFF)."""
        self._workspace_state.set("screen_reading_active", True)
        self._pause_event.set()
        self._logger.info("Screen Monitor RESUMED.")

    def stop(self):
        """Signal the thread to stop."""
        self._stop_event.set()
        self._pause_event.set()  # Unblock if paused so thread can exit
        self.join(timeout=5.0)
5.0)
