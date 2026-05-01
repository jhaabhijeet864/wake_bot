"""
WakeBot Configuration Module
Unified configuration management for all WakeBot components.
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional, List, Tuple


@dataclass
class WakeBotConfig:
    """WakeBot configuration dataclass"""
    # Audio Settings
    chunk_size: int = 1024
    sample_rate: int = 44100
    channels: int = 1
    
    # Detection Settings (Clap)
    clap_enabled: bool = True
    threshold: int = 3000
    cooldown_ms: int = 100
    double_clap_window_ms: int = 500
    triple_clap_window_ms: int = 700
    
    # Voice Settings
    voice_enabled: bool = True
    wake_phrases: List[str] = ("wake up", "daddy's home", "wake up daddy's home")
    voice_confidence: float = 0.5
    model_path: str = "model"
    
    # Vision Settings
    vision_enabled: bool = False
    camera_index: int = 0
    vision_fps: float = 5.0
    absence_threshold: float = 120.0
    screen_interval: float = 10.0
    vlm_provider: str = "ollama"
    vlm_interval: float = 60.0
    
    # Privacy Settings
    privacy_mode: bool = False
    sensitive_apps: tuple = ("keepass", "1password", "bitwarden", "lastpass")
    local_only: bool = False
    
    # Action Settings
    youtube_url: str = "https://www.youtube.com"
    wake_key: str = "shift"
    open_lock_screen: bool = True
    
    # Operational Settings
    start_active: bool = True
    log_rms_values: bool = False
    action_cooldown_s: float = 5.0
    
    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WakeBotConfig':
        """Create config from dictionary"""
        # Handle tuple/list conversion if necessary
        if "wake_phrases" in data and isinstance(data["wake_phrases"], list):
            data["wake_phrases"] = tuple(data["wake_phrases"])
        if "sensitive_apps" in data and isinstance(data["sensitive_apps"], list):
            data["sensitive_apps"] = tuple(data["sensitive_apps"])
        
        # Filter for only valid dataclass fields
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        
        return cls(**filtered_data)


def load_config(config_path: str = "wakebot_config.json") -> WakeBotConfig:
    """
    Load configuration from JSON file or return defaults.
    """
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                return WakeBotConfig.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
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
    Save configuration to JSON file.
    """
    try:
        with open(config_path, 'w') as f:
            json.dump(config.to_dict(), f, indent=4)
    except Exception as e:
        print(f"Warning: Could not save config to {config_path}: {e}")
