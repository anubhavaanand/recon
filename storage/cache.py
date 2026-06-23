import sqlite3
import json
import hashlib
import dataclasses
import contextlib
from pathlib import Path
from typing import Optional
from core.models import PatentRecord, CrossReference

SCHEMA = """
-- ============================================================================
-- PRAGMAS (set per-connection in _init_db; repeated here for executescript)
-- ============================================================================
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

-- ============================================================================
-- 1. search_results: Primary cache for patent search responses
-- ============================================================================
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

-- ============================================================================
-- 2. collections: User-saved patents for export and analysis (no TTL)
-- ============================================================================
CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patent_id TEXT NOT NULL,
    patent_json TEXT NOT NULL,
    source_api TEXT NOT NULL,
    collection_name TEXT NOT NULL DEFAULT 'default',
    saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    tags TEXT DEFAULT '[]',
    score_at_save INTEGER,
    hit_count INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_collections_name ON collections(collection_name);
CREATE INDEX IF NOT EXISTS idx_collections_patent_id ON collections(patent_id);
CREATE INDEX IF NOT EXISTS idx_collections_saved_at ON collections(saved_at DESC);

-- ============================================================================
-- 3. citations: Cross-reference graph for patent families and citations
-- ============================================================================
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

-- ============================================================================
-- 4. search_history: Query log for autocomplete and session recovery
-- ============================================================================
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

-- ============================================================================
-- 5. cache_health: Corruption detection and vacuum tracking
-- ============================================================================
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

-- ============================================================================
-- 6. api_metadata: Per-source tracking (rate limits, circuit breaker)
-- ============================================================================
CREATE TABLE IF NOT EXISTS api_metadata (
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

CREATE INDEX IF NOT EXISTS idx_api_metadata_circuit ON api_metadata(circuit_open);

-- ============================================================================
-- 7. export_log: Audit trail of exported files
-- ============================================================================
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

-- ============================================================================
-- 8. terminal_sessions: TUI session state for crash recovery
-- ============================================================================
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

-- ============================================================================
-- Legacy tables (kept for backward compatibility)
-- ============================================================================
CREATE TABLE IF NOT EXISTS translation_cache (
    source_hash TEXT PRIMARY KEY,
    source_text TEXT,
    translated_text TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS enrichment_cache (
    patent_id TEXT PRIMARY KEY,
    cross_refs_json TEXT,
    enriched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 9. embeddings: Vector cache for semantic search (nomic-embed-text)
-- ============================================================================
CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patent_id TEXT NOT NULL,
    embedding_json TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(patent_id)
);

CREATE INDEX IF NOT EXISTS idx_embeddings_patent ON embeddings(patent_id);

-- ============================================================================
-- FTS5: Full-text search on collections tags
-- ============================================================================
CREATE VIRTUAL TABLE IF NOT EXISTS idx_collections_tags USING fts5(
    tags,
    content='collections',
    content_rowid='id',
    tokenize='porter unicode61'
);

-- Triggers to keep FTS5 index in sync with collections table
CREATE TRIGGER IF NOT EXISTS idx_collections_tags_ai AFTER INSERT ON collections BEGIN
    INSERT INTO idx_collections_tags(rowid, tags) VALUES (new.id, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS idx_collections_tags_ad AFTER DELETE ON collections BEGIN
    INSERT INTO idx_collections_tags(idx_collections_tags, rowid, tags) VALUES ('delete', old.id, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS idx_collections_tags_au AFTER UPDATE ON collections BEGIN
    INSERT INTO idx_collections_tags(idx_collections_tags, rowid, tags) VALUES ('delete', old.id, old.tags);
    INSERT INTO idx_collections_tags(rowid, tags) VALUES (new.id, new.tags);
END;
"""


def _query_hash(query: str) -> str:
    return hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()


def _normalize_patent_id(patent_id: str) -> str:
    if not patent_id:
        return ""
    return "".join(c for c in patent_id if c.isalnum()).upper()


