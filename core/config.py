import os
import tomllib
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

CONFIG_PATH = Path.home() / ".config" / "recon" / "config.toml"

@dataclass
class Config:
    uspto_api_key: Optional[str] = None
    epo_consumer_key: Optional[str] = None
    epo_consumer_secret: Optional[str] = None
    lens_api_key: Optional[str] = None

def load_config() -> Config:
    """Load configuration from ~/.config/recon/config.toml"""
    if not CONFIG_PATH.exists():
        return Config()
    
    try:
        with open(CONFIG_PATH, "rb") as f:
            data = tomllib.load(f)
            return Config(
                uspto_api_key=data.get("uspto_api_key"),
                epo_consumer_key=data.get("epo_consumer_key"),
                epo_consumer_secret=data.get("epo_consumer_secret"),
                lens_api_key=data.get("lens_api_key")
            )
    except Exception:
        return Config()

def save_config(config: Config) -> None:
    """Save configuration to ~/.config/recon/config.toml"""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    lines = []
    if config.uspto_api_key:
        lines.append(f'uspto_api_key = "{config.uspto_api_key}"')
    if config.epo_consumer_key:
        lines.append(f'epo_consumer_key = "{config.epo_consumer_key}"')
    if config.epo_consumer_secret:
        lines.append(f'epo_consumer_secret = "{config.epo_consumer_secret}"')
    if config.lens_api_key:
        lines.append(f'lens_api_key = "{config.lens_api_key}"')
    
    with open(CONFIG_PATH, "w") as f:
        f.write("\n".join(lines))
