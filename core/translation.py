"""Non-English patent text translation via local Ollama.

Detects non-English text, translates via Ollama REST API, caches results
in SQLite. Gracefully degrades when Ollama is unavailable — logs a dry
ERR: and returns the original text.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path

import httpx


_CACHE_DB = "recon_cache.db"


def _is_non_english(text: str) -> bool:
    """Heuristic: return True if text contains significant non-ASCII content."""
    if not text or text in ("[?]", "UNKNOWN"):
        return False

    # Count characters in non-European Unicode blocks
    # CJK, Cyrillic, Arabic, Greek, etc. — anything beyond Latin-1 supplement
    non_european = sum(1 for c in text if ord(c) > 0x02AF)
    total = len(text.strip())
    if total == 0:
        return False
    return non_european > 0


def _cache_key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _get_cached_translation(text: str) -> str | None:
    """Return cached translation if available, else None."""
    key = _cache_key(text)
    try:
        with sqlite3.connect(_CACHE_DB) as conn:
            row = conn.execute(
                "SELECT translated_text FROM translation_cache WHERE source_hash = ?",
                (key,),
            ).fetchone()
            if row:
                return row[0]
    except Exception:
        pass
    return None


def _save_translation_cache(text: str, translated: str) -> None:
    key = _cache_key(text)
    try:
        with sqlite3.connect(_CACHE_DB) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO translation_cache (source_hash, source_text, translated_text) VALUES (?, ?, ?)",
                (key, text[:500], translated),
            )
            conn.commit()
    except Exception:
        pass


async def translate_text(text: str, target_language: str = "English") -> str:
    """Translate non-English text to target language via DeepSeek or local Ollama.

    Tries DeepSeek API if DEEPSEEK_API_KEY is configured; falls back to local
    Ollama (llama3). Returns translated text with [t] prefix, or original text
    if translation is not needed or all engines are unreachable.
    Never crashes — always returns a string.
    """
    if not text or text in ("[?]", "UNKNOWN"):
        return text

    if text.startswith("[t]") or "\n\n[t]" in text:
        return text

    if not _is_non_english(text):
        return text

    cached = _get_cached_translation(text)
    if cached:
        return f"[t]{cached}"

    prompt = (
        f"Translate the following patent text to {target_language}. "
        "Provide ONLY the translation, with no conversational filler, no apologies. "
        "Maintain a dry, technical, factual voice.\n\n"
        f"Text:\n{text}"
    )

    from core.config import load_config
    cfg = load_config()
    if cfg.deepseek_api_key:
        translated = await _translate_via_deepseek(text, prompt, cfg.deepseek_api_key)
        if translated is not None:
            return f"[t]{translated}"

    translated = await _translate_via_ollama(text, prompt)
    if translated is not None:
        return f"[t]{translated}"

    return text


async def _translate_via_deepseek(text: str, prompt: str, api_key: str) -> str | None:
    """Translate via DeepSeek API (deepseek-chat). Returns None on failure."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.0,
                    "stream": False,
                },
            )
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if content:
                    _save_translation_cache(text, content)
                    return content
            return None
    except Exception:
        return None


async def _translate_via_ollama(text: str, prompt: str) -> str | None:
    """Translate via local Ollama (llama3). Returns None on failure."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0},
                },
            )
            if response.status_code == 200:
                data = response.json()
                translated = data.get("response", "").strip()
                if translated:
                    _save_translation_cache(text, translated)
                    return translated
            return None
    except Exception:
        return None
