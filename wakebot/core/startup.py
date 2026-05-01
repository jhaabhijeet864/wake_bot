"""
WakeBot Windows Startup Manager
Register/unregister WakeBot to start automatically with Windows.

Uses the HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run registry key.
This is a per-user, non-admin operation.
"""

import os
import sys
from wakebot.core.logger import WakeBotLogger

_logger = WakeBotLogger()
_REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_NAME = "WakeBot"


def _get_launch_command() -> str:
    """Build the command line that Windows will execute on startup."""
    # Use pythonw to avoid a console window
    python_exe = sys.executable
    pythonw = python_exe.replace("python.exe", "pythonw.exe")
    if os.path.exists(pythonw):
        python_exe = pythonw

    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return f'"{python_exe}" -m wakebot tray'


def register_startup() -> bool:
    """
    Register WakeBot to start automatically with Windows.

    Returns:
        True if registration succeeded, False otherwise.
    """
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REG_KEY_PATH,
            0,
            winreg.KEY_SET_VALUE,
        )
        command = _get_launch_command()
        winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
        _logger.info(f"WakeBot registered for Windows startup: {command}")
        return True
    except ImportError:
        _logger.error("winreg module not available (non-Windows platform).")
        return False
    except Exception as e:
        _logger.error(f"Failed to register startup: {e}")
        return False


def unregister_startup() -> bool:
    """
    Remove WakeBot from Windows startup.

    Returns:
        True if removal succeeded, False otherwise.
    """
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REG_KEY_PATH,
            0,
            winreg.KEY_SET_VALUE,
        )
        try:
            winreg.DeleteValue(key, _APP_NAME)
            _logger.info("WakeBot removed from Windows startup.")
        except FileNotFoundError:
            _logger.info("WakeBot was not registered for startup.")
        winreg.CloseKey(key)
        return True
    except ImportError:
        _logger.error("winreg module not available (non-Windows platform).")
        return False
    except Exception as e:
        _logger.error(f"Failed to unregister startup: {e}")
        return False


def is_registered() -> bool:
    """Check if WakeBot is currently registered for startup."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REG_KEY_PATH,
            0,
            winreg.KEY_READ,
        )
        try:
            winreg.QueryValueEx(key, _APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False
