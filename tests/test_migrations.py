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
    MigrationError,
    SchemaTooNewError,
    open_store,
    upsert_word,
)
from tests._support import V1, make_tempdir


class _Watchdog(unittest.TestCase):
    """Per-test hang guard: a snapshot taken inside an open transaction hangs.

    Armed per test, so a slow VM only loses the run if one test hangs, and the
    traceback names that test.
    """

    def setUp(self):
        faulthandler.dump_traceback_later(60, exit=True)
        self.addCleanup(faulthandler.cancel_dump_traceback_later)


def _add_probe(conn):
    conn.execute("ALTER TABLE words ADD COLUMN probe TEXT")


def _fail(conn):
    raise RuntimeError("boom")


def _make_v1(path, rows):
    conn = open_store(path, migrations=V1)
    try:
        for word in rows:
            upsert_word(conn, word, "tr-" + word, "ctx " + word, now=10)
    finally:
        conn.close()


def _columns(conn):
    return [r[1] for r in conn.execute("PRAGMA table_info(words)")]


M2 = V1 + (_add_probe,)  # synthetic second schema version (D-19)


class SchemaLifecycleTests(_Watchdog):
    def setUp(self):
        super().setUp()
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
        first = open_store(path)  # created at the current version
        upsert_word(first, "run", now=1)
        first.close()
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
            open_store(path, migrations=V1 + (_add_probe, _fail))
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


class ConcurrentVersionChangeTests(_Watchdog):
    """WR-05: data is never migrated without a backup of the version it starts from."""

    def setUp(self):
        super().setUp()
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

        def racing(conn, deadline):
            real(conn, deadline)
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
        noops = V1 + tuple((lambda c: None) for _ in range(9))

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

    def test_newer_version_seen_under_write_lock_refused(self):
        # IN-08: the step-7 branch; a newer build migrated after our version read.
        _make_v1(self.path, ["run"])
        real = store._snapshot

        def racing(conn, p, old_version):
            tmp = real(conn, p, old_version)
            other = sqlite3.connect(p, isolation_level=None)
            try:
                other.execute("PRAGMA user_version = 99")
            finally:
                other.close()
            return tmp

        with mock.patch.object(store, "_snapshot", racing):
            with self.assertRaises(SchemaTooNewError) as ctx:
                open_store(self.path, migrations=M2)
        self.assertIn("99", str(ctx.exception))
        self.assertEqual(self.files("*.tmp"), [])
        self.assertEqual(self.files("*.bak-v*"), [])
        p = sqlite3.connect(self.path)
        self.addCleanup(p.close)
        self.assertEqual(p.execute("PRAGMA user_version").fetchone()[0], 99)
        self.assertNotIn("probe", _columns(p))

    def test_stale_snapshot_temp_files_removed(self):
        # IN-06: a killed open leaves t.db.bak-vN.<pid>.tmp; a later open removes it.
        _make_v1(self.path, ["run"])
        old = self.root / "t.db.bak-v1.4242.tmp"
        fresh = self.root / "t.db.bak-v1.4343.tmp"
        other = self.root / "other.db.bak-v1.4242.tmp"
        for f in (old, fresh, other):
            f.write_bytes(b"x")
        stamp = time.time() - store._STALE_SNAPSHOT_AGE - 60
        os.utime(old, (stamp, stamp))
        os.utime(other, (stamp, stamp))
        open_store(self.path).close()
        self.assertFalse(old.exists())
        self.assertTrue(fresh.exists())  # may belong to an open running right now
        self.assertTrue(other.exists())  # another database's file


