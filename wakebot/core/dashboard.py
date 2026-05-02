"""
WakeBot Dashboard — Principal Architect Version
A high-performance, dark-themed UI for real-time monitoring and control.
Optimized for HighDPI displays, system resource tracking, and GPU telemetry.
"""

import time
import queue
import threading
import tkinter as tk
from typing import Optional

try:
    import psutil
except ImportError:
    psutil = None

try:
    import customtkinter as ctk
    from PIL import Image
except ImportError:
    ctk = None
    Image = None

from wakebot.core.workspace_state import WorkspaceState
from wakebot.core.logger import WakeBotLogger
from wakebot.core.hardware_monitor import HardwareMonitor

# Configure CustomTkinter appearance
if ctk:
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")


class WakeBotDashboard(ctk.CTk if ctk else tk.Tk):
    """
    Main Dashboard Window.
    Runs on the Main Thread.
    """

    def __init__(
        self,
        workspace_state: WorkspaceState,
        frame_queue: queue.Queue,
        presence_monitor=None,
        screen_monitor=None,
        vlm_engine=None,
        audio_engine=None,
        clap_detector=None,
        voice_detector=None,
        audio_paused=None,
        logger=None,
    ):
        super().__init__()

        self.workspace_state = workspace_state
        self.frame_queue = frame_queue

        # Subsystem instances for direct control
        self.presence_monitor = presence_monitor
        self.screen_monitor = screen_monitor
        self.vlm_engine = vlm_engine

        # Audio subsystem references
        self.audio_engine = audio_engine
        self.clap_detector = clap_detector
        self.voice_detector = voice_detector
        self.audio_paused = audio_paused  # threading.Event — set = paused

        self.logger = logger or WakeBotLogger()

        # Hardware telemetry
        self.hw_monitor = HardwareMonitor()

        # Window Setup
        self.title("WakeBot Control Center — Big Bot v2.1")
        self.geometry("1100x780")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # UI State
        self._current_ctk_image = None
        self._ollama_status = "Checking..."

        self._build_sidebar()
        self._build_main_view()
        self._build_status_bar()

        # Start update loops
        self._update_ui()
        self._update_feed()
        self._check_ollama()

        # Cleanup on window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_sidebar(self):
        """Create the left control panel."""
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)  # Spacer

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, text="WAKEBOT",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 5))

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar_frame, text="Control Center",
            font=ctk.CTkFont(size=12, slant="italic"), text_color="gray"
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 25))

        # ---- Engine Toggles ----
        toggle_header = ctk.CTkLabel(
            self.sidebar_frame, text="ENGINE CONTROL",
            font=ctk.CTkFont(size=10, weight="bold"), text_color="#888888"
        )
        toggle_header.grid(row=2, column=0, padx=20, pady=(5, 5), sticky="w")

        self.audio_switch = ctk.CTkSwitch(
            self.sidebar_frame, text="\U0001F3A7 Audio Engine",
            command=self._toggle_audio
        )
        self.audio_switch.grid(row=3, column=0, padx=20, pady=6, sticky="w")
        self.audio_switch.select()

        self.vision_switch = ctk.CTkSwitch(
            self.sidebar_frame, text="Presence Engine",
            command=self._toggle_vision
        )
        self.vision_switch.grid(row=4, column=0, padx=20, pady=6, sticky="w")
        self.vision_switch.select()

        self.ocr_switch = ctk.CTkSwitch(
            self.sidebar_frame, text="Screen Monitor",
            command=self._toggle_screen
        )
        self.ocr_switch.grid(row=5, column=0, padx=20, pady=6, sticky="w")
        self.ocr_switch.select()

        self.vlm_switch = ctk.CTkSwitch(
            self.sidebar_frame, text="AI Multi-Modal",
            command=self._toggle_vlm
        )
        self.vlm_switch.grid(row=6, column=0, padx=20, pady=6, sticky="w")
        self.vlm_switch.select()

        # ---- System Metrics ----
        metrics_header = ctk.CTkLabel(
            self.sidebar_frame, text="SYSTEM METRICS",
            font=ctk.CTkFont(size=10, weight="bold"), text_color="#888888"
        )
        metrics_header.grid(row=7, column=0, padx=20, pady=(20, 5), sticky="w")

        self.metrics_container = ctk.CTkFrame(
            self.sidebar_frame, fg_color="#1a1a1a", corner_radius=8
        )
        self.metrics_container.grid(row=8, column=0, padx=15, pady=5, sticky="ew")

        self.cpu_lbl = ctk.CTkLabel(
            self.metrics_container, text="CPU      0%",
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.cpu_lbl.grid(row=0, column=0, padx=10, pady=(8, 2), sticky="w")

        self.ram_lbl = ctk.CTkLabel(
            self.metrics_container, text="RAM      0%",
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.ram_lbl.grid(row=1, column=0, padx=10, pady=2, sticky="w")

        # ---- GPU Metrics ----
        gpu_header = ctk.CTkLabel(
            self.sidebar_frame, text="GPU TELEMETRY",
            font=ctk.CTkFont(size=10, weight="bold"), text_color="#888888"
        )
        gpu_header.grid(row=9, column=0, padx=20, pady=(15, 5), sticky="w")

        self.gpu_container = ctk.CTkFrame(
            self.sidebar_frame, fg_color="#1a1a1a", corner_radius=8
        )
        self.gpu_container.grid(row=10, column=0, padx=15, pady=5, sticky="ew")

        self.gpu_name_lbl = ctk.CTkLabel(
            self.gpu_container, text="GPU  N/A",
            font=ctk.CTkFont(family="Consolas", size=11), text_color="#4FC3F7"
        )
        self.gpu_name_lbl.grid(row=0, column=0, padx=10, pady=(8, 2), sticky="w")

        self.gpu_vram_lbl = ctk.CTkLabel(
            self.gpu_container, text="VRAM 0 / 0 MB",
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.gpu_vram_lbl.grid(row=1, column=0, padx=10, pady=2, sticky="w")

        self.gpu_util_lbl = ctk.CTkLabel(
            self.gpu_container, text="UTIL 0%",
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.gpu_util_lbl.grid(row=2, column=0, padx=10, pady=2, sticky="w")

        self.gpu_temp_lbl = ctk.CTkLabel(
            self.gpu_container, text="TEMP 0°C",
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.gpu_temp_lbl.grid(row=3, column=0, padx=10, pady=(2, 2), sticky="w")

        self.gpu_accel_badge = ctk.CTkLabel(
            self.gpu_container, text="● GPU ACCELERATED",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#00C853"
        )
        self.gpu_accel_badge.grid(row=4, column=0, padx=10, pady=(0, 8), sticky="w")

    def _build_main_view(self):
        """Create the central visualization area."""
        self.main_frame = ctk.CTkFrame(
            self, corner_radius=15, fg_color="transparent"
        )
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Video Preview Container
        self.video_container = ctk.CTkFrame(
            self.main_frame, fg_color="#0a0a0a", corner_radius=10
        )
        self.video_container.grid(row=0, column=0, sticky="nsew")

        self.video_label = ctk.CTkLabel(
            self.video_container, text="[ INITIALIZING FEED ]",
            text_color="#333333",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.video_label.pack(expand=True, fill="both")

        # Live Metrics Panel
        self.metrics_frame = ctk.CTkFrame(self.main_frame, height=120)
        self.metrics_frame.grid(row=1, column=0, pady=(20, 0), sticky="ew")
        self.metrics_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.presence_lbl = ctk.CTkLabel(
            self.metrics_frame, text="Presence: AWAY",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.presence_lbl.grid(row=0, column=0, padx=20, pady=25)

        self.window_lbl = ctk.CTkLabel(
            self.metrics_frame, text="Focused: Desktop",
            font=ctk.CTkFont(size=13)
        )
        self.window_lbl.grid(row=0, column=1, padx=20, pady=25)

        self.vlm_status_lbl = ctk.CTkLabel(
            self.metrics_frame, text="Ollama: Checking...",
            font=ctk.CTkFont(size=13), text_color="#FFD740"
        )
        self.vlm_status_lbl.grid(row=0, column=2, padx=20, pady=25)

    def _build_status_bar(self):
        """Create the bottom status bar."""
        self.status_bar = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_bar.grid(row=1, column=1, sticky="ew")

        self.status_label = ctk.CTkLabel(
            self.status_bar, text="Ready — All Systems Online",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(side="left", padx=20)

    # ------------------------------------------------------------------
    # Toggle Callbacks
    # ------------------------------------------------------------------
    def _toggle_audio(self):
        active = self.audio_switch.get()
        if self.audio_paused:
            if active:
                self.audio_paused.clear()  # clear = unpaused (threads run)
                self.logger.info("Audio Engine RESUMED via Dashboard.")
            else:
                self.audio_paused.set()  # set = paused (threads skip work)
                self.logger.info("Audio Engine PAUSED via Dashboard.")
        self.status_label.configure(
            text=f"Audio Engine {'Resumed' if active else 'Paused'}"
        )

    def _toggle_vision(self):
        active = self.vision_switch.get()
        if self.presence_monitor:
            if active:
                self.presence_monitor.resume()
            else:
                self.presence_monitor.pause()
        self.status_label.configure(
            text=f"Presence Engine {'Resumed' if active else 'Paused'}"
        )

    def _toggle_screen(self):
        active = self.ocr_switch.get()
        if self.screen_monitor:
            if active:
                self.screen_monitor.resume()
            else:
                self.screen_monitor.pause()
        self.status_label.configure(
            text=f"Screen Monitor {'Resumed' if active else 'Paused'}"
        )

    def _toggle_vlm(self):
        active = self.vlm_switch.get()
        if self.vlm_engine:
            if active:
                self.vlm_engine.resume()
            else:
                self.vlm_engine.pause()
        self.status_label.configure(
            text=f"VLM Engine {'Resumed' if active else 'Paused'}"
        )

    # ------------------------------------------------------------------
    # Update Loops
    # ------------------------------------------------------------------
    def _check_ollama(self):
        """Verify Ollama availability in a background thread."""
        def task():
            try:
                import requests
                resp = requests.get(
                    "http://localhost:11434/api/tags", timeout=2
                )
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    model_names = [m.get("name", "") for m in models]
                    has_vision = any(
                        "llava" in n or "bakllava" in n for n in model_names
                    )
                    if has_vision:
                        status = "Ollama: Online (LLaVA)"
                        color = "#00C853"
                    else:
                        status = "Ollama: Online (no vision model)"
                        color = "#FFD740"
                else:
                    status = "Ollama: Error"
                    color = "#FFD740"
            except Exception:
                status = "Ollama: Offline"
                color = "#FF5252"

            # Schedule UI update on main thread
            self.after(0, lambda: self.vlm_status_lbl.configure(
                text=status, text_color=color
            ))

        threading.Thread(target=task, daemon=True).start()
        self.after(30000, self._check_ollama)

    def _update_ui(self):
        """Fetch latest data from WorkspaceState and hardware."""
        state = self.workspace_state.snapshot()

        # Presence
        present = state.get("user_present", False)
        self.presence_lbl.configure(
            text=f"Presence: {'AT DESK' if present else 'AWAY'}",
            text_color="#00C853" if present else "#FF5252"
        )

        # Active Window
        window = state.get("active_window", "Desktop")
        if len(window) > 35:
            window = window[:32] + "..."
        self.window_lbl.configure(text=f"Focused: {window}")

        # System Metrics
        if psutil:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            self.cpu_lbl.configure(text=f"CPU      {cpu:5.1f}%")
            self.ram_lbl.configure(text=f"RAM      {ram:5.1f}%")

        # GPU Telemetry
        gpu = self.hw_monitor.snapshot()
        self.workspace_state.update(gpu)

        name = gpu["gpu_name"]
        if len(name) > 25:
            name = name[:22] + "..."
        self.gpu_name_lbl.configure(text=f"GPU  {name}")
        self.gpu_vram_lbl.configure(
            text=f"VRAM {gpu['gpu_vram_used_mb']:>5} / {gpu['gpu_vram_total_mb']} MB"
        )
        self.gpu_util_lbl.configure(text=f"UTIL {gpu['gpu_util_percent']:>3}%")

        temp = gpu["gpu_temp_c"]
        temp_color = "#00C853" if temp < 70 else "#FFD740" if temp < 85 else "#FF5252"
        self.gpu_temp_lbl.configure(
            text=f"TEMP {temp:>3}°C", text_color=temp_color
        )

        self.after(500, self._update_ui)

    def _update_feed(self):
        """Process frames from the PresenceMonitor with HighDPI support."""
        try:
            frame = None
            while not self.frame_queue.empty():
                frame = self.frame_queue.get_nowait()

            if frame is not None and self.vision_switch.get():
                import cv2
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(img_rgb)

                self._current_ctk_image = ctk.CTkImage(
                    light_image=pil_img,
                    dark_image=pil_img,
                    size=(760, 500)
                )
                self.video_label.configure(
                    image=self._current_ctk_image, text=""
                )
            elif not self.vision_switch.get():
                self.video_label.configure(
                    image=None, text="[ FEED PAUSED ]"
                )

        except Exception:
            pass

        self.after(50, self._update_feed)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def _on_close(self):
        """Cleanup hardware monitor and close."""
        self.hw_monitor.shutdown()
        self.destroy()

    def start_dashboard(self):
        self.mainloop()
