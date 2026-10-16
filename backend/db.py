import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS family_members (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    relation   TEXT    NOT NULL,
    birth_year INTEGER NOT NULL,
    status     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id   INTEGER NOT NULL REFERENCES family_members(id),
    doc_type    TEXT    NOT NULL,
    expiry_date TEXT    NOT NULL
    -- Never store ID numbers, passport numbers, or similar identifiers.
);

CREATE TABLE IF NOT EXISTS tasks (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    title     TEXT    NOT NULL,
    due_date  TEXT    NOT NULL,
    member_id INTEGER REFERENCES family_members(id),
    done      INTEGER NOT NULL DEFAULT 0
);
"""


def get_connection(db_path=None):
    """Open the SQLite database. Path comes from the argument, then GLEAN_DB_PATH, then glean.db."""
    path = db_path or os.environ.get("GLEAN_DB_PATH", "glean.db")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    """Create the tables if they don't exist yet."""
    conn.executescript(SCHEMA)
    conn.commit()