"""
WakeBot Gaze Tracker — GPU-Accelerated Head-Pose & Attention State Engine
Issue #21

Uses MediaPipe FaceMesh (478 landmarks, refine_iris=True) to compute:
  - 3D head-pose (pitch, yaw, roll) via cv2.solvePnP
  - Iris-based gaze direction vector
  - Attention state: LOOKING_AT_SCREEN / LOOKING_AT_BOT / DISTRACTED

Emits GAZE_STATE_CHANGED events on the central EventBus.
"""

import os
import time
import math
import threading
from typing import Optional, List, Tuple
from collections import deque, Counter
from enum import Enum

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


class AttentionState(Enum):
    UNKNOWN = "UNKNOWN"
    LOOKING_AT_SCREEN = "LOOKING_AT_SCREEN"
    LOOKING_AT_BOT = "LOOKING_AT_BOT"
    DISTRACTED = "DISTRACTED"


# 3D model points for solvePnP (nose, chin, eye corners, mouth corners)
_MODEL_POINTS_3D = None

def _get_model_points():
    global _MODEL_POINTS_3D
    if _MODEL_POINTS_3D is None and np is not None:
        _MODEL_POINTS_3D = np.array([
            (0.0, 0.0, 0.0),          # Nose tip
            (0.0, -63.6, -12.5),       # Chin
            (-43.3, 32.7, -26.0),      # Left eye outer
            (43.3, 32.7, -26.0),       # Right eye outer
            (-28.9, -28.9, -24.1),     # Left mouth
            (28.9, -28.9, -24.1),      # Right mouth
        ], dtype=np.float64)
    return _MODEL_POINTS_3D

# MediaPipe landmark indices for the 6 canonical face points
_FACE_IDS = [1, 152, 33, 263, 61, 291]

# Iris landmarks (refine_iris=True)
_L_IRIS = 468
_R_IRIS = 473
_L_EYE_IN = 133
_L_EYE_OUT = 33
_R_EYE_IN = 362
_R_EYE_OUT = 263


