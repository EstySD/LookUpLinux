"""SQLite store for looked-up words: versioned schema, data path, atomic counter (DATA-01).

Privacy rule (V7): this module never prints or logs. Exception messages carry
versions and type names only, never word, context or translation text.
"""
import os
import random
import re
import sqlite3
import time
from pathlib import Path

DB_ENV = "LOOKUP_DB"
CONTEXT_MAX_CHARS = 500  # D-19
_MIN_SQLITE = (3, 35, 0)  # RETURNING
# Upper bound, in seconds, on waiting for a locked database during open_store
# steps 3-4 (version read plus WAL switch; hotkey latency budget). The
# effective deadline is min(timeout, _WAL_MAX_WAIT).
_WAL_MAX_WAIT = 2.0
# busy_timeout (ms) for a single attempt in steps 3-4; the retry loop owns the waiting.
_WAL_ATTEMPT_BUSY_MS = 50
# How often open_store re-snapshots when another process changes the schema
# version between the version read and BEGIN IMMEDIATE (D-14).
_MIGRATE_ATTEMPTS = 5


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


# A step takes a guarded connection (_StepConnection: execute, executemany,
# executescript) and runs inside the caller's transaction. It must not control
# that transaction: BEGIN/COMMIT/END/ROLLBACK and commit()/rollback() raise
# MigrationError, and open_store re-checks after every step that the
# transaction is still open.
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


def _until_unlocked(attempt, deadline, what):
    """Call attempt() until it stops failing with 'locked' or deadline passes.

    The caller sets a short busy_timeout (_WAL_ATTEMPT_BUSY_MS) so SQLite's
    busy handler cannot stretch a single attempt past the deadline.
    """
    last = None
    while True:
        try:
            return attempt()
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower():
                raise
            last = exc
        if time.monotonic() >= deadline:
            raise sqlite3.OperationalError(
                "could not %s: database is locked" % what
            ) from last
        time.sleep(random.uniform(0.005, 0.05))


def _read_version(conn, deadline):
    return _until_unlocked(
        lambda: conn.execute("PRAGMA user_version").fetchone()[0],
        deadline,
        "read the schema version",
    )


def _ensure_wal(conn, deadline):
    """Switch to WAL once, read-first and retrying on 'locked' (Pitfall 1, D-20).

    Must run outside a transaction, with the short per-attempt busy_timeout
    set by open_store. Gives up at deadline.
    """

    def attempt():
        if conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal":
            return
        row = conn.execute("PRAGMA journal_mode=WAL").fetchone()
        if row is not None and str(row[0]).lower() == "wal":
            return
        raise sqlite3.OperationalError("could not switch database to WAL")

    _until_unlocked(attempt, deadline, "switch database to WAL")


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
    elif isinstance(now, bool) or not isinstance(now, (int, float)):
        raise TypeError("now must be int, got " + type(now).__name__)
    else:
        now = int(now)  # D-13: INTEGER Unix seconds, also for now=time.time()
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


_SQL_LEAD = re.compile(r"(?:\s+|--[^\n]*(?:\n|\Z)|/\*.*?(?:\*/|\Z))*", re.S)
_SQL_WORDS = re.compile(r"(\w+)(?:\s+(\w+))?(?:\s+(\w+))?")
_TX_CONTROL = frozenset(("BEGIN", "COMMIT", "END", "ROLLBACK"))


def _sql_body(sql):
    """`sql` without leading whitespace and comments."""
    return sql[_SQL_LEAD.match(sql).end():]


def _check_step_sql(sql):
    """Reject statements that would end or restart the migration transaction."""
    m = _SQL_WORDS.match(_sql_body(sql))
    if m is None:
        return
    words = [w.upper() for w in m.groups() if w]
    if words[0] not in _TX_CONTROL:
        return
    if words[0] == "ROLLBACK" and "TO" in words[1:]:
        return  # ROLLBACK [TRANSACTION] TO [SAVEPOINT] name stays inside the transaction
    raise MigrationError("a migration step must not run %s" % words[0])


class _StepConnection:
    """The connection a migration step receives: no transaction control.

    executescript() runs the script statement by statement through execute(),
    because sqlite3's own executescript() COMMITs a pending transaction first.
    """

    __slots__ = ("_conn",)
    _PASS_THROUGH = frozenset(
        ("create_function", "create_aggregate", "create_collation", "total_changes")
    )

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, parameters=()):
        _check_step_sql(sql)
        return self._conn.execute(sql, parameters)

    def executemany(self, sql, seq_of_parameters):
        _check_step_sql(sql)
        return self._conn.executemany(sql, seq_of_parameters)

    def executescript(self, script):
        buf = []
        for ch in script:
            buf.append(ch)
            if ch == ";":
                stmt = "".join(buf)
                if sqlite3.complete_statement(stmt):
                    self._run_script_part(stmt)
                    buf = []
        self._run_script_part("".join(buf))

    def _run_script_part(self, stmt):
        if _sql_body(stmt).strip(" \t\r\n;"):
            self.execute(stmt)

    @property
    def in_transaction(self):
        return self._conn.in_transaction

    def commit(self):
        raise MigrationError("a migration step must not commit")

    def rollback(self):
        raise MigrationError("a migration step must not roll back")

    def __getattr__(self, name):
        if name in _StepConnection._PASS_THROUGH:
            return getattr(self._conn, name)
        raise AttributeError(
            "migration steps may not use Connection.%s" % name
        )


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
        # Steps 3-4 share one wall-clock budget, min(timeout, _WAL_MAX_WAIT),
        # even under an EXCLUSIVE lock that blocks the version read itself.
        deadline = time.monotonic() + max(0.0, min(timeout, _WAL_MAX_WAIT))
        conn.execute("PRAGMA busy_timeout=%d" % _WAL_ATTEMPT_BUSY_MS)
        try:
            # 3
            v = _read_version(conn, deadline)
            target = len(migrations)
            if v > target:
                raise SchemaTooNewError(
                    "База версии %d новее программы (знает до %d): обновите программу."
                    % (v, target)
                )
            # 4
            _ensure_wal(conn, deadline)
        finally:
            conn.execute("PRAGMA busy_timeout=%d" % int(timeout * 1000))
        conn.execute("PRAGMA synchronous=NORMAL")
    except BaseException:
        conn.close()
        raise
    # 5
    if v == target:
        return conn
    tmp = None
    try:
        for _attempt in range(_MIGRATE_ATTEMPTS):
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
            if locked_v != v and 0 < locked_v < target:
                # Another process moved the schema to locked_v after step 3, and
                # we still have steps to run. D-14: existing data is never
                # migrated without a backup of exactly that version, so drop the
                # lock and snapshot locked_v outside the transaction.
                conn.execute("ROLLBACK")
                _remove_quietly(tmp)
                tmp = None
                v = locked_v
                continue
            if tmp is not None:
                if locked_v == v:
                    os.replace(tmp, path.with_name("%s.bak-v%d" % (path.name, v)))
                else:
                    _remove_quietly(tmp)  # locked_v == target: nothing to migrate
                tmp = None
            guarded = _StepConnection(conn)
            for number, step in enumerate(migrations[locked_v:], locked_v + 1):
                step(guarded)
                if not conn.in_transaction:
                    raise MigrationError(
                        "migration step to v%d ended the transaction" % number
                    )
            conn.execute("PRAGMA user_version = %d" % target)
            conn.execute("COMMIT")
            # 9
            return conn
        raise MigrationError(
            "schema version kept changing during open (last v%d); reopen to retry" % v
        )
    except (SchemaTooNewError, MigrationError):
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
