"""Shared BaseScraper with resilience mechanisms.

Rotating User-Agents, randomized delays, DDG concurrency cap (Semaphore 2),
per-source circuit breakers, and shared httpx.AsyncClient.
"""

from __future__ import annotations

import asyncio
import random
from contextlib import asynccontextmanager
from typing import Optional

import httpx


ROTATING_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (X11; Linux i686; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 OPR/111.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 OPR/111.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Samsung SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]


class RateLimitedError(Exception):
    """Raised when a scraper source returns a rate-limit response (429)."""


class SourceDisabledError(Exception):
    """Raised when a source has been disabled by the circuit breaker."""


_shared_client: Optional[httpx.AsyncClient] = None


async def _get_client() -> httpx.AsyncClient:
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
    return _shared_client


class BaseScraper:
    """Shared scraper base with resilience mechanisms.

    All scraper clients in clients/scrapers.py should either use this
    class's methods or inherit from it.
    """

    _ddg_semaphore = None

    @classmethod
    def get_ddg_semaphore(cls) -> asyncio.Semaphore:
        if cls._ddg_semaphore is None:
            cls._ddg_semaphore = asyncio.Semaphore(2)
        return cls._ddg_semaphore

    def __init__(self, source_name: str = "generic"):
        self.source_name = source_name
        self._failure_count = 0
        self._disabled = False

    async def _rate_limited_request(
        self, url: str, *, source: str = "", is_ddg: bool = False
    ) -> httpx.Response:
        """Make a rate-limited HTTP GET with rotating UA, jitter, and CB."""
        if self._disabled:
            raise SourceDisabledError(f"{source or self.source_name} is circuit-broken")

        await asyncio.sleep(random.uniform(1.0, 3.0))

        client = await _get_client()
        headers = {
            "User-Agent": random.choice(ROTATING_USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        if is_ddg:
            async with self.get_ddg_semaphore():
                response = await client.get(url, headers=headers, follow_redirects=True)
        else:
            response = await client.get(url, headers=headers, follow_redirects=True)

        if response.status_code == 429:
            self._failure_count += 1
            if self._failure_count >= 3:
                self._disabled = True
            raise RateLimitedError(f"{source or self.source_name} returned 429")

        self._failure_count = 0
        response.raise_for_status()
        return response

    async def fetch_html(
        self, url: str, *, timeout: float = 15.0, is_ddg: bool = False
    ) -> Optional[str]:
        """Fetch HTML with resilience. Returns None on failure."""
        try:
            resp = await self._rate_limited_request(url, source=self.source_name, is_ddg=is_ddg)
            return resp.text
        except (RateLimitedError, SourceDisabledError, httpx.HTTPError):
            return None

    def reset_circuit_breaker(self) -> None:
        """Reset the per-source circuit breaker (e.g., on new search)."""
        self._failure_count = 0
        self._disabled = False
