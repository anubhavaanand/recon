import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from clients.base import BaseAsyncClient

@pytest.mark.asyncio
async def test_client_backoff():
    client = BaseAsyncClient()
    
    # Mock response
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    
    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    
    # Mock the shared client's get method
    mock_get = AsyncMock(side_effect=[mock_response_429, mock_response_200])
    
    with patch("httpx.AsyncClient.get", mock_get):
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            response = await client.get_with_backoff("http://test.com")
            
            assert response.status_code == 200
            assert mock_get.call_count == 2
            mock_sleep.assert_called_once_with(1)
