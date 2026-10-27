import sqlite3
import time
import unittest
from unittest import mock

from lookup import store
from lookup.normalize import normalize
from lookup.store import CONTEXT_MAX_CHARS, CURRENT_VERSION, open_store, upsert_word
from tests._support import V1, make_tempdir


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

    def test_schema_v3_tables_and_columns(self):
        info = self.conn.execute("PRAGMA table_info(words)").fetchall()
        self.assertEqual(
            [r[1] for r in info],
            ["word", "translation", "context", "count", "first_seen", "last_seen", "lemma",
             "context_start", "context_end", "context_token", "context_meaning", "context_provider"],
        )
        self.assertEqual([r[1] for r in info if r[5]], ["word"])
        tables = [
            r[0]
            for r in self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        ]
        self.assertEqual(sorted(tables), ["contextual_translations", "meta", "translations", "words"])
        self.assertEqual(self.conn.execute("PRAGMA user_version").fetchone()[0], CURRENT_VERSION)
        self.assertEqual(CURRENT_VERSION, 3)
        tr = self.conn.execute("PRAGMA table_info(translations)").fetchall()
        self.assertEqual(
            [r[1] for r in tr], ["text", "kind", "provider", "payload", "fetched_at"]
        )
        self.assertEqual(sorted(r[1] for r in tr if r[5]), ["kind", "text"])
        meta = self.conn.execute("PRAGMA table_info(meta)").fetchall()
        self.assertEqual([r[1] for r in meta], ["key", "value"])
        self.assertEqual([r[1] for r in meta if r[5]], ["key"])
        upsert_word(self.conn, "run", now=1)
        self.assertIsNone(self.row("run")[6])

    def test_translations_kind_check(self):
        insert = (
            "INSERT INTO translations (text, kind, provider, payload, fetched_at) "
            "VALUES (?, ?, 'p', '{}', 1)"
        )
        for kind in ("word", "phrase", "sentence"):
            self.conn.execute(insert, ("run", kind))
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(insert, ("run", "paragraph"))
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(insert, ("run", "word"))  # same (text, kind)
        self.conn.execute(
            insert + " ON CONFLICT(text, kind) DO UPDATE SET provider = 'q'",
            ("run", "word"),
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT provider FROM translations WHERE text='run' AND kind='word'"
            ).fetchone()[0],
            "q",
        )

    def test_lemma_stored_and_coalesced(self):
        upsert_word(self.conn, "running", lemma="run", now=1)
        self.assertEqual(self.row("running")[6], "run")
        upsert_word(self.conn, "running", lemma=None, now=2)
        self.assertEqual(self.row("running")[6], "run")
        upsert_word(self.conn, "running", lemma="  ", now=3)
        self.assertEqual(self.row("running")[6], "run")
        upsert_word(self.conn, "running", lemma="jog", now=4)
        self.assertEqual(self.row("running")[6], "jog")
        self.assertEqual(self.row("running")[3], 4)  # key stays the surface form (D-12)
        self.assertIsNone(self.row("run"))

    def test_lemma_bound_not_interpolated(self):
        evil = "o'neil'; DROP TABLE words; --"
        upsert_word(self.conn, "x", lemma=evil, now=1)
        self.assertEqual(self.row("x")[6], evil)
        self.assertEqual(self.count_rows(), 1)

    def test_lemma_type_checked(self):
        with self.assertRaises(TypeError):
            upsert_word(self.conn, "running", lemma=5)
        self.assertEqual(self.count_rows(), 0)

    def test_positional_callers_unchanged(self):
        self.assertEqual(upsert_word(self.conn, "run", "bezhat", "ctx", 7), 1)
        self.assertEqual(self.row("run")[:6], ("run", "bezhat", "ctx", 1, 7, 7))
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


