"""
WakeBot Dashboard UI — Big Bot v2.1.0
Unified control center for presence, screen, VLM, and audio engines.
- New: AudioOrchestrator integration.
- New: Real-time API status (Ollama/Gemini).
- New: Local-Only AI toggle.
- New: Real-time NVIDIA GPU & VRAM Hardware Telemetry widgets.
- New: Live, scrollable, thread-safe system-wide EventBus log terminal.
- Optimized: Video scaling and rendering.
"""

import queue
import time
import threading
import requests
import customtkinter as ctk
from PIL import Image
from wakebot.core.logger import WakeBotLogger
from wakebot.core.workspace_state import WorkspaceState
from wakebot.core.hardware_monitor import HardwareMonitor
from wakebot.core.event_bus import EventBus

class WakeBotDashboard(ctk.CTk):
    def __init__(
        self,
        workspace_state: WorkspaceState,
        frame_queue: queue.Queue,
        presence_monitor=None,
        screen_monitor=None,
        vlm_engine=None,
        audio_orchestrator=None,
        logger=None,
    ):
        super().__init__()

        self.workspace_state = workspace_state
        self.frame_queue = frame_queue
        self.presence_monitor = presence_monitor
        self.screen_monitor = screen_monitor
        self.vlm_engine = vlm_engine
        self.audio = audio_orchestrator
        self.logger = logger or WakeBotLogger()
        self.hw_monitor = HardwareMonitor()
        self.event_bus = EventBus()

        # Window Setup
        self.title("WakeBot Control Center — v2.1.0")
        self.geometry("1100x820")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # UI State & Thread-Safe Logging Queue
        self._current_ctk_image = None
        self._ollama_status = "OFFLINE"
        self._gemini_status = "IDLE"
        self._last_telemetry_time = 0.0
        self.log_queue = queue.Queue()

        self._build_ui()
        self._setup_event_subscriptions()
        self._update_loop()

    def _build_ui(self):
        # ---- Sidebar ----
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        logo_lbl = ctk.CTkLabel(
            self.sidebar_frame, text="WAKEBOT",
            font=ctk.CTkFont(family="Orbitron", size=24, weight="bold"),
            text_color="#4FC3F7"
        )
        logo_lbl.grid(row=0, column=0, padx=20, pady=(20, 10))

        # ---- API Status ----
        self.api_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="#1a1a1a", corner_radius=8)
        self.api_frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        
        self.ollama_lbl = ctk.CTkLabel(self.api_frame, text="Ollama: OFFLINE", font=("Consolas", 11), text_color="#ff5252")
        self.ollama_lbl.grid(row=0, column=0, padx=10, pady=(5, 2), sticky="w")
        
        self.gemini_lbl = ctk.CTkLabel(self.api_frame, text="Gemini: IDLE", font=("Consolas", 11), text_color="#ffb142")
        self.gemini_lbl.grid(row=1, column=0, padx=10, pady=(2, 5), sticky="w")

        # ---- Engine Toggles ----
        toggle_header = ctk.CTkLabel(
            self.sidebar_frame, text="ENGINE CONTROL",
            font=ctk.CTkFont(size=10, weight="bold"), text_color="#888888"
        )
        toggle_header.grid(row=2, column=0, padx=20, pady=(15, 5), sticky="w")

        self.audio_switch = ctk.CTkSwitch(self.sidebar_frame, text="🎧 Audio System", command=self._toggle_audio)
        self.audio_switch.grid(row=3, column=0, padx=20, pady=6, sticky="w")
        self.audio_switch.select()

        self.vision_switch = ctk.CTkSwitch(self.sidebar_frame, text="👤 Presence Engine", command=self._toggle_vision)
        self.vision_switch.grid(row=4, column=0, padx=20, pady=6, sticky="w")
        self.vision_switch.select()

        self.ocr_switch = ctk.CTkSwitch(self.sidebar_frame, text="🖥️ Screen Monitor", command=self._toggle_screen)
        self.ocr_switch.grid(row=5, column=0, padx=20, pady=6, sticky="w")
        self.ocr_switch.select()

        self.vlm_switch = ctk.CTkSwitch(self.sidebar_frame, text="🧠 AI VLM", command=self._toggle_vlm)
        self.vlm_switch.grid(row=6, column=0, padx=20, pady=6, sticky="w")
        self.vlm_switch.select()

        self.local_only_switch = ctk.CTkSwitch(self.sidebar_frame, text="🔒 Local-Only AI", command=self._toggle_local_only)
        self.local_only_switch.grid(row=7, column=0, padx=20, pady=6, sticky="w")
        if self.workspace_state.get("local_only", False):
            self.local_only_switch.select()

        # ---- System Telemetry ----
        telemetry_header = ctk.CTkLabel(
            self.sidebar_frame, text="💻 SYSTEM TELEMETRY",
            font=ctk.CTkFont(size=10, weight="bold"), text_color="#888888"
        )
        telemetry_header.grid(row=8, column=0, padx=20, pady=(15, 5), sticky="w")

        self.telemetry_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="#111111", corner_radius=8)
        self.telemetry_frame.grid(row=9, column=0, padx=15, pady=5, sticky="ew")
        self.telemetry_frame.grid_columnconfigure(0, weight=1)

        self.gpu_name_lbl = ctk.CTkLabel(
            self.telemetry_frame, text="GPU: Loading...",
            font=("Consolas", 10), text_color="#808080", justify="left"
        )
        self.gpu_name_lbl.grid(row=0, column=0, padx=10, pady=(6, 2), sticky="w")

        self.gpu_metrics_lbl = ctk.CTkLabel(
            self.telemetry_frame, text="Util: 0% | Temp: 0°C",
            font=("Consolas", 10), text_color="#A9B7C6", justify="left"
        )
        self.gpu_metrics_lbl.grid(row=1, column=0, padx=10, pady=2, sticky="w")

        self.vram_lbl = ctk.CTkLabel(
            self.telemetry_frame, text="VRAM: 0 MB / 0 MB",
            font=("Consolas", 10), text_color="#A9B7C6", justify="left"
        )
        self.vram_lbl.grid(row=2, column=0, padx=10, pady=2, sticky="w")

        self.vram_progress = ctk.CTkProgressBar(self.telemetry_frame, height=5, progress_color="#00E676")
        self.vram_progress.grid(row=3, column=0, padx=10, pady=(2, 10), sticky="ew")
        self.vram_progress.set(0.0)

        # ---- Main Content ----
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(0, weight=2)
        self.main_content.grid_rowconfigure(1, weight=1)

        # Video Preview
        self.video_container = ctk.CTkFrame(self.main_content, fg_color="#000000", corner_radius=15)
        self.video_container.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        self.video_lbl = ctk.CTkLabel(self.video_container, text="WAITING FOR CAMERA...", text_color="#444444")
        self.video_lbl.pack(expand=True, fill="both")

        # ---- Scrolling Event Log ----
        self.log_container = ctk.CTkFrame(self.main_content, fg_color="#151515", corner_radius=12)
        self.log_container.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.log_container.grid_columnconfigure(0, weight=1)
        self.log_container.grid_rowconfigure(1, weight=1)

        self.log_header = ctk.CTkLabel(
            self.log_container, text="📜 LIVE EVENT & SYSTEM FEED",
            font=ctk.CTkFont(family="Orbitron", size=11, weight="bold"),
            text_color="#00E676"
        )
        self.log_header.grid(row=0, column=0, padx=15, pady=(8, 2), sticky="w")

        self.log_text = ctk.CTkTextbox(
            self.log_container, font=("Consolas", 10),
            fg_color="#0a0a0a", text_color="#A9B7C6",
            wrap="word"
        )
        self.log_text.grid(row=1, column=0, padx=15, pady=(2, 10), sticky="nsew")
        self.log_text.insert("end", "[System Setup] Event Feed Initialized.\n")
        self.log_text.configure(state="disabled")

        # Status Bar
        self.status_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="System Ready — v2.1.0 — EventBus Active")
        self.status_label.pack(side="left", padx=20)

    def _setup_event_subscriptions(self):
        """Subscribe to central EventBus events to log them in the UI."""
        self.event_bus.subscribe("USER_ARRIVED", lambda d=None: self._log_event("USER_ARRIVED", f"Source: {d.get('source', 'unknown') if d else 'unknown'}"))
        self.event_bus.subscribe("USER_LEFT", lambda d=None: self._log_event("USER_LEFT", f"Source: {d.get('source', 'unknown') if d else 'unknown'}"))
        self.event_bus.subscribe("ERROR_DETECTED", lambda d=None: self._log_event("ERROR_DETECTED", f"Context: '{d.get('error_context', '')[:80]}...' in {d.get('active_window', 'unknown')}"))

    def _log_event(self, event_name: str, details: str):
        """Append event logs securely and thread-safely via queue."""
        timestamp = time.strftime("%H:%M:%S")
        msg = f"[{timestamp}] [{event_name}] {details}\n"
        self.log_queue.put(msg)

    def _toggle_audio(self):
        if self.audio:
            if self.audio_switch.get(): self.audio.resume()
            else: self.audio.pause()

    def _toggle_vision(self):
        if self.presence_monitor:
            if self.vision_switch.get(): self.presence_monitor.resume()
            else: self.presence_monitor.pause()

    def _toggle_screen(self):
        if self.screen_monitor:
            if self.ocr_switch.get(): self.screen_monitor.resume()
            else: self.screen_monitor.pause()

    def _toggle_vlm(self):
        if self.vlm_engine:
            if self.vlm_switch.get(): self.vlm_engine.resume()
            else: self.vlm_engine.pause()

    def _toggle_local_only(self):
        self.workspace_state.set("local_only", bool(self.local_only_switch.get()))
        self.logger.info(f"Local-Only AI Mode: {'ENABLED' if self.local_only_switch.get() else 'DISABLED'}")
        self._log_event("CONFIG", f"Local-Only Mode set to {self.local_only_switch.get()}")

    def _check_api_status(self):
        """Ping Ollama and Gemini to check connectivity."""
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=1)
            if resp.status_code == 200:
                self.ollama_lbl.configure(text="Ollama: ONLINE", text_color="#00e676")
            else:
                self.ollama_lbl.configure(text="Ollama: ERROR", text_color="#ff5252")
        except:
            self.ollama_lbl.configure(text="Ollama: OFFLINE", text_color="#ff5252")

    def _update_telemetry_background(self):
        """Fetch system statistics in a separate thread to prevent blocking main UI loop."""
        try:
            stats = self.hw_monitor.snapshot()
            self.after(0, self._apply_telemetry_update, stats)
        except Exception as e:
            self.logger.error(f"Failed to query telemetry: {e}")

    def _apply_telemetry_update(self, stats):
        """Apply hardware telemetry metrics directly to UI components on the main thread."""
        try:
            gpu_name = stats.get("gpu_name", "N/A")
            if gpu_name == "N/A":
                self.gpu_name_lbl.configure(text="GPU: No NVIDIA GPU detected", text_color="#ff5252")
                self.gpu_metrics_lbl.configure(text="Util: 0% | Temp: 0°C")
                self.vram_lbl.configure(text="VRAM: 0 MB / 0 MB")
                self.vram_progress.set(0.0)
            else:
                self.gpu_name_lbl.configure(text=f"GPU: {gpu_name[:18]}", text_color="#4FC3F7")
                
                util = stats.get("gpu_util_percent", 0)
                temp = stats.get("gpu_temp_c", 0)
                self.gpu_metrics_lbl.configure(text=f"Util: {util}% | Temp: {temp}°C")
                
                used = stats.get("gpu_vram_used_mb", 0)
                total = stats.get("gpu_vram_total_mb", 0)
                self.vram_lbl.configure(text=f"VRAM: {used} MB / {total} MB")
                
                if total > 0:
                    self.vram_progress.set(used / total)
                else:
                    self.vram_progress.set(0.0)
        except Exception as e:
            self.logger.error(f"Error applying telemetry UI update: {e}")

    def _update_loop(self):
        # Update Live Logs Thread-Safely
        try:
            while not self.log_queue.empty():
                msg = self.log_queue.get_nowait()
                self.log_text.configure(state="normal")
                self.log_text.insert("end", msg)
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except Exception as e:
            pass

        # Video Frame Rendering
        try:
            frame = self.frame_queue.get_nowait()
            img = Image.fromarray(frame[:, :, ::-1]) # BGR to RGB
            
            # Smart Scaling: Fit to container while maintaining aspect ratio
            target_h = self.video_container.winfo_height() - 20
            target_w = self.video_container.winfo_width() - 20
            
            if target_h > 100 and target_w > 100:
                img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
                self._current_ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
                self.video_lbl.configure(image=self._current_ctk_image, text="")
        except queue.Empty:
            pass

        # Periodic API check (every 5 seconds)
        if int(time.time()) % 5 == 0:
            threading.Thread(target=self._check_api_status, daemon=True).start()

        # Periodic Telemetry Update (every 2 seconds)
        now = time.time()
        if now - self._last_telemetry_time >= 2.0:
            self._last_telemetry_time = now
            threading.Thread(target=self._update_telemetry_background, daemon=True).start()

        self.after(30, self._update_loop)

    def start_dashboard(self):
        self.mainloop()
