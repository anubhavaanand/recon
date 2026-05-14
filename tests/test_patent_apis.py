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
    monkeypatch.setattr("clients.patent_apis.load_config", lambda: Config(epo_consumer_key="K", epo_consumer_secret="S"))
    
    async def mock_get_token(*args, **kwargs):
        return "mock_token"
    monkeypatch.setattr(EPOClient, "_get_access_token", mock_get_token)
    
    async def mock_get(self, url, params=None, headers=None, max_retries=4):
        return httpx.Response(200, json={
            "ops:world-patent-data": {
                "ops:biblio-search": {
                    "ops:search-result": {
                        "exchange-documents": [{
                            "exchange-document": {
                                "@country": "EP",
                                "@doc-number": "123",
                                "bibliographic-data": {
                                    "invention-title": {"@lang": "en", "$": "Mock EPO"}
                                }
                            }
                        }]
                    }
                }
            }
        })
    monkeypatch.setattr(BaseAsyncClient, "get_with_backoff", mock_get)
    
    client = EPOClient()
    results = await client.search("quantum computing")
    assert len(results) > 0
    assert results[0].id == "EP123"

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
    monkeypatch.setattr("clients.patent_apis.load_config", lambda: Config(lens_api_key="TEST_LENS"))
    
    async def mock_post(self, url, json=None, headers=None, max_retries=4):
        return httpx.Response(200, json={
            "data": [{
                "lens_id": "LENS-123",
                "biblio": {"title": "Mock Lens"}
            }]
        })
        
    class MockClient:
        async def post(self, url, json=None, headers=None):
            return await mock_post(self, url, json, headers)
            
    async def mock_get_client(self):
        return MockClient()
        
    monkeypatch.setattr(LensClient, "get_client", mock_get_client)
    
    client = LensClient()
    results = await client.search("quantum computing")
    assert len(results) > 0
    assert results[0].id == "LENS-123"

@pytest.mark.asyncio
async def test_google_patents_search_mocked(monkeypatch):
    client = GooglePatentsClient()
    results = await client.search("quantum computing")
    assert len(results) == 0

