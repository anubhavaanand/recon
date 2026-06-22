import sqlite3
import json
import dataclasses
from pathlib import Path
from core.models import PatentRecord, CrossReference

SCHEMA = """
CREATE TABLE IF NOT EXISTS document_content (
    id TEXT PRIMARY KEY,
    content TEXT
);

CREATE TABLE IF NOT EXISTS status_metadata (
    id TEXT PRIMARY KEY,
    status TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS citations (
    patent_id TEXT,
    cited_patent_id TEXT
);

CREATE TABLE IF NOT EXISTS family_links (
    id TEXT,
    family_id TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, family_id)
);

CREATE TABLE IF NOT EXISTS collections (
    patent_id TEXT PRIMARY KEY,
    data TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS search_results (
    query TEXT PRIMARY KEY,
    results TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

class CacheDatabase:
    def __init__(self, db_path: str = "recon_cache.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite cache schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA)

    def get_connection(self) -> sqlite3.Connection:
        """Return a configured connection with row_factory set."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_to_collection(self, record: PatentRecord):
        """Save a patent record to the local collection."""
        with self.get_connection() as conn:
            data = json.dumps(dataclasses.asdict(record))
            conn.execute(
                "INSERT OR REPLACE INTO collections (patent_id, data) VALUES (?, ?)",
                (record.id, data)
            )
            conn.commit()

    def clear_collection(self) -> None:
        """Remove all patents from the collection."""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM collections")
            conn.commit()

    def collection_count(self) -> int:
        """Return the number of patents in the collection."""
        with self.get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS cnt FROM collections").fetchone()
            return row["cnt"] if row else 0

    def get_collection(self) -> list[PatentRecord]:
        """Retrieve all patent records in the local collection."""
        with self.get_connection() as conn:
            rows = conn.execute("SELECT data FROM collections ORDER BY timestamp DESC").fetchall()
        
        records = []
        for row in rows:
            data_dict = json.loads(row["data"])
            # Reconstruct CrossReference objects if present
            if "cross_references" in data_dict:
                data_dict["cross_references"] = [CrossReference(**cr) for cr in data_dict["cross_references"]]
            records.append(PatentRecord(**data_dict))
        return records

    def get_cached_search(self, query: str) -> list[PatentRecord] | None:
        """Retrieve cached search results if they are less than 30 days old."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT results FROM search_results WHERE query = ? AND timestamp > datetime('now', '-30 days')",
                (query,)
            ).fetchone()
            
        if not row:
            return None
            
        data_list = json.loads(row["results"])
        records = []
        for data_dict in data_list:
            if "cross_references" in data_dict:
                data_dict["cross_references"] = [CrossReference(**cr) for cr in data_dict["cross_references"]]
            records.append(PatentRecord(**data_dict))
        return records

    def save_search_results(self, query: str, records: list[PatentRecord]):
        """Save search results to the cache."""
        with self.get_connection() as conn:
            data = json.dumps([dataclasses.asdict(r) for r in records])
            conn.execute(
                "INSERT OR REPLACE INTO search_results (query, results, timestamp, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (query, data)
            )
            conn.commit()
