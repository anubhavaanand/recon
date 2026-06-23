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
async def test_epo_search_no_keys_falls_to_mock(monkeypatch):
    """When no EPO keys configured, fall through to mock data."""
    monkeypatch.setattr("clients.patent_apis.load_config", lambda: Config(epo_consumer_key=None, epo_consumer_secret=None))
    client = EPOClient()
    results = await client.search("quantum computing")
    assert len(results) > 0
    assert "EPMOCK" in results[0].id


@pytest.mark.asyncio
async def test_epo_search_valid_keys_uses_api(monkeypatch):
    """When valid EPO keys configured, use OPS API."""
    monkeypatch.setattr("clients.patent_apis.load_config", lambda: Config(epo_consumer_key="KEY", epo_consumer_secret="SECRET"))

    async def mock_token_post(self, url, data=None, headers=None):
        return httpx.Response(200, json={"access_token": "test_token", "expires_in": 3600})

    async def mock_ops_get(self, url, params=None, headers=None, max_retries=4):
        return httpx.Response(200, json={
            "ops:world-patent-data": {
                "ops:biblio-search": {
                    "ops:search-result": {
                        "exchange-documents": [{
                            "exchange-document": {
                                "@country": "EP",
                                "@doc-number": "12345678",
                                "@family-id": "F001",
                                "bibliographic-data": {
                                    "invention-title": [{"@lang": "en", "$": "Mock EPO API Patent"}],
                                    "abstract": [{"@lang": "en", "p": {"$": "Mock abstract from EPO API."}}],
                                    "parties": {
                                        "applicants": {
                                            "applicant": [{
                                                "applicant-name": {"name": {"$": "EPO Applicant GmbH"}}
                                            }]
                                        }
                                    },
                                    "publication-reference": {
                                        "document-id": [{"date": {"$": "20230615"}}]
                                    }
                                }
                            }
                        }]
                    }
                }
            }
        })

    monkeypatch.setattr(BaseAsyncClient, "get_with_backoff", mock_ops_get)
    monkeypatch.setattr("httpx.AsyncClient.post", mock_token_post)

    client = EPOClient()
    results = await client.search("quantum computing")
    assert len(results) == 1
    assert results[0].id == "EP12345678"
    assert results[0].title == "Mock EPO API Patent"


@pytest.mark.asyncio
async def test_epo_search_api_failure_falls_to_mock(monkeypatch):
    """When OPS API errors, fall through to mock data."""
    monkeypatch.setattr("clients.patent_apis.load_config", lambda: Config(epo_consumer_key="KEY", epo_consumer_secret="SECRET"))

    async def mock_token_post(self, url, data=None, headers=None):
        return httpx.Response(200, json={"access_token": "test_token", "expires_in": 3600})

    async def mock_ops_get(self, url, params=None, headers=None, max_retries=4):
        raise Exception("OPS API Rate Limited")

    monkeypatch.setattr(BaseAsyncClient, "get_with_backoff", mock_ops_get)
    monkeypatch.setattr("httpx.AsyncClient.post", mock_token_post)

    client = EPOClient()
    results = await client.search("quantum computing")
    assert len(results) > 0
    assert "EPMOCK" in results[0].id


@pytest.mark.asyncio
async def test_epo_validate_credentials_no_keys(monkeypatch):
    monkeypatch.setattr("clients.patent_apis.load_config", lambda: Config(epo_consumer_key=None, epo_consumer_secret=None))
    client = EPOClient()
    ok, msg = await client.validate_credentials()
    assert ok is False
    assert "Missing/invalid" in msg


@pytest.mark.asyncio
async def test_epo_validate_credentials_valid_keys(monkeypatch):
    monkeypatch.setattr("clients.patent_apis.load_config", lambda: Config(epo_consumer_key="KEY", epo_consumer_secret="SECRET"))

    async def mock_token_post(self, url, data=None, headers=None):
        return httpx.Response(200, json={"access_token": "test_token", "expires_in": 3600})

    monkeypatch.setattr("httpx.AsyncClient.post", mock_token_post)
    client = EPOClient()
    ok, msg = await client.validate_credentials()
    assert ok is True
    assert "VALID" in msg


@pytest.mark.asyncio
async def test_epo_validate_credentials_invalid_keys(monkeypatch):
    monkeypatch.setattr("clients.patent_apis.load_config", lambda: Config(epo_consumer_key="BAD", epo_consumer_secret="BAD"))

    async def mock_token_post(self, url, data=None, headers=None):
        return httpx.Response(401, json={"error": "invalid_client"})

    monkeypatch.setattr("httpx.AsyncClient.post", mock_token_post)
    client = EPOClient()
    ok, msg = await client.validate_credentials()
    assert ok is False
    assert "Missing/invalid" in msg


@pytest.mark.asyncio
async def test_wipo_search_returns_mock():
    """WIPO now returns mock data directly."""
    client = WIPOClient()
    results = await client.search("quantum computing")
    assert len(results) > 0
    assert "WO" in results[0].id


@pytest.mark.asyncio
async def test_lens_search_returns_mock():
    """Lens now returns mock data directly."""
    client = LensClient()
    results = await client.search("quantum computing")
    assert len(results) > 0
    assert "MOCK" in results[0].id


@pytest.mark.asyncio
async def test_google_patents_search_returns_mock():
    """GooglePatents now returns mock data directly."""
    client = GooglePatentsClient()
    results = await client.search("quantum computing")
    assert len(results) == 2


@pytest.mark.asyncio
async def test_lens_validate_credentials_no_keys_needed():
    client = LensClient()
    ok, msg = await client.validate_credentials()
    assert ok is True
    assert "mock data" in msg


@pytest.mark.asyncio
async def test_lens_fetch_citations_returns_empty():
    client = LensClient()
    result = await client.fetch_citations("US123")
    assert result == {"forward": [], "backward": []}
