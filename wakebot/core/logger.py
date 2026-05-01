import sys
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for Windows
init()

class WakeBotLogger:
    """Centralized logger for WakeBot with color support."""
    
    def __init__(self, quiet=False):
        self.quiet = quiet

    def _log(self, level: str, color: str, message: str):
        if self.quiet and level == "INFO":
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Style.DIM}[{timestamp}]{Style.RESET_ALL} {color}{Style.BRIGHT}{level:7}{Style.RESET_ALL} | {message}")

    def info(self, message: str):
        self._log("INFO", Fore.CYAN, message)

    def warning(self, message: str):
        self._log("WARNING", Fore.YELLOW, message)

    def error(self, message: str):
        self._log("ERROR", Fore.RED, message)

    def action(self, message: str):
        self._log("ACTION", Fore.GREEN, message)

