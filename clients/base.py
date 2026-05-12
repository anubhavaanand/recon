import asyncio
from typing import Optional, Dict, Any
import httpx

class BaseAsyncClient:
    def __init__(self, base_url: str = "", timeout: float = 10.0):
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

    async def get_with_backoff(
        self, url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 4
    ) -> httpx.Response:
        """
        Auto-backoff on 429: 1s -> 2s -> 4s -> 8s -> graceful fail
        """
        backoff_delays = [1, 2, 4, 8]
        
        for attempt in range(max_retries + 1):
            response = await self.client.get(url, params=params)
            
            if response.status_code == 429:
                if attempt < max_retries:
                    delay = backoff_delays[attempt]
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Graceful fail on max retries reached, 
                    # user's spec says: "1s -> 2s -> 4s -> 8s -> graceful fail"
                    # For now, return the 429 response so the caller can format an error
                    # or raise an exception as per the error voice rule.
                    break
            
            response.raise_for_status()
            return response
            
        return response

    async def aclose(self) -> None:
        """Close the async HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()
