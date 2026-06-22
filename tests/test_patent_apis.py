import pytest
import httpx
from clients.patent_apis import USPTOClient, EPOClient, WIPOClient, LensClient, GooglePatentsClient, PatsnapClient
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
async def test_epo_search_falls_back_to_mock(monkeypatch):
    async def mock_search_epo(*args, **kwargs):
        return []

    monkeypatch.setattr("clients.scrapers.search_epo_patents", mock_search_epo)
    client = EPOClient()
    results = await client.search("quantum computing")
    assert len(results) > 0
    assert "MOCK" in results[0].id


@pytest.mark.asyncio
async def test_wipo_search_mocked(monkeypatch):
    async def mock_search(*args, **kwargs):
        return []

    monkeypatch.setattr("clients.scrapers.search_wipo_patents", mock_search)
    client = WIPOClient()
    results = await client.search("quantum computing")
    assert len(results) > 0


@pytest.mark.asyncio
async def test_lens_search_falls_back_to_mock(monkeypatch):
    async def mock_search_lens(*args, **kwargs):
        return []

    monkeypatch.setattr("clients.scrapers.search_lens_patents", mock_search_lens)
    client = LensClient()
    results = await client.search("quantum computing")
    assert len(results) > 0
    assert "MOCK" in results[0].id


@pytest.mark.asyncio
async def test_google_patents_search_falls_back_to_mock(monkeypatch):
    async def mock_search(*args, **kwargs):
        return []

    monkeypatch.setattr("clients.scrapers.search_google_patents", mock_search)
    client = GooglePatentsClient()
    results = await client.search("quantum computing")
    assert len(results) == 2


@pytest.mark.asyncio
async def test_epo_validate_credentials_no_keys_needed():
    client = EPOClient()
    ok, msg = await client.validate_credentials()
    assert ok is True
    assert "scraper" in msg


@pytest.mark.asyncio
async def test_lens_validate_credentials_no_keys_needed():
    client = LensClient()
    ok, msg = await client.validate_credentials()
    assert ok is True
    assert "scraper" in msg


@pytest.mark.asyncio
async def test_lens_fetch_citations_returns_empty():
    client = LensClient()
    result = await client.fetch_citations("US123")
    assert result == {"forward": [], "backward": []}
