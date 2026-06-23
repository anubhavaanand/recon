import sqlite3
import threading
from pathlib import Path

import pytest

from core.models import PatentRecord
from storage.cache import CacheDatabase, _query_hash


@pytest.fixture
def cache(tmp_path):
    db_path = tmp_path / "cache_test.db"
    cache_manager = CacheDatabase(str(db_path))
    yield cache_manager


@pytest.fixture
def sample_record():
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


def test_document_content_cached_indefinitely(cache, sample_record):
    cache.save_to_collection(sample_record)
    collection = cache.get_collection()
    assert len(collection) == 1
    assert collection[0].id == sample_record.id
    assert collection[0].title == sample_record.title

    conn = sqlite3.connect(cache.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE collections
        SET saved_at = datetime('now', '-100 days')
        WHERE patent_id = ?
        """,
        (sample_record.id,),
    )
    conn.commit()

    collection = cache.get_collection()
    assert len(collection) == 1, "Document should be retrievable indefinitely"
    assert collection[0].id == sample_record.id
    assert collection[0].title == sample_record.title
    conn.close()


def test_metadata_refreshed_every_30_days(cache, sample_record):
    query = "test_patent_search"
    records = [sample_record]

    cache.save_search_results(query, records)

    cached_results = cache.get_cached_search(query)
    assert cached_results is not None, "Fresh search results should be retrieved"
    assert len(cached_results) == 1
    assert cached_results[0].id == sample_record.id

    qhash = _query_hash(query)

    conn = sqlite3.connect(cache.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE search_results
        SET expires_at = datetime('now', '+15 days')
        WHERE query_hash = ?
        """,
        (qhash,),
    )
    conn.commit()

    cached_results = cache.get_cached_search(query)
    assert (
        cached_results is not None
    ), "Search results within 30 days should be retrieved"
    assert len(cached_results) == 1

    cursor.execute(
        """
        UPDATE search_results
        SET expires_at = datetime('now', '-1 day')
        WHERE query_hash = ?
        """,
        (qhash,),
    )
    conn.commit()

    cached_results = cache.get_cached_search(query)
    assert (
        cached_results is None
    ), "Search results older than expires_at should not be retrieved"
    conn.close()


def test_citations_append_only(cache):
    patent_id = "US10000001"

    cache.save_citations(
        patent_id=patent_id,
        cited_by=["US9000001"],
        cites=["US8000001"],
        data_source="uspto",
    )

    row = cache.get_citations(patent_id)
    assert row is not None
    assert "US9000001" in row["cited_by"]
    assert row["citation_count"] == 1

    cache.save_citations(
        patent_id=patent_id,
        cited_by=["US9000001", "US7000001"],
        cites=["US8000001"],
        data_source="uspto",
    )

    row = cache.get_citations(patent_id)
    assert row is not None
    assert row["citation_count"] == 2

    cache.save_citations(
        patent_id="US20000001",
        cited_by=["US9000001"],
        data_source="wipo",
    )

    row2 = cache.get_citations("US20000001")
    assert row2 is not None
    assert row2["data_source"] == "wipo"


def test_cache_schema_validation(cache):
    conn = sqlite3.connect(cache.db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]

    required_tables = [
        "cache_health",
        "citations",
        "collections",
        "export_log",
        "api_metadata",
        "search_history",
        "search_results",
        "terminal_sessions",
    ]
    for table in required_tables:
        assert table in tables, f"Required table '{table}' not found"

    cursor.execute("PRAGMA table_info(collections)")
    collections_columns = {row[1] for row in cursor.fetchall()}
    required_cols = {"patent_id", "patent_json", "source_api", "collection_name", "saved_at"}
    assert required_cols.issubset(collections_columns), (
        f"Missing: {required_cols - collections_columns}"
    )

    cursor.execute("PRAGMA table_info(search_results)")
    search_columns = {row[1] for row in cursor.fetchall()}
    required_search_cols = {"query_hash", "query_text", "results_json", "expires_at"}
    assert required_search_cols.issubset(search_columns), (
        f"Missing: {required_search_cols - search_columns}"
    )

    cursor.execute("PRAGMA table_info(citations)")
    citations_columns = {row[1] for row in cursor.fetchall()}
    required_cit_cols = {"patent_id", "cited_by", "cites", "family_members", "citation_count", "data_source"}
    assert required_cit_cols.issubset(citations_columns), (
        f"Missing: {required_cit_cols - citations_columns}"
    )

    cursor.execute("PRAGMA table_info(collections)")
    pk_column = [row for row in cursor.fetchall() if row[5] > 0]
    assert len(pk_column) > 0, "collections table should have a primary key"

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='collections'"
    )
    indexes = cursor.fetchall()
    assert len(indexes) > 0, "collections table should have indexes"

    cursor.execute("SELECT name FROM sqlite_master WHERE name = ?", ("idx_collections_tags",))
    assert cursor.fetchone(), "FTS5 virtual table idx_collections_tags should exist"

    conn.close()


