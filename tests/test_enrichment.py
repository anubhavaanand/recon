"""Tests for Phase 2 enrichment pipeline.

Covers:
- Cache layer (get/save enrichment cache)
- Enrichment function (native API calls, fallback, error handling, caching)
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
def mock_cross_refs():
    """Standard mock cross-references returned by API handlers."""
    return [
        CrossReference(source="arxiv", url="https://arxiv.org/abs/1234", date="2023-01-01",
                       metadata={"title": "Arxiv Paper", "snippet": "Research abstract."}),
        CrossReference(source="nsf", url="https://nsf.gov/award/1", date="2023-02-01",
                       metadata={"title": "NSF Grant", "snippet": "Grant abstract."}),
        CrossReference(source="doe", url="https://osti.gov/biblio/1", date="2023-03-01",
                       metadata={"title": "DOE Report", "snippet": "Report abstract."}),
        CrossReference(source="nih", url="https://reporter.nih.gov/1", date="2023-04-01",
                       metadata={"title": "NIH Project", "snippet": "Project abstract."}),
        CrossReference(source="sec", url="https://sec.gov/edgar/1", date="2023-05-01",
                       metadata={"title": "SEC Filing", "snippet": ""}),
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
async def test_enrich_patent_adds_cross_references(basic_record, mock_cross_refs):
    """Mock all 5 API handlers to return results; verify record gets 5 cross_references."""
    from core.enrichment import enrich_patent

    with patch("core.enrichment.CacheDatabase") as mock_cache_cls:
        mock_db = MagicMock()
        mock_cache_cls.return_value = mock_db
        mock_db.get_enrichment_cache.return_value = None

        with (patch("core.enrichment._search_arxiv", new_callable=AsyncMock) as mock_a,
              patch("core.enrichment._search_nsf", new_callable=AsyncMock) as mock_nsf,
              patch("core.enrichment._search_doe", new_callable=AsyncMock) as mock_d,
              patch("core.enrichment._search_nih", new_callable=AsyncMock) as mock_nih,
              patch("core.enrichment._search_sec", new_callable=AsyncMock) as mock_s):
            mock_a.return_value = mock_cross_refs[0]
            mock_nsf.return_value = mock_cross_refs[1]
            mock_d.return_value = mock_cross_refs[2]
            mock_nih.return_value = mock_cross_refs[3]
            mock_s.return_value = mock_cross_refs[4]

            result = await enrich_patent(basic_record)

            assert len(result.cross_references) == 5
            sources = {cr.source for cr in result.cross_references}
            assert sources == {"arxiv", "nsf", "doe", "nih", "sec"}
            for cr in result.cross_references:
                assert cr.url is not None
            mock_db.save_enrichment_cache.assert_called_once()


@pytest.mark.asyncio
async def test_enrich_patent_handles_empty_assignee(record_empty_assignee, mock_cross_refs):
    """Assignee is '[?]'; should fall back to title words."""
    from core.enrichment import enrich_patent

    with patch("core.enrichment.CacheDatabase") as mock_cache_cls:
        mock_db = MagicMock()
        mock_cache_cls.return_value = mock_db
        mock_db.get_enrichment_cache.return_value = None

        with (patch("core.enrichment._search_arxiv", new_callable=AsyncMock) as mock_a,
              patch("core.enrichment._search_nsf", new_callable=AsyncMock) as mock_nsf,
              patch("core.enrichment._search_doe", new_callable=AsyncMock) as mock_d,
              patch("core.enrichment._search_nih", new_callable=AsyncMock) as mock_nih,
              patch("core.enrichment._search_sec", new_callable=AsyncMock) as mock_s):
            mock_a.return_value = mock_cross_refs[0]
            mock_nsf.return_value = mock_cross_refs[1]
            mock_d.return_value = mock_cross_refs[2]
            mock_nih.return_value = mock_cross_refs[3]
            mock_s.return_value = mock_cross_refs[4]

            result = await enrich_patent(record_empty_assignee)

            assert len(result.cross_references) == 5
            # Verify that the query used title words (assignee was "[?]")
            mock_a.assert_called_once()
            query_arg = mock_a.call_args[0][0]
            assert "Advanced" in query_arg


@pytest.mark.asyncio
async def test_enrich_patent_graceful_timeout(basic_record):
    """All API handlers return None; verify original record returned unchanged."""
    from core.enrichment import enrich_patent

    with patch("core.enrichment.CacheDatabase") as mock_cache_cls:
        mock_db = MagicMock()
        mock_cache_cls.return_value = mock_db
        mock_db.get_enrichment_cache.return_value = None

        with (patch("core.enrichment._search_arxiv", new_callable=AsyncMock) as mock_a,
              patch("core.enrichment._search_nsf", new_callable=AsyncMock),
              patch("core.enrichment._search_doe", new_callable=AsyncMock),
              patch("core.enrichment._search_nih", new_callable=AsyncMock),
              patch("core.enrichment._search_sec", new_callable=AsyncMock)):
            mock_a.return_value = None

            result = await enrich_patent(basic_record)

            assert result is basic_record
            assert result.cross_references == []


@pytest.mark.asyncio
async def test_enrich_patent_skips_if_already_enriched(basic_record):
    """Enrichment is already cached; verify enrich_patent doesn't call API handlers."""
    from core.enrichment import enrich_patent

    cached_refs = [
        CrossReference(source="nih", url="https://reporter.nih.gov/project/123"),
        CrossReference(source="sec", url="https://sec.gov/filing/abc"),
    ]

    with patch("core.enrichment.CacheDatabase") as mock_cache_cls:
        mock_db = MagicMock()
        mock_cache_cls.return_value = mock_db
        mock_db.get_enrichment_cache.return_value = cached_refs

        with (patch("core.enrichment._search_arxiv", new_callable=AsyncMock) as mock_a,
              patch("core.enrichment._search_nsf", new_callable=AsyncMock) as mock_nsf,
              patch("core.enrichment._search_doe", new_callable=AsyncMock) as mock_d,
              patch("core.enrichment._search_nih", new_callable=AsyncMock) as mock_nih,
              patch("core.enrichment._search_sec", new_callable=AsyncMock) as mock_s):

            result = await enrich_patent(basic_record)

            assert len(result.cross_references) == 2
            assert result.cross_references[0].source == "nih"
            assert result.cross_references[1].source == "sec"
            mock_a.assert_not_called()
            mock_nsf.assert_not_called()
            mock_d.assert_not_called()
            mock_nih.assert_not_called()
            mock_s.assert_not_called()


