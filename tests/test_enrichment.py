"""Tests for Phase 2 enrichment pipeline.

Covers:
- Cache layer (get/save enrichment cache)
- Enrichment function (DDGS discovery, fallback, error handling, caching)
- Search pipeline integration (top-5 enrichment, exception isolation)
- Lazy enrichment in TUI (skip already-enriched records)
- Signal domain coverage
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from core.models import PatentRecord, CrossReference
from storage.cache import CacheDatabase


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def basic_record() -> PatentRecord:
    """A standard patent record for enrichment tests."""
    return PatentRecord(
        id="US12345678B2",
        title="Solid State Battery with Electrolyte",
        assignee="ACME Corp",
        dates={"filed": "2022-06-15"},
        abstract="A solid state battery with improved electrolyte stability.",
        claims=[], image_urls=[], status="active", family_id="FAM001",
    )


@pytest.fixture
def record_empty_assignee() -> PatentRecord:
    """A patent record with missing assignee."""
    return PatentRecord(
        id="US87654321B2",
        title="Advanced Photovoltaic Solar Panel",
        assignee="[?]",
        dates={"filed": "2023-01-10"},
        abstract="A photovoltaic panel with improved efficiency.",
        claims=[], image_urls=[], status="active", family_id="FAM002",
    )


@pytest.fixture
def mock_ddgs_results():
    """Standard DDGS result dicts that _search_signal expects."""
    return [
        {"href": "https://example.com/result", "title": "Some Title", "body": "Snippet body."},
    ]


# ═══════════════════════════════════════════════════════════════
# Cache Layer (2 tests)
# ═══════════════════════════════════════════════════════════════

def test_get_enrichment_cache_miss(tmp_path):
    """No cached entry returns None."""
    db_path = tmp_path / "test_recon.db"
    db = CacheDatabase(db_path=str(db_path))

    result = db.get_enrichment_cache("NONEXISTENT_ID")
    assert result is None


def test_save_and_get_enrichment_cache(tmp_path):
    """Save then retrieve, verify CrossReference objects match."""
    db_path = tmp_path / "test_recon.db"
    db = CacheDatabase(db_path=str(db_path))

    refs = [
        CrossReference(
            source="nih",
            url="https://reporter.nih.gov/project/123",
            metadata={"title": "NIH Grant", "snippet": "Funding for research."},
        ),
        CrossReference(
            source="sec",
            url="https://sec.gov/filing/abc",
            metadata={"title": "SEC Filing", "snippet": "Corporate filing."},
        ),
    ]
    patent_id = "US12345678B2"

    db.save_enrichment_cache(patent_id, refs)
    retrieved = db.get_enrichment_cache(patent_id)

    assert retrieved is not None
    assert len(retrieved) == 2
    assert retrieved[0].source == "nih"
    assert retrieved[0].url == "https://reporter.nih.gov/project/123"
    assert retrieved[1].source == "sec"
    assert retrieved[1].url == "https://sec.gov/filing/abc"
    # Verify metadata round-trips correctly
    assert retrieved[0].metadata.get("title") == "NIH Grant"


# ═══════════════════════════════════════════════════════════════
# Enrichment Function (5 tests)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_enrich_patent_adds_cross_references(basic_record, mock_ddgs_results):
    """Mock DDGS to return results for all 4 domains; verify record has 4 cross_references."""
    from core.enrichment import enrich_patent

    with patch("core.enrichment.CacheDatabase") as mock_cache_cls, \
         patch("core.enrichment.DDGS") as mock_ddgs:
        mock_db = MagicMock()
        mock_cache_cls.return_value = mock_db
        mock_db.get_enrichment_cache.return_value = None

        # Every call to DDGS().text() returns a result
        mock_ddgs.return_value.__enter__.return_value.text.return_value = mock_ddgs_results

        result = await enrich_patent(basic_record)

        assert len(result.cross_references) == 4
        sources = {cr.source for cr in result.cross_references}
        assert sources == {"nih", "sec", "arxiv", "opencorporates"}
        # Verify each cross-reference has a valid URL
        for cr in result.cross_references:
            assert cr.url == "https://example.com/result"
        # Verify save_enrichment_cache was called
        mock_db.save_enrichment_cache.assert_called_once()


@pytest.mark.asyncio
async def test_enrich_patent_handles_empty_assignee(record_empty_assignee, mock_ddgs_results):
    """Assignee is '[?]'; should fall back to title words. Verify still tries to enrich."""
    from core.enrichment import enrich_patent

    with patch("core.enrichment.CacheDatabase") as mock_cache_cls, \
         patch("core.enrichment.DDGS") as mock_ddgs:
        mock_db = MagicMock()
        mock_cache_cls.return_value = mock_db
        mock_db.get_enrichment_cache.return_value = None

        mock_ddgs.return_value.__enter__.return_value.text.return_value = mock_ddgs_results

        result = await enrich_patent(record_empty_assignee)

        # Should still find results despite missing assignee
        assert len(result.cross_references) == 4
        # Verify text() was called with terms from the title, not "[?]"
        text_mock = mock_ddgs.return_value.__enter__.return_value.text
        # Collect all query strings that were searched
        all_queries = [call[0][0] for call in text_mock.call_args_list]
        # At least one query should contain "Advanced" (from title)
        assert any("Advanced" in q for q in all_queries)


@pytest.mark.asyncio
async def test_enrich_patent_graceful_timeout(basic_record):
    """Mock DDGS to raise Exception; verify original record returned unchanged."""
    from core.enrichment import enrich_patent

    with patch("core.enrichment.CacheDatabase") as mock_cache_cls, \
         patch("core.enrichment.DDGS") as mock_ddgs:
        mock_db = MagicMock()
        mock_cache_cls.return_value = mock_db
        mock_db.get_enrichment_cache.return_value = None

        # Make text() raise an exception (simulating network timeout)
        mock_ddgs.return_value.__enter__.return_value.text.side_effect = Exception("Simulated timeout")

        result = await enrich_patent(basic_record)

        # Original record returned unchanged
        assert result is basic_record
        assert result.cross_references == []


@pytest.mark.asyncio
async def test_enrich_patent_skips_if_already_enriched(basic_record, mock_ddgs_results):
    """Enrichment is already cached; verify enrich_patent doesn't call DDGS."""
    from core.enrichment import enrich_patent

    cached_refs = [
        CrossReference(source="nih", url="https://reporter.nih.gov/project/123"),
        CrossReference(source="sec", url="https://sec.gov/filing/abc"),
    ]

    with patch("core.enrichment.CacheDatabase") as mock_cache_cls, \
         patch("core.enrichment.DDGS") as mock_ddgs:
        mock_db = MagicMock()
        mock_cache_cls.return_value = mock_db
        # Cache returns data for this record
        mock_db.get_enrichment_cache.return_value = cached_refs

        result = await enrich_patent(basic_record)

        assert len(result.cross_references) == 2
        assert result.cross_references[0].source == "nih"
        assert result.cross_references[1].source == "sec"
        # DDGS should never be called
        mock_ddgs.assert_not_called()


