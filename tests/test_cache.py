from storage.cache import CacheDatabase
from core.models import PatentRecord


def test_cache_init(tmp_path):
    db_path = tmp_path / "test_cache.db"
    cache = CacheDatabase(db_path=str(db_path))

    conn = cache.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert "search_results" in tables
    assert "collections" in tables
    assert "citations" in tables
    assert "search_history" in tables
    assert "cache_health" in tables
    assert "api_metadata" in tables
    assert "export_log" in tables
    assert "terminal_sessions" in tables
    conn.close()


def test_search_caching(tmp_path):
    db_path = tmp_path / "test_cache.db"
    cache = CacheDatabase(db_path=str(db_path))

    query = "test query"
    records = [
        PatentRecord(
            id="1",
            title="T1",
            assignee="A1",
            dates={"filed": "2020-01-01"},
            abstract="AB",
            claims=[],
            image_urls=[],
            status="S",
            family_id="F",
        )
    ]

    cache.save_search_results(query, records)

    cached = cache.get_cached_search(query)
    assert cached is not None
    assert len(cached) == 1
    assert cached[0].id == "1"
    assert cached[0].title == "T1"


def test_search_cache_expiration(tmp_path, monkeypatch):
    db_path = tmp_path / "test_cache.db"
    cache = CacheDatabase(db_path=str(db_path))

    query = "old query"
    records = [
        PatentRecord(
            id="1",
            title="T1",
            assignee="A1",
            dates={"filed": "2020-01-01"},
            abstract="AB",
            claims=[],
            image_urls=[],
            status="S",
            family_id="F",
        )
    ]

    cache.save_search_results(query, records)

    from storage.cache import _query_hash

    qhash = _query_hash(query)
    with cache.get_connection() as conn:
        conn.execute(
            "UPDATE search_results SET expires_at = datetime('now', '-1 day') WHERE query_hash = ?",
            (qhash,),
        )
        conn.commit()

    cached = cache.get_cached_search(query)
    assert cached is None
