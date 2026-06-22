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
    """Translate non-English text to target language via local Ollama.

    Returns translated text, or original text if translation is not needed
    or Ollama is unreachable. Never crashes — always returns a string.
    """
    if not text or text in ("[?]", "UNKNOWN"):
        return text

    # Skip if already translated (marked with [t] prefix)
    if text.startswith("[t]") or "\n\n[t]" in text:
        return text

    # Skip English text
    if not _is_non_english(text):
        return text

    # Check cache
    cached = _get_cached_translation(text)
    if cached:
        return f"[t]{cached}"

    ollama_url = "http://localhost:11434/api/generate"
    prompt = (
        f"Translate the following patent text to {target_language}. "
        "Provide ONLY the translation, with no conversational filler, no apologies. "
        "Maintain a dry, technical, factual voice.\n\n"
        f"Text:\n{text}"
    )

    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0},
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(ollama_url, json=payload)
            if response.status_code == 200:
                data = response.json()
                translated = data.get("response", "").strip()
                if translated:
                    _save_translation_cache(text, translated)
                    return f"[t]{translated}"

                return text

            if response.status_code == 404:
                return text

            return text

    except (httpx.ConnectError, httpx.TimeoutException):
        # Ollama not running — silently return original
        return text
    except Exception:
        return text
