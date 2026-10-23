import faulthandler
import hashlib
import os
import sqlite3
import time
import unittest
from pathlib import Path
from unittest import mock

from lookup import store
from lookup.store import (
    CURRENT_VERSION,
    MIGRATIONS,
    MigrationError,
    SchemaTooNewError,
    open_store,
    upsert_word,
)
from tests._support import make_tempdir


def setUpModule():
    # A snapshot taken inside an open transaction hangs; fail with a traceback instead.
    faulthandler.dump_traceback_later(120, exit=True)


def tearDownModule():
    faulthandler.cancel_dump_traceback_later()


def _add_probe(conn):
    conn.execute("ALTER TABLE words ADD COLUMN probe TEXT")


def _fail(conn):
    raise RuntimeError("boom")


def _make_v1(path, rows):
    conn = open_store(path)
    try:
        for word in rows:
            upsert_word(conn, word, "tr-" + word, "ctx " + word, now=10)
    finally:
        conn.close()


def _columns(conn):
    return [r[1] for r in conn.execute("PRAGMA table_info(words)")]


M2 = MIGRATIONS + (_add_probe,)  # synthetic second schema version (D-19)


class SchemaLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)

    def open(self, *args, **kwargs):
        conn = open_store(*args, **kwargs)
        self.addCleanup(conn.close)
        return conn

    def plain(self, path):
        conn = sqlite3.connect(path, isolation_level=None)
        self.addCleanup(conn.close)
        return conn

    def files(self, directory, pattern):
        return sorted(p.name for p in Path(directory).glob(pattern))

    def test_creates_file_under_missing_data_dir(self):
        expected = Path(os.environ["LOOKUP_DB"])
        self.assertFalse(expected.parent.exists())
        conn = self.open()
        self.assertTrue(expected.is_file())
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], CURRENT_VERSION)

    def test_reopen_keeps_rows_and_wal(self):
        path = self.root / "t.db"
        conn = open_store(path)
        upsert_word(conn, "run", now=1)
        upsert_word(conn, "run", now=2)
        upsert_word(conn, "walk", now=3)
        conn.close()
        conn = self.open(path)
        rows = dict(conn.execute("SELECT word, count FROM words"))
        self.assertEqual(rows, {"run": 2, "walk": 1})
        self.assertEqual(conn.execute("PRAGMA journal_mode").fetchone()[0], "wal")

    def test_up_to_date_open_makes_no_backup(self):
        path = self.root / "t.db"
        _make_v1(path, ["run"])
        conn = self.open(path)
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], CURRENT_VERSION)
        self.assertEqual(self.files(self.root, "*.bak-v*"), [])

    def test_fresh_db_applies_all_steps_without_backup(self):
        path = self.root / "fresh.db"
        conn = self.open(path, migrations=M2)
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 2)
        self.assertIn("probe", _columns(conn))
        self.assertEqual(self.files(self.root, "*.bak-v*"), [])

    def test_old_version_db_migrated_without_losing_words(self):
        path = self.root / "t.db"
        _make_v1(path, ["run", "walk"])
        conn = self.open(path, migrations=M2)
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 2)
        self.assertEqual(dict(conn.execute("SELECT word, count FROM words")), {"run": 1, "walk": 1})
        self.assertIn("probe", _columns(conn))
        backup = self.root / "t.db.bak-v1"
        self.assertTrue(backup.is_file())
        b = self.plain(backup)
        self.assertEqual(dict(b.execute("SELECT word, count FROM words")), {"run": 1, "walk": 1})
        self.assertEqual(b.execute("PRAGMA user_version").fetchone()[0], 1)
        self.assertNotIn("probe", _columns(b))
        self.assertEqual(self.files(self.root, "*.tmp"), [])

    def test_newer_db_refused_untouched(self):
        path = self.root / "newer.db"
        raw = sqlite3.connect(path)
        raw.execute("CREATE TABLE words (word TEXT PRIMARY KEY)")
        raw.execute("INSERT INTO words VALUES ('run')")
        raw.commit()
        raw.execute("PRAGMA user_version = 99")
        raw.commit()
        raw.close()
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaises(SchemaTooNewError) as ctx:
            open_store(path)
        self.assertIn("99", str(ctx.exception))
        self.assertIn(str(CURRENT_VERSION), str(ctx.exception))
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)
        self.assertFalse((self.root / "newer.db-wal").exists())

    def test_failing_step_rolls_back_all_steps(self):
        path = self.root / "t.db"
        _make_v1(path, ["run", "walk"])
        with self.assertRaises(MigrationError):
            open_store(path, migrations=MIGRATIONS + (_add_probe, _fail))
        p = self.plain(path)
        self.assertEqual(p.execute("PRAGMA user_version").fetchone()[0], 1)
        self.assertNotIn("probe", _columns(p))
        self.assertEqual(p.execute("SELECT COUNT(*) FROM words").fetchone()[0], 2)
        p.close()
        conn = self.open(path)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM words").fetchone()[0], 2)

    def test_stale_snapshot_discarded_when_another_process_migrated_first(self):
        path = self.root / "t.db"
        _make_v1(path, ["run", "walk"])
        real = store._snapshot

        def racing(conn, p, old_version):
            tmp = real(conn, p, old_version)
            other = sqlite3.connect(p, isolation_level=None)
            try:
                other.execute("BEGIN IMMEDIATE")
                other.execute("ALTER TABLE words ADD COLUMN probe TEXT")
                other.execute("PRAGMA user_version = 2")
                other.execute("COMMIT")
            finally:
                other.close()
            return tmp

        with mock.patch.object(store, "_snapshot", racing):
            conn = self.open(path, migrations=M2)
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 2)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM words").fetchone()[0], 2)
        self.assertIn("probe", _columns(conn))
        self.assertFalse((self.root / "t.db.bak-v1").exists())
        self.assertEqual(self.files(self.root, "*.tmp"), [])


