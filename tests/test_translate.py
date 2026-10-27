"""Offline-first orchestration, persistent cache and bounded context workers."""
import faulthandler
import contextlib
import io
import threading
import time
import unittest
from unittest import mock

from lookup import online
from lookup import translate as t
from lookup.dicts import Article, SearchResult
from lookup.store import open_store
from tests._support import forbid_network, make_tempdir


def answer(main="бег", lemma=None, client="gtx"):
    return online.OnlineResult("google", client, main,
                               (("noun", ("бег", "ход", "пробег")),),
                               None, lemma, "en")


def article(senses=(("noun", ("бег", "ход", "пробег", "серия")),), text="entry"):
    return Article("test", "run", None, senses, text)


class FakeDictSet:
    def __init__(self, result=SearchResult()):
        self.result = result
        self.calls = []

    def find(self, key):
        self.calls.append(key)
        return self.result


class DatabaseTest(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)
        self.conn = open_store(self.root / "t.db")
        self.addCleanup(self.conn.close)
        self.network = forbid_network(self)

    def rows(self, table):
        return self.conn.execute("SELECT * FROM " + table).fetchall()


class ClassifyTests(unittest.TestCase):
    def test_classification(self):
        cases = [("run", "word", "run"), ("Running,", "word", "running"),
                 ("Break out", "phrase", "break out"), ("well-known", "word", "well-known"),
                 ("  Hello,   world ", "phrase", "hello world"),
                 ("one two three four", "phrase", "one two three four"),
                 ("The  quick brown fox jumps", "sentence", "The quick brown fox jumps"),
                 ("I have 3 apples, e.g. red ones", "sentence", "I have 3 apples, e.g. red ones")]
        for text, kind, key in cases:
            with self.subTest(text=text):
                self.assertEqual(t.classify(text), t.Query(kind, key))
        for text in ("12345", "COVID-19", "", "  ", "рун"):
            self.assertEqual(t.classify(text), t.Query("invalid", None))
        with self.assertRaises(TypeError):
            t.classify(None)
        self.assertEqual(t.classify("word " * 25000).kind, "sentence")


class ShortTranslationTests(unittest.TestCase):
    def test_dictionary_senses_and_fallback(self):
        self.assertEqual(t.short_translation((article(),), None), "бег; ход; пробег")
        self.assertEqual(t.short_translation((article((), "x" * 100 + "\nsecond"),), None), "x" * 80)
        self.assertEqual(t.short_translation((article((), "plain"), article()), None), "бег; ход; пробег")

    def test_online_deduplicates_and_caps(self):
        self.assertEqual(t.short_translation((), answer()), "бег; ход; пробег")
        self.assertEqual(t.short_translation((), answer("побежал")), "побежал; бег; ход")
        self.assertEqual(len(t.short_translation((), answer("x" * 300))), t.SHORT_MAX_CHARS)
        self.assertIsNone(t.short_translation((), None))