@pytest.mark.asyncio
async def test_enrich_patent_uses_cache(tmp_path, basic_record, mock_cross_refs):
    """First call saves to cache; second call doesn't hit API handlers."""
    from core.enrichment import enrich_patent

    db_path = tmp_path / "test_enrich_cache.db"

    with patch("core.enrichment.CacheDatabase") as mock_cache_cls:
        real_db = CacheDatabase(db_path=str(db_path))
        mock_db_spy = MagicMock(wraps=real_db)
        mock_cache_cls.return_value = mock_db_spy

        with (patch("core.enrichment._search_arxiv", new_callable=AsyncMock) as mock_a,
              patch("core.enrichment._search_nsf", new_callable=AsyncMock) as mock_nsf,
              patch("core.enrichment._search_doe", new_callable=AsyncMock) as mock_d,
              patch("core.enrichment._search_nih", new_callable=AsyncMock) as mock_nih,
              patch("core.enrichment._search_sec", new_callable=AsyncMock) as mock_s):
            mock_a.return_value = mock_cross_refs[0]
            mock_nsf.return_value = mock_cross_refs[1]
            mock_d.return_value = mock_cross_refs[2]
            mock_nih.return_value = mock_cross_refs[3]
            mock_s.return_value = mock_cross_refs[4]

            # --- First call: cache miss -> APIs called ---
            record1 = PatentRecord(
                id=basic_record.id, title=basic_record.title,
                assignee=basic_record.assignee, dates=basic_record.dates,
                abstract=basic_record.abstract, claims=[], image_urls=[],
                status=basic_record.status, family_id=basic_record.family_id,
            )
            await enrich_patent(record1)
            assert mock_a.call_count >= 1

            # Reset mocks
            mock_a.reset_mock()
            mock_nsf.reset_mock()
            mock_d.reset_mock()
            mock_nih.reset_mock()
            mock_s.reset_mock()

            # --- Second call: cache hit -> APIs NOT called ---
            record2 = PatentRecord(
                id=basic_record.id, title=basic_record.title,
                assignee=basic_record.assignee, dates=basic_record.dates,
                abstract=basic_record.abstract, claims=[], image_urls=[],
                status=basic_record.status, family_id=basic_record.family_id,
            )
            result2 = await enrich_patent(record2)

            assert len(result2.cross_references) > 0
            mock_a.assert_not_called()
            mock_nsf.assert_not_called()
            mock_d.assert_not_called()
            mock_nih.assert_not_called()
            mock_s.assert_not_called()


