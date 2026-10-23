import faulthandler
import hashlib
import os
import sqlite3
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


if __name__ == "__main__":
    unittest.main()
