from storage.cache import CacheDatabase
from core.models import PatentRecord

def test_cache_init(tmp_path):
    db_path = tmp_path / "test_cache.db"
    cache = CacheDatabase(db_path=str(db_path))
    
    conn = cache.get_connection()
    cursor = conn.cursor()
    
    # Verify tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert "document_content" in tables
    assert "status_metadata" in tables
    assert "citations" in tables
    assert "family_links" in tables
    assert "search_results" in tables

def test_search_caching(tmp_path):
    db_path = tmp_path / "test_cache.db"
    cache = CacheDatabase(db_path=str(db_path))
    
    query = "test query"
    records = [PatentRecord(id="1", title="T1", assignee="A1", dates={"filed": "2020-01-01"}, abstract="AB", claims=[], image_urls=[], status="S", family_id="F")]
    
    # Save to cache
    cache.save_search_results(query, records)
    
    # Retrieve from cache
    cached = cache.get_cached_search(query)
    assert cached is not None
    assert len(cached) == 1
    assert cached[0].id == "1"
    assert cached[0].title == "T1"

def test_search_cache_expiration(tmp_path, monkeypatch):
    db_path = tmp_path / "test_cache.db"
    cache = CacheDatabase(db_path=str(db_path))
    
    query = "old query"
    records = [PatentRecord(id="1", title="T1", assignee="A1", dates={"filed": "2020-01-01"}, abstract="AB", claims=[], image_urls=[], status="S", family_id="F")]
    
    cache.save_search_results(query, records)
    
    # Manually backdate the updated_at
    with cache.get_connection() as conn:
        conn.execute("UPDATE search_results SET timestamp = datetime('now', '-31 days'), updated_at = datetime('now', '-31 days') WHERE query = ?", (query,))
        conn.commit()
        
    # Should be expired
    cached = cache.get_cached_search(query)
    assert cached is None
