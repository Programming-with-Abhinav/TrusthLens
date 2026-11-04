"""SQLite persistence module for TrustLens AI (FR-P3).
Provides persistent L1 cache and audit history across server restarts.
"""
import sqlite3
import json
import time
import os
import glob
import hashlib
import uuid
from typing import Any

DB_PATH = os.environ.get("TRUSTLENS_DB_PATH") or os.path.join(os.path.dirname(__file__), "trustlens.db")
MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def init_db():
    with sqlite3.connect(DB_PATH, timeout=30) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trustlens_migration_history (
                version TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                checksum TEXT NOT NULL,
                applied_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trustlens_migration_locks (
                lock_name TEXT PRIMARY KEY,
                owner TEXT NOT NULL,
                acquired_at REAL NOT NULL
            )
        """)

        migration_paths = sorted(
            glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")),
            key=lambda path: os.path.basename(path)
        )
        if not migration_paths:
            raise RuntimeError("No TrustLens migrations found")

        for migration_path in migration_paths:
            filename = os.path.basename(migration_path)
            version = filename.split("_", 1)[0]
            with open(migration_path, "r", encoding="utf-8") as migration_file:
                sql = migration_file.read()

            checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
            previous = conn.execute(
                "SELECT checksum FROM trustlens_migration_history WHERE version = ?",
                (version,),
            ).fetchone()
            if previous:
                if previous[0] != checksum:
                    raise RuntimeError(
                        f"Migration {filename} changed after it was applied"
                    )
                continue

            owner = f"{os.getpid()}:{uuid.uuid4()}"
            try:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("DELETE FROM trustlens_migration_locks")
                conn.execute(
                    "INSERT INTO trustlens_migration_locks(lock_name, owner, acquired_at) VALUES (?, ?, ?)",
                    ("trustlens:migrations", owner, time.time()),
                )

                statements: list[str] = []
                for raw_statement in sql.split(";"):
                    statement: str = "\n".join(
                        line for line in raw_statement.splitlines()
                        if line.strip() and not line.lstrip().startswith("--")
                    ).strip()
                    if statement:
                        statements.append(statement)
                for statement in statements:
                    conn.execute(statement)

                existing_tables = {
                    row[0] for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
                if "cache" in existing_tables:
                    conn.execute("""
                        INSERT OR REPLACE INTO trustlens_cache(key, value, created_at)
                        SELECT key, value, created_at FROM cache
                    """)
                required_tables = ("trustlens_cache",)
                for table_name in required_tables:
                    exists = conn.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (table_name,),
                    ).fetchone()
                    if not exists:
                        raise RuntimeError(
                            f"Migration {filename} did not create required table {table_name}"
                        )

                conn.execute(
                    "INSERT INTO trustlens_migration_history(version, name, checksum, applied_at) VALUES (?, ?, ?, ?)",
                    (version, filename, checksum, time.time()),
                )
                conn.execute(
                    "DELETE FROM trustlens_migration_locks WHERE lock_name=? AND owner=?",
                    ("trustlens:migrations", owner),
                )
                conn.execute("COMMIT")
            except Exception:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise

# Initialize tables upon module import, then purge the retired history surface.
init_db()

def get_cached(key: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM trustlens_cache WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
    except Exception:
        pass
    return None

def set_cached(key: str, value: dict[str, Any]):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO trustlens_cache (key, value, created_at) VALUES (?, ?, ?)",
                (key, json.dumps(value), time.time())
            )
            conn.commit()
    except Exception:
        pass

def count_cache() -> int:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trustlens_cache")
            return cursor.fetchone()[0]
    except Exception:
        return 0

def delete_history_data() -> None:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DROP TABLE IF EXISTS trustlens_history")
            conn.execute("DROP TABLE IF EXISTS history")
            conn.commit()
    except Exception:
        pass

delete_history_data()
