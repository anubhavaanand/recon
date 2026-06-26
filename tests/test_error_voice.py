import builtins

import httpx
import pytest

from clients.patent_apis import USPTOClient
from core.config import Config


@pytest.mark.asyncio
async def test_uspto_error_voice(monkeypatch):
    monkeypatch.setattr("clients.patent_apis.load_config", lambda: Config(uspto_api_key="TEST"))

    async def mock_get(*args, **kwargs):
        raise httpx.TimeoutException("Timeout")

    monkeypatch.setattr("clients.base.BaseAsyncClient.get_with_backoff", mock_get)
    async def mock_sleep(x): pass
    monkeypatch.setattr("asyncio.sleep", mock_sleep)

    client = USPTOClient()

    # Capture print output
    printed_output = []
    def mock_print(*args, **kwargs):
        printed_output.append(" ".join(map(str, args)))

    monkeypatch.setattr(builtins, "print", mock_print)

    results = await client.search("test")
    assert len(results) == 0
    assert len(printed_output) > 0
    assert printed_output[0].startswith("ERR: ")
    assert "Oops" not in printed_output[0]
    assert "Sorry" not in printed_output[0]
    assert "Please" not in printed_output[0]

@pytest.mark.asyncio
async def test_uspto_validation_error_voice(monkeypatch):
    monkeypatch.setattr("clients.patent_apis.load_config", lambda: Config(uspto_api_key="TEST"))

    async def mock_get(*args, **kwargs):
        return httpx.Response(401)

    class MockClient:
        async def get(self, *args, **kwargs):
            return await mock_get(*args, **kwargs)

    async def mock_get_client(self):
        return MockClient()

    monkeypatch.setattr(USPTOClient, "get_client", mock_get_client)

    client = USPTOClient()
    ok, msg = await client.validate_credentials()
    assert not ok
    assert msg.startswith("ERR: ")