class CacheDatabase:
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = str(Path.home() / ".cache" / "recon" / "cache.db")
        self.db_path = str(db_path)
        self._init_db()
        self.enforce_eviction_policy()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.executescript(SCHEMA)
        finally:
            conn.close()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    # ── search_results ──────────────────────────────────────────────────────

    def get_cached_search(self, query: str) -> Optional[list[PatentRecord]]:
        qhash = _query_hash(query)
        with contextlib.closing(self.get_connection()) as conn:
            row = conn.execute(
                "SELECT results_json FROM search_results WHERE query_hash = ? AND expires_at > CURRENT_TIMESTAMP",
                (qhash,),
            ).fetchone()

        if not row:
            return None

        with contextlib.closing(self.get_connection()) as conn:
            conn.execute(
                "UPDATE search_results SET hit_count = hit_count + 1, last_accessed = CURRENT_TIMESTAMP WHERE query_hash = ?",
                (qhash,),
            )
            conn.commit()

        data_list = json.loads(row["results_json"])
        records = []
        for data_dict in data_list:
            if "cross_references" in data_dict:
                data_dict["cross_references"] = [
                    CrossReference(**cr) for cr in data_dict["cross_references"]
                ]
            records.append(PatentRecord(**data_dict))
        return records

    def save_search_results(
        self, query: str, records: list[PatentRecord], sources: Optional[list[str]] = None
    ) -> None:
        qhash = _query_hash(query)
        data = json.dumps([dataclasses.asdict(r) for r in records])
        with contextlib.closing(self.get_connection()) as conn:
            with conn:
                conn.execute(
                    """INSERT OR REPLACE INTO search_results
                       (query_hash, query_text, results_json, result_count, sources_queried, expires_at, hit_count)
                       VALUES (?, ?, ?, ?, ?, datetime('now', '+30 days'), 0)""",
                    (qhash, query, data, len(records), json.dumps(sources or [])),
                )

    def is_cache_valid(self, query: str) -> bool:
        """Check if a cached search result exists and has not expired."""
        qhash = _query_hash(query)
        with contextlib.closing(self.get_connection()) as conn:
            row = conn.execute(
                "SELECT 1 FROM search_results WHERE query_hash = ? AND expires_at > CURRENT_TIMESTAMP",
                (qhash,),
            ).fetchone()
        return row is not None

    # ── collections ──────────────────────────────────────────────────────────

    def save_to_collection(
        self,
        record: PatentRecord,
        source_api: str = "",
        collection_name: str = "default",
        notes: Optional[str] = None,
        tags: Optional[list[str]] = None,
        score_at_save: Optional[int] = None,
    ) -> None:
        norm_id = _normalize_patent_id(record.id)
        record_copy = dataclasses.replace(record, id=norm_id)
        _source = source_api or _infer_source(norm_id)
        _tags = json.dumps(tags or [])
        data = json.dumps(dataclasses.asdict(record_copy))
        with contextlib.closing(self.get_connection()) as conn:
            with conn:
                conn.execute(
                    """INSERT INTO collections
                       (patent_id, patent_json, source_api, collection_name, notes, tags, score_at_save)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (norm_id, data, _source, collection_name, notes, _tags, score_at_save),
                )

    def get_collection(self, collection_name: str = "default") -> list[PatentRecord]:
        with contextlib.closing(self.get_connection()) as conn:
            rows = conn.execute(
                "SELECT patent_json FROM collections WHERE collection_name = ? ORDER BY saved_at DESC",
                (collection_name,),
            ).fetchall()

        records = []
        for row in rows:
            data_dict = json.loads(row["patent_json"])
            if "cross_references" in data_dict:
                data_dict["cross_references"] = [
                    CrossReference(**cr) for cr in data_dict["cross_references"]
                ]
            records.append(PatentRecord(**data_dict))
        return records

    def collection_count(self, collection_name: str = "default") -> int:
        with contextlib.closing(self.get_connection()) as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM collections WHERE collection_name = ?",
                (collection_name,),
            ).fetchone()
            return row["cnt"] if row else 0

    def get_all_collections(self) -> list[str]:
        """Return a list of all distinct collection names."""
        with contextlib.closing(self.get_connection()) as conn:
            rows = conn.execute(
                "SELECT DISTINCT collection_name FROM collections ORDER BY collection_name"
            ).fetchall()
        return [r["collection_name"] for r in rows]

    def clear_collection(self, collection_name: Optional[str] = None) -> None:
        with contextlib.closing(self.get_connection()) as conn:
            with conn:
                if collection_name:
                    conn.execute(
                        "DELETE FROM collections WHERE collection_name = ?",
                        (collection_name,),
                    )
                else:
                    conn.execute("DELETE FROM collections")

    # ── citations ────────────────────────────────────────────────────────────

    def get_citations(self, patent_id: str) -> Optional[dict]:
        patent_id = _normalize_patent_id(patent_id)
        with contextlib.closing(self.get_connection()) as conn:
            row = conn.execute(
                "SELECT * FROM citations WHERE patent_id = ?",
                (patent_id,),
            ).fetchone()
        return dict(row) if row else None

    def save_citations(
        self,
        patent_id: str,
        cited_by: Optional[list[str]] = None,
        cites: Optional[list[str]] = None,
        family_members: Optional[list[str]] = None,
        family_id: Optional[str] = None,
        data_source: str = "web",
    ) -> None:
        patent_id = _normalize_patent_id(patent_id)
        _cited_by = json.dumps(cited_by or [])
        _cites = json.dumps(cites or [])
        _family = json.dumps(family_members or [])
        _count = len(cited_by or [])
        with contextlib.closing(self.get_connection()) as conn:
            with conn:
                conn.execute(
                    """INSERT OR REPLACE INTO citations
                       (patent_id, cited_by, cites, family_members, family_id, citation_count, updated_at, data_source)
                       VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)""",
                    (patent_id, _cited_by, _cites, _family, family_id, _count, data_source),
                )

    # ── search_history ───────────────────────────────────────────────────────

    def add_search_history(
        self,
        query_text: str,
        result_count: Optional[int] = None,
        sources: Optional[list[str]] = None,
        execution_time_ms: Optional[int] = None,
        cache_hit: bool = False,
        tui_mode: bool = False,
    ) -> int:
        qhash = _query_hash(query_text)
        with contextlib.closing(self.get_connection()) as conn:
            with conn:
                cursor = conn.execute(
                    """INSERT INTO search_history
                       (query_text, query_hash, result_count, sources, execution_time_ms, cache_hit, tui_mode)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (query_text, qhash, result_count, json.dumps(sources or []), execution_time_ms, cache_hit, tui_mode),
                )
                return cursor.lastrowid

    def get_search_history(self, limit: int = 50) -> list[dict]:
        with contextlib.closing(self.get_connection()) as conn:
            rows = conn.execute(
                "SELECT * FROM search_history ORDER BY searched_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def autocomplete_queries(self, prefix: str, limit: int = 10) -> list[str]:
        with contextlib.closing(self.get_connection()) as conn:
            rows = conn.execute(
                """SELECT DISTINCT query_text FROM search_history
                   WHERE query_text LIKE ? AND searched_at > datetime('now', '-30 days')
                   ORDER BY searched_at DESC LIMIT ?""",
                (prefix + "%", limit),
            ).fetchall()
            return [r["query_text"] for r in rows]

    # ── cache_health ─────────────────────────────────────────────────────────

    def record_cache_health(self) -> dict:
        tables = [
            "search_results", "collections", "citations", "search_history",
            "cache_health", "api_metadata", "export_log", "terminal_sessions",
        ]
        table_data = []
        with contextlib.closing(self.get_connection()) as conn:
            with conn:
                for table in tables:
                    try:
                        count = conn.execute(f"SELECT COUNT(*) AS cnt FROM {table}").fetchone()
                        row_count = count[0] if isinstance(count, tuple) else count["cnt"]
                    except Exception:
                        row_count = -1
                    corrupt = 0
                    expired = 0
                    if table == "search_results":
                        try:
                            for row in conn.execute("SELECT results_json FROM search_results").fetchall():
                                try:
                                    json.loads(row[0] if isinstance(row, tuple) else row["results_json"])
                                except (json.JSONDecodeError, TypeError):
                                    corrupt += 1
                        except Exception:
                            pass
                        try:
                            expired = conn.execute(
                                "SELECT COUNT(*) FROM search_results WHERE expires_at < CURRENT_TIMESTAMP"
                            ).fetchone()[0]
                        except Exception:
                            pass

                    db_size = Path(self.db_path).stat().st_size / (1024 * 1024)
                    vacuum_needed = db_size > 1000 or corrupt > 0
                    conn.execute(
                        """INSERT INTO cache_health (table_name, row_count, corrupt_rows, db_size_mb, vacuum_needed)
                           VALUES (?, ?, ?, ?, ?)""",
                        (table, row_count, corrupt, round(db_size, 2), vacuum_needed),
                    )
                    table_data.append({
                        "table": table,
                        "row_count": row_count,
                        "corrupt": corrupt,
                        "expired_rows": expired,
                    })
        return {
            "db_size_mb": round(db_size, 2),
            "tables_checked": len(tables),
            "tables": table_data,
        }

    # ── api_metadata ──────────────────────────────────────────────────────────

    def get_all_source_health(self) -> list[dict]:
        with contextlib.closing(self.get_connection()) as conn:
            rows = conn.execute(
                """SELECT source_name, base_url, auth_type, rate_limit_per_minute,
                          requests_this_hour, last_request_at, last_error_at,
                          last_error_code, consecutive_errors, circuit_open
                   FROM api_metadata ORDER BY source_name"""
            ).fetchall()
            return [dict(r) for r in rows]

    def get_api_metadata(self, source_name: str) -> Optional[dict]:
        with contextlib.closing(self.get_connection()) as conn:
            row = conn.execute(
                "SELECT * FROM api_metadata WHERE source_name = ?",
                (source_name,),
            ).fetchone()
            return dict(row) if row else None

    def upsert_api_metadata(self, source_name: str, **kwargs) -> None:
        fields = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values())
        with contextlib.closing(self.get_connection()) as conn:
            with conn:
                conn.execute(
                    f"INSERT OR REPLACE INTO api_metadata (source_name, {', '.join(kwargs.keys())}) "
                    f"VALUES (?, {', '.join('?' for _ in kwargs)})",
                    (source_name, *values),
                )

    # ── export_log ───────────────────────────────────────────────────────────

    def log_export(
        self,
        export_format: str,
        file_path: str,
        collection_name: Optional[str] = None,
        record_count: int = 0,
        file_size_bytes: Optional[int] = None,
        cli_mode: bool = True,
    ) -> int:
        with contextlib.closing(self.get_connection()) as conn:
            with conn:
                cursor = conn.execute(
                    """INSERT INTO export_log
                       (export_format, file_path, collection_name, record_count, file_size_bytes, cli_mode)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (export_format, file_path, collection_name, record_count, file_size_bytes, cli_mode),
                )
                return cursor.lastrowid

    # ── terminal_sessions ────────────────────────────────────────────────────

    def create_terminal_session(self, session_id: str) -> None:
        with contextlib.closing(self.get_connection()) as conn:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO terminal_sessions (session_id) VALUES (?)",
                    (session_id,),
                )

    def update_terminal_session(self, session_id: str, **kwargs) -> None:
        fields = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values())
        with contextlib.closing(self.get_connection()) as conn:
            with conn:
                conn.execute(
                    f"UPDATE terminal_sessions SET {fields}, last_activity = CURRENT_TIMESTAMP WHERE session_id = ?",
                    (*values, session_id),
                )

    def get_active_session(self) -> Optional[dict]:
        with contextlib.closing(self.get_connection()) as conn:
            row = conn.execute(
                "SELECT * FROM terminal_sessions WHERE is_active = TRUE ORDER BY last_activity DESC LIMIT 1",
            ).fetchone()
            return dict(row) if row else None

    def close_terminal_session(self, session_id: str) -> None:
        with contextlib.closing(self.get_connection()) as conn:
            with conn:
                conn.execute(
                    "UPDATE terminal_sessions SET is_active = FALSE, last_activity = CURRENT_TIMESTAMP WHERE session_id = ?",
                    (session_id,),
                )

    # ── enrichment_cache (legacy) ────────────────────────────────────────────

    def get_enrichment_cache(self, patent_id: str) -> Optional[list[CrossReference]]:
        patent_id = _normalize_patent_id(patent_id)
        with contextlib.closing(self.get_connection()) as conn:
            row = conn.execute(
                "SELECT cross_refs_json FROM enrichment_cache WHERE patent_id = ? AND enriched_at > datetime('now', '-7 days')",
                (patent_id,),
            ).fetchone()

        if not row:
            return None

        data_list = json.loads(row["cross_refs_json"])
        return [CrossReference(**cr) for cr in data_list]

    def save_enrichment_cache(self, patent_id: str, refs: list[CrossReference]) -> None:
        patent_id = _normalize_patent_id(patent_id)
        data = json.dumps([dataclasses.asdict(r) for r in refs])
        with contextlib.closing(self.get_connection()) as conn:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO enrichment_cache (patent_id, cross_refs_json, enriched_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                    (patent_id, data),
                )

    # ── embeddings ───────────────────────────────────────────────────────────

    def save_embedding(self, patent_id: str, embedding: list[float]) -> None:
        patent_id = _normalize_patent_id(patent_id)
        with contextlib.closing(self.get_connection()) as conn:
            with conn:
                conn.execute(
                    """INSERT OR REPLACE INTO embeddings (patent_id, embedding_json)
                       VALUES (?, ?)""",
                    (patent_id, json.dumps(embedding)),
                )

    def get_embedding(self, patent_id: str) -> list[float] | None:
        patent_id = _normalize_patent_id(patent_id)
        with contextlib.closing(self.get_connection()) as conn:
            row = conn.execute(
                "SELECT embedding_json FROM embeddings WHERE patent_id = ?",
                (patent_id,),
            ).fetchone()
            if row:
                return json.loads(row["embedding_json"])
            return None

    def get_all_embeddings(self) -> dict[str, list[float]]:
        with contextlib.closing(self.get_connection()) as conn:
            rows = conn.execute(
                "SELECT patent_id, embedding_json FROM embeddings"
            ).fetchall()
            return {r["patent_id"]: json.loads(r["embedding_json"]) for r in rows}

    # ── eviction ─────────────────────────────────────────────────────────────

    def enforce_eviction_policy(self, max_db_mb: int = 1000) -> dict:
        stats = {"deleted_expired": 0, "deleted_lru": 0, "deleted_history": 0, "db_size_mb": 0.0, "vacuum_freed_mb": 0.0}

        with contextlib.closing(self.get_connection()) as conn:
            with conn:
                cursor = conn.execute(
                    "DELETE FROM search_results WHERE expires_at < CURRENT_TIMESTAMP"
                )
                stats["deleted_expired"] = cursor.rowcount

                cursor = conn.execute(
                    "DELETE FROM search_history WHERE searched_at < datetime('now', '-1 year')"
                )
                stats["deleted_history"] = cursor.rowcount

        db_size = Path(self.db_path).stat().st_size / (1024 * 1024)
        stats["db_size_mb"] = round(db_size, 2)

        if db_size > max_db_mb:
            with contextlib.closing(self.get_connection()) as conn:
                with conn:
                    excess_mb = db_size - max_db_mb
                    target_patents = int((excess_mb / db_size) * 10_000) + 100
                    cursor = conn.execute(
                        """DELETE FROM search_results WHERE query_hash IN (
                            SELECT query_hash FROM search_results
                            ORDER BY hit_count ASC, last_accessed ASC
                            LIMIT ?
                        )""",
                        (target_patents,),
                    )
                    stats["deleted_lru"] = cursor.rowcount

            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")

            vacuum_result = self.vacuum()
            stats["vacuum_freed_mb"] = round(vacuum_result["freed_bytes"] / (1024 * 1024), 2)

        return stats

    def vacuum(self) -> dict:
        """Run SQLite VACUUM to reclaim disk space. Returns freed bytes estimate."""
        with contextlib.closing(self.get_connection()) as conn:
            before = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
            conn.execute("VACUUM")
            after = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
        return {"freed_bytes": before - after, "before_bytes": before, "after_bytes": after}


def _infer_source(patent_id: str) -> str:
    prefix = _normalize_patent_id(patent_id)[:2].upper()
    mapping = {"US": "uspto", "EP": "epo", "WO": "wipo", "JP": "jpo", "CN": "cnipa"}
    return mapping.get(prefix, "web")
