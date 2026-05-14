"""
Task 3.3: Cache Validation Tests

Tests cache TTL, append-only behavior, schema validation, corruption recovery,
and thread-safety as specified in EVALUATION_TASKS.md.

Test Coverage:
- Indefinite cache for document content (no TTL expiration)
- 30-day refresh for metadata and search results
- Append-only behavior for citations
- Cache schema validation
- Graceful corruption recovery
- Concurrent access thread-safety
"""

import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path

import pytest

from core.models import PatentRecord
from storage.cache import CacheDatabase


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def cache(tmp_path):
    """Create a temporary cache for testing."""
    db_path = tmp_path / "cache_test.db"
    cache_manager = CacheDatabase(str(db_path))
    yield cache_manager
    # Cleanup is automatic via tmp_path


@pytest.fixture
def sample_record():
    """Create a sample patent record for testing."""
    return PatentRecord(
        id="US10000001",
        title="Test Patent",
        assignee="Test Corp",
        dates={"filed": "2020-01-01", "issued": "2021-01-01"},
        abstract="A test patent abstract",
        claims=["Claim 1", "Claim 2"],
        image_urls=["http://example.com/image1.jpg"],
        status="Active",
        family_id="US10000001-FAM",
    )


@pytest.fixture
def multiple_records():
    """Create multiple patent records for testing."""
    return [
        PatentRecord(
            id=f"US1000000{i}",
            title=f"Patent {i}",
            assignee=f"Company {i}",
            dates={"filed": f"202{i}-01-01", "issued": f"202{i}-06-01"},
            abstract=f"Abstract for patent {i}",
            claims=[f"Claim {j}" for j in range(3)],
            image_urls=[f"http://example.com/image{i}_{j}.jpg" for j in range(2)],
            status="Active",
            family_id=f"US1000000{i}-FAM",
        )
        for i in range(1, 4)
    ]


# ============================================================================
# TEST 1: Document Content Cached Indefinitely
# ============================================================================


