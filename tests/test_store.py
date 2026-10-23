import time
import unittest
from unittest import mock

from lookup import store
from lookup.normalize import normalize
from lookup.store import CONTEXT_MAX_CHARS, CURRENT_VERSION, open_store, upsert_word
from tests._support import make_tempdir


class UpsertTests(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)
        self.conn = open_store(self.root / "t.db")
        self.addCleanup(self.conn.close)

    def row(self, word):
        return self.conn.execute(
            "SELECT word, translation, context, count, first_seen, last_seen, lemma "
            "FROM words WHERE word = ?",
            (word,),
        ).fetchone()

    def count_rows(self):
        return self.conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]

    def test_schema_v1_columns_and_only_words_table(self):
        info = self.conn.execute("PRAGMA table_info(words)").fetchall()
        self.assertEqual(
            [r[1] for r in info],
            ["word", "translation", "context", "count", "first_seen", "last_seen", "lemma"],
        )
        self.assertEqual([r[1] for r in info if r[5]], ["word"])
        tables = [
            r[0]
            for r in self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        ]
        self.assertEqual(tables, ["words"])
        self.assertEqual(self.conn.execute("PRAGMA user_version").fetchone()[0], CURRENT_VERSION)
        self.assertEqual(CURRENT_VERSION, 1)
        upsert_word(self.conn, "run", now=1)
        self.assertIsNone(self.row("run")[6])

    def test_connection_pragmas(self):
        self.assertEqual(self.conn.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        self.assertEqual(self.conn.execute("PRAGMA synchronous").fetchone()[0], 1)
        self.assertEqual(self.conn.execute("PRAGMA busy_timeout").fetchone()[0], 5000)

    def test_two_saves_one_row(self):
        upsert_word(self.conn, "run", "bezhat", "I run fast", now=100)
        upsert_word(self.conn, "run", "bezhat", "They run away", now=200)
        self.assertEqual(self.count_rows(), 1)
        word, tr, ctx, cnt, first, last, _ = self.row("run")
        self.assertEqual((word, tr, ctx, cnt, first, last),
                         ("run", "bezhat", "They run away", 2, 100, 200))

    def test_returning_count_sequence(self):
        self.assertEqual([upsert_word(self.conn, "run", now=i) for i in (1, 2, 3)], [1, 2, 3])

    def test_empty_context_and_none_translation_keep_old(self):
        upsert_word(self.conn, "run", "bezhat", "ctx one", now=1)
        self.assertEqual(upsert_word(self.conn, "run", None, "", now=2), 2)
        self.assertEqual(self.row("run")[1:3], ("bezhat", "ctx one"))
        self.assertEqual(upsert_word(self.conn, "run", "  ", "  \n ", now=3), 3)
        self.assertEqual(self.row("run")[1:3], ("bezhat", "ctx one"))
        self.assertEqual(upsert_word(self.conn, "run", None, "ctx two", now=4), 4)
        self.assertEqual(self.row("run")[1:3], ("bezhat", "ctx two"))

    def test_context_truncated_to_500(self):
        long_ctx = "x" * 2000
        upsert_word(self.conn, "run", context=long_ctx, now=1)
        self.assertEqual(len(self.row("run")[2]), CONTEXT_MAX_CHARS)
        upsert_word(self.conn, "run", context="y" * 2000, now=2)
        self.assertEqual(len(self.row("run")[2]), CONTEXT_MAX_CHARS)
        self.assertEqual(self.row("run")[2], "y" * CONTEXT_MAX_CHARS)

    def test_times_are_integer_utc_seconds(self):
        before = int(time.time())
        upsert_word(self.conn, "run")
        after = int(time.time())
        types = self.conn.execute(
            "SELECT typeof(first_seen), typeof(last_seen) FROM words"
        ).fetchone()
        self.assertEqual(types, ("integer", "integer"))
        _, _, _, _, first, last, _ = self.row("run")
        self.assertTrue(before <= first <= after)
        self.assertTrue(before <= last <= after)

    def test_float_now_stored_as_integer_seconds(self):
        # WR-04: now=time.time() must not store REAL timestamps (D-13).
        upsert_word(self.conn, "run", now=1729771234.7)
        upsert_word(self.conn, "run", now=1729771300.2)
        row = self.conn.execute(
            "SELECT typeof(first_seen), typeof(last_seen), first_seen, last_seen FROM words"
        ).fetchone()
        self.assertEqual(row, ("integer", "integer", 1729771234, 1729771300))

    def test_invalid_now_rejected(self):
        for bad in (True, False, "100", b"100", [1]):
            with self.subTest(now=bad):
                with self.assertRaises(TypeError):
                    upsert_word(self.conn, "run", now=bad)
        self.assertEqual(self.count_rows(), 0)

    def test_distinct_words_distinct_rows(self):
        self.assertEqual(upsert_word(self.conn, "run", now=1), 1)
        self.assertEqual(upsert_word(self.conn, "walk", now=1), 1)
        self.assertEqual(self.count_rows(), 2)

    def test_sql_text_is_bound_not_interpolated(self):
        evil = "'; DROP TABLE words; --"
        upsert_word(self.conn, evil, evil, evil, now=1)
        upsert_word(self.conn, "O'Neil", "O'Neil", "it's O'Neil", now=1)
        self.assertEqual(self.count_rows(), 2)
        self.assertEqual(self.row(evil)[:3], (evil, evil, evil))
        self.assertEqual(self.row("O'Neil")[2], "it's O'Neil")

    def test_invalid_word_rejected(self):
        for bad in (None, 5):
            with self.assertRaises(TypeError):
                upsert_word(self.conn, bad)
        for bad in ("", "   "):
            with self.assertRaises(ValueError):
                upsert_word(self.conn, bad)
        self.assertEqual(self.count_rows(), 0)

    def test_normalized_variants_share_one_row(self):
        results = [
            upsert_word(self.conn, normalize(v), now=i)
            for i, v in enumerate(["Book", "“Book’s”", "book,"], 1)
        ]
        self.assertEqual(results, [1, 2, 3])
        self.assertEqual(self.count_rows(), 1)
        self.assertIsNotNone(self.row("book"))
        key = normalize("12345")
        self.assertIsNone(key)
        if key is not None:  # caller-side pattern: skip on None
            upsert_word(self.conn, key)
        self.assertEqual(self.count_rows(), 1)

    def test_sqlite_version_floor(self):
        target = self.root / "old.db"
        with mock.patch.object(store.sqlite3, "sqlite_version_info", (3, 34, 0)):
            with self.assertRaises(RuntimeError):
                open_store(target)
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
