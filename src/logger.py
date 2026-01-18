"""
WakeBot Logger Module
Provides colored terminal output using colorama
"""

from colorama import init, Fore, Style
from datetime import datetime

# Initialize colorama for Windows compatibility
init(autoreset=True)


class WakeBotLogger:
    """Colored terminal logger for WakeBot"""
    
    @staticmethod
    def info(message: str):
        """Log informational message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Fore.CYAN}[{timestamp}] INFO: {message}{Style.RESET_ALL}")
    
    @staticmethod
    def clap_detected(clap_type: str, rms_value: float):
        """Log detected clap pattern"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Fore.GREEN}[{timestamp}] CLAP: {clap_type} (RMS: {rms_value:.0f}){Style.RESET_ALL}")
    
    @staticmethod
    def action(action_name: str):
        """Log action execution"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Fore.YELLOW}[{timestamp}] ACTION: {action_name}{Style.RESET_ALL}")
    
    @staticmethod
    def error(message: str):
        """Log error message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Fore.RED}[{timestamp}] ERROR: {message}{Style.RESET_ALL}")
    
    @staticmethod
    def status(is_active: bool):
        """Log bot status"""
        status = "ACTIVE" if is_active else "PAUSED (Safe Mode)"
        color = Fore.GREEN if is_active else Fore.RED
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] STATUS: WakeBot is {status}{Style.RESET_ALL}")
    
    @staticmethod
    def calibration(rms_value: float, min_rms: float, max_rms: float, avg_rms: float):
        """Log calibration data"""
        print(f"{Fore.MAGENTA}RMS: {rms_value:.0f} | Min: {min_rms:.0f} | Max: {max_rms:.0f} | Avg: {avg_rms:.0f}{Style.RESET_ALL}", end='\r')