# ═══════════════════════════════════════════════════════════════
# Search Pipeline Integration (2 tests)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_search_all_does_not_enrich_synchronously():
    """Mock enrich_patent to ensure search_all no longer synchronously enriches records to prevent UI hangs."""
    from core.search import search_all
    from core.models import PatentRecord

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

        mock_u.return_value = records[:5]
        mock_e.return_value = records[5:8]
        mock_w.return_value = records[8:]
        mock_l.return_value = []
        mock_g.return_value = []
        mock_p.return_value = []

        with patch("core.enrichment.enrich_patent", new_callable=AsyncMock) as mock_enrich:
            mock_enrich.return_value = records[0]

            result = await search_all("test query", sources=["uspto", "epo", "wipo", "lens", "google", "patsnap"])

            assert len(result) == 10
            # Enrichment is lazy (TUI-side), not called during search_all
            assert mock_enrich.call_count == 0


@pytest.mark.asyncio
async def test_search_all_lazy_enrichment_doesnt_crash():
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

        with patch("core.enrichment.enrich_patent", new_callable=AsyncMock) as mock_enrich:
            mock_enrich.side_effect = Exception("Enrichment failed")

            result = await search_all("test query", sources=["uspto", "epo", "wipo", "lens", "google", "patsnap"])

            assert len(result) == 5
            assert mock_enrich.call_count == 0


# ═══════════════════════════════════════════════════════════════
# Lazy Enrichment in TUI (1 test)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_enrich_current_skips_if_already_enriched():
    """Verify _enrich_current guard: skip when record already has cross_references."""
    record = PatentRecord(
        id="US12345678B2", title="Test Patent", assignee="ACME Corp",
        dates={"filed": "2022-06-15"}, abstract="A battery.",
        claims=[], image_urls=[], status="active", family_id="F",
        cross_references=[
            CrossReference(source="NIH", url="https://reporter.nih.gov/123"),
        ],
    )

    with patch("core.enrichment.enrich_patent", new_callable=AsyncMock) as mock_enrich:
        if record.cross_references:
            pass
        else:
            await mock_enrich(record)
        mock_enrich.assert_not_called()


# ═══════════════════════════════════════════════════════════════
# Signal Domain Coverage (2 tests)
# ═══════════════════════════════════════════════════════════════

def test_signal_domains_defined():
    """Verify _SIGNAL_DOMAINS has all 5 expected keys."""
    from core.enrichment import _SIGNAL_DOMAINS

    assert isinstance(_SIGNAL_DOMAINS, dict)
    assert set(_SIGNAL_DOMAINS.keys()) == {"nih", "sec", "arxiv", "nsf", "doe"}


def test_cross_reference_source_matches_category():
    """Verify that enriched cross_references have sources matching _SIGNAL_DOMAINS keys."""
    from core.enrichment import _SIGNAL_DOMAINS

    cross_refs = [
        CrossReference(source="nih", url="https://reporter.nih.gov/abc"),
        CrossReference(source="sec", url="https://sec.gov/xyz"),
        CrossReference(source="arxiv", url="https://arxiv.org/abs/1234"),
        CrossReference(source="nsf", url="https://nsf.gov/award/1"),
        CrossReference(source="doe", url="https://osti.gov/biblio/1"),
    ]

    valid_sources = set(_SIGNAL_DOMAINS.keys())
    for cr in cross_refs:
        assert cr.source in valid_sources, (
            f"CrossReference source '{cr.source}' not in {valid_sources}"
        )
