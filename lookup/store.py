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
# Upper bound on the whole WAL-switch retry loop, in seconds (hotkey latency
# budget). The effective deadline is min(timeout, _WAL_MAX_WAIT).
_WAL_MAX_WAIT = 2.0
# busy_timeout (ms) for a single WAL-switch attempt; the retry loop owns the waiting.
_WAL_ATTEMPT_BUSY_MS = 50


class SchemaTooNewError(RuntimeError):
    """The database was written by a newer version of the program."""


class MigrationError(RuntimeError):
    """Migrating the database failed (snapshot, write lock or a step); nothing was committed.

    Open failures that happen before any migration work (locked or corrupt
    file, failed WAL switch) are raised as the underlying sqlite3.Error or
    OSError instead.
    """


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


def _ensure_wal(conn, timeout):
    """Switch to WAL once, read-first and retrying on 'locked' (Pitfall 1, D-20).

    Must run outside a transaction. The whole loop is bounded by wall-clock
    time, min(timeout, _WAL_MAX_WAIT): each attempt runs with a short
    busy_timeout so SQLite's busy handler cannot multiply the wait. The
    connection's busy_timeout is restored afterwards.
    """
    deadline = time.monotonic() + max(0.0, min(timeout, _WAL_MAX_WAIT))
    conn.execute("PRAGMA busy_timeout=%d" % _WAL_ATTEMPT_BUSY_MS)
    try:
        last = None
        while True:
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
                last = exc
            if time.monotonic() >= deadline:
                raise sqlite3.OperationalError(
                    "could not switch database to WAL: database is locked"
                ) from last
            time.sleep(random.uniform(0.005, 0.05))
    finally:
        conn.execute("PRAGMA busy_timeout=%d" % int(timeout * 1000))


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


def _snapshot(conn, path, old_version) -> Path:
    """Copy the database to a temporary file beside it and return that path.

    Uses Connection.backup (consistent, includes WAL content). Call it only
    while `conn` has NO open transaction: a backup from the connection that
    holds BEGIN IMMEDIATE on a WAL database hangs forever.
    """
    path = Path(path)
    tmp = path.with_name("%s.bak-v%d.%d.tmp" % (path.name, old_version, os.getpid()))
    dst = sqlite3.connect(tmp)
    try:
        try:
            conn.backup(dst)
        finally:
            dst.close()
    except BaseException:
        _remove_quietly(tmp)
        raise
    return tmp


def _remove_quietly(path):
    if path is None:
        return
    try:
        os.remove(path)
    except OSError:
        pass


def open_store(path=None, migrations=MIGRATIONS, timeout=5.0):
    """Open (creating and migrating if needed) the word database.

    The numbered order below is locked (D-14): version check before any write,
    snapshot before the write lock, all steps plus the version bump in one
    transaction.

    Errors:
    - SchemaTooNewError: the database is newer than this program; untouched.
    - sqlite3.Error / OSError, unwrapped: the database could not be opened
      (locked, corrupt, not a database, unwritable directory). Steps 1-5.
    - MigrationError: migrating failed (snapshot, write lock or a step);
      nothing was committed. Steps 6-7; the cause is in __cause__.
    """
    # 1
    path = Path(path) if path is not None else default_db_path()
    # 2
    conn = _connect(path, timeout)
    try:
        # 3
        v = conn.execute("PRAGMA user_version").fetchone()[0]
        target = len(migrations)
        if v > target:
            raise SchemaTooNewError(
                "База версии %d новее программы (знает до %d): обновите программу."
                % (v, target)
            )
        # 4
        _ensure_wal(conn, timeout)
        conn.execute("PRAGMA synchronous=NORMAL")
    except BaseException:
        conn.close()
        raise
    # 5
    if v == target:
        return conn
    tmp = None
    try:
        # 6
        if v > 0:
            tmp = _snapshot(conn, path, v)
        # 7
        conn.execute("BEGIN IMMEDIATE")
        locked_v = conn.execute("PRAGMA user_version").fetchone()[0]
        if locked_v > target:
            raise SchemaTooNewError(
                "База версии %d новее программы (знает до %d): обновите программу."
                % (locked_v, target)
            )
        if tmp is not None:
            if locked_v == v:
                os.replace(tmp, path.with_name("%s.bak-v%d" % (path.name, v)))
            else:
                _remove_quietly(tmp)
            tmp = None
        for step in migrations[locked_v:]:
            step(conn)
        conn.execute("PRAGMA user_version = %d" % target)
        conn.execute("COMMIT")
        # 9
        return conn
    except SchemaTooNewError:
        _abort(conn, tmp)
        raise
    except Exception as exc:
        # 8
        _abort(conn, tmp)
        raise MigrationError(type(exc).__name__ + ": " + str(exc)) from exc
    except BaseException:
        _abort(conn, tmp)
        raise


def _abort(conn, tmp):
    try:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
    except sqlite3.Error:
        pass
    conn.close()
    _remove_quietly(tmp)
