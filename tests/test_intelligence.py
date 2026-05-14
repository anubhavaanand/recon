import pytest
import httpx
from clients.intelligence import IntelligenceClient, gather_intelligence
from core.models import CrossReference

@pytest.mark.asyncio
async def test_intelligence_client_mocked(monkeypatch):
    async def mock_post(self, url, json=None, headers=None):
        if "reporter.nih.gov" in url:
            return httpx.Response(200, json={
                "results": [
                    {"project_num": "123", "project_title": "NIH Mock"}
                ]
            })
        return httpx.Response(404)
        
    async def mock_get(self, url, params=None, headers=None):
        if "/works" in url:
            return httpx.Response(200, json={
                "results": [{"id": "W123", "title": "OpenAlex Mock"}]
            })
        elif "/institutions" in url:
            return httpx.Response(200, json={
                "results": [{"id": "I123"}]
            })
        return httpx.Response(404)

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
        async def post(self, url, json=None, headers=None):
            return await mock_post(self, url, json, headers)
        async def get(self, url, params=None, headers=None):
            return await mock_get(self, url, params, headers)

    monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)

    signals = await gather_intelligence("Test Entity")
    assert isinstance(signals, list)
    assert len(signals) == 2
    sources = [s.source for s in signals]
    assert "NIH" in sources
    assert "OpenAlex" in sources
    assert signals[0].url == "https://reporter.nih.gov/search/search/project-details/123"
    assert signals[1].url == "W123"
