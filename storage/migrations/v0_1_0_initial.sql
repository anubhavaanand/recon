-- v0.1.0 Initial Schema
-- 8 tables: search_results, collections, citations, search_history,
--           cache_health, scraper_metadata, export_log, terminal_sessions

PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS search_results (
    query_hash TEXT PRIMARY KEY,
    query_text TEXT NOT NULL,
    results_json TEXT NOT NULL,
    result_count INTEGER NOT NULL DEFAULT 0,
    sources_queried TEXT NOT NULL DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    hit_count INTEGER NOT NULL DEFAULT 0,
    last_accessed TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_search_results_expires ON search_results(expires_at);
CREATE INDEX IF NOT EXISTS idx_search_results_accessed ON search_results(last_accessed);
CREATE INDEX IF NOT EXISTS idx_search_results_hit_count ON search_results(hit_count DESC);

CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patent_id TEXT NOT NULL,
    patent_json TEXT NOT NULL,
    source_api TEXT NOT NULL,
    collection_name TEXT NOT NULL DEFAULT 'default',
    saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    tags TEXT DEFAULT '[]',
    score_at_save INTEGER
);

CREATE INDEX IF NOT EXISTS idx_collections_name ON collections(collection_name);
CREATE INDEX IF NOT EXISTS idx_collections_patent_id ON collections(patent_id);
CREATE INDEX IF NOT EXISTS idx_collections_saved_at ON collections(saved_at DESC);

CREATE TABLE IF NOT EXISTS citations (
    patent_id TEXT PRIMARY KEY,
    cited_by TEXT NOT NULL DEFAULT '[]',
    cites TEXT NOT NULL DEFAULT '[]',
    family_members TEXT NOT NULL DEFAULT '[]',
    family_id TEXT,
    citation_count INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_source TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_citations_family ON citations(family_id);
CREATE INDEX IF NOT EXISTS idx_citations_count ON citations(citation_count DESC);
CREATE INDEX IF NOT EXISTS idx_citations_updated ON citations(updated_at);

CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    query_hash TEXT NOT NULL,
    result_count INTEGER,
    sources TEXT NOT NULL DEFAULT '[]',
    execution_time_ms INTEGER,
    cache_hit BOOLEAN NOT NULL DEFAULT FALSE,
    searched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tui_mode BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_search_history_query ON search_history(query_text);
CREATE INDEX IF NOT EXISTS idx_search_history_hash ON search_history(query_hash);
CREATE INDEX IF NOT EXISTS idx_search_history_time ON search_history(searched_at DESC);

CREATE TABLE IF NOT EXISTS cache_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    table_name TEXT NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    corrupt_rows INTEGER NOT NULL DEFAULT 0,
    db_size_mb REAL NOT NULL DEFAULT 0.0,
    vacuum_needed BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_cache_health_table ON cache_health(table_name, check_at DESC);

CREATE TABLE IF NOT EXISTS scraper_metadata (
    source_name TEXT PRIMARY KEY,
    base_url TEXT NOT NULL,
    auth_type TEXT NOT NULL,
    rate_limit_per_minute INTEGER NOT NULL DEFAULT 0,
    actual_limit_used INTEGER NOT NULL DEFAULT 0,
    requests_this_hour INTEGER NOT NULL DEFAULT 0,
    last_request_at TIMESTAMP,
    last_error_at TIMESTAMP,
    last_error_code INTEGER,
    consecutive_errors INTEGER NOT NULL DEFAULT 0,
    circuit_open BOOLEAN NOT NULL DEFAULT FALSE,
    api_key_masked TEXT
);

CREATE INDEX IF NOT EXISTS idx_scraper_metadata_circuit ON scraper_metadata(circuit_open);

CREATE TABLE IF NOT EXISTS export_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    export_format TEXT NOT NULL,
    file_path TEXT NOT NULL,
    collection_name TEXT,
    record_count INTEGER NOT NULL DEFAULT 0,
    file_size_bytes INTEGER,
    exported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cli_mode BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_export_log_format ON export_log(export_format, exported_at DESC);
CREATE INDEX IF NOT EXISTS idx_export_log_collection ON export_log(collection_name);

CREATE TABLE IF NOT EXISTS terminal_sessions (
    session_id TEXT PRIMARY KEY,
    query_text TEXT,
    selected_index INTEGER,
    active_tab TEXT,
    screen_name TEXT NOT NULL DEFAULT 'SearchScreen',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_terminal_sessions_active ON terminal_sessions(is_active, last_activity DESC);

CREATE TABLE IF NOT EXISTS schema_version (version TEXT PRIMARY KEY);
INSERT OR REPLACE INTO schema_version (version) VALUES ('0.1.0');