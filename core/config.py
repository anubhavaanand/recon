import os
import tomllib
import base64
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

CONFIG_PATH = Path.home() / ".config" / "recon" / "config.toml"
ENV_PATH = Path.cwd() / ".env"
PROJECT_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
_KEY_PATH = Path.home() / ".cache" / "recon" / ".key"

_ENCRYPTED_PREFIX = "enc:"


def _get_or_create_key() -> bytes:
    """Load or generate a 32-byte AES-256 key stored at ~/.cache/recon/.key."""
    _KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if _KEY_PATH.exists():
        return _KEY_PATH.read_bytes()
    key = os.urandom(32)
    _KEY_PATH.write_bytes(key)
    os.chmod(_KEY_PATH, 0o600)
    return key


def _encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext string with AES-256-GCM. Returns base64."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = _get_or_create_key()
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return _ENCRYPTED_PREFIX + base64.b64encode(nonce + ciphertext).decode()


def _decrypt_value(ciphertext: str) -> str:
    """Decrypt a value previously encrypted with _encrypt_value."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    if not ciphertext.startswith(_ENCRYPTED_PREFIX):
        return ciphertext
    raw = base64.b64decode(ciphertext[len(_ENCRYPTED_PREFIX):])
    nonce, ct = raw[:12], raw[12:]
    key = _get_or_create_key()
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode("utf-8")


def _decrypt_optional(value: Optional[str]) -> Optional[str]:
    """Decrypt a string if present and encrypted, else return None."""
    if not value:
        return None
    return _decrypt_value(value)


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
    deepseek_api_key: Optional[str] = None
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
                cfg.uspto_api_key = _decrypt_optional(data.get("uspto_api_key"))
                cfg.epo_consumer_key = _decrypt_optional(data.get("epo_consumer_key"))
                cfg.epo_consumer_secret = _decrypt_optional(data.get("epo_consumer_secret"))
                cfg.lens_api_key = _decrypt_optional(data.get("lens_api_key"))
                cfg.patsnap_api_key = _decrypt_optional(data.get("patsnap_api_key"))
                cfg.deepseek_api_key = _decrypt_optional(data.get("deepseek_api_key"))
                cfg.terminal_detection_seen = data.get("terminal_detection_seen", False)
                cfg.terminal_protocol = data.get("terminal_protocol", "external")
        except Exception:
            pass

    if not cfg.patsnap_api_key:
        cfg.patsnap_api_key = env_vars.get("PATSNAP_API_KEY") or os.environ.get("PATSNAP_API_KEY")
    if not cfg.uspto_api_key:
        cfg.uspto_api_key = env_vars.get("USPTO_API_KEY") or os.environ.get("USPTO_API_KEY")
    if not cfg.deepseek_api_key:
        cfg.deepseek_api_key = env_vars.get("DEEPSEEK_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")

    return cfg

def save_config(config: Config) -> None:
    """Save configuration to ~/.config/recon/config.toml"""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    if config.uspto_api_key:
        lines.append(f'uspto_api_key = "{_encrypt_value(config.uspto_api_key)}"')
    if config.epo_consumer_key:
        lines.append(f'epo_consumer_key = "{_encrypt_value(config.epo_consumer_key)}"')
    if config.epo_consumer_secret:
        lines.append(f'epo_consumer_secret = "{_encrypt_value(config.epo_consumer_secret)}"')
    if config.lens_api_key:
        lines.append(f'lens_api_key = "{_encrypt_value(config.lens_api_key)}"')
    if config.patsnap_api_key:
        lines.append(f'patsnap_api_key = "{_encrypt_value(config.patsnap_api_key)}"')
    if config.deepseek_api_key:
        lines.append(f'deepseek_api_key = "{_encrypt_value(config.deepseek_api_key)}"')
    lines.append(f'terminal_detection_seen = {"true" if config.terminal_detection_seen else "false"}')
    lines.append(f'terminal_protocol = "{config.terminal_protocol}"')

    with open(CONFIG_PATH, "w") as f:
        f.write("\n".join(lines))

    os.chmod(CONFIG_PATH, 0o600)
