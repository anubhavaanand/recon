import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

MIGRATIONS = [
    ("0.1.0", "v0_1_0_initial.sql"),
    ("0.2.0", "v0_2_0_gaps.sql"),
]


def get_current_version(conn: sqlite3.Connection) -> str:
    try:
        row = conn.execute(
            "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else "0.0.0"
    except Exception:
        return "0.0.0"


def migrate(db_path: str, target_version: str | None = None) -> list[str]:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.executescript(
        "CREATE TABLE IF NOT EXISTS schema_version (version TEXT PRIMARY KEY);"
    )

    current = get_current_version(conn)

    # Bootstrap check: If the DB was initialized with the v0.2.0 schema directly,
    # we can set current version to '0.2.0' to prevent executing legacy migration scripts.
    if current == "0.0.0":
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='api_metadata'"
            ).fetchone()
            if row and row[0] > 0:
                conn.execute(
                    "INSERT OR REPLACE INTO schema_version (version) VALUES ('0.2.0')"
                )
                conn.commit()
                current = "0.2.0"
        except Exception:
            pass

    applied: list[str] = []

    for version, filename in MIGRATIONS:
        if version > current:
            if target_version and version > target_version:
                break

            # Special check for v0.2.0: if api_metadata already exists,
            # we don't need to run v0_2_0_gaps.sql because the DB is already
            # at or beyond v0.2.0 structure.
            if version == "0.2.0":
                try:
                    row = conn.execute(
                        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='api_metadata'"
                    ).fetchone()
                    if row and row[0] > 0:
                        conn.execute(
                            "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                            (version,),
                        )
                        conn.commit()
                        applied.append(version)
                        current = version
                        continue
                except Exception:
                    pass

            sql_path = MIGRATIONS_DIR / filename
            if not sql_path.exists():
                continue
            conn.executescript(sql_path.read_text())
            conn.execute(
                "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                (version,),
            )
            conn.commit()
            applied.append(version)

    conn.close()
    return applied


def validate(db_path: str) -> list[str]:
    conn = sqlite3.connect(db_path)
    tables = [
        "search_results", "collections", "citations", "search_history",
        "cache_health", "api_metadata", "export_log", "terminal_sessions",
        "schema_version",
    ]
    missing = []
    for table in tables:
        row = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        if row[0] == 0:
            missing.append(table)
    conn.close()
    return missing


if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "recon_cache.db"
    applied = migrate(db_path)
    if applied:
        print(f"Applied migrations: {', '.join(applied)}")
    else:
        print("Already up to date.")
    missing = validate(db_path)
    if missing:
        print(f"Missing tables: {', '.join(missing)}")
    else:
        print("All tables present.")
