import asyncio
from typing import Optional, Dict, Any
import httpx

class BaseAsyncClient:
    _shared_client: Optional[httpx.AsyncClient] = None

    def __init__(self, base_url: str = "", timeout: float = 10.0):
        self.base_url = base_url
        self.timeout = timeout

    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        if cls._shared_client is None or cls._shared_client.is_closed:
            cls._shared_client = httpx.AsyncClient(timeout=30.0, trust_env=False)
        return cls._shared_client

    async def get_with_backoff(
        self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, max_retries: int = 4
    ) -> httpx.Response:
        """
        Auto-backoff on 429: 1s -> 2s -> 4s -> 8s -> graceful fail
        """
        backoff_delays = [1, 2, 4, 8]
        client = await self.get_client()
        
        # Ensure url is absolute if base_url is set
        full_url = self.base_url + url if url.startswith("/") else url
        
        for attempt in range(max_retries + 1):
            response = await client.get(full_url, params=params, headers=headers)
            
            if response.status_code == 429:
                if attempt < max_retries:
                    delay = backoff_delays[attempt]
                    await asyncio.sleep(delay)
                    continue
                else:
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
