import pytest
import httpx
from clients.patent_apis import USPTOClient, EPOClient, WIPOClient, LensClient, GooglePatentsClient
from clients.base import BaseAsyncClient
from core.models import PatentRecord
from core.config import Config

@pytest.mark.asyncio
async def test_uspto_search_mocked(monkeypatch):
    monkeypatch.setattr("clients.patent_apis.load_config", lambda: Config(uspto_api_key="TEST"))
    
    async def mock_get(self, url, params=None, headers=None, max_retries=4):
        return httpx.Response(200, json={"response": {"docs": [{"patentNumber": "US123", "inventionTitle": "Mock USPTO", "applicantName": "Assignee", "filingDate": "2020-01-01", "abstractText": ["Mock abstract"], "applicationStatusCategory": "active"}]}})
    
    monkeypatch.setattr(BaseAsyncClient, "get_with_backoff", mock_get)
    async def mock_sleep(x):
        pass
    monkeypatch.setattr("asyncio.sleep", mock_sleep)

    client = USPTOClient()
    results = await client.search("quantum computing")
    assert isinstance(results, list)
    assert len(results) > 0
    assert isinstance(results[0], PatentRecord)

@pytest.mark.asyncio
async def test_epo_search_mocked(monkeypatch):
    client = EPOClient()
    results = await client.search("quantum computing")
    assert len(results) > 0

@pytest.mark.asyncio
async def test_wipo_search_mocked(monkeypatch):
    async def mock_get(self, url, params=None, headers=None, max_retries=4):
        return httpx.Response(200)
    monkeypatch.setattr(BaseAsyncClient, "get_with_backoff", mock_get)
    async def mock_sleep(x):
        pass
    monkeypatch.setattr("asyncio.sleep", mock_sleep)
    
    client = WIPOClient()
    results = await client.search("quantum computing")
    assert len(results) > 0

@pytest.mark.asyncio
async def test_lens_search_mocked(monkeypatch):
    client = LensClient()
    results = await client.search("quantum computing")
    assert len(results) > 0

@pytest.mark.asyncio
async def test_google_patents_search_mocked(monkeypatch):
    client = GooglePatentsClient()
    results = await client.search("quantum computing")
    assert len(results) > 0

