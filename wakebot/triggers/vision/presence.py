"""
WakeBot Presence Monitor — Phase 1 (v2.1.0)
Decoupled trigger: Emits USER_ARRIVED / USER_LEFT via EventBus.
- New: Thread-safe get_latest_frame() for VLM integration.
"""

import os
import time
import threading
from typing import Optional
from wakebot.core.logger import WakeBotLogger
from wakebot.core.event_bus import EventBus
from wakebot.triggers.vision.engine import CameraEngine

# Force pure-Python protobuf parser for MediaPipe compatibility
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

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
    Daemon thread that monitors the webcam and emits events.
    """
    def __init__(
        self,
        camera_index: int = 0,
        target_fps: float = 5.0,
        absence_threshold: float = 120.0,
        logger: Optional[WakeBotLogger] = None,
    ):
        super().__init__(name="PresenceMonitor", daemon=True)
        self.logger = logger or WakeBotLogger()
        self.event_bus = EventBus()
        self.stop_event = threading.Event()
        self.paused = False
        
        self.camera = CameraEngine(camera_index=camera_index)
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.absence_threshold = absence_threshold
        
        self.user_present = False
        self.last_seen_time = time.monotonic()
        self.frame_queue = None
        self._latest_frame = None
        self._frame_lock = threading.Lock()
        self.face_detection = None

    def get_latest_frame(self):
        """Thread-safe access to the most recent webcam frame."""
        with self._frame_lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None

    def run(self):
        """Main vision loop."""
        if not mp or not cv2:
            self.logger.error("MediaPipe or OpenCV missing. Presence detection disabled.")
            return

        try:
            # Robust MediaPipe init
            from mediapipe.python.solutions import face_detection as mp_face
            self.face_detection = mp_face.FaceDetection(
                model_selection=0, 
                min_detection_confidence=0.5
            )
        except Exception as e:
            self.logger.error(f"Failed to init MediaPipe FaceDetection: {e}")
            return

        if not self.camera.initialize():
            self.logger.error("Camera failed to initialize.")
            return

        self.logger.info("Presence Monitor active.")

        while not self.stop_event.is_set():
            if self.paused:
                if self.camera.is_opened(): self.camera.release()
                self.stop_event.wait(0.5)
                continue

            if not self.camera.is_opened():
                if not self.camera.initialize():
                    self.stop_event.wait(2.0)
                    continue

            start_time = time.monotonic()
            ret, frame = self.camera.read_frame()
            
            if ret:
                # Store latest frame for VLM
                with self._frame_lock:
                    self._latest_frame = frame.copy()

                # Share frame with UI
                if self.frame_queue and not self.frame_queue.full():
                    try: self.frame_queue.put_nowait(frame.copy())
                    except: pass

                # Detection
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.face_detection.process(rgb)
                
                now = time.monotonic()
                if results.detections:
                    self.last_seen_time = now
                    if not self.user_present:
                        self.user_present = True
                        self.event_bus.emit("USER_ARRIVED", {"source": "vision"})
                else:
                    if self.user_present and (now - self.last_seen_time > self.absence_threshold):
                        self.user_present = False
                        self.event_bus.emit("USER_LEFT", {"source": "vision"})

            # Throttling
            elapsed = time.monotonic() - start_time
            sleep_time = max(0.0, self.frame_interval - elapsed)
            self.stop_event.wait(sleep_time)

        self._cleanup()

    def _cleanup(self):
        self.camera.release()
        if self.face_detection: self.face_detection.close()

    def pause(self): self.paused = True
    def resume(self): self.paused = False
    def stop(self):
        self.stop_event.set()
        self.join(timeout=3.0)