class GazeTracker(threading.Thread):
    """
    Daemon thread: head-pose, gaze vector, and attention state from webcam.
    Consumes frames from PresenceMonitor.get_latest_frame().
    """

    def __init__(
        self,
        presence_monitor,
        target_fps: float = 5.0,
        smoothing_window: int = 5,
        screen_yaw_threshold: float = 15.0,
        bot_yaw_threshold: float = 45.0,
        logger: Optional[WakeBotLogger] = None,
    ):
        super().__init__(name="GazeTracker", daemon=True)
        self._presence = presence_monitor
        self._fps = target_fps
        self._interval = 1.0 / target_fps
        self._smooth_n = smoothing_window
        self._screen_yaw = screen_yaw_threshold
        self._bot_yaw = bot_yaw_threshold
        self._logger = logger or WakeBotLogger()
        self._bus = EventBus()
        self._stop = threading.Event()
        self._paused = False

        self._state = AttentionState.UNKNOWN
        self._lock = threading.Lock()
        self._history: deque = deque(maxlen=smoothing_window)
        self._head_pose: Optional[Tuple[float, float, float]] = None
        self._gaze_vec: Optional[List[float]] = None
        self._device = "cuda" if (HAS_TORCH and torch.cuda.is_available()) else "cpu"
        self._mesh = None

    # -- Public API --
    def get_attention_state(self) -> AttentionState:
        with self._lock:
            return self._state

    def get_head_pose(self) -> Optional[Tuple[float, float, float]]:
        with self._lock:
            return self._head_pose

    def get_gaze_vector(self) -> Optional[List[float]]:
        with self._lock:
            return self._gaze_vec

    # -- Thread lifecycle --
    def run(self):
        if not all([cv2, np, mp]):
            self._logger.error("GazeTracker requires opencv, numpy, mediapipe.")
            return
        try:
            self._mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False, max_num_faces=1,
                refine_iris=True, min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
        except Exception as e:
            self._logger.error(f"FaceMesh init failed: {e}")
            return

        self._logger.info(
            f"Gaze Tracker active: {self._fps} FPS, "
            f"GPU={'ON' if self._device == 'cuda' else 'OFF'}"
        )

        while not self._stop.is_set():
            if self._paused:
                self._stop.wait(0.5)
                continue
            t0 = time.monotonic()
            try:
                self._process()
            except Exception as e:
                self._logger.error(f"Gaze error: {e}")
            elapsed = time.monotonic() - t0
            self._stop.wait(max(0.0, self._interval - elapsed))

        if self._mesh:
            self._mesh.close()
        self._logger.info("Gaze Tracker stopped.")

    def _process(self):
        frame = self._presence.get_latest_frame()
        if frame is None:
            return

        frame = self._gpu_resize(frame, 480)
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self._mesh.process(rgb)

        if not res.multi_face_landmarks:
            self._commit_state(AttentionState.DISTRACTED, None, None)
            return

        lm = res.multi_face_landmarks[0]
        yaw, pitch, roll = self._head_pose_pnp(lm, w, h)
        gaze = self._iris_gaze(lm, w, h)

        with self._lock:
            self._head_pose = (yaw, pitch, roll)
            self._gaze_vec = gaze

        state = self._classify(yaw, gaze)
        self._commit_state(state, yaw, pitch)

    # -- Head Pose via solvePnP --
    def _head_pose_pnp(self, lm, w, h):
        model = _get_model_points()
        pts2d = np.array([
            (lm.landmark[i].x * w, lm.landmark[i].y * h)
            for i in _FACE_IDS
        ], dtype=np.float64)

        cam = np.array([
            [w, 0, w / 2], [0, w, h / 2], [0, 0, 1]
        ], dtype=np.float64)
        dist = np.zeros((4, 1), dtype=np.float64)

        ok, rvec, tvec = cv2.solvePnP(
            model, pts2d, cam, dist, flags=cv2.SOLVEPNP_ITERATIVE
        )
        if not ok:
            return 0.0, 0.0, 0.0

        rmat, _ = cv2.Rodrigues(rvec)
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
        return float(angles[1]), float(angles[0]), float(angles[2])

    # -- Iris Gaze Vector --
    def _iris_gaze(self, lm, w, h):
        def pt(i):
            return np.array([lm.landmark[i].x * w, lm.landmark[i].y * h])

        l_iris, l_in, l_out = pt(_L_IRIS), pt(_L_EYE_IN), pt(_L_EYE_OUT)
        r_iris, r_in, r_out = pt(_R_IRIS), pt(_R_EYE_IN), pt(_R_EYE_OUT)

        l_w = np.linalg.norm(l_in - l_out)
        r_w = np.linalg.norm(r_in - r_out)
        l_off = (l_iris - (l_in + l_out) / 2) / (l_w + 1e-6)
        r_off = (r_iris - (r_in + r_out) / 2) / (r_w + 1e-6)

        avg = (l_off + r_off) / 2.0
        gaze = [float(avg[0]), float(avg[1]), 1.0]
        mag = math.sqrt(sum(g * g for g in gaze))
        return [g / mag for g in gaze] if mag > 0 else gaze

    # -- Attention Classification --
    def _classify(self, yaw, gaze):
        ay = abs(yaw)
        if ay > self._bot_yaw:
            return AttentionState.DISTRACTED
        if ay > self._screen_yaw:
            return AttentionState.LOOKING_AT_BOT
        if gaze and abs(gaze[0]) < 0.3:
            return AttentionState.LOOKING_AT_SCREEN
        return AttentionState.LOOKING_AT_BOT

    def _commit_state(self, candidate, yaw, pitch):
        self._history.append(candidate)
        if len(self._history) < 3:
            return
        counts = Counter(self._history)
        best, n = counts.most_common(1)[0]
        if n < 3:
            return
        with self._lock:
            prev = self._state
            if best != prev:
                self._state = best
                self._logger.info(
                    f"Attention: {prev.value} -> {best.value}"
                )
                self._bus.emit("GAZE_STATE_CHANGED", {
                    "state": best.value,
                    "prev_state": prev.value,
                    "yaw": yaw or 0.0,
                    "pitch": pitch or 0.0,
                    "gaze_vector": self._gaze_vec or [0, 0, 1],
                })

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
        self._logger.info("Gaze Tracker PAUSED.")

    def resume(self):
        self._paused = False
        self._logger.info("Gaze Tracker RESUMED.")

    def stop(self):
        self._stop.set()
        self.join(timeout=3.0)
