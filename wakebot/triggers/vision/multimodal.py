"""
WakeBot Multi-Modal Engine — Phase 3
Combines webcam and screen feeds for Vision-Language Model analysis.

Supports:
  - Periodic analysis (every vlm_interval seconds)
  - On-demand queries (triggered by hotword from audio module)
  - Ollama (local LLaVA) and Gemini 1.5 Pro backends
"""

import time
import base64
import threading
from typing import Optional, Callable

from wakebot.core.logger import WakeBotLogger

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import mss
    import mss.tools
except ImportError:
    mss = None

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


class MultiModalEngine(threading.Thread):
    """
    Daemon thread that periodically sends combined webcam + screen frames
    to a Vision-Language Model for contextual analysis.
    GPU Accelerated resizing via PyTorch.
    """

    def __init__(
        self,
        workspace_state,
        camera_index: int = 0,
        interval: float = 60.0,
        vlm_provider: str = "ollama",
        privacy_mode: bool = False,
        sensitive_apps: tuple = (),
        logger: Optional[WakeBotLogger] = None,
        presence_monitor=None,
    ):
        super().__init__(name="MultiModalEngine", daemon=True)

        self._workspace_state = workspace_state
        self._camera_index = camera_index
        self._interval = interval
        self._vlm_provider = vlm_provider
        self._privacy_mode = privacy_mode
        self._sensitive_apps = [app.lower() for app in sensitive_apps]
        self._stop_event = threading.Event()
        self._query_event = threading.Event()
        self._pending_query: Optional[str] = None
        self._query_lock = threading.Lock()
        self._logger = logger or WakeBotLogger()
        self._response_callback: Optional[Callable[[str], None]] = None
        self._paused = False # UI Toggle state
        self._presence_monitor = presence_monitor  # Optional: for frame sharing

        # GPU State
        self._device = "cuda" if (HAS_TORCH and torch.cuda.is_available()) else "cpu"

    # ------------------------------------------------------------------
    # Thread entry
    # ------------------------------------------------------------------
    def run(self):
        """Main loop — periodic + on-demand VLM queries."""
        self._logger.info(
            f"Multi-Modal Engine started: {self._interval}s interval, "
            f"provider={self._vlm_provider} (GPU Accel: {'ON' if self._device == 'cuda' else 'OFF'})"
        )

        while not self._stop_event.is_set():
            triggered = self._query_event.wait(timeout=self._interval)

            if self._stop_event.is_set():
                break

            if self._paused:
                continue

            if triggered:
                self._query_event.clear()
                with self._query_lock:
                    query = self._pending_query or (
                        "Analyze the user's current state and surroundings."
                    )
                    self._pending_query = None
                self._run_analysis(query, on_demand=True)
            else:
                self._run_analysis(
                    "Briefly describe what the user is doing right now. "
                    "Are they working, relaxing, or away?",
                    on_demand=False,
                )

        self._logger.info("Multi-Modal Engine stopped.")

    # ------------------------------------------------------------------
    # Core analysis pipeline
    # ------------------------------------------------------------------
    def _run_analysis(self, prompt: str, on_demand: bool = False):
        """Capture frames, encode, send to VLM, update state."""
        try:
            # Privacy guard: skip screen capture if sensitive app is focused
            screen_b64 = None
            if self._sensitive_apps:
                try:
                    import win32gui
                    hwnd = win32gui.GetForegroundWindow()
                    active_window = win32gui.GetWindowText(hwnd).lower()
                    if any(app in active_window for app in self._sensitive_apps):
                        self._logger.info(
                            "VLM screen capture SKIPPED: sensitive app detected."
                        )
                    else:
                        screen_b64 = self._capture_screen()
                except Exception:
                    screen_b64 = self._capture_screen()
            else:
                screen_b64 = self._capture_screen()

            webcam_b64 = self._capture_webcam()

            if not webcam_b64 and not screen_b64:
                self._logger.error("No frames captured for VLM analysis.")
                return

            response = self._query_vlm(prompt, webcam_b64, screen_b64)

            if response:
                self._workspace_state.update({
                    "vlm_last_analysis": response,
                    "vlm_last_timestamp": time.time(),
                })

                tag = "[ON-DEMAND]" if on_demand else "[PERIODIC]"
                self._logger.info(f"VLM {tag}: {response[:120]}...")

                if on_demand and self._response_callback:
                    self._response_callback(response)

        except Exception as e:
            self._logger.error(f"VLM analysis failed: {e}")

    # ------------------------------------------------------------------
    # GPU Resizing Helper
    # ------------------------------------------------------------------
    def _gpu_resize(self, img_np: "np.ndarray", max_dim: int = 640) -> "np.ndarray":
        """Resize image on GPU using PyTorch."""
        if self._device != "cuda" or not HAS_TORCH:
            return img_np
            
        try:
            import numpy as np
            # Ensure 3-channel
            if img_np.shape[2] == 4:
                img_np = img_np[:, :, :3]
                
            t_img = torch.from_numpy(img_np).to(self._device).permute(2, 0, 1).float()
            h, w = t_img.shape[1], t_img.shape[2]
            
            if max(h, w) > max_dim:
                scale = max_dim / float(max(h, w))
                new_size = (int(h * scale), int(w * scale))
                t_img = torch.nn.functional.interpolate(
                    t_img.unsqueeze(0), size=new_size, mode="bilinear", align_corners=False
                ).squeeze(0)
                
            return t_img.byte().permute(1, 2, 0).cpu().numpy()
        except Exception as e:
            self._logger.error(f"VLM GPU Resize failed: {e}")
            return img_np

    # ------------------------------------------------------------------
    # Frame capture helpers
    # ------------------------------------------------------------------
    def _capture_webcam(self) -> Optional[str]:
        """Grab a single webcam frame -> base64 JPEG."""
        if not cv2:
            return None
        
        import numpy as np

        # Priority 1: Use shared frame from PresenceMonitor to avoid resource conflict
        frame = None
        if self._presence_monitor:
            try:
                frame = self._presence_monitor.get_latest_frame()
            except Exception as e:
                self._logger.error(f"Failed to get frame from PresenceMonitor: {e}")

        # Priority 2: Direct capture fallback (only if no PresenceMonitor)
        if frame is None:
            cap = None
            try:
                cap = cv2.VideoCapture(self._camera_index)
                ret, frame = cap.read()
                if not ret:
                    return None
            except Exception:
                return None
            finally:
                if cap is not None:
                    cap.release()
        
        if frame is not None:
            # GPU Accel: Resize before encoding
            frame = self._gpu_resize(frame, max_dim=480)
            _, buf = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 60]
            )
            return base64.b64encode(buf).decode("utf-8")
        
        return None

    def _capture_screen(self) -> Optional[str]:
        """Grab primary monitor screenshot -> base64 PNG."""
        if not mss:
            return None
        
        import numpy as np

        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                img_np = np.array(screenshot)[:, :, :3]
                
                # GPU Accel: Resize before encoding (VLM doesn't need 4K)
                img_np = self._gpu_resize(img_np, max_dim=720)
                
                _, buf = cv2.imencode(".png", img_np)
                return base64.b64encode(buf).decode("utf-8")
        except Exception as e:
            self._logger.error(f"Screen capture for VLM failed: {e}")
            return None

    # ------------------------------------------------------------------
    # VLM dispatch
    # ------------------------------------------------------------------
    def _query_vlm(
        self,
        prompt: str,
        webcam_b64: Optional[str],
        screen_b64: Optional[str],
    ) -> Optional[str]:
        """Route to the configured VLM backend."""
        effective_provider = self._vlm_provider

        # Privacy mode: force local-only processing
        if self._privacy_mode and effective_provider == "gemini":
            self._logger.info(
                "Privacy mode active: blocking Gemini, falling back to Ollama."
            )
            effective_provider = "ollama"

        if effective_provider == "ollama":
            return self._query_ollama(prompt, webcam_b64, screen_b64)
        elif effective_provider == "gemini":
            return self._query_gemini(prompt, webcam_b64, screen_b64)
        else:
            self._logger.error(f"Unknown VLM provider: {effective_provider}")
            return None

    def _query_ollama(
        self, prompt, webcam_b64, screen_b64
    ) -> Optional[str]:
        """Query a local Ollama instance running a vision model."""
        try:
            import requests

            images = [i for i in (webcam_b64, screen_b64) if i]
            payload = {
                "model": "llava",
                "prompt": prompt,
                "images": images,
                "stream": False,
            }
            resp = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json().get("response", "")
        except Exception as e:
            self._logger.error(f"Ollama query failed: {e}")
            return None

    def _query_gemini(
        self, prompt, webcam_b64, screen_b64
    ) -> Optional[str]:
        """Query Google Gemini Vision API."""
        try:
            import google.generativeai as genai
            from wakebot.core.credentials import get_credential

            api_key = get_credential("GEMINI_API_KEY")
            if not api_key:
                self._logger.error("GEMINI_API_KEY not found. Use: python -m wakebot credentials set GEMINI_API_KEY <key>")
                return None

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-pro")

            parts = [prompt]
            if webcam_b64:
                parts.append({"mime_type": "image/jpeg", "data": webcam_b64})
            if screen_b64:
                parts.append({"mime_type": "image/png", "data": screen_b64})

            response = model.generate_content(parts)
            return response.text
        except Exception as e:
            self._logger.error(f"Gemini query failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def query(
        self,
        prompt: str,
        callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Submit an on-demand query (e.g., from a hotword trigger).
        Thread-safe. Non-blocking.
        """
        with self._query_lock:
            self._pending_query = prompt
            self._response_callback = callback
        self._query_event.set()

    def pause(self):
        """Pause VLM analysis."""
        self._paused = True
        self._logger.info("Multi-Modal Engine PAUSED.")

    def resume(self):
        """Resume VLM analysis."""
        self._paused = False
        self._logger.info("Multi-Modal Engine RESUMED.")

    def stop(self):
        """Signal the thread to stop."""
        self._stop_event.set()
        self._query_event.set()  # Unblock if waiting
        self.join(timeout=5.0)
