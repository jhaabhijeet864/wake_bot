"""
WakeBot Gesture Controller — GPU-Accelerated Hand Gesture Media Control
Issue #21

Uses MediaPipe Hand Landmarkers to detect gestures and map them to
system actions:
  - Raise Palm  -> Media Pause/Play
  - Finger Pinch -> Mic Mute Toggle
  - Swipe Left  -> Next Track
  - Swipe Right -> Previous Track

Emits GESTURE_DETECTED events on the central EventBus.
"""

import os
import time
import ctypes
import threading
from typing import Optional
from collections import deque

from wakebot.core.logger import WakeBotLogger
from wakebot.core.event_bus import EventBus

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    import mediapipe as mp
except ImportError:
    mp = None

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Windows Virtual Key codes for media control
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
KEYEVENTF_KEYUP = 0x0002

# MediaPipe hand landmark indices
WRIST = 0
THUMB_TIP = 4
INDEX_TIP = 8
MIDDLE_TIP = 12
RING_TIP = 16
PINKY_TIP = 20
INDEX_MCP = 5
MIDDLE_MCP = 9
RING_MCP = 13
PINKY_MCP = 17
THUMB_MCP = 2


class GestureController(threading.Thread):
    """
    Daemon thread: detects hand gestures from webcam frames and
    executes corresponding media/system actions.
    Consumes frames from PresenceMonitor.get_latest_frame().
    """

    def __init__(
        self,
        presence_monitor,
        target_fps: float = 5.0,
        cooldown_s: float = 1.5,
        min_confidence: float = 0.7,
        logger: Optional[WakeBotLogger] = None,
    ):
        super().__init__(name="GestureController", daemon=True)
        self._presence = presence_monitor
        self._fps = target_fps
        self._interval = 1.0 / target_fps
        self._cooldown = cooldown_s
        self._min_conf = min_confidence
        self._logger = logger or WakeBotLogger()
        self._bus = EventBus()
        self._stop = threading.Event()
        self._paused = False

        self._last_action_time = 0.0
        self._hands = None
        self._device = "cuda" if (HAS_TORCH and torch.cuda.is_available()) else "cpu"
        self._mic_muted = False

        # Swipe detection state
        self._swipe_history: deque = deque(maxlen=10)
        self._swipe_start_time = 0.0
        self._swipe_start_x = None

        # Palm hold detection
        self._palm_start_time = 0.0
        self._palm_held = False

        # Pinch hold detection
        self._pinch_start_time = 0.0
        self._pinch_held = False

    # -- Thread lifecycle --
    def run(self):
        if not all([cv2, np, mp]):
            self._logger.error("GestureController requires opencv, numpy, mediapipe.")
            return
        try:
            self._hands = mp.solutions.hands.Hands(
                static_image_mode=False,
                model_complexity=1,
                max_num_hands=1,
                min_detection_confidence=self._min_conf,
                min_tracking_confidence=0.5,
            )
        except Exception as e:
            self._logger.error(f"MediaPipe Hands init failed: {e}")
            return

        self._logger.info(
            f"Gesture Controller active: {self._fps} FPS, "
            f"cooldown={self._cooldown}s, GPU={'ON' if self._device == 'cuda' else 'OFF'}"
        )

        while not self._stop.is_set():
            if self._paused:
                self._stop.wait(0.5)
                continue
            t0 = time.monotonic()
            try:
                self._process()
            except Exception as e:
                self._logger.error(f"Gesture error: {e}")
            elapsed = time.monotonic() - t0
            self._stop.wait(max(0.0, self._interval - elapsed))

        if self._hands:
            self._hands.close()
        self._logger.info("Gesture Controller stopped.")

    def _process(self):
        frame = self._presence.get_latest_frame()
        if frame is None:
            return

        frame = self._gpu_resize(frame, 480)
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self._hands.process(rgb)

        if not res.multi_hand_landmarks:
            self._reset_gesture_state()
            return

        lm = res.multi_hand_landmarks[0]
        now = time.monotonic()

        # Check cooldown
        if now - self._last_action_time < self._cooldown:
            return

        # Priority: Palm > Pinch > Swipe
        if self._check_palm(lm, now):
            return
        if self._check_pinch(lm, w, h, now):
            return
        self._check_swipe(lm, w, now)

    # -- Gesture: Raise Palm --
    def _check_palm(self, lm, now) -> bool:
        """All 5 fingertips above their MCP joints = open palm."""
        tips = [THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]
        mcps = [THUMB_MCP, INDEX_MCP, MIDDLE_MCP, RING_MCP, PINKY_MCP]

        all_up = all(
            lm.landmark[t].y < lm.landmark[m].y
            for t, m in zip(tips, mcps)
        )

        if all_up:
            if not self._palm_held:
                self._palm_held = True
                self._palm_start_time = now
            elif now - self._palm_start_time >= 0.5:
                self._fire("RAISE_PALM", "MEDIA_PAUSE")
                self._send_media_key(VK_MEDIA_PLAY_PAUSE)
                self._palm_held = False
                return True
        else:
            self._palm_held = False
        return False

    # -- Gesture: Finger Pinch --
    def _check_pinch(self, lm, w, h, now) -> bool:
        """Thumb tip close to index tip = pinch."""
        thumb = np.array([lm.landmark[THUMB_TIP].x * w, lm.landmark[THUMB_TIP].y * h])
        index = np.array([lm.landmark[INDEX_TIP].x * w, lm.landmark[INDEX_TIP].y * h])
        dist = np.linalg.norm(thumb - index)

        # Normalize threshold relative to frame size
        threshold = w * 0.04  # ~4% of frame width

        if dist < threshold:
            if not self._pinch_held:
                self._pinch_held = True
                self._pinch_start_time = now
            elif now - self._pinch_start_time >= 0.3:
                self._mic_muted = not self._mic_muted
                action = "MIC_MUTE" if self._mic_muted else "MIC_UNMUTE"
                self._fire("FINGER_PINCH", action)
                self._toggle_mic_mute()
                self._pinch_held = False
                return True
        else:
            self._pinch_held = False
        return False

    # -- Gesture: Horizontal Swipe --
    def _check_swipe(self, lm, w, now):
        """Track index finger horizontal movement for swipe detection."""
        ix = lm.landmark[INDEX_TIP].x

        if self._swipe_start_x is None:
            self._swipe_start_x = ix
            self._swipe_start_time = now
            return

        dt = now - self._swipe_start_time
        dx = ix - self._swipe_start_x

        # Must complete within 0.4s and move >30% of frame
        if dt > 0.4:
            self._swipe_start_x = ix
            self._swipe_start_time = now
            return

        if abs(dx) > 0.3:
            if dx > 0:
                self._fire("SWIPE_RIGHT", "MEDIA_NEXT_TRACK")
                self._send_media_key(VK_MEDIA_NEXT_TRACK)
            else:
                self._fire("SWIPE_LEFT", "MEDIA_PREV_TRACK")
                self._send_media_key(VK_MEDIA_PREV_TRACK)
            self._swipe_start_x = None

    def _reset_gesture_state(self):
        self._palm_held = False
        self._pinch_held = False
        self._swipe_start_x = None

    # -- Action Dispatch --
    def _fire(self, gesture: str, action: str):
        self._last_action_time = time.monotonic()
        self._logger.info(f"Gesture: {gesture} -> {action}")
        self._bus.emit("GESTURE_DETECTED", {
            "gesture": gesture,
            "action": action,
        })

    @staticmethod
    def _send_media_key(vk_code: int):
        """Send a media key press/release on Windows."""
        try:
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
        except Exception:
            pass

    @staticmethod
    def _toggle_mic_mute():
        """Toggle system microphone mute via Windows multimedia keys."""
        # Use the dedicated mic mute virtual key if available (Win10+),
        # otherwise this is a no-op. For full control, pycaw can be added.
        try:
            # Some keyboards/systems support VK 0xAD (volume mute) but
            # mic mute requires deeper COM. For now, simulate Ctrl+Shift+M
            # which is a common mic-mute shortcut in Teams/Zoom/Discord.
            import pyautogui
            pyautogui.hotkey("ctrl", "shift", "m")
        except Exception:
            pass

    # -- GPU Resize --
    def _gpu_resize(self, frame, max_dim=480):
        if self._device != "cuda" or not HAS_TORCH:
            return frame
        try:
            h, w = frame.shape[:2]
            if max(h, w) <= max_dim:
                return frame
            t = torch.from_numpy(frame).to(self._device).permute(2, 0, 1).float()
            s = max_dim / float(max(h, w))
            ns = (int(h * s), int(w * s))
            t = torch.nn.functional.interpolate(
                t.unsqueeze(0), size=ns, mode="bilinear", align_corners=False
            ).squeeze(0)
            return t.byte().permute(1, 2, 0).cpu().numpy()
        except Exception:
            return frame

    # -- Controls --
    def pause(self):
        self._paused = True
        self._logger.info("Gesture Controller PAUSED.")

    def resume(self):
        self._paused = False
        self._logger.info("Gesture Controller RESUMED.")

    def stop(self):
        self._stop.set()
        self.join(timeout=3.0)
