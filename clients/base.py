import asyncio
import time
from typing import Any, Dict, Optional

import httpx


class TokenBucket:
    """Proactive rate limiter with 24% headroom.

    Maintains exactly 76% of documented rate limit to stay under
    provider thresholds.
    """

    def __init__(self, rate_per_minute: int):
        self.max_tokens = int(rate_per_minute * 0.76)
        self.tokens = float(self.max_tokens)
        self.period = 60.0
        self.last_refill = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self) -> float:
        """Wait for a token and return the current utilization ratio (0.0-1.0)."""
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(
                self.max_tokens,
                self.tokens + elapsed * (self.max_tokens / self.period),
            )
            self.last_refill = now

            if self.tokens < 1:
                wait = (1 - self.tokens) * (self.period / self.max_tokens)
                await asyncio.sleep(wait)
                self.tokens = 0.0

            self.tokens -= 1.0
            return 1.0 - (self.tokens / self.max_tokens) if self.max_tokens > 0 else 0.0


class BaseAsyncClient:
    _shared_client: Optional[httpx.AsyncClient] = None

    def __init__(self, base_url: str = "", timeout: float = 10.0, respect_retry_after: bool = True):
        self.base_url = base_url
        self.timeout = timeout
        self.respect_retry_after = respect_retry_after

    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        if cls._shared_client is None or cls._shared_client.is_closed:
            cls._shared_client = httpx.AsyncClient(timeout=30.0, trust_env=False)
        return cls._shared_client

    async def get_with_backoff(
        self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, max_retries: int = 4
    ) -> httpx.Response:
        """
        Auto-backoff on 429/503/504, unless respect_retry_after is False.

        When respect_retry_after=False (default for scrapers), HTTP 429
        immediately raises httpx.HTTPStatusError (fail fast).
        """
        client = await self.get_client()

        full_url = self.base_url + url if url.startswith("/") else url

        if not self.respect_retry_after:
            response = await client.get(full_url, params=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response

        backoff_delays = [1, 2, 4, 8]
        for attempt in range(max_retries + 1):
            response = await client.get(full_url, params=params, headers=headers, timeout=self.timeout)

            if response.status_code in (429, 503, 504):
                if attempt < max_retries:
                    delay = backoff_delays[attempt]
                    print(f"ERR: API rate limited ({response.status_code}). Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    continue
                break

            response.raise_for_status()
            return response

        return response


    async def aclose(self) -> None:
        """Close the shared async HTTP client."""
        if self._shared_client:
            await self._shared_client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # We don't close the shared client on __aexit__ to keep it alive for others
        pass
