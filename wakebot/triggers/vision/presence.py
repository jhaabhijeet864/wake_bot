"""
WakeBot Presence Monitor — Phase 1
Background daemon thread for lightweight desk presence detection.
Uses MediaPipe FaceDetection (model_selection=0, short-range <2m).

Thread-safety contract:
  - Communicates ONLY via threading.Event (wake_event / sleep_event).
  - Never calls WakeBotActions directly.
  - Camera is released on stop() or on unrecoverable failure.
"""

import time
import threading
from typing import Optional

from wakebot.core.logger import WakeBotLogger
from wakebot.triggers.vision.engine import CameraEngine

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import mediapipe as mp
except ImportError:
    mp = None


class PresenceMonitor(threading.Thread):
    """
    Daemon thread that monitors the webcam for user presence.

    Emits:
        wake_event  — set when user arrives (face detected after absence)
        sleep_event — set when user has been absent > absence_threshold seconds
    """

    def __init__(
        self,
        wake_event: threading.Event,
        sleep_event: threading.Event,
        camera_index: int = 0,
        target_fps: float = 5.0,
        absence_threshold: float = 120.0,
        detection_confidence: float = 0.5,
        logger: Optional[WakeBotLogger] = None,
    ):
        super().__init__(name="PresenceMonitor", daemon=True)

        self._wake_event = wake_event
        self._sleep_event = sleep_event
        self._stop_event = threading.Event()

        self._camera = CameraEngine(camera_index=camera_index)
        self._target_fps = target_fps
        self._frame_interval = 1.0 / target_fps
        self._absence_threshold = absence_threshold
        self._detection_confidence = detection_confidence
        self._logger = logger or WakeBotLogger()

        # Internal state
        self._user_present = False
        self._last_seen_time = time.monotonic()

        # MediaPipe face detector (lazy — validated in run())
        self._face_detection = None

    # ------------------------------------------------------------------
    # Thread entry
    # ------------------------------------------------------------------
    def run(self):
        """Main vision loop — time-delta gated at target FPS."""
        if not mp or not cv2:
            self._logger.error(
                "mediapipe or opencv-python not installed. "
                "Presence monitoring disabled."
            )
            return

        self._face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=0,  # short-range (<2 m), ideal for desk
            min_detection_confidence=self._detection_confidence,
        )

        if not self._camera.initialize():
            self._logger.error(
                "Camera initialization failed. Presence monitoring disabled."
            )
            return

        self._logger.info(
            f"Presence Monitor started: {self._target_fps} FPS, "
            f"{self._absence_threshold}s absence threshold"
        )

        consecutive_failures = 0

        while not self._stop_event.is_set():
            frame_start = time.monotonic()

            # --- Frame acquisition ---
            ret, frame = self._camera.read_frame()
            if not ret:
                consecutive_failures += 1
                if consecutive_failures >= 10:
                    self._logger.error(
                        "Camera lost (10 consecutive failures). "
                        "Sleeping 5 s before re-init..."
                    )
                    self._stop_event.wait(5.0)
                    self._camera.release()
                    if self._camera.initialize():
                        self._logger.info("Camera re-initialized successfully.")
                        consecutive_failures = 0
                    continue
                self._stop_event.wait(0.5)
                continue

            consecutive_failures = 0

            # --- Detection ---
            face_found = self._process_frame(frame)
            now = time.monotonic()

            if face_found:
                self._last_seen_time = now
                if not self._user_present:
                    self._user_present = True
                    self._logger.action("USER ARRIVED — Presence detected.")
                    self._wake_event.set()
            else:
                if self._user_present and (
                    now - self._last_seen_time > self._absence_threshold
                ):
                    self._user_present = False
                    self._logger.action(
                        f"USER LEFT — Absent for >{self._absence_threshold:.0f}s."
                    )
                    self._sleep_event.set()

            # --- Enforce FPS via interruptible sleep ---
            elapsed = time.monotonic() - frame_start
            sleep_time = max(0.0, self._frame_interval - elapsed)
            if sleep_time > 0:
                self._stop_event.wait(sleep_time)

        # Cleanup on exit
        self._cleanup()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _process_frame(self, frame) -> bool:
        """Run MediaPipe face detection on a single BGR frame."""
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self._face_detection.process(rgb)
            return bool(results.detections)
        except Exception as e:
            self._logger.error(f"Frame processing error: {e}")
            return False

    def _cleanup(self):
        """Release all resources."""
        self._camera.release()
        if self._face_detection:
            self._face_detection.close()
        self._logger.info("Presence Monitor stopped and resources released.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def stop(self):
        """Signal the thread to stop and wait for it to finish."""
        self._stop_event.set()
        self.join(timeout=3.0)
