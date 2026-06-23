"""Single AI interface module: embeddings (Ollama/nomic), LLM (NVIDIA NIM).

Zero-AI default — no endpoint is called without explicit user consent/toggle.
"""

from __future__ import annotations

import json
import math
import os
from typing import Optional

import httpx


NVIDIA_NIM_BASE = "https://api.nvcf.nvidia.com/v2/nvcf"

OLLAMA_BASE = "http://localhost:11434/api"
NOMIC_MODEL = "nomic-embed-text"
LOCAL_FALLBACK_MODEL = "qwen2.5:0.5b"


class AIProvider:
    """Single AI interface. Methods return None on unavailability — never raise."""

    def __init__(self, nvidia_nim_key: str | None = None):
        self.nvidia_nim_key = nvidia_nim_key

    # ── Embeddings (nomic-embed-text via Ollama) ────────────────────────

    @staticmethod
    def nomic_is_installed() -> bool:
        """Check if nomic-embed-text model is installed in Ollama."""
        try:
            import subprocess
            r = subprocess.run(
                ["ollama", "list"], capture_output=True, text=True, timeout=5
            )
            return NOMIC_MODEL in r.stdout
        except Exception:
            return False

    @staticmethod
    async def pull_nomic() -> bool:
        """Pull nomic-embed-text model via ollama pull. Returns True on success."""
        import asyncio
        proc = await asyncio.create_subprocess_exec(
            "ollama", "pull", NOMIC_MODEL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            rc = await asyncio.wait_for(proc.wait(), timeout=300)
            return rc == 0
        except asyncio.TimeoutError:
            proc.kill()
            return False

    async def generate_embedding(self, text: str) -> list[float] | None:
        """Generate embedding via nomic-embed-text. Returns None on failure."""
        if not text:
            return None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{OLLAMA_BASE}/embeddings",
                    json={"model": NOMIC_MODEL, "prompt": text[:8192]},
                )
                if resp.status_code == 200:
                    return resp.json().get("embedding")
                return None
        except Exception:
            return None

    # ── NVIDIA NIM (translation, summarization, synthesis) ──────────────

    def _nim_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.nvidia_nim_key}",
            "Content-Type": "application/json",
        }

    async def _nim_chat(self, prompt: str, model: str = "meta/llama3-70b-instruct") -> str | None:
        """Send a chat completion request to NVIDIA NIM. Returns None on failure."""
        if not self.nvidia_nim_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{NVIDIA_NIM_BASE}/chat/completions",
                    headers=self._nim_headers(),
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.0,
                        "max_tokens": 2048,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip()
                    )
                return None
        except Exception:
            return None

    async def translate(self, text: str, target_lang: str = "English") -> str | None:
        """Translate text via NVIDIA NIM. Returns None on failure."""
        if not self.nvidia_nim_key:
            print("ERR: Translation requires NVIDIA NIM API key. Run: recon config set --nim-key <KEY>")
            return None
        prompt = (
            f"Translate the following patent text to {target_lang}. "
            "Provide ONLY the translation, dry and technical:\n\n"
            f"{text}"
        )
        return await self._nim_chat(prompt)

    async def summarize(self, text: str) -> str | None:
        """Summarize patent text via NVIDIA NIM. Returns None on failure."""
        if not self.nvidia_nim_key:
            print("ERR: Summarization requires NVIDIA NIM API key. Run: recon config set --nim-key <KEY>")
            return None
        prompt = (
            "Summarize the following patent in 2-3 sentences. Dry, factual:\n\n"
            f"{text}"
        )
        return await self._nim_chat(prompt)

    async def synthesize(self, query: str, results_text: str) -> str | None:
        """Synthesize multiple patent results via NVIDIA NIM. Returns None."""
        if not self.nvidia_nim_key:
            print("ERR: Synthesis requires NVIDIA NIM API key. Run: recon config set --nim-key <KEY>")
            return None
        prompt = (
            f"Search query: {query}\n\n"
            f"Patent results:\n{results_text[:6000]}\n\n"
            "Synthesize key trends, major players, and technical white space. "
            "Dry, authoritative, no filler:"
        )
        return await self._nim_chat(prompt)

    # ── Local fallback (qwen2.5:0.5b via Ollama) ───────────────────────

    async def _local_chat(self, prompt: str) -> str | None:
        """Query local Ollama with qwen2.5:0.5b. Returns None on failure."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{OLLAMA_BASE}/generate",
                    json={
                        "model": LOCAL_FALLBACK_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.0},
                    },
                )
                if resp.status_code == 200:
                    return resp.json().get("response", "").strip()
                return None
        except Exception:
            return None


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