def _add_probe2(conn):
    conn.execute("ALTER TABLE words ADD COLUMN probe2 TEXT")


M3 = M2 + (_add_probe2,)


class ConcurrentVersionChangeTests(unittest.TestCase):
    """WR-05: data is never migrated without a backup of the version it starts from."""

    def setUp(self):
        self.root = make_tempdir(self)
        self.path = self.root / "t.db"

    def files(self, pattern):
        return sorted(p.name for p in self.root.glob(pattern))

    def bump_to_v2(self, p):
        other = sqlite3.connect(p, isolation_level=None)
        try:
            other.execute("BEGIN IMMEDIATE")
            other.execute("ALTER TABLE words ADD COLUMN probe TEXT")
            other.execute("PRAGMA user_version = 2")
            other.execute("COMMIT")
        finally:
            other.close()

    def test_intermediate_version_is_snapshotted_again(self):
        _make_v1(self.path, ["run", "walk"])
        real = store._snapshot
        calls = []

        def racing(conn, p, old_version):
            calls.append(old_version)
            tmp = real(conn, p, old_version)
            if len(calls) == 1:
                self.bump_to_v2(p)  # an older build migrated v1 -> v2 meanwhile
            return tmp

        with mock.patch.object(store, "_snapshot", racing):
            conn = open_store(self.path, migrations=M3)
        self.addCleanup(conn.close)
        self.assertEqual(calls, [1, 2])
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 3)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM words").fetchone()[0], 2)
        self.assertEqual(self.files("*.bak-v*"), ["t.db.bak-v2"])
        b = sqlite3.connect(self.root / "t.db.bak-v2")
        self.addCleanup(b.close)
        self.assertEqual(b.execute("PRAGMA user_version").fetchone()[0], 2)
        self.assertIn("probe", _columns(b))
        self.assertNotIn("probe2", _columns(b))
        self.assertEqual(b.execute("SELECT COUNT(*) FROM words").fetchone()[0], 2)

    def test_fresh_db_populated_concurrently_gets_backup(self):
        real = store._ensure_wal

        def racing(conn, timeout):
            real(conn, timeout)
            # Another process creates a v1 database with data after our version read.
            other = sqlite3.connect(self.path, isolation_level=None)
            try:
                other.execute("BEGIN IMMEDIATE")
                store._v1(other)
                other.execute(
                    "INSERT INTO words (word, first_seen, last_seen) VALUES ('run', 1, 1)"
                )
                other.execute("PRAGMA user_version = 1")
                other.execute("COMMIT")
            finally:
                other.close()

        with mock.patch.object(store, "_ensure_wal", racing):
            conn = open_store(self.path, migrations=M2)
        self.addCleanup(conn.close)
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 2)
        self.assertEqual(self.files("*.bak-v*"), ["t.db.bak-v1"])
        b = sqlite3.connect(self.root / "t.db.bak-v1")
        self.addCleanup(b.close)
        self.assertEqual(b.execute("SELECT word FROM words").fetchall(), [("run",)])

    def test_endlessly_changing_version_gives_up(self):
        _make_v1(self.path, ["run"])
        real = store._snapshot
        noops = MIGRATIONS + tuple((lambda c: None) for _ in range(9))

        def racing(conn, p, old_version):
            tmp = real(conn, p, old_version)
            other = sqlite3.connect(p, isolation_level=None)
            try:
                other.execute("PRAGMA user_version = %d" % (old_version + 1))
            finally:
                other.close()
            return tmp

        with mock.patch.object(store, "_snapshot", racing):
            with self.assertRaises(MigrationError):
                open_store(self.path, migrations=noops)
        self.assertEqual(self.files("*.tmp"), [])
        self.assertEqual(self.files("*.bak-v*"), [])


