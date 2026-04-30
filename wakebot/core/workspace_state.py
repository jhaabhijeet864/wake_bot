"""
WakeBot Workspace State
Thread-safe global state container for cross-module communication.
All vision subsystems write here; action/decision modules read from here.
"""

import time
import threading
from typing import Any, Dict


class WorkspaceState:
    """
    Thread-safe container for the bot's understanding of the user's environment.
    Uses a single lock to serialize all reads and writes.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._state: Dict[str, Any] = {
            # Phase 1: Presence
            "user_present": False,
            "last_seen_timestamp": 0.0,

            # Phase 2: Screen Awareness
            "active_window": "",
            "extracted_text": "",
            "is_fullscreen_media": False,
            "is_error_detected": False,
            "error_context": "",
            "screen_reading_active": True,

            # Phase 3: Multi-Modal
            "vlm_last_analysis": "",
            "vlm_last_timestamp": 0.0,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Thread-safe single key read."""
        with self._lock:
            return self._state.get(key, default)

    def set(self, key: str, value: Any):
        """Thread-safe single key write."""
        with self._lock:
            self._state[key] = value

    def update(self, updates: Dict[str, Any]):
        """Thread-safe batch update."""
        with self._lock:
            self._state.update(updates)

    def snapshot(self) -> Dict[str, Any]:
        """Return a shallow copy of the entire state (thread-safe)."""
        with self._lock:
            return dict(self._state)