class CacheTests(DatabaseTest):
    def test_roundtrip_replace_and_separate_kinds(self):
        for kind in ("word", "phrase", "sentence"):
            t.cache_put(self.conn, "same", kind, answer(), now=1)
            self.assertEqual(t.cache_get(self.conn, "same", kind), answer())
        t.cache_put(self.conn, "same", "word", answer("новый"), now=2)
        self.assertEqual(t.cache_get(self.conn, "same", "word"), answer("новый"))
        self.assertEqual(self.conn.execute("SELECT fetched_at FROM translations WHERE kind='word'").fetchone()[0], 2)
        self.assertEqual(len(self.rows("translations")), 3)
        self.assertEqual(self.network.call_count, 0)

    def test_bad_payloads_are_misses(self):
        for payload in ("invalid", "[]", "null", "{}", '"text"', "[" * 2000):
            t.cache_put(self.conn, "run", "word", answer())
            self.conn.execute("UPDATE translations SET payload=?", (payload,))
            self.assertIsNone(t.cache_get(self.conn, "run", "word"))
        for fn, args in ((t.cache_get, ()), (t.cache_put, (answer(),))):
            with self.assertRaises(ValueError):
                fn(self.conn, "run", "bad", *args)

    def test_sentence_limit_and_ties(self):
        for i in range(1005):
            t.cache_put(self.conn, str(i), "sentence", answer(), now=i)
            t.cache_put(self.conn, str(i), "word", answer(), now=i)
        self.assertEqual(len(self.rows("translations")), 2005)
        for i in range(5):
            self.assertIsNone(t.cache_get(self.conn, str(i), "sentence"))
        t.cache_put(self.conn, "new", "sentence", answer(), now=1004)
        self.assertIsNotNone(t.cache_get(self.conn, "new", "sentence"))
        self.assertIsNone(t.cache_get(self.conn, "5", "sentence"))

    def test_meta_bound_parameters(self):
        key = "'; DROP TABLE words; --"
        self.assertIsNone(t.get_meta(self.conn, key))
        for value in ("gtx", "at"):
            t.set_meta(self.conn, key, value)
            self.assertEqual(t.get_meta(self.conn, key), value)
        self.assertEqual(self.rows("words"), [])

    def test_lookup_cache_and_client_preference(self):
        t.set_meta(self.conn, t.META_GOOGLE_CLIENT, "at")
        with mock.patch.object(online, "translate_online", return_value=answer()) as call:
            first = t.lookup("Run", conn=self.conn, clients=("at", "gtx"), now=42)
        call.assert_called_once_with("run", "word", clients=("at", "gtx"), first_client="at")
        self.assertTrue(first.online_attempted)
        with mock.patch.object(online, "translate_online", side_effect=AssertionError):
            second = t.lookup("run", conn=self.conn)
        self.assertTrue(second.from_cache)
        self.assertFalse(second.online_attempted)
        self.assertEqual(second.count, 2)
        self.assertEqual(t.get_meta(self.conn, t.META_GOOGLE_CLIENT), "gtx")


class OfflineFirstTests(DatabaseTest):
    def test_dictionary_hit_never_calls_online(self):
        for text in ("Run", "Break out"):
            dictionaries = FakeDictSet(SearchResult((article(),), "run"))
            with mock.patch.object(online, "translate_online", side_effect=AssertionError):
                res = t.lookup(text, dictset=dictionaries, conn=self.conn)
            self.assertEqual(dictionaries.calls, [text.lower()])
            self.assertFalse(res.online_attempted)
            self.assertEqual(res.lemma, "run")
            self.assertEqual(res.translation, "бег; ход; пробег")
            self.assertEqual(set(res.timings), {"classify", "dicts", "cache", "online", "context", "db", "total", "first_useful", "meaning_ready"})
            self.assertTrue(all(ms >= 0 for ms in res.timings.values()))

    def test_missing_and_broken_dictionary_fall_back(self):
        dictionaries = mock.Mock()
        dictionaries.find.side_effect = RuntimeError("private text")
        with mock.patch.object(online, "translate_online", return_value=answer()):
            self.assertEqual(t.lookup("run", dictset=dictionaries).online, answer())
            self.assertEqual(t.lookup("run").online, answer())

    def test_offline_and_invalid_never_access_network(self):
        dictionaries = FakeDictSet()
        with mock.patch.object(online, "translate_online", side_effect=AssertionError):
            res = t.lookup("run", dictset=dictionaries, conn=self.conn, online=False)
            self.assertFalse(res.online_enabled)
            self.assertFalse(res.online_attempted)
            self.assertIsNone(res.online_error)
            dictionaries.calls.clear()
            res = t.lookup("COVID-19", dictset=dictionaries, conn=self.conn, context="A sentence")
        self.assertEqual(res.kind, "invalid")
        self.assertEqual(dictionaries.calls, [])
        self.assertEqual(len(self.rows("words")), 1)
        self.assertEqual(self.rows("translations"), [])