class StepTransactionGuardTests(unittest.TestCase):
    """WR-03: a step cannot end the migration transaction."""

    def setUp(self):
        self.root = make_tempdir(self)
        self.path = self.root / "t.db"
        _make_v1(self.path, ["run", "walk"])

    def assert_untouched(self):
        p = sqlite3.connect(self.path, isolation_level=None)
        try:
            self.assertEqual(p.execute("PRAGMA user_version").fetchone()[0], 1)
            self.assertEqual(
                _columns(p),
                ["word", "translation", "context", "count", "first_seen", "last_seen", "lemma"],
            )
            self.assertEqual(p.execute("SELECT COUNT(*) FROM words").fetchone()[0], 2)
        finally:
            p.close()
        conn = open_store(self.path)  # still opens with the real migrations
        conn.close()

    def test_executescript_runs_inside_the_transaction(self):
        # Reviewer's repro: sqlite3's executescript() would COMMIT first and
        # leave column z behind with user_version still 1.
        steps = MIGRATIONS + (
            lambda c: c.executescript("ALTER TABLE words ADD COLUMN z TEXT;"),
            _fail,
        )
        with self.assertRaises(MigrationError):
            open_store(self.path, migrations=steps)
        self.assert_untouched()

    def test_multi_statement_script_with_trigger_migrates(self):
        script = (
            "-- v2\n"
            "ALTER TABLE words ADD COLUMN a TEXT; CREATE INDEX ix_a ON words(a);\n"
            "CREATE TRIGGER tr AFTER INSERT ON words BEGIN "
            "UPDATE words SET a = 'x' WHERE word = NEW.word; END;\n"
            "/* trailing comment */"
        )
        conn = open_store(self.path, migrations=MIGRATIONS + (lambda c: c.executescript(script),))
        self.addCleanup(conn.close)
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 2)
        self.assertIn("a", _columns(conn))
        names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master")}
        self.assertTrue({"ix_a", "tr"} <= names, names)

    def test_transaction_control_rejected(self):
        bad = [
            lambda c: c.commit(),
            lambda c: c.rollback(),
            lambda c: c.execute("COMMIT"),
            lambda c: c.execute("  /* x */ -- y\n end transaction"),
            lambda c: c.execute("ROLLBACK"),
            lambda c: c.execute("BEGIN"),
            lambda c: c.executescript("ALTER TABLE words ADD COLUMN z TEXT; COMMIT;"),
            lambda c: c.cursor(),
        ]
        for i, step in enumerate(bad):
            with self.subTest(i=i):
                with self.assertRaises(MigrationError):
                    open_store(self.path, migrations=MIGRATIONS + (_add_probe, step))
                self.assert_untouched()

    def test_savepoint_rollback_to_allowed(self):
        def step(c):
            c.execute("SAVEPOINT s")
            c.execute("ALTER TABLE words ADD COLUMN gone TEXT")
            c.execute("ROLLBACK TO s")
            c.execute("RELEASE s")
            c.execute("ALTER TABLE words ADD COLUMN probe TEXT")

        conn = open_store(self.path, migrations=MIGRATIONS + (step,))
        self.addCleanup(conn.close)
        self.assertIn("probe", _columns(conn))
        self.assertNotIn("gone", _columns(conn))

    def test_step_that_ends_transaction_out_of_band_is_detected(self):
        captured = []
        real_connect = store._connect

        def connect(path, timeout):
            conn = real_connect(path, timeout)
            captured.append(conn)
            return conn

        def sneaky(c):
            captured[0].execute("COMMIT")

        with mock.patch.object(store, "_connect", connect):
            with self.assertRaises(MigrationError) as ctx:
                open_store(self.path, migrations=MIGRATIONS + (sneaky,))
        self.assertIn("v2", str(ctx.exception))
        self.assert_untouched()


