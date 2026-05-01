"""
WakeBot Presence Monitor — Phase 1
Background daemon thread for lightweight desk presence detection.
Uses MediaPipe FaceDetection (model_selection=0, short-range <2m).

Thread-safety contract:
  - Communicates ONLY via threading.Event (wake_event / sleep_event).
  - Never calls WakeBotActions directly.
  - Camera is released on stop() or on unrecoverable failure.
"""

# CRITICAL: Must be set before mediapipe is imported anywhere.
# protobuf 5.x C++ parser cannot parse MediaPipe's internal graph configs.
# Forces pure-Python parser. One-time init cost only, no per-frame impact.
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

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

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


class PresenceMonitor(threading.Thread):
    """
    Daemon thread that monitors the webcam for user presence.
    GPU Accelerated via PyTorch CUDA for frame processing and motion detection.
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
        self._frame_queue = None # Set by UI if needed

        # Internal state
        self._user_present = False
        self._last_seen_time = time.monotonic()
        self._prev_frame_gpu = None # For GPU motion detection
        self._paused = False # UI Toggle state
        self._latest_frame = None
        self._frame_lock = threading.Lock()

        # MediaPipe face detector (lazy — validated in run())
        self._face_detection = None
        
        # GPU State
        self._device = "cuda" if (HAS_TORCH and torch.cuda.is_available()) else "cpu"
        if self._device == "cuda":
            self._logger.info(f"PresenceMonitor: Using GPU ({torch.cuda.get_device_name(0)}) for vision acceleration.")
        else:
            self._logger.info("PresenceMonitor: Using CPU for vision processing.")

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

        try:
            self._face_detection = mp.solutions.face_detection.FaceDetection(
                model_selection=0,  # short-range (<2 m), ideal for desk
                min_detection_confidence=self._detection_confidence,
            )
        except Exception as e:
            self._logger.warning(
                f"AI Face Detection initialization failed: {e}. "
                "Falling back to GPU-accelerated Motion Detection."
            )
            self._face_detection = None

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
            if self._paused:
                if self._camera.is_opened():
                    self._camera.release()
                with self._frame_lock:
                    self._latest_frame = None
                self._stop_event.wait(0.5)
                continue

            if not self._camera.is_opened():
                if not self._camera.initialize():
                    self._stop_event.wait(2.0)
                    continue

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

            # Store latest frame thread-safely
            with self._frame_lock:
                self._latest_frame = frame.copy()

            # --- Detection ---
            face_found = False
            
            # Move frame to GPU if available
            t_frame = None
            if self._device == "cuda":
                t_frame = torch.from_numpy(frame).to(self._device)
            
            # 1. Try AI Face Detection (MediaPipe legacy is CPU-bound on Windows)
            if self._face_detection:
                face_found = self._process_frame(frame, t_frame)
            
            # 2. Fallback to GPU-accelerated Motion Detection
            else:
                face_found = self._detect_motion_gpu(t_frame if t_frame is not None else frame)
            
            # Share frame with UI if queue is present
            if self._frame_queue and not self._frame_queue.full():
                try:
                    self._frame_queue.put_nowait(frame.copy())
                except:
                    pass

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
    def _process_frame(self, frame, t_frame: Optional[torch.Tensor] = None) -> bool:
        """Run MediaPipe face detection. Uses GPU for color conversion if possible."""
        try:
            if t_frame is not None:
                # GPU Color Conversion: BGR to RGB
                # PyTorch tensor [H, W, C]
                t_rgb = t_frame[:, :, [2, 1, 0]]
                rgb = t_rgb.cpu().numpy()
            else:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            results = self._face_detection.process(rgb)
            return bool(results.detections)
        except Exception as e:
            self._logger.error(f"Frame processing error: {e}")
            return False

    def _detect_motion_gpu(self, frame_data) -> bool:
        """GPU-accelerated frame differencing using PyTorch."""
        try:
            if self._device != "cuda" or not isinstance(frame_data, torch.Tensor):
                return self._detect_motion_cpu(frame_data)

            # 1. Grayscale (approximate: 0.299R + 0.587G + 0.114B)
            # BGR format in t_frame
            weights = torch.tensor([0.114, 0.587, 0.299], device=self._device)
            gray = (frame_data.float() * weights).sum(dim=-1).byte()
            
            # 2. Simple Gaussian Blur equivalent (box blur for speed)
            # We skip heavy blur on GPU if difference is clean enough
            
            if self._prev_frame_gpu is None:
                self._prev_frame_gpu = gray
                return False

            # 3. Calculate absolute difference
            diff = torch.abs(self._prev_frame_gpu.float() - gray.float())
            
            # 4. Thresholding
            thresh = (diff > 25).byte()
            
            # 5. Check if motion is above threshold (area of changed pixels)
            motion_pixels = torch.sum(thresh).item()
            self._prev_frame_gpu = gray

            # If > 1% of pixels changed
            return motion_pixels > (gray.shape[0] * gray.shape[1] * 0.01)
        except Exception as e:
            self._logger.error(f"GPU Motion Detection error: {e}")
            return self._detect_motion_cpu(frame_data if not isinstance(frame_data, torch.Tensor) else frame_data.cpu().numpy())

    def _detect_motion_cpu(self, frame) -> bool:
        """Standard CPU fallback for motion detection."""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            if not hasattr(self, '_prev_frame_cpu'):
                self._prev_frame_cpu = None

            if self._prev_frame_cpu is None:
                self._prev_frame_cpu = gray
                return False

            frame_delta = cv2.absdiff(self._prev_frame_cpu, gray)
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            motion_area = (thresh > 0).sum()
            self._prev_frame_cpu = gray

            return motion_area > (frame.shape[0] * frame.shape[1] * 0.01)
        except Exception:
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
    def pause(self):
        """Pause monitoring and release camera."""
        self._paused = True
        self._logger.info("Presence Monitor PAUSED via Dashboard.")

    def resume(self):
        """Resume monitoring and re-acquire camera."""
        self._paused = False
        self._logger.info("Presence Monitor RESUMED.")

    def stop(self):
        """Signal the thread to stop and wait for it to finish."""
        self._stop_event.set()
        self.join(timeout=3.0)

    def get_latest_frame(self):
        """Thread-safe access to the last captured frame."""
        with self._frame_lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None