class SchemaV2Tests(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)

    def test_phase1_database_migrates_to_v2_keeping_words(self):
        path = self.root / "t.db"
        old = open_store(path, migrations=V1)
        upsert_word(old, "run", "bezhat", "I run", now=1)
        upsert_word(old, "run", None, None, now=2)
        old.close()

        conn = open_store(path, migrations=store.MIGRATIONS[:2])
        self.addCleanup(conn.close)
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 2)
        self.assertEqual(
            conn.execute(
                "SELECT word, translation, context, count, first_seen, last_seen, lemma "
                "FROM words"
            ).fetchall(),
            [("run", "bezhat", "I run", 2, 1, 2, None)],
        )
        tables = sorted(
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        )
        self.assertEqual(tables, ["meta", "translations", "words"])
        backup = self.root / "t.db.bak-v1"
        self.assertTrue(backup.is_file())
        b = sqlite3.connect(backup)
        self.addCleanup(b.close)
        self.assertEqual(b.execute("PRAGMA user_version").fetchone()[0], 1)
        self.assertEqual(b.execute("SELECT count FROM words").fetchone()[0], 2)


class ContextPairTests(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)
        self.conn = open_store(self.root/'pair.db')
        self.addCleanup(self.conn.close)
        self.context = '  They sat on the bank\nof the river.  '
        start = self.context.index('bank')
        self.span = (start,start+4)

    def save(self, token='event-one', **kwargs):
        return upsert_word(self.conn,'bank','словарь',self.context,now=10,
                           context_span=self.span,context_token=token,**kwargs)

    def enrich(self, token='event-one', text=None, span=None):
        from lookup.context import ContextResult, PROVIDER
        return store.enrich_word_context(self.conn,'bank',token,
                                         self.context if text is None else text,
                                         self.span if span is None else span,
                                         ContextResult('берег',PROVIDER))

    def test_exact_source_pair_and_snapshot_without_recount(self):
        self.assertEqual(self.save(),1)
        self.assertTrue(self.enrich())
        self.assertTrue(self.enrich())
        row = store.get_word_context(self.conn,'bank')
        self.assertEqual(row['context'],self.context)
        self.assertEqual(row['span'],self.span)
        self.assertEqual(row['meaning'],'берег')
        self.assertEqual(row['translation'],'словарь')
        self.assertEqual(self.conn.execute('SELECT count,first_seen,last_seen FROM words').fetchone(),(1,10,10))
        self.assertIsNone(store.get_word_context(self.conn,'absent'))

    def test_new_event_clears_old_meaning_and_refuses_old_token(self):
        self.save()
        self.enrich()
        self.assertEqual(self.save('event-two'),2)
        self.assertFalse(self.enrich())
        self.assertIsNone(store.get_word_context(self.conn,'bank')['meaning'])
        self.assertTrue(self.enrich('event-two'))

    def test_exact_context_span_and_recreated_record_are_guarded(self):
        self.save()
        self.assertFalse(self.enrich(text=self.context.strip()))
        self.assertFalse(self.enrich(span=(self.span[0]-1,self.span[1])))
        self.conn.execute('DELETE FROM words')
        self.save('recreated-event')
        self.assertFalse(self.enrich())
        self.assertEqual(self.conn.execute('SELECT count FROM words').fetchone()[0],1)

    def test_lookup_without_span_keeps_legacy_context_but_clears_sense(self):
        self.save()
        self.enrich()
        upsert_word(self.conn,'bank',context=None,now=11)
        row = store.get_word_context(self.conn,'bank')
        self.assertEqual(row['context'],self.context)
        self.assertIsNone(row['meaning'])
        self.assertIsNone(row['span'])
        self.assertFalse(self.enrich())

    def test_invalid_exact_pair_does_not_count_or_truncate(self):
        for text, span, token in ((self.context,(True,5),'x'),(self.context,(-1,5),'x'),
                                  (self.context,(0,500),'x'),('x'*501,(0,4),'x'),
                                  (self.context,self.span,None)):
            with self.subTest(span=span,token=token):
                with self.assertRaises((ValueError,TypeError)):
                    upsert_word(self.conn,'bank',context=text,context_span=span,context_token=token)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM words').fetchone()[0],0)

    def test_legacy_schema_writes_still_work_but_cannot_claim_enrichment(self):
        old = open_store(self.root/'v1.db',migrations=V1)
        self.addCleanup(old.close)
        self.assertEqual(upsert_word(old,'bank','банк','The bank.',now=1),1)
        with self.assertRaises(sqlite3.OperationalError):
            upsert_word(old,'bank',context=self.context,context_span=self.span,context_token='x')
        self.assertEqual(old.execute('SELECT count FROM words').fetchone()[0],1)


if __name__ == "__main__":
    unittest.main()
