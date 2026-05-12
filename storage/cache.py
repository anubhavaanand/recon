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
    id TEXT,
    citation_id TEXT,
    PRIMARY KEY (id, citation_id)
);

CREATE TABLE IF NOT EXISTS family_links (
    id TEXT,
    family_id TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, family_id)
);

CREATE TABLE IF NOT EXISTS collections (
    id TEXT PRIMARY KEY,
    data TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                "INSERT OR REPLACE INTO collections (id, data) VALUES (?, ?)",
                (record.id, data)
            )
            conn.commit()

    def get_collection(self) -> list[PatentRecord]:
        """Retrieve all patent records in the local collection."""
        with self.get_connection() as conn:
            rows = conn.execute("SELECT data FROM collections ORDER BY added_at DESC").fetchall()
        
        records = []
        for row in rows:
            data_dict = json.loads(row["data"])
            # Reconstruct CrossReference objects if present
            if "cross_references" in data_dict:
                data_dict["cross_references"] = [CrossReference(**cr) for cr in data_dict["cross_references"]]
            records.append(PatentRecord(**data_dict))
        return records