class SaveRulesTests(DatabaseTest):
    def test_save_matrix(self):
        for kind, text in (("word", "running"), ("phrase", "break out"), ("sentence", "I run every single morning")):
            for reason in (None, "not_found", "no_network", "blocked", "timeout", "bad_response", "offline"):
                with self.subTest(kind=kind, reason=reason):
                    self.conn.execute("DELETE FROM words")
                    self.conn.execute("DELETE FROM translations")
                    with mock.patch.object(online, "translate_online", return_value=answer(lemma="run"),
                                           side_effect=online.TranslateError(reason) if reason not in (None, "offline") else None):
                        res = t.lookup(text, conn=self.conn, online=reason != "offline", now=42)
                    expected = kind != "sentence" and reason != "not_found"
                    self.assertEqual(res.saved, expected)
                    self.assertEqual(len(self.rows("words")), int(expected))
                    self.assertEqual(len(self.rows("translations")), int(reason is None))
                    self.assertEqual(res.online_error, reason if reason not in (None, "offline") else None)
                    if expected:
                        row = self.rows("words")[0]
                        self.assertEqual(row[1], "бег; ход; пробег" if reason is None else None)
                        self.assertEqual(row[4], 42)
                        self.assertEqual(row[6], "run" if reason is None and kind == "word" else None)

    def test_no_save_still_caches_but_does_not_count(self):
        with mock.patch.object(online, "translate_online", return_value=answer()):
            res = t.lookup("run", conn=self.conn, context="I run every morning", save=False)
        self.assertFalse(res.saved)
        self.assertEqual(self.rows("words"), [])
        self.assertEqual(len(self.rows("translations")), 2)
        self.assertEqual(t.get_meta(self.conn, t.META_GOOGLE_CLIENT), "gtx")

    def test_dictionary_lemma_wins_and_context_is_saved(self):
        dictionaries = FakeDictSet(SearchResult((), "dictionary"))
        with mock.patch.object(online, "translate_online", return_value=answer(lemma="online")):
            res = t.lookup("running", dictset=dictionaries, conn=self.conn, context="original context")
        self.assertEqual(res.lemma, "dictionary")
        row = self.rows("words")[0]
        self.assertEqual(row[2], "original context")
        self.assertEqual(row[6], "dictionary")

    def test_offline_value_is_filled_later(self):
        t.lookup("run", conn=self.conn, online=False)
        with mock.patch.object(online, "translate_online", return_value=answer(lemma="RUN")):
            res = t.lookup("run", conn=self.conn)
        self.assertEqual(res.count, 2)
        self.assertIsNone(res.lemma)
        self.assertEqual(self.rows("words")[0][1], "бег; ход; пробег")

    def test_no_output_and_no_connection(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), mock.patch.object(online, "translate_online", side_effect=online.TranslateError("blocked")):
            res = t.lookup("run")
        self.assertFalse(res.saved)
        self.assertIsNone(res.count)
        self.assertEqual((out.getvalue(), err.getvalue()), ("", ""))
        self.assertGreaterEqual(res.timings["total"] + 0.01, sum(v for k, v in res.timings.items() if k != "total"))