class OpenFailureTests(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)

    def _locked_rollback_db(self):
        """A rollback-journal DB whose SHARED lock is held by another connection."""
        path = self.root / "locked.db"
        raw = sqlite3.connect(path)
        raw.execute("CREATE TABLE t (x)")
        raw.commit()
        raw.close()
        reader = sqlite3.connect(path, isolation_level=None)
        self.addCleanup(reader.close)
        reader.execute("BEGIN")
        reader.execute("SELECT * FROM t").fetchall()
        return path

    def _assert_wal_lock_failure(self, path, timeout, bound):
        start = time.monotonic()
        with self.assertRaises(sqlite3.OperationalError) as ctx:
            open_store(path, timeout=timeout)
        elapsed = time.monotonic() - start
        self.assertLess(elapsed, bound)
        # WR-02: a busy DB is not reported as a migration failure.
        self.assertNotIsInstance(ctx.exception, MigrationError)
        self.assertIn("locked", str(ctx.exception).lower())
        self.assertIsInstance(ctx.exception.__cause__, sqlite3.OperationalError)

    def test_wal_switch_under_lock_fails_fast_with_default_timeout(self):
        # WR-01: was ~50 x busy_timeout (minutes); now bounded by _WAL_MAX_WAIT.
        path = self._locked_rollback_db()
        self._assert_wal_lock_failure(path, 5.0, store._WAL_MAX_WAIT + 1.5)

    def test_wal_switch_deadline_follows_short_timeout(self):
        path = self._locked_rollback_db()
        self._assert_wal_lock_failure(path, 0.3, 1.5)

    def test_not_a_database_raises_sqlite_error_not_migration_error(self):
        path = self.root / "garbage.db"
        path.write_bytes(b"this is not an sqlite database" * 100)
        with self.assertRaises(sqlite3.DatabaseError) as ctx:
            open_store(path)
        self.assertNotIsInstance(ctx.exception, MigrationError)
        # The connection was closed (Windows refuses to delete an open file).
        os.remove(path)

    def test_migration_failure_keeps_cause_and_type_name(self):
        path = self.root / "t.db"
        _make_v1(path, ["run"])
        with self.assertRaises(MigrationError) as ctx:
            open_store(path, migrations=MIGRATIONS + (_fail,))
        self.assertIsInstance(ctx.exception.__cause__, RuntimeError)
        self.assertTrue(str(ctx.exception).startswith("RuntimeError: "))

    def test_busy_timeout_restored_after_wal_switch(self):
        conn = open_store(self.root / "t.db", timeout=1.5)
        self.addCleanup(conn.close)
        self.assertEqual(conn.execute("PRAGMA busy_timeout").fetchone()[0], 1500)


if __name__ == "__main__":
    unittest.main()