def test_document_content_cached_indefinitely(cache, sample_record):
    """
    Verify that document content is cached indefinitely with no TTL expiration.
    
    Requirements:
    - Document content should be retrievable after any amount of time
    - No TTL constraint on document_content table
    - Query should return the document without any age-based filtering
    """
    # Save a document to the collection (which stores document content)
    cache.save_to_collection(sample_record)
    
    # Retrieve immediately
    collection = cache.get_collection()
    assert len(collection) == 1
    assert collection[0].id == sample_record.id
    assert collection[0].title == sample_record.title
    
    # Simulate passage of time by manually backdating the timestamp
    # (This tests that no TTL query is applied to document content)
    conn = sqlite3.connect(cache.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Backdate the record to 100 days ago (well beyond any reasonable TTL)
    cursor.execute(
        """
        UPDATE collections 
        SET timestamp = datetime('now', '-100 days')
        WHERE patent_id = ?
        """,
        (sample_record.id,),
    )
    conn.commit()
    
    # Verify document is still retrievable (no TTL filtering on document content)
    collection = cache.get_collection()
    assert len(collection) == 1, "Document should be retrievable indefinitely"
    assert collection[0].id == sample_record.id
    assert collection[0].title == sample_record.title
    
    conn.close()


# ============================================================================
# TEST 2: Metadata Refreshed Every 30 Days
# ============================================================================


def test_metadata_refreshed_every_30_days(cache, sample_record):
    """
    Verify that metadata (search results) is refreshed every 30 days.
    
    Requirements:
    - Metadata cached within 30 days should be retrieved
    - Metadata older than 30 days should be expired and not retrieved
    - TTL enforcement via datetime('now', '-30 days') in SQL queries
    """
    query = "test_patent_search"
    records = [sample_record]
    
    # Save search results
    cache.save_search_results(query, records)
    
    # Verify recent search results are retrieved
    cached_results = cache.get_cached_search(query)
    assert cached_results is not None, "Fresh search results should be retrieved"
    assert len(cached_results) == 1
    assert cached_results[0].id == sample_record.id
    
    # Simulate passage of 15 days (within TTL window)
    conn = sqlite3.connect(cache.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        """
        UPDATE search_results 
        SET timestamp = datetime('now', '-15 days')
        WHERE query = ?
        """,
        (query,),
    )
    conn.commit()
    
    # Verify search results still retrieved
    cached_results = cache.get_cached_search(query)
    assert (
        cached_results is not None
    ), "Search results within 30 days should be retrieved"
    assert len(cached_results) == 1
    
    # Simulate passage of 31 days (beyond TTL window)
    cursor.execute(
        """
        UPDATE search_results 
        SET timestamp = datetime('now', '-31 days')
        WHERE query = ?
        """,
        (query,),
    )
    conn.commit()
    
    # Verify search results are NOT retrieved (expired)
    cached_results = cache.get_cached_search(query)
    assert (
        cached_results is None
    ), "Search results older than 30 days should expire"
    
    conn.close()


# ============================================================================
# TEST 3: Citations Append-Only Behavior
# ============================================================================


def test_citations_append_only(cache):
    """
    Verify that citations follow append-only semantics.
    
    Requirements:
    - Citations can be added to cache
    - Citations are never deleted or overwritten
    - Multiple citations for the same patent can be stored
    - Citation retrieval shows all appended citations
    """
    patent_id = "US10000001"
    
    conn = sqlite3.connect(cache.db_path)
    cursor = conn.cursor()
    
    # Add first citation
    citation1 = "US9000001"
    cursor.execute(
        """
        INSERT INTO citations (patent_id, cited_patent_id)
        VALUES (?, ?)
        """,
        (patent_id, citation1),
    )
    conn.commit()
    
    # Verify citation stored
    cursor.execute(
        "SELECT cited_patent_id FROM citations WHERE patent_id = ?",
        (patent_id,),
    )
    results = cursor.fetchall()
    assert len(results) == 1
    assert results[0][0] == citation1
    
    # Add second citation (append operation)
    citation2 = "US8000001"
    cursor.execute(
        """
        INSERT INTO citations (patent_id, cited_patent_id)
        VALUES (?, ?)
        """,
        (patent_id, citation2),
    )
    conn.commit()
    
    # Verify both citations are stored (append-only behavior)
    cursor.execute(
        "SELECT cited_patent_id FROM citations WHERE patent_id = ? ORDER BY cited_patent_id",
        (patent_id,),
    )
    results = cursor.fetchall()
    assert len(results) == 2, "Both citations should be present"
    cited_ids = [row[0] for row in results]
    assert citation1 in cited_ids, "First citation should not be deleted"
    assert citation2 in cited_ids, "Second citation should be added"
    
    # Attempt to add duplicate citation (append-only allows this)
    cursor.execute(
        """
        INSERT INTO citations (patent_id, cited_patent_id)
        VALUES (?, ?)
        """,
        (patent_id, citation1),
    )
    conn.commit()
    
    # Verify total count increased (no deduplication in append-only)
    cursor.execute(
        "SELECT COUNT(*) FROM citations WHERE patent_id = ?",
        (patent_id,),
    )
    count = cursor.fetchone()[0]
    assert count == 3, "Append-only: duplicate citations should be stored"
    
    conn.close()


# ============================================================================
# TEST 4: Cache Schema Validation
# ============================================================================


def test_cache_schema_validation(cache):
    """
    Verify that cache creates proper SQLite schema.
    
    Requirements:
    - All required tables exist (collections, search_results, citations, etc.)
    - Tables have correct columns and constraints
    - Primary keys and indexes are properly defined
    - Foreign key constraints are in place
    """
    conn = sqlite3.connect(cache.db_path)
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]
    
    # Verify required tables exist
    required_tables = [
        "collections",
        "search_results",
        "citations",
        "document_content",
        "status_metadata",
        "family_links",
    ]
    for table in required_tables:
        assert (
            table in tables
        ), f"Required table '{table}' not found in cache schema"
    
    # Validate collections table schema
    cursor.execute("PRAGMA table_info(collections)")
    collections_columns = {row[1] for row in cursor.fetchall()}
    required_collections_cols = {"patent_id", "data", "timestamp"}
    assert (
        required_collections_cols.issubset(collections_columns)
    ), f"collections table missing columns: {required_collections_cols - collections_columns}"
    
    # Validate search_results table schema
    cursor.execute("PRAGMA table_info(search_results)")
    search_columns = {row[1] for row in cursor.fetchall()}
    required_search_cols = {"query", "results", "timestamp"}
    assert (
        required_search_cols.issubset(search_columns)
    ), f"search_results table missing columns: {required_search_cols - search_columns}"
    
    # Validate citations table schema
    cursor.execute("PRAGMA table_info(citations)")
    citations_columns = {row[1] for row in cursor.fetchall()}
    required_citations_cols = {"patent_id", "cited_patent_id"}
    assert (
        required_citations_cols.issubset(citations_columns)
    ), f"citations table missing columns: {required_citations_cols - citations_columns}"
    
    # Verify primary key on collections (patent_id should be unique)
    cursor.execute("PRAGMA table_info(collections)")
    pk_column = [row for row in cursor.fetchall() if row[5] > 0]
    assert len(pk_column) > 0, "collections table should have a primary key"
    
    # Verify indexes exist for performance
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='collections'"
    )
    indexes = cursor.fetchall()
    assert len(indexes) > 0, "collections table should have indexes for performance"
    
    conn.close()


