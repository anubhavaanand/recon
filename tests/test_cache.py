from storage.cache import CacheDatabase

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