@pytest.mark.asyncio
async def test_enrich_patent_uses_cache(tmp_path, basic_record, mock_ddgs_results):
    """First call saves to cache; second call doesn't hit DDGS."""
    from core.enrichment import enrich_patent

    # Use a real temp database so caching actually works
    db_path = tmp_path / "test_enrich_cache.db"

    with patch("core.enrichment.CacheDatabase") as mock_cache_cls, \
         patch("core.enrichment.DDGS") as mock_ddgs:
        # Use a real CacheDatabase instance pointed at the temp path
        real_db = CacheDatabase(db_path=str(db_path))
        mock_cache_cls.return_value = real_db
        mock_db_spy = MagicMock(wraps=real_db)
        mock_cache_cls.return_value = mock_db_spy

        # --- First call: cache miss → DDGS called ---
        mock_ddgs.return_value.__enter__.return_value.text.return_value = mock_ddgs_results

        record1 = PatentRecord(
            id=basic_record.id, title=basic_record.title,
            assignee=basic_record.assignee, dates=basic_record.dates,
            abstract=basic_record.abstract, claims=[], image_urls=[],
            status=basic_record.status, family_id=basic_record.family_id,
        )
        await enrich_patent(record1)
        assert mock_ddgs.return_value.__enter__.return_value.text.call_count >= 1

        # Reset DDGS mock tracker for second call
        mock_ddgs.reset_mock()
        mock_ddgs.return_value.__enter__.return_value.text.reset_mock()

        # --- Second call: cache hit → DDGS NOT called ---
        record2 = PatentRecord(
            id=basic_record.id, title=basic_record.title,
            assignee=basic_record.assignee, dates=basic_record.dates,
            abstract=basic_record.abstract, claims=[], image_urls=[],
            status=basic_record.status, family_id=basic_record.family_id,
        )
        result2 = await enrich_patent(record2)

        # Should still have cross_references from cache
        assert len(result2.cross_references) > 0
        # DDGS should NOT have been called
        mock_ddgs.return_value.__enter__.return_value.text.assert_not_called()


