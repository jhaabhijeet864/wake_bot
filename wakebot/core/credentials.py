"""
WakeBot Credential Manager
3-tier credential resolution for secure API key management.

Resolution order:
  1. Windows Credential Manager (via keyring) — most secure
  2. .env file in project root (via python-dotenv) — developer-friendly
  3. Environment variable fallback — CI/container compatibility

Usage:
    from wakebot.core.credentials import get_credential, store_credential
    api_key = get_credential("GEMINI_API_KEY")
"""

import os
from typing import Optional
from wakebot.core.logger import WakeBotLogger

_logger = WakeBotLogger(quiet=True)

# Service namespace for Windows Credential Manager
_SERVICE_NAME = "WakeBot"


def _load_dotenv() -> None:
    """Load .env file from the project root if python-dotenv is available."""
    try:
        from dotenv import load_dotenv
        # Walk up from this file to find project root (contains wakebot_config.json)
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        env_path = os.path.join(project_root, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
    except ImportError:
        pass  # python-dotenv not installed; skip silently


def get_credential(key: str) -> Optional[str]:
    """
    Resolve a credential using the 3-tier fallback chain.

    Args:
        key: The credential name (e.g., "GEMINI_API_KEY")

    Returns:
        The credential value, or None if not found in any tier.
    """
    # Tier 1: Windows Credential Manager (keyring)
    try:
        import keyring
        value = keyring.get_password(_SERVICE_NAME, key)
        if value:
            _logger.info(f"Credential '{key}' resolved via Windows Credential Manager.")
            return value
    except ImportError:
        pass  # keyring not installed
    except Exception as e:
        _logger.warning(f"Keyring lookup failed for '{key}': {e}")

    # Tier 2: .env file
    _load_dotenv()

    # Tier 3: Environment variable (also catches .env values loaded above)
    value = os.environ.get(key)
    if value:
        _logger.info(f"Credential '{key}' resolved via environment variable.")
        return value

    _logger.warning(f"Credential '{key}' not found in any tier.")
    return None


def store_credential(key: str, value: str) -> bool:
    """
    Store a credential in the Windows Credential Manager.

    Args:
        key: The credential name (e.g., "GEMINI_API_KEY")
        value: The credential value

    Returns:
        True if stored successfully, False otherwise.
    """
    try:
        import keyring
        keyring.set_password(_SERVICE_NAME, key, value)
        _logger.info(f"Credential '{key}' stored in Windows Credential Manager.")
        return True
    except ImportError:
        _logger.error(
            "keyring is not installed. Install it with: pip install keyring"
        )
        return False
    except Exception as e:
        _logger.error(f"Failed to store credential '{key}': {e}")
        return False


def delete_credential(key: str) -> bool:
    """
    Delete a credential from the Windows Credential Manager.

    Args:
        key: The credential name to remove

    Returns:
        True if deleted successfully, False otherwise.
    """
    try:
        import keyring
        keyring.delete_password(_SERVICE_NAME, key)
        _logger.info(f"Credential '{key}' deleted from Windows Credential Manager.")
        return True
    except ImportError:
        _logger.error(
            "keyring is not installed. Install it with: pip install keyring"
        )
        return False
    except Exception as e:
        _logger.error(f"Failed to delete credential '{key}': {e}")
        return False
