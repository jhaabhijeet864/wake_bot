import sys
from datetime import datetime

class WakeBotLogger:
    """Centralized logger for WakeBot."""
    
    def __init__(self):
        pass

    def _log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def info(self, message: str):
        self._log("INFO", message)

    def warning(self, message: str):
        self._log("WARNING", message)

    def error(self, message: str):
        self._log("ERROR", message)

    def action(self, message: str):
        self._log("ACTION", message)
