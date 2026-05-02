"""
WakeBot: Unified System Automation via Audio and Vision Triggers.
"""

from wakebot.core.actions import WakeBotActions
from wakebot.core.config import load_config, WakeBotConfig
from wakebot.core.logger import WakeBotLogger

__version__ = "2.1.0"

__author__ = "WakeBot Contributors"

__all__ = [
    "WakeBotActions",
    "load_config",
    "WakeBotConfig",
    "WakeBotLogger"
]