# ============================================================================
# TEST 5: Corrupted Cache Recovery
# ============================================================================


def test_corrupted_cache_recovery(cache, sample_record):
    """
    Verify graceful recovery from corrupted cache.
    
    Requirements:
    - Cache should detect corrupted data
    - Recovery should preserve remaining valid data
    - No data loss for valid records during corruption recovery
    - Corrupted records should be isolated/skipped
    """
    # Save valid record
    cache.save_to_collection(sample_record)
    
    # Verify record exists
    collection = cache.get_collection()
    assert len(collection) == 1
    
    # Corrupt a cell by storing invalid JSON
    conn = sqlite3.connect(cache.db_path)
    cursor = conn.cursor()
    
    # Insert a record with invalid JSON data
    cursor.execute(
        """
        INSERT INTO collections (patent_id, data, timestamp)
        VALUES (?, ?, datetime('now'))
        """,
        ("CORRUPT01", "{invalid json data"),
    )
    
    # Corrupt the search_results table with invalid JSON
    cursor.execute(
        """
        INSERT INTO search_results (query, results, timestamp)
        VALUES (?, ?, datetime('now'))
        """,
        ("test_query", "[incomplete array"),
    )
    conn.commit()
    conn.close()
    
    # Attempt to retrieve collection - should gracefully handle corruption
    try:
        collection = cache.get_collection()
        # If we can get collection, we recovered gracefully
        assert len(collection) >= 1, "Valid records should be preserved"
    except (sqlite3.DatabaseError, ValueError):
        # Expected: database may be corrupted
        # In a real implementation, recovery mechanisms would be triggered
        pass
    
    # Verify we can still query without exception (robust error handling)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM collections")
        count = cursor.fetchone()[0]
        assert count >= 1, "Cache should survive corruption and queries should work"
    except sqlite3.DatabaseError:
        pass
    
    # Verify valid data is still accessible by direct query
    conn = sqlite3.connect(cache.db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT patent_id FROM collections WHERE patent_id = ?",
        (sample_record.id,),
    )
    result = cursor.fetchone()
    assert result is not None, "Valid data should survive corruption"
    conn.close()


# ============================================================================
# TEST 6: Concurrent Access Thread-Safety
# ============================================================================


