"""
WakeBot Dashboard — Principal Architect Version
A high-performance, dark-themed UI for real-time monitoring and control.
Optimized for HighDPI displays and system resource tracking.
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
        logger=None,
    ):
        super().__init__()

        self.workspace_state = workspace_state
        self.frame_queue = frame_queue
        
        # Subsystem instances for direct control
        self.presence_monitor = presence_monitor
        self.screen_monitor = screen_monitor
        self.vlm_engine = vlm_engine
        
        self.logger = logger or WakeBotLogger()

        # Window Setup
        self.title("WakeBot Control Center — Big Bot v2.0")
        self.geometry("1100x750")
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

    def _build_sidebar(self):
        """Create the left control panel."""
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1) # Spacer
        
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, text="WAKEBOT", font=ctk.CTkFont(size=24, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 5))

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar_frame, text="Principal Architect", font=ctk.CTkFont(size=12, slant="italic"), text_color="gray"
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 30))

        # --- Controls ---
        self.vision_switch = ctk.CTkSwitch(
            self.sidebar_frame, text="Presence Engine", command=self._toggle_vision
        )
        self.vision_switch.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.vision_switch.select()

        self.ocr_switch = ctk.CTkSwitch(
            self.sidebar_frame, text="Screen Monitor", command=self._toggle_screen
        )
        self.ocr_switch.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        self.ocr_switch.select()

        self.vlm_switch = ctk.CTkSwitch(
            self.sidebar_frame, text="AI Multi-Modal", command=self._toggle_vlm
        )
        self.vlm_switch.grid(row=4, column=0, padx=20, pady=10, sticky="w")
        self.vlm_switch.select()

        # --- Resource Metrics ---
        self.res_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.res_frame.grid(row=5, column=0, padx=20, pady=(30, 10), sticky="ew")
        
        self.cpu_lbl = ctk.CTkLabel(self.res_frame, text="CPU: 0%", font=ctk.CTkFont(size=11))
        self.cpu_lbl.grid(row=0, column=0, sticky="w")
        
        self.ram_lbl = ctk.CTkLabel(self.res_frame, text="RAM: 0%", font=ctk.CTkFont(size=11))
        self.ram_lbl.grid(row=1, column=0, sticky="w")

        # --- System Status Box ---
        self.info_box = ctk.CTkTextbox(self.sidebar_frame, width=180, height=180, font=ctk.CTkFont(size=11))
        self.info_box.grid(row=6, column=0, padx=20, pady=10, sticky="nsew")
        self.info_box.insert("0.0", "LOGS & ENGINE STATUS\n" + "-"*20 + "\n")
        self.info_box.configure(state="disabled")

    def _build_main_view(self):
        """Create the central visualization area."""
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Video Preview Container
        self.video_container = ctk.CTkFrame(self.main_frame, fg_color="#0a0a0a", corner_radius=10)
        self.video_container.grid(row=0, column=0, sticky="nsew")
        
        self.video_label = ctk.CTkLabel(self.video_container, text="[ FEED PAUSED ]", text_color="#333333", font=ctk.CTkFont(size=20, weight="bold"))
        self.video_label.pack(expand=True, fill="both")

        # Live Metrics Panel
        self.metrics_frame = ctk.CTkFrame(self.main_frame, height=120)
        self.metrics_frame.grid(row=1, column=0, pady=(20, 0), sticky="ew")
        self.metrics_frame.grid_columnconfigure((0,1,2), weight=1)
        
        self.presence_lbl = ctk.CTkLabel(self.metrics_frame, text="Presence: AWAY", font=ctk.CTkFont(size=15, weight="bold"))
        self.presence_lbl.grid(row=0, column=0, padx=20, pady=25)

        self.window_lbl = ctk.CTkLabel(self.metrics_frame, text="Focused: Desktop", font=ctk.CTkFont(size=13))
        self.window_lbl.grid(row=0, column=1, padx=20, pady=25)

        self.vlm_status_lbl = ctk.CTkLabel(self.metrics_frame, text="Ollama: Offline", font=ctk.CTkFont(size=13), text_color="#FF5252")
        self.vlm_status_lbl.grid(row=0, column=2, padx=20, pady=25)

    def _build_status_bar(self):
        """Create the bottom status bar."""
        self.status_bar = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_bar.grid(row=1, column=1, sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready — System Online", font=ctk.CTkFont(size=11))
        self.status_label.pack(side="left", padx=20)

    # --- Callbacks ---
    def _toggle_vision(self):
        active = self.vision_switch.get()
        if self.presence_monitor:
            if active: self.presence_monitor.resume()
            else: self.presence_monitor.pause()
        self.status_label.configure(text=f"Presence Engine {'Resumed' if active else 'Paused'}")

    def _toggle_screen(self):
        active = self.ocr_switch.get()
        if self.screen_monitor:
            if active: self.screen_monitor.resume()
            else: self.screen_monitor.pause()
        self.status_label.configure(text=f"Screen Monitor {'Resumed' if active else 'Paused'}")

    def _toggle_vlm(self):
        active = self.vlm_switch.get()
        if self.vlm_engine:
            if active: self.vlm_engine.resume()
            else: self.vlm_engine.pause()
        self.status_label.configure(text=f"VLM Engine {'Resumed' if active else 'Paused'}")

    # --- Update Loops ---
    def _check_ollama(self):
        """Verify Ollama availability."""
        def task():
            try:
                import requests
                resp = requests.get("http://localhost:11434/api/tags", timeout=2)
                if resp.status_code == 200:
                    self._ollama_status = "Ollama: Online (LLaVA)"
                    self.vlm_status_lbl.configure(text=self._ollama_status, text_color="#00C853")
                else:
                    self._ollama_status = "Ollama: Error"
                    self.vlm_status_lbl.configure(text=self._ollama_status, text_color="#FFD740")
            except:
                self._ollama_status = "Ollama: Offline"
                self.vlm_status_lbl.configure(text=self._ollama_status, text_color="#FF5252")
        
        threading.Thread(target=task, daemon=True).start()
        self.after(30000, self._check_ollama) # Check every 30s

    def _update_ui(self):
        """Fetch latest data from WorkspaceState and System."""
        state = self.workspace_state.snapshot()
        
        # Update Presence
        presence_text = "Presence: AT DESK" if state.get("user_present") else "Presence: AWAY"
        color = "#00C853" if state.get("user_present") else "#FF5252"
        self.presence_lbl.configure(text=presence_text, text_color=color)

        # Update Window
        window = state.get("active_window", "Desktop")
        if len(window) > 40: window = window[:37] + "..."
        self.window_lbl.configure(text=f"Focused: {window}")

        # Update System Metrics
        if psutil:
            self.cpu_lbl.configure(text=f"CPU: {psutil.cpu_percent()}%")
            self.ram_lbl.configure(text=f"RAM: {psutil.virtual_memory().percent}%")

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
                
                # Use CTkImage for proper scaling
                self._current_ctk_image = ctk.CTkImage(
                    light_image=pil_img,
                    dark_image=pil_img,
                    size=(760, 500) # Match your container size
                )
                self.video_label.configure(image=self._current_ctk_image, text="")
            elif not self.vision_switch.get():
                self.video_label.configure(image=None, text="[ FEED PAUSED ]")
                
        except Exception:
            pass

        self.after(50, self._update_feed) # ~20 FPS preview

    def start_dashboard(self):
        self.mainloop()
