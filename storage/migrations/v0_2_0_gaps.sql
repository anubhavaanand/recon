-- v0.2.0: Table renames, new columns, FTS5 index naming

-- Rename scraper_metadata -> api_metadata
ALTER TABLE scraper_metadata RENAME TO api_metadata;

-- Recreate index on renamed table
CREATE INDEX IF NOT EXISTS idx_api_metadata_circuit ON api_metadata(circuit_open);
DROP INDEX IF EXISTS idx_scraper_metadata_circuit;

-- Add hit_count to collections
ALTER TABLE collections ADD COLUMN hit_count INTEGER NOT NULL DEFAULT 0;

-- Recreate FTS5 index with correct name
DROP TABLE IF EXISTS idx_collections_tags;
CREATE VIRTUAL TABLE IF NOT EXISTS idx_collections_tags USING fts5(
    tags,
    content='collections',
    content_rowid='id',
    tokenize='porter unicode61'
);

-- Drop old FTS5 table and triggers
DROP TRIGGER IF EXISTS collections_tags_ai;
DROP TRIGGER IF EXISTS collections_tags_ad;
DROP TRIGGER IF EXISTS collections_tags_au;
DROP TABLE IF EXISTS collections_tags_fts;

-- Recreate triggers for new FTS5 name
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