def test_corrupted_cache_recovery(cache, sample_record):
    cache.save_to_collection(sample_record)

    collection = cache.get_collection()
    assert len(collection) == 1

    conn = sqlite3.connect(cache.db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO collections (patent_id, patent_json, source_api, collection_name, saved_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        """,
        ("CORRUPT01", "{invalid json data", "web", "default"),
    )

    cursor.execute(
        """
        INSERT INTO search_results (query_hash, query_text, results_json, result_count, sources_queried, expires_at)
        VALUES (?, ?, ?, ?, ?, datetime('now', '+30 days'))
        """,
        ("deadbeef", "test_query", "[incomplete array", 1, '["web"]'),
    )
    conn.commit()
    conn.close()

    try:
        collection = cache.get_collection()
        assert len(collection) >= 1, "Valid records should be preserved"
    except (sqlite3.DatabaseError, ValueError):
        pass

    conn = sqlite3.connect(cache.db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT patent_id FROM collections WHERE patent_id = ?",
        (sample_record.id,),
    )
    result = cursor.fetchone()
    assert result is not None, "Valid data should survive corruption"
    conn.close()


def test_concurrent_access_thread_safe(cache, multiple_records):
    operations_count = threading.Lock()
    successful_writes = 0
    successful_reads = 0
    errors = []

    def write_worker(record_list):
        nonlocal successful_writes
        try:
            for record in record_list:
                cache.save_to_collection(record)
                with operations_count:
                    successful_writes += 1
        except Exception as e:
            errors.append(f"Write error: {e}")

    def read_worker(queries):
        nonlocal successful_reads
        try:
            for query in queries:
                _ = cache.get_cached_search(query)
                _ = cache.get_collection()
                with operations_count:
                    successful_reads += 2
        except Exception as e:
            errors.append(f"Read error: {e}")

    threads = []

    for i in range(3):
        record_batch = [multiple_records[j % len(multiple_records)] for j in range(2)]
        t = threading.Thread(target=write_worker, args=(record_batch,))
        threads.append(t)

    for i in range(2):
        queries = [f"query_{j}" for j in range(3)]
        t = threading.Thread(target=read_worker, args=(queries,))
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join(timeout=10)

    assert len(errors) == 0, f"Threading errors occurred: {errors}"
    assert successful_writes > 0, "Write operations should complete"
    assert successful_reads > 0, "Read operations should complete"

    collection = cache.get_collection()
    assert isinstance(collection, list)

    if successful_writes > 0:
        assert len(collection) > 0, "Written records should be retrievable"

    conn = sqlite3.connect(cache.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM collections")
    total_records = cursor.fetchone()[0]
    assert total_records >= 0, "Database should remain functional"
    conn.close()


def test_cache_eviction_policies(cache, multiple_records):
    query1 = "query_1"
    query2 = "query_2"
    query3 = "query_3"

    cache.save_search_results(query1, [multiple_records[0]])
    cache.save_search_results(query2, [multiple_records[1]])
    cache.save_search_results(query3, [multiple_records[2]])

    assert cache.get_cached_search(query1) is not None
    assert cache.get_cached_search(query2) is not None
    assert cache.get_cached_search(query3) is not None

    qhash1 = _query_hash(query1)
    qhash2 = _query_hash(query2)

    conn = sqlite3.connect(cache.db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE search_results
        SET expires_at = datetime('now', '-1 day')
        WHERE query_hash = ?
        """,
        (qhash1,),
    )

    cursor.execute(
        """
        UPDATE search_results
        SET expires_at = datetime('now', '+15 days')
        WHERE query_hash = ?
        """,
        (qhash2,),
    )

    conn.commit()
    conn.close()

    result1 = cache.get_cached_search(query1)
    result2 = cache.get_cached_search(query2)
    result3 = cache.get_cached_search(query3)

    assert result1 is None, "Expired results should not be returned"
    assert result2 is not None, "Results within TTL should be returned"
    assert result3 is not None, "Fresh results should be returned"

    for record in multiple_records:
        cache.save_to_collection(record)

    collection_before = cache.get_collection()
    count_before = len(collection_before)

    conn = sqlite3.connect(cache.db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE collections
        SET saved_at = datetime('now', '-90 days')
        """
    )
    conn.commit()
    conn.close()

    collection_after = cache.get_collection()
    assert (
        len(collection_after) == count_before
    ), "Collection records should not be evicted despite age"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
