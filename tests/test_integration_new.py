import pytest
import os
from pathlib import Path
from core.config import Config, save_config, load_config
from core.search import search_all
from storage.cache import CacheDatabase

@pytest.mark.anyio
async def test_search_all_with_mocked_clients(monkeypatch, tmp_path):
    # Setup mock config
    mock_config_dir = tmp_path / ".config" / "recon"
    mock_config_dir.mkdir(parents=True)
    mock_config_file = mock_config_dir / "config.toml"
    
    # Use monkeypatch to redirect CONFIG_PATH in core.config
    import core.config
    monkeypatch.setattr(core.config, "CONFIG_PATH", mock_config_file)
    
    config = Config(uspto_api_key="TEST_KEY")
    save_config(config)
    
    # Setup mock cache
    db_path = tmp_path / "recon_cache.db"
    monkeypatch.setattr("storage.cache.Path", lambda x: Path(db_path) if x == "recon_cache.db" else Path(x))
    
    # For now, we expect live APIs to fail or return empty if they can't connect,
    # but we want to verify the orchestration.
    
    # Mock USPTOClient.get_with_backoff to avoid real network calls
    from clients.base import BaseAsyncClient
    import httpx

    async def mock_get(self, url, params=None, headers=None, **kwargs):
        return httpx.Response(200, json={"response": {"docs": [{"patentNumber": "US123", "inventionTitle": "Mock USPTO"}]}})

    monkeypatch.setattr(BaseAsyncClient, "get_with_backoff", mock_get)

    
    results = await search_all("quantum")
    
    assert len(results) >= 1
    assert any(r.id == "US123" for r in results)
    
    # Check if results were cached
    db = CacheDatabase(db_path=str(db_path))
    cached = db.get_cached_search("quantum")
    assert cached is not None
    assert any(r.id == "US123" for r in cached)

def test_config_roundtrip(tmp_path, monkeypatch):
    mock_config_file = tmp_path / "config.toml"
    import core.config
    monkeypatch.setattr(core.config, "CONFIG_PATH", mock_config_file)
    
    config = Config(uspto_api_key="KEY123", epo_consumer_key="EPO123")
    save_config(config)
    
    loaded = load_config()
    assert loaded.uspto_api_key == "KEY123"
    assert loaded.epo_consumer_key == "EPO123"
    assert loaded.epo_consumer_secret is None
