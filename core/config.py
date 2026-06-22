import os
import tomllib
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

CONFIG_PATH = Path.home() / ".config" / "recon" / "config.toml"
ENV_PATH = Path.cwd() / ".env"
PROJECT_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_env_file(path: Path) -> dict[str, str]:
    env = {}
    if path.exists():
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip().strip("\"'")
    return env


@dataclass
class Config:
    uspto_api_key: Optional[str] = None
    epo_consumer_key: Optional[str] = None
    epo_consumer_secret: Optional[str] = None
    lens_api_key: Optional[str] = None
    patsnap_api_key: Optional[str] = None
    terminal_detection_seen: bool = False
    terminal_protocol: str = "external"

def load_config() -> Config:
    """Load configuration from ~/.config/recon/config.toml, fallback to .env."""
    env_vars = {}
    env_vars = load_env_file(ENV_PATH)
    if not env_vars:
        env_vars = load_env_file(PROJECT_ENV_PATH)

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
                cfg.terminal_detection_seen = data.get("terminal_detection_seen", False)
                cfg.terminal_protocol = data.get("terminal_protocol", "external")
        except Exception:
            pass

    if not cfg.patsnap_api_key:
        cfg.patsnap_api_key = env_vars.get("PATSNAP_API_KEY") or os.environ.get("PATSNAP_API_KEY")
    if not cfg.uspto_api_key:
        cfg.uspto_api_key = env_vars.get("USPTO_API_KEY") or os.environ.get("USPTO_API_KEY")

    return cfg

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
    if config.patsnap_api_key:
        lines.append(f'patsnap_api_key = "{config.patsnap_api_key}"')
    lines.append(f'terminal_detection_seen = {"true" if config.terminal_detection_seen else "false"}')
    lines.append(f'terminal_protocol = "{config.terminal_protocol}"')
    
    with open(CONFIG_PATH, "w") as f:
        f.write("\n".join(lines))
    
    # Restrict permissions: 600 (Owner Read/Write only)
    os.chmod(CONFIG_PATH, 0o600)
