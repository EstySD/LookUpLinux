"""SQLite store for looked-up words: versioned schema, data path, atomic counter (DATA-01).

Privacy rule (V7): this module never prints or logs. Exception messages carry
versions and type names only, never word, context or translation text.
"""
import os
import random
import sqlite3
import time
from pathlib import Path

DB_ENV = "LOOKUP_DB"
CONTEXT_MAX_CHARS = 500  # D-19
_MIN_SQLITE = (3, 35, 0)  # RETURNING
_WAL_RETRIES = 50


class SchemaTooNewError(RuntimeError):
    """The database was written by a newer version of the program."""


class MigrationError(RuntimeError):
    """A migration step failed; the database was rolled back."""


def _v1(conn):
    conn.execute(
        "CREATE TABLE words ("
        "word TEXT PRIMARY KEY, "
        "translation TEXT, "
        "context TEXT, "
        "count INTEGER NOT NULL DEFAULT 1, "
        "first_seen INTEGER NOT NULL, "
        "last_seen INTEGER NOT NULL, "
        "lemma TEXT)"
    )


# A step takes the connection, runs inside the caller's transaction, never commits.
MIGRATIONS = (_v1,)
CURRENT_VERSION = len(MIGRATIONS)


def default_db_path() -> Path:
    """Resolve the database path (D-11). Creates nothing on disk."""
    explicit = os.environ.get(DB_ENV)
    if explicit:
        return Path(explicit)
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg and os.path.isabs(xdg):
        return Path(xdg) / "lookup" / "lookup.db"
    return Path.home() / ".local" / "share" / "lookup" / "lookup.db"


def _connect(path, timeout):
    """Open an autocommit connection with busy_timeout; no schema or journal work."""
    if sqlite3.sqlite_version_info < _MIN_SQLITE:
        raise RuntimeError(
            "SQLite >= %d.%d.%d required (RETURNING)" % _MIN_SQLITE
        )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    conn = sqlite3.connect(path, timeout=timeout, isolation_level=None)
    try:
        conn.execute("PRAGMA busy_timeout=%d" % int(timeout * 1000))
    except BaseException:
        conn.close()
        raise
    return conn


def _ensure_wal(conn):
    """Switch to WAL once, read-first and retrying on 'locked' (Pitfall 1).

    Must run outside a transaction.
    """
    for _ in range(_WAL_RETRIES):
        try:
            if conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal":
                return
            row = conn.execute("PRAGMA journal_mode=WAL").fetchone()
            if row is not None and str(row[0]).lower() == "wal":
                return
            raise sqlite3.OperationalError("could not switch database to WAL")
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower():
                raise
            time.sleep(random.uniform(0.005, 0.05))
    raise sqlite3.OperationalError("could not switch database to WAL")


def _clean_text(value, limit=None):
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("text must be str, got " + type(value).__name__)
    value = value.strip()
    if not value:
        return None
    if limit is not None:
        value = value[:limit]
    return value


def upsert_word(conn, word, translation=None, context=None, now=None) -> int:
    """Count one search of `word` and return the new counter value.

    `word` is the key from lookup.normalize.normalize(); the store does not
    normalise. Empty context/translation never overwrite stored values.
    """
    if not isinstance(word, str):
        raise TypeError("word must be str, got " + type(word).__name__)
    word = word.strip()
    if not word:
        raise ValueError("word must not be empty")
    translation = _clean_text(translation)
    context = _clean_text(context, CONTEXT_MAX_CHARS)
    if now is None:
        now = int(time.time())
    cur = conn.execute(
        "INSERT INTO words (word, translation, context, first_seen, last_seen) "
        "VALUES (?, NULLIF(?, ''), NULLIF(?, ''), ?, ?) "
        "ON CONFLICT(word) DO UPDATE SET "
        "count = words.count + 1, "
        "last_seen = excluded.last_seen, "
        "translation = COALESCE(NULLIF(excluded.translation, ''), words.translation), "
        "context = COALESCE(NULLIF(excluded.context, ''), words.context) "
        "RETURNING count",
        (word, translation, context, now, now),
    )
    rows = cur.fetchall()
    return int(rows[0][0])
