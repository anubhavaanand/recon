import base64
import os
import platform
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

CONFIG_PATH = Path.home() / ".config" / "recon" / "config.toml"
_CACHE_DIR = Path.home() / ".cache" / "recon"
_SALT_PATH = _CACHE_DIR / ".config_salt"
_ENCRYPTION_PREFIX = "enc:AES256GCM:"


class ConfigEncryption:
    """AES-256-GCM encryption for API keys at rest.

    Key derived from machine fingerprint via PBKDF2-HMAC-SHA256 + random salt.
    Uses AES-256-GCM (nonce 12 bytes prepended to ciphertext).
    """

    def _get_salt(self) -> bytes:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        if _SALT_PATH.exists():
            return _SALT_PATH.read_bytes()
        salt = os.urandom(16)
        _SALT_PATH.write_bytes(salt)
        return salt

    def _derive_key(self) -> bytes:
        try:
            login = os.getlogin()
        except OSError:
            login = os.environ.get("USER", "recon")
        fingerprint = f"{os.uname().nodename}:{login}:{platform.machine()}"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._get_salt(),
            iterations=100000,
        )
        return kdf.derive(fingerprint.encode())

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return plaintext
        key = self._derive_key()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
        combined = base64.b64encode(nonce + ct).decode()
        return f"{_ENCRYPTION_PREFIX}{combined}"

    def decrypt(self, ciphertext: str) -> str | None:
        if not ciphertext:
            return ciphertext
        if not ciphertext.startswith(_ENCRYPTION_PREFIX):
            return ciphertext
        key = self._derive_key()
        aesgcm = AESGCM(key)
        token = ciphertext.replace(_ENCRYPTION_PREFIX, "")
        try:
            combined = base64.b64decode(token)
            nonce = combined[:12]
            ct = combined[12:]
            return aesgcm.decrypt(nonce, ct, None).decode()
        except Exception:
            return None

@dataclass
class Config:
    uspto_api_key: Optional[str] = None
    epo_consumer_key: Optional[str] = None
    epo_consumer_secret: Optional[str] = None
    lens_api_key: Optional[str] = None
    patsnap_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    nvidia_nim_api_key: Optional[str] = None
    nomic_consent_given: bool = False
    semantic_search_enabled: bool = False
    ai_translation_enabled: bool = False
    terminal_detection_seen: bool = False
    terminal_protocol: str = "external"

def load_config() -> Config:
    """Load configuration from ~/.config/recon/config.toml."""
    cfg = Config()
    crypto = ConfigEncryption()

    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "rb") as f:
                data = tomllib.load(f)
                raw_uspto = data.get("uspto_api_key", "")
                cfg.uspto_api_key = crypto.decrypt(raw_uspto) if raw_uspto else None
                raw_epo_key = data.get("epo_consumer_key", "")
                cfg.epo_consumer_key = crypto.decrypt(raw_epo_key) if raw_epo_key else None
                raw_epo_secret = data.get("epo_consumer_secret", "")
                cfg.epo_consumer_secret = crypto.decrypt(raw_epo_secret) if raw_epo_secret else None
                raw_lens = data.get("lens_api_key", "")
                cfg.lens_api_key = crypto.decrypt(raw_lens) if raw_lens else None
                raw_patsnap = data.get("patsnap_api_key", "")
                cfg.patsnap_api_key = crypto.decrypt(raw_patsnap) if raw_patsnap else None
                raw_deepseek = data.get("deepseek_api_key", "")
                cfg.deepseek_api_key = crypto.decrypt(raw_deepseek) if raw_deepseek else None
                raw_nim = data.get("nvidia_nim_api_key", "")
                cfg.nvidia_nim_api_key = crypto.decrypt(raw_nim) if raw_nim else None
                cfg.nomic_consent_given = data.get("nomic_consent_given", False)
                cfg.semantic_search_enabled = data.get("semantic_search_enabled", False)
                cfg.ai_translation_enabled = data.get("ai_translation_enabled", False)
                cfg.terminal_detection_seen = data.get("terminal_detection_seen", False)
                cfg.terminal_protocol = data.get("terminal_protocol", "external")
        except tomllib.TOMLDecodeError:
            pass

    return cfg

def save_config(cfg: Config) -> None:
    """Save configuration to ~/.config/recon/config.toml."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    crypto = ConfigEncryption()

    lines = []

    if cfg.uspto_api_key:
        lines.append(f'uspto_api_key = "{crypto.encrypt(cfg.uspto_api_key)}"')
    if cfg.epo_consumer_key:
        lines.append(f'epo_consumer_key = "{crypto.encrypt(cfg.epo_consumer_key)}"')
    if cfg.epo_consumer_secret:
        lines.append(f'epo_consumer_secret = "{crypto.encrypt(cfg.epo_consumer_secret)}"')
    if cfg.lens_api_key:
        lines.append(f'lens_api_key = "{crypto.encrypt(cfg.lens_api_key)}"')
    if cfg.patsnap_api_key:
        lines.append(f'patsnap_api_key = "{crypto.encrypt(cfg.patsnap_api_key)}"')
    if cfg.deepseek_api_key:
        lines.append(f'deepseek_api_key = "{crypto.encrypt(cfg.deepseek_api_key)}"')
    if cfg.nvidia_nim_api_key:
        lines.append(f'nvidia_nim_api_key = "{crypto.encrypt(cfg.nvidia_nim_api_key)}"')

    lines.append(f'nomic_consent_given = {"true" if cfg.nomic_consent_given else "false"}')
    lines.append(f'semantic_search_enabled = {"true" if cfg.semantic_search_enabled else "false"}')
    lines.append(f'ai_translation_enabled = {"true" if cfg.ai_translation_enabled else "false"}')
    lines.append(f'terminal_detection_seen = {"true" if cfg.terminal_detection_seen else "false"}')
    lines.append(f'terminal_protocol = "{cfg.terminal_protocol}"')

    with open(CONFIG_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")

    os.chmod(CONFIG_PATH, 0o600)