class StepTransactionGuardTests(_Watchdog):
    """WR-03: a step cannot end the migration transaction."""

    def setUp(self):
        super().setUp()
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
        steps = V1 + (
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
        conn = open_store(self.path, migrations=V1 + (lambda c: c.executescript(script),))
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
                    open_store(self.path, migrations=V1 + (_add_probe, step))
                self.assert_untouched()

    def test_savepoint_rollback_to_allowed(self):
        def step(c):
            c.execute("SAVEPOINT s")
            c.execute("ALTER TABLE words ADD COLUMN gone TEXT")
            c.execute("ROLLBACK TO s")
            c.execute("RELEASE s")
            c.execute("ALTER TABLE words ADD COLUMN probe TEXT")

        conn = open_store(self.path, migrations=V1 + (step,))
        self.addCleanup(conn.close)
        self.assertIn("probe", _columns(conn))
        self.assertNotIn("gone", _columns(conn))

    def test_commit_through_cursor_connection_denied(self):
        # Verification W1: cursor.connection is the raw connection.
        def sneaky(c):
            c.execute("ALTER TABLE words ADD COLUMN z TEXT")
            c.execute("SELECT 1").connection.commit()

        with self.assertRaises(MigrationError) as ctx:
            open_store(self.path, migrations=V1 + (sneaky, _fail))
        self.assertIn("not authorized", str(ctx.exception))
        self.assert_untouched()

    def test_commit_through_guard_slot_denied(self):
        def sneaky(c):
            c.execute("ALTER TABLE words ADD COLUMN z TEXT")
            c._conn.execute("COMMIT")

        with self.assertRaises(MigrationError):
            open_store(self.path, migrations=V1 + (sneaky,))
        self.assert_untouched()

    def test_raw_executescript_denied(self):
        # sqlite3's own executescript() COMMITs a pending transaction first.
        def sneaky(c):
            c.execute("SELECT 1").connection.executescript(
                "ALTER TABLE words ADD COLUMN z TEXT;"
            )

        with self.assertRaises(MigrationError):
            open_store(self.path, migrations=V1 + (sneaky,))
        self.assert_untouched()

    def test_authorizer_removed_after_migration(self):
        conn = open_store(self.path, migrations=M2)
        self.addCleanup(conn.close)
        conn.execute("BEGIN")
        conn.execute("COMMIT")

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
                open_store(self.path, migrations=V1 + (sneaky,))
        # Now denied by the authorizer before the post-step check runs.
        self.assertIn("not authorized", str(ctx.exception))
        self.assert_untouched()


class OpenFailureTests(_Watchdog):
    def setUp(self):
        super().setUp()
        self.root = make_tempdir(self)

    def _locked_rollback_db(self, exclusive=False):
        """A rollback-journal DB locked by another connection (SHARED or EXCLUSIVE)."""
        path = self.root / "locked.db"
        raw = sqlite3.connect(path)
        raw.execute("CREATE TABLE t (x)")
        raw.commit()
        raw.close()
        holder = sqlite3.connect(path, isolation_level=None)
        self.addCleanup(holder.close)
        if exclusive:
            holder.execute("BEGIN EXCLUSIVE")
        else:
            holder.execute("BEGIN")
            holder.execute("SELECT * FROM t").fetchall()
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

    def test_exclusive_lock_blocks_version_read_within_same_bound(self):
        # UAT 01 test 2: EXCLUSIVE blocks step 3 too; it used to wait the full 5 s.
        path = self._locked_rollback_db(exclusive=True)
        self._assert_wal_lock_failure(path, 5.0, store._WAL_MAX_WAIT + 1.5)

    def test_exclusive_lock_deadline_follows_short_timeout(self):
        path = self._locked_rollback_db(exclusive=True)
        self._assert_wal_lock_failure(path, 0.3, 1.5)

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
            open_store(path, migrations=V1 + (_fail,))
        self.assertIsInstance(ctx.exception.__cause__, RuntimeError)
        # IN-04 / V7: only the type name; a step's message may carry row values.
        self.assertEqual(str(ctx.exception), "RuntimeError")

    def test_sqlite_error_text_kept_in_migration_error(self):
        path = self.root / "t.db"
        _make_v1(path, ["run"])

        def bad_sql(c):
            c.execute("ALTER TABLE no_such_table ADD COLUMN x")

        with self.assertRaises(MigrationError) as ctx:
            open_store(path, migrations=V1 + (bad_sql,))
        self.assertIn("OperationalError: no such table", str(ctx.exception))

    @unittest.skipUnless(os.name == "posix", "POSIX file modes")
    def test_new_files_private_in_existing_0755_dir(self):
        # IN-05: the directory exists already, so mkdir(mode=0o700) does not apply.
        d = self.root / "shared"
        d.mkdir(mode=0o755)
        os.chmod(d, 0o755)
        path = d / "t.db"
        conn = open_store(path, migrations=V1)
        upsert_word(conn, "run")
        conn.close()
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        conn = open_store(path, migrations=M2)
        conn.close()
        self.assertEqual((d / "t.db.bak-v1").stat().st_mode & 0o777, 0o600)

    @unittest.skipUnless(os.name == "posix", "POSIX file modes")
    def test_existing_file_mode_left_alone(self):
        path = self.root / "t.db"
        open_store(path).close()
        os.chmod(path, 0o640)
        open_store(path).close()
        self.assertEqual(path.stat().st_mode & 0o777, 0o640)

    def test_busy_timeout_restored_after_wal_switch(self):
        conn = open_store(self.root / "t.db", timeout=1.5)
        self.addCleanup(conn.close)
        self.assertEqual(conn.execute("PRAGMA busy_timeout").fetchone()[0], 1500)


if __name__ == "__main__":
    unittest.main()
