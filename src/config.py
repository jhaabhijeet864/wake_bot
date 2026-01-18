"""
WakeBot Configuration Module
Centralized configuration with JSON file support
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class WakeBotConfig:
    """WakeBot configuration dataclass"""
    # Audio Settings
    chunk_size: int = 1024
    sample_rate: int = 44100
    channels: int = 1
    
    # Detection Settings
    threshold: int = 3000  # Calibrate this!
    cooldown_ms: int = 100
    double_clap_window_ms: int = 500
    triple_clap_window_ms: int = 700
    
    # Action Settings
    youtube_url: str = "https://www.youtube.com"
    wake_key: str = "shift"
    
    # Operational Settings
    start_active: bool = True
    log_rms_values: bool = False  # Enable for debugging
    
    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WakeBotConfig':
        """Create config from dictionary"""
        return cls(**data)


def load_config(config_path: str = "wakebot_config.json") -> WakeBotConfig:
    """
    Load configuration from JSON file or return defaults
    
    Args:
        config_path: Path to configuration JSON file
        
    Returns:
        WakeBotConfig instance
    """
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                return WakeBotConfig.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
            print("Using default configuration.")
            return WakeBotConfig()
    else:
        # Create default config file
        config = WakeBotConfig()
        save_config(config, config_path)
        return config


def save_config(config: WakeBotConfig, config_path: str = "wakebot_config.json"):
    """
    Save configuration to JSON file
    
    Args:
        config: WakeBotConfig instance
        config_path: Path to save configuration
    """
    try:
        with open(config_path, 'w') as f:
            json.dump(config.to_dict(), f, indent=4)
    except Exception as e:
        print(f"Warning: Could not save config to {config_path}: {e}")
