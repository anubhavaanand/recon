import pytest
from unittest.mock import AsyncMock
from core.search import search_all, ALL_SOURCES, SOURCE_REGISTRY, sort_and_merge_results
from core.models import PatentRecord


_MOCK_RECORD = PatentRecord(
    id="MOCK", title="T", assignee="X", dates={"filed": "2023-01-01"},
    abstract="", claims=[], image_urls=[], status="active", family_id="F",
)


def _make_client_stub(records):
    """Create a stub class whose instances return fixed records on search()."""
    class StubClient:
        async def search(self, query):
            return records
    return StubClient


def _patch_registry(monkeypatch, src_map: dict[str, list]):
    """Replace SOURCE_REGISTRY entries so selected srcs return given records."""
    import core.search as search_module

    patched = {}
    for src, (display, _) in SOURCE_REGISTRY.items():
        records = src_map.get(src, [])
        patched[src] = (display, _make_client_stub(records))
    monkeypatch.setattr(search_module, "SOURCE_REGISTRY", patched)


@pytest.mark.asyncio
async def test_search_all_default_uses_all_sources(monkeypatch):
    """When sources=None, all registered sources should be used."""
    src_map = {src: [] for src in ALL_SOURCES}
    src_map["uspto"] = [_MOCK_RECORD]
    _patch_registry(monkeypatch, src_map)
    result = await search_all("sf_default_sources_test")
    assert len(result) == 1


@pytest.mark.asyncio
async def test_search_all_filters_by_source(monkeypatch):
    """When sources list is provided, only those sources should be searched."""
    src_map = {}
    for src in ALL_SOURCES:
        src_map[src] = [_MOCK_RECORD] if src in ("uspto", "wipo", "patsnap") else []
    _patch_registry(monkeypatch, src_map)

    result = await search_all("sf_filter_test", sources=["uspto", "wipo", "patsnap"])
    assert len(result) == 3


@pytest.mark.asyncio
async def test_search_all_unknown_source_warns(monkeypatch):
    """Unknown source names should print a warning and be skipped."""
    src_map = {src: [_MOCK_RECORD] if src in ("uspto", "wipo") else [] for src in ALL_SOURCES}
    _patch_registry(monkeypatch, src_map)

    result = await search_all("sf_unknown_test", sources=["uspto", "bogus_source", "wipo"])
    assert len(result) == 2


@pytest.mark.asyncio
async def test_search_all_empty_source_list_returns_empty(monkeypatch):
    """Empty source list should return empty results."""
    _patch_registry(monkeypatch, {})
    result = await search_all("sf_empty_test", sources=[])
    assert result == []


@pytest.mark.asyncio
async def test_search_all_single_source(monkeypatch):
    """Searching with a single source should work."""
    src_map = {src: ([] if src != "patsnap" else [_MOCK_RECORD]) for src in ALL_SOURCES}
    _patch_registry(monkeypatch, src_map)

    result = await search_all("sf_single_test", sources=["patsnap"])
    assert len(result) == 1


@pytest.mark.asyncio
async def test_search_all_case_insensitive_sources(monkeypatch):
    """Source names should be case-insensitive."""
    src_map = {src: [_MOCK_RECORD] if src in ("uspto", "wipo") else [] for src in ALL_SOURCES}
    _patch_registry(monkeypatch, src_map)

    result = await search_all("sf_case_test", sources=["USPTO", "WIPO"])
    assert len(result) == 2


@pytest.mark.asyncio
async def test_search_all_cache_still_works(monkeypatch):
    """Cache should still be used regardless of source filter."""
    src_map = {"uspto": [_MOCK_RECORD]}
    for s in ALL_SOURCES:
        if s not in src_map:
            src_map[s] = []
    _patch_registry(monkeypatch, src_map)

    result = await search_all("source_filter_cache_test", sources=["uspto"])
    assert len(result) > 0
    ids = [r.id for r in result]
    assert "MOCK" in ids
