"""SC3: ten spawn-started processes upserting one word (DATA-01, D-20)."""
import multiprocessing
import sqlite3
import time
import unittest
from pathlib import Path
from unittest import mock

from lookup.store import open_store, upsert_word
from tests import _workers
from tests._support import V1, make_tempdir

# Upper bound for the reader loop; a hung child fails the test instead of the run.
_WRITERS_DEADLINE = 90


class ConcurrentWriterTests(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)

    def _run_writers(self, path, n=10, reader=None):
        ctx = multiprocessing.get_context("spawn")
        barrier = ctx.Barrier(n)
        queue = ctx.Queue()
        procs = [
            ctx.Process(target=_workers.child, args=(str(path), barrier, queue, i))
            for i in range(n)
        ]

        def _reap():
            for p in procs:
                if p.is_alive():
                    p.terminate()
                p.join(5)

        self.addCleanup(_reap)
        for p in procs:
            p.start()

        reader_values = []
        if reader is not None:
            deadline = time.monotonic() + _WRITERS_DEADLINE
            while any(p.is_alive() for p in procs):
                if time.monotonic() > deadline:
                    self.fail(
                        "writer processes did not finish in %d s" % _WRITERS_DEADLINE
                    )
                row = reader.execute(
                    "SELECT count FROM words WHERE word = 'run'"
                ).fetchone()
                reader_values.append(row[0] if row else None)
                time.sleep(0.01)

        results = [queue.get(timeout=60) for _ in range(n)]
        for p in procs:
            p.join(30)
        return results, reader_values

    def _assert_writers_ok(self, results, path):
        errors = [r[1] for r in results if r[0] != "ok"]
        self.assertEqual(errors, [])
        counts = sorted(r[1] for r in results)
        self.assertEqual(counts, list(range(1, 11)))

        conn = open_store(Path(path))
        try:
            rows = conn.execute(
                "SELECT word, translation, context, count FROM words"
            ).fetchall()
            self.assertEqual(len(rows), 1)
            word, translation, context, count = rows[0]
            self.assertEqual(word, "run")
            self.assertEqual(count, 10)
            self.assertEqual(translation, "бежать")
            self.assertTrue(context)
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            self.assertEqual(mode, "wal")
        finally:
            conn.close()

    def test_ten_writers_on_precreated_db(self):
        path = self.root / "pre" / "lookup.db"
        open_store(path).close()
        reader = sqlite3.connect(str(path), timeout=5)
        self.addCleanup(reader.close)

        results, seen = self._run_writers(path, reader=reader)

        self._assert_writers_ok(results, path)
        self.assertTrue(seen, "reader never ran while the writers were alive")
        prev = 0
        for value in seen:
            self.assertTrue(value is None or 1 <= value <= 10, value)
            cur = 0 if value is None else value
            self.assertGreaterEqual(cur, prev)
            prev = cur

    def test_reader_loop_has_deadline(self):
        # WR-06: a stuck writer must fail the test, not hang the suite.
        path = self.root / "deadline" / "lookup.db"
        open_store(path).close()
        reader = sqlite3.connect(str(path), timeout=5)
        self.addCleanup(reader.close)
        with mock.patch(__name__ + "._WRITERS_DEADLINE", -1):
            with self.assertRaises(AssertionError) as ctx:
                self._run_writers(path, reader=reader)
        self.assertIn("did not finish", str(ctx.exception))

    def test_ten_writers_on_fresh_db(self):
        for round_no in range(3):
            with self.subTest(round=round_no):
                path = self.root / ("fresh%d" % round_no) / "lookup.db"
                self.assertFalse(path.exists())
                results, _ = self._run_writers(path)
                self._assert_writers_ok(results, path)

    def test_ten_processes_migrate_v1_to_v2_once(self):
        # IN-08: real processes, not a simulated race, upgrading one v1 database.
        path = self.root / "mig" / "lookup.db"
        conn = open_store(path, migrations=V1)
        upsert_word(conn, "run")
        upsert_word(conn, "walk")
        conn.close()

        n = 10
        ctx = multiprocessing.get_context("spawn")
        barrier = ctx.Barrier(n)
        queue = ctx.Queue()
        procs = [
            ctx.Process(target=_workers.migrate_child, args=(str(path), barrier, queue))
            for _ in range(n)
        ]

        def _reap():
            for p in procs:
                if p.is_alive():
                    p.terminate()
                p.join(5)

        self.addCleanup(_reap)
        for p in procs:
            p.start()
        results = [queue.get(timeout=60) for _ in range(n)]
        for p in procs:
            p.join(30)

        self.assertEqual(results, [("ok", 2)] * n)
        self.assertEqual(
            sorted(f.name for f in path.parent.iterdir() if ".bak-v" in f.name),
            ["lookup.db.bak-v1"],
        )
        check = sqlite3.connect(path)
        self.addCleanup(check.close)
        self.assertEqual(check.execute("PRAGMA user_version").fetchone()[0], 2)
        self.assertEqual(
            check.execute("SELECT word, count FROM words ORDER BY word").fetchall(),
            [("run", 1), ("walk", 1)],
        )
        cols = [r[1] for r in check.execute("PRAGMA table_info(words)")]
        self.assertIn("probe", cols)


if __name__ == "__main__":
    unittest.main()