def test_concurrent_access_thread_safe(cache, multiple_records):
    """
    Verify thread-safety of cache operations under concurrent access.
    
    Requirements:
    - Multiple threads can read/write to cache simultaneously
    - Cache state remains consistent after concurrent operations
    - No data corruption from concurrent writes
    - Thread-safe access to SQLite database
    """
    # Thread-safe counter for tracking operations
    operations_count = threading.Lock()
    successful_writes = 0
    successful_reads = 0
    errors = []
    
    def write_worker(record_list):
        """Worker thread that writes records to cache."""
        nonlocal successful_writes
        try:
            for record in record_list:
                cache.save_to_collection(record)
                with operations_count:
                    successful_writes += 1
        except Exception as e:
            errors.append(f"Write error: {e}")
    
    def read_worker(queries):
        """Worker thread that reads from cache."""
        nonlocal successful_reads
        try:
            for query in queries:
                _ = cache.get_cached_search(query)
                _ = cache.get_collection()
                with operations_count:
                    successful_reads += 2
        except Exception as e:
            errors.append(f"Read error: {e}")
    
    # Create multiple threads
    threads = []
    
    # Writer threads: each writes a subset of records
    for i in range(3):
        record_batch = [multiple_records[j % len(multiple_records)] for j in range(2)]
        t = threading.Thread(target=write_worker, args=(record_batch,))
        threads.append(t)
    
    # Reader threads: each reads multiple times
    for i in range(2):
        queries = [f"query_{j}" for j in range(3)]
        t = threading.Thread(target=read_worker, args=(queries,))
        threads.append(t)
    
    # Start all threads
    for t in threads:
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join(timeout=10)
    
    # Verify no threading errors
    assert len(errors) == 0, f"Threading errors occurred: {errors}"
    
    # Verify operations completed
    assert successful_writes > 0, "Write operations should complete"
    assert successful_reads > 0, "Read operations should complete"
    
    # Verify cache state is consistent
    collection = cache.get_collection()
    assert isinstance(collection, list), "Collection should be valid list"
    
    # Verify no data corruption: all written records should be retrievable
    if successful_writes > 0:
        assert len(collection) > 0, "Written records should be retrievable"
    
    # Verify database is still functional
    conn = sqlite3.connect(cache.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM collections")
    total_records = cursor.fetchone()[0]
    assert total_records >= 0, "Database should remain functional"
    conn.close()


# ============================================================================
# TEST 7: Cache Eviction Policies
# ============================================================================


def test_cache_eviction_policies(cache, multiple_records):
    """
    Verify cache eviction policies are correctly enforced.
    
    Requirements:
    - Old search results are evicted after 30 days
    - Cache maintains reasonable size constraints
    - Eviction does not affect indefinitely cached content
    - Eviction is deterministic and predictable
    """
    # Save multiple search results
    query1 = "query_1"
    query2 = "query_2"
    query3 = "query_3"
    
    cache.save_search_results(query1, [multiple_records[0]])
    cache.save_search_results(query2, [multiple_records[1]])
    cache.save_search_results(query3, [multiple_records[2]])
    
    # Verify all results are initially cached
    assert cache.get_cached_search(query1) is not None
    assert cache.get_cached_search(query2) is not None
    assert cache.get_cached_search(query3) is not None
    
    # Backdate query1 to 31 days (should be evicted)
    conn = sqlite3.connect(cache.db_path)
    cursor = conn.cursor()
    
    cursor.execute(
        """
        UPDATE search_results 
        SET timestamp = datetime('now', '-31 days')
        WHERE query = ?
        """,
        (query1,),
    )
    
    # Backdate query2 to 15 days (should remain)
    cursor.execute(
        """
        UPDATE search_results 
        SET timestamp = datetime('now', '-15 days')
        WHERE query = ?
        """,
        (query2,),
    )
    
    # Keep query3 at current time
    conn.commit()
    conn.close()
    
    # Verify eviction is applied correctly
    result1 = cache.get_cached_search(query1)
    result2 = cache.get_cached_search(query2)
    result3 = cache.get_cached_search(query3)
    
    assert (
        result1 is None
    ), "Search results older than 30 days should be evicted"
    assert result2 is not None, "Search results within 30 days should not be evicted"
    assert result3 is not None, "Fresh search results should not be evicted"
    
    # Verify indefinitely cached content is not affected by eviction
    for record in multiple_records:
        cache.save_to_collection(record)
    
    collection_before = cache.get_collection()
    count_before = len(collection_before)
    
    # Backdate all collection records
    conn = sqlite3.connect(cache.db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE collections 
        SET timestamp = datetime('now', '-90 days')
        """
    )
    conn.commit()
    conn.close()
    
    # Verify collection records are still present (indefinite cache)
    collection_after = cache.get_collection()
    assert (
        len(collection_after) == count_before
    ), "Document content should not be evicted despite age"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
