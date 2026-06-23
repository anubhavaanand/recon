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
    patsnap_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    terminal_detection_seen: bool = False
    terminal_protocol: str = "external"

def load_config() -> Config:
    """Load configuration from ~/.config/recon/config.toml."""
    cfg = Config()

    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "rb") as f:
                data = tomllib.load(f)
                cfg.uspto_api_key = data.get("uspto_api_key")
                cfg.epo_consumer_key = data.get("epo_consumer_key")
                cfg.epo_consumer_secret = data.get("epo_consumer_secret")
                cfg.lens_api_key = data.get("lens_api_key")
                cfg.patsnap_api_key = data.get("patsnap_api_key")
                cfg.deepseek_api_key = data.get("deepseek_api_key")
                cfg.terminal_detection_seen = data.get("terminal_detection_seen", False)
                cfg.terminal_protocol = data.get("terminal_protocol", "external")
        except tomllib.TOMLDecodeError:
            pass

    return cfg

def save_config(cfg: Config) -> None:
    """Save configuration to ~/.config/recon/config.toml."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    lines = []
    
    if cfg.uspto_api_key:
        lines.append(f'uspto_api_key = "{cfg.uspto_api_key}"')
    if cfg.epo_consumer_key:
        lines.append(f'epo_consumer_key = "{cfg.epo_consumer_key}"')
    if cfg.epo_consumer_secret:
        lines.append(f'epo_consumer_secret = "{cfg.epo_consumer_secret}"')
    if cfg.lens_api_key:
        lines.append(f'lens_api_key = "{cfg.lens_api_key}"')
    if cfg.patsnap_api_key:
        lines.append(f'patsnap_api_key = "{cfg.patsnap_api_key}"')
    if cfg.deepseek_api_key:
        lines.append(f'deepseek_api_key = "{cfg.deepseek_api_key}"')
        
    lines.append(f'terminal_detection_seen = {"true" if cfg.terminal_detection_seen else "false"}')
    lines.append(f'terminal_protocol = "{cfg.terminal_protocol}"')

    with open(CONFIG_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")
        
    os.chmod(CONFIG_PATH, 0o600)
