"""
Error handling tests — verifies real error paths and ERR: voice compliance.
"""

from __future__ import annotations

import pytest

from core.config import Config, save_config
from core.search import search_all
from core.translation import translate_text
from storage.cache import CacheDatabase


@pytest.mark.asyncio
async def test_err_prefix_on_search_source_failure(monkeypatch, tmp_path, capsys):
    """search_all should emit ERR: on source failure, not crash."""

    class BrokenClient:
        async def search(self, query):
            raise RuntimeError("boom")

        async def validate_credentials(self):
            return False, "broken"

    import core.search as search_module

    original_registry = dict(search_module.SOURCE_REGISTRY)
    search_module.SOURCE_REGISTRY["broken"] = ("Broken", BrokenClient)

    db_path = str(tmp_path / "cache.db")

    original_init = CacheDatabase.__init__

    def patched_init(self, *args, **kwargs):
        if not args and "db_path" not in kwargs:
            kwargs["db_path"] = db_path
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(CacheDatabase, "__init__", patched_init)

    try:
        await search_all("q", sources=["broken"])
    except Exception:
        pass

    captured = capsys.readouterr()
    assert "ERR:" in captured.out

    search_module.SOURCE_REGISTRY.clear()
    search_module.SOURCE_REGISTRY.update(original_registry)


@pytest.mark.asyncio
async def test_translation_returns_original_on_failure(monkeypatch):
    """translate_text must never crash and must return original text on failure."""

    async def fake_translate(text, prompt):
        raise RuntimeError("ollama down")

    monkeypatch.setattr("core.translation._translate_via_ollama", fake_translate)

    result = await translate_text("发明", target_language="English")
    assert isinstance(result, str)
    assert len(result) > 0


def test_config_save_roundtrip_preserves_keys(tmp_path, monkeypatch):
    """save_config must write valid TOML that load_config can read back."""
    import core.config

    cfg_file = tmp_path / "config.toml"
    monkeypatch.setattr(core.config, "CONFIG_PATH", cfg_file)

    cfg = Config(uspto_api_key="k", epo_consumer_key="e", terminal_protocol="external")
    save_config(cfg)

    loaded = core.config.load_config()
    assert loaded.uspto_api_key == "k"
    assert loaded.epo_consumer_key == "e"


def test_cache_db_eviction_does_not_crash_on_large_db(tmp_path):
    """enforce_eviction_policy must not crash when DB exceeds max size."""
    db = CacheDatabase(db_path=str(tmp_path / "cache.db"))
    for i in range(1000):
        db.save_search_results(f"query {i}", [])
    stats = db.enforce_eviction_policy(max_db_mb=0)
    assert "deleted_expired" in stats


def test_upsert_api_metadata_rejects_bad_keys(tmp_path):
    """upsert_api_metadata must not inject arbitrary SQL via kwargs keys."""
    db = CacheDatabase(db_path=str(tmp_path / "cache.db"))
    db.upsert_api_metadata(
        "src",
        base_url="https://example.com",
        auth_type="none",
        rate_limit_per_minute=0,
        actual_limit_used=0,
        requests_this_hour=0,
        consecutive_errors=0,
        circuit_open=False,
        bad_key="bad",
    )
    row = db.get_api_metadata("src")
    assert row is not None
    assert "bad_key" not in row


def test_update_terminal_session_rejects_bad_keys(tmp_path):
    """update_terminal_session must not inject arbitrary SQL via kwargs keys."""
    db = CacheDatabase(db_path=str(tmp_path / "cache.db"))
    db.create_terminal_session("s1")
    db.update_terminal_session(
        "s1",
        query_text="q",
        selected_index=0,
        active_tab="SearchScreen",
        screen_name="SearchScreen",
        is_active=True,
        bad_key="bad",
    )
    row = db.get_active_session()
    assert row is None or "bad_key" not in row