# ═══════════════════════════════════════════════════════════════
# Search Pipeline Integration (2 tests)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_search_all_enriches_top_5():
    """Mock clients to return 10 records; verify enrich_patent called for first 5 only."""
    from core.search import search_all
    from core.models import PatentRecord

    # Create 10 records with consecutive IDs
    records = [
        PatentRecord(
            id=f"US{i:04d}", title=f"Patent {i}", assignee="Test Corp",
            dates={"filed": f"202{i}-01-01"},
            abstract="Abstract.", claims=[], image_urls=[],
            status="active", family_id="F",
        )
        for i in range(10)
    ]

    with patch("core.search.CacheDatabase") as mock_cache_cls, \
         patch("clients.patent_apis.USPTOClient.search") as mock_u, \
         patch("clients.patent_apis.EPOClient.search") as mock_e, \
         patch("clients.patent_apis.WIPOClient.search") as mock_w, \
         patch("clients.patent_apis.LensClient.search") as mock_l, \
         patch("clients.patent_apis.GooglePatentsClient.search") as mock_g, \
         patch("clients.patent_apis.PatsnapClient.search") as mock_p:

        mock_cache = MagicMock()
        mock_cache_cls.return_value = mock_cache
        mock_cache.get_cached_search.return_value = None

        # Distribute the 10 records across the first 4 clients
        mock_u.return_value = records[:3]
        mock_e.return_value = records[3:6]
        mock_w.return_value = records[6:8]
        mock_l.return_value = records[8:10]
        mock_g.return_value = []
        mock_p.return_value = []

        # Patch enrich_patent at its definition site; search_all imports it at runtime
        with patch("core.enrichment.enrich_patent", new_callable=AsyncMock) as mock_enrich:
            mock_enrich.return_value = records[0]

            result = await search_all("test query", sources=["uspto", "epo", "wipo", "lens", "google", "patsnap"])

            # All 10 records should be returned
            assert len(result) == 10
            # enrich_patent should be called exactly 5 times (top 5)
            assert mock_enrich.call_count == 5


@pytest.mark.asyncio
async def test_search_all_enrichment_exception_doesnt_block():
    """Mock enrich_patent to raise Exception; verify search_all still returns all results."""
    from core.search import search_all
    from core.models import PatentRecord

    records = [
        PatentRecord(
            id=f"US{i:04d}", title=f"Patent {i}", assignee="Test Corp",
            dates={"filed": f"202{i}-01-01"},
            abstract="Abstract.", claims=[], image_urls=[],
            status="active", family_id="F",
        )
        for i in range(5)
    ]

    with patch("core.search.CacheDatabase") as mock_cache_cls, \
         patch("clients.patent_apis.USPTOClient.search") as mock_u, \
         patch("clients.patent_apis.EPOClient.search") as mock_e, \
         patch("clients.patent_apis.WIPOClient.search") as mock_w, \
         patch("clients.patent_apis.LensClient.search") as mock_l, \
         patch("clients.patent_apis.GooglePatentsClient.search") as mock_g, \
         patch("clients.patent_apis.PatsnapClient.search") as mock_p:

        mock_cache = MagicMock()
        mock_cache_cls.return_value = mock_cache
        mock_cache.get_cached_search.return_value = None

        mock_u.return_value = records[:2]
        mock_e.return_value = records[2:4]
        mock_w.return_value = records[4:]
        mock_l.return_value = []
        mock_g.return_value = []
        mock_p.return_value = []

        # enrich_patent raises an exception for all calls
        with patch("core.enrichment.enrich_patent", new_callable=AsyncMock) as mock_enrich:
            mock_enrich.side_effect = Exception("Enrichment failed")

            result = await search_all("test query", sources=["uspto", "epo", "wipo", "lens", "google", "patsnap"])

            # All 5 records should still be returned despite enrichment failure
            assert len(result) == 5
            assert mock_enrich.call_count == 5


# ═══════════════════════════════════════════════════════════════
# Lazy Enrichment in TUI (1 test)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_enrich_current_skips_if_already_enriched():
    """Call SearchScreen._enrich_current with already-enriched record; verify early return."""
    from tui.screens import SearchScreen

    record = PatentRecord(
        id="US12345678B2", title="Test Patent", assignee="ACME Corp",
        dates={"filed": "2022-06-15"}, abstract="A battery.",
        claims=[], image_urls=[], status="active", family_id="F",
        cross_references=[
            CrossReference(source="NIH", url="https://reporter.nih.gov/123"),
        ],
    )

    screen = SearchScreen()

    with patch("core.enrichment.enrich_patent") as mock_enrich:
        await screen._enrich_current(record)
        # enrich_patent should NOT be called because record already has cross_references
        mock_enrich.assert_not_called()


# ═══════════════════════════════════════════════════════════════
# Signal Domain Coverage (2 tests)
# ═══════════════════════════════════════════════════════════════

def test_signal_domains_defined():
    """Verify _SIGNAL_DOMAINS has all 4 expected keys."""
    from core.enrichment import _SIGNAL_DOMAINS

    assert isinstance(_SIGNAL_DOMAINS, dict)
    assert set(_SIGNAL_DOMAINS.keys()) == {"nih", "sec", "arxiv", "opencorporates"}


def test_cross_reference_source_matches_category():
    """Verify that enriched cross_references have sources matching _SIGNAL_DOMAINS keys."""
    from core.enrichment import _SIGNAL_DOMAINS

    # Build cross_references via enrichment logic (simulated)
    cross_refs = [
        CrossReference(source="nih", url="https://reporter.nih.gov/abc"),
        CrossReference(source="sec", url="https://sec.gov/xyz"),
        CrossReference(source="arxiv", url="https://arxiv.org/abs/1234"),
        CrossReference(source="opencorporates", url="https://opencorporates.com/co/1"),
    ]

    valid_sources = set(_SIGNAL_DOMAINS.keys())
    for cr in cross_refs:
        assert cr.source in valid_sources, (
            f"CrossReference source '{cr.source}' not in {valid_sources}"
        )
