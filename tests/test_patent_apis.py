import pytest
from clients.patent_apis import USPTOClient, EPOClient, WIPOClient, LensClient, GooglePatentsClient
from core.models import PatentRecord

@pytest.mark.asyncio
async def test_uspto_search_mocked(monkeypatch):
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