class SentenceTests(DatabaseTest):
    def setUp(self):
        super().setUp()
        faulthandler.dump_traceback_later(60, exit=True)
        self.addCleanup(faulthandler.cancel_dump_traceback_later)

    def event(self):
        event = threading.Event()
        self.addCleanup(event.set)
        return event

    def test_context_overlaps_dictionary_and_caches_on_owner_thread(self):
        started, release = self.event(), self.event()
        owner = threading.get_ident()
        def translate(*args, **kwargs):
            self.assertNotEqual(threading.get_ident(), owner)
            self.assertTrue(threading.current_thread().daemon)
            started.set()
            release.wait(2)
            return answer("контекст")
        def find(key):
            self.assertTrue(started.wait(1))
            self.assertFalse(release.is_set())
            release.set()
            return SearchResult((article(),))
        with mock.patch.object(online, "translate_online", side_effect=translate):
            res = t.lookup("run", dictset=mock.Mock(find=find), conn=self.conn, context="I run every morning.")
        self.assertEqual(res.context_translation, "контекст")
        self.assertFalse(res.context_from_cache)
        self.assertIsNotNone(t.cache_get(self.conn, "I run every morning.", "sentence"))

    def test_context_cache_starts_no_thread(self):
        t.cache_put(self.conn, "I run every morning.", "sentence", answer("контекст"))
        with mock.patch.object(threading, "Thread", side_effect=AssertionError), mock.patch.object(online, "translate_online", side_effect=AssertionError):
            res = t.lookup("run", dictset=FakeDictSet(SearchResult((article(),))), conn=self.conn, context="I run every morning.")
        self.assertTrue(res.context_from_cache)
        self.assertEqual(res.context_translation, "контекст")

    def test_context_errors(self):
        for error, reason in ((online.TranslateError("blocked"), "blocked"), (RuntimeError("private"), "bad_response")):
            with mock.patch.object(online, "translate_online", side_effect=error):
                res = t.lookup("run", dictset=FakeDictSet(SearchResult((article(),))), conn=self.conn, context="I run every morning.")
            self.assertEqual(res.context_error, reason)
            self.assertIsNone(res.context_translation)
            self.assertTrue(res.saved)
            self.assertEqual(self.rows("translations"), [])

    def test_timeout_is_bounded_and_does_not_write_late(self):
        release, finished = self.event(), self.event()
        def translate(*args, **kwargs):
            release.wait(2)
            finished.set()
            return answer()
        start = time.perf_counter()
        with mock.patch.object(t, "CONTEXT_JOIN_S", 0.2), mock.patch.object(online, "translate_online", side_effect=translate):
            res = t.lookup("run", dictset=FakeDictSet(SearchResult((article(),))), conn=self.conn, context="I run every morning.")
            elapsed = time.perf_counter() - start
            self.assertEqual(res.context_error, "timeout")
            self.assertGreaterEqual(elapsed, 0.18)
            self.assertLess(elapsed, 1)
            release.set()
            self.assertTrue(finished.wait(1))
        self.assertEqual(self.rows("translations"), [])

    def test_ignored_contexts(self):
        for context in (None, "", "  ", "  RUN  "):
            with mock.patch.object(threading, "Thread", side_effect=AssertionError), mock.patch.object(online, "translate_online", side_effect=AssertionError):
                res = t.lookup("run", dictset=FakeDictSet(SearchResult((article(),))), context=context)
            self.assertIsNone(res.context_error)
        with mock.patch.object(online, "translate_online", side_effect=AssertionError):
            res = t.lookup("run", context="I run every morning", online=False)
        self.assertIsNone(res.context_translation)

    def test_sentence_and_context_keys_are_capped(self):
        text = "I run every morning " * 100
        key = online.prepare_text(text)
        with mock.patch.object(online, "translate_online", return_value=answer()) as call:
            res = t.lookup(text, context="ignored context", conn=self.conn, dictset=mock.Mock(find=mock.Mock(side_effect=AssertionError)))
        call.assert_called_once_with(key, "sentence", clients=None, first_client=None)
        self.assertIsNotNone(t.cache_get(self.conn, key, "sentence"))
        self.assertFalse(res.saved)
        with mock.patch.object(online, "translate_online", return_value=answer()) as call:
            t.lookup("run", dictset=FakeDictSet(SearchResult((article(),))), conn=self.conn, context=text + "different")
        call.assert_not_called()

    def test_word_online_and_context_run_concurrently(self):
        context_started = self.event()
        def translate(text, kind, **kwargs):
            if kind == "sentence":
                context_started.set()
            else:
                self.assertTrue(context_started.wait(1))
            return answer()
        with mock.patch.object(online, "translate_online", side_effect=translate) as call:
            res = t.lookup("run", context="I run every morning.")
        self.assertEqual(call.call_count, 2)
        self.assertEqual(res.context_translation, "бег")

    def test_long_context_is_prepared_before_request_and_cache(self):
        text = "I run every morning " * 100
        key = online.prepare_text(text)
        with mock.patch.object(online, "translate_online", return_value=answer()) as call:
            t.lookup("run", dictset=FakeDictSet(SearchResult((article(),))), conn=self.conn, context=text)
        call.assert_called_once_with(key, "sentence", clients=None, first_client=None)
        self.assertIsNotNone(t.cache_get(self.conn, key, "sentence"))

    def test_dictionary_time_consumes_join_budget(self):
        release = self.event()
        def translate(*args, **kwargs):
            release.wait(2)
            return answer()
        def find(key):
            time.sleep(0.25)
            return SearchResult((article(),))
        with mock.patch.object(t, "CONTEXT_JOIN_S", 0.2), mock.patch.object(online, "translate_online", side_effect=translate):
            res = t.lookup("run", dictset=mock.Mock(find=find), context="I run every morning")
        self.assertEqual(res.context_error, "timeout")
        self.assertLess(res.timings["context"], 100)


if __name__ == "__main__":
    unittest.main()
