"""Online translation client: parsers, payload round trip, text preparation (D-13, D-14, D-30, D-31)."""
import json
import unittest
from pathlib import Path

from lookup import online
from lookup.online import OnlineResult, TranslateError

FIXTURES = Path(__file__).parent / "fixtures"
FOX = "The quick brown fox jumps over the lazy dog."


def gtx(name: str) -> bytes:
    return (FIXTURES / "gtx" / f"{name}.json").read_bytes()


def mm(name: str) -> bytes:
    return (FIXTURES / "mymemory" / f"{name}.json").read_bytes()


class ParseGoogleTests(unittest.TestCase):
    def assertReason(self, body, kind, reason, text=None):
        with self.assertRaises(TranslateError) as cm:
            online.parse_google(body, kind, text)
        self.assertEqual(cm.exception.reason, reason)

    def test_word_run(self):
        r = online.parse_google(gtx("word_run"), "word", "run")
        self.assertTrue(r.main)
        self.assertTrue(r.parts)
        self.assertIsInstance(r.parts[0][0], str)
        for _pos, terms in r.parts:
            self.assertTrue(0 < len(terms) <= 5)
        self.assertLessEqual(len(r.parts), 8)
        self.assertEqual(r.src_lang, "en")
        self.assertEqual(r.lemma, "run")
        self.assertEqual(r.provider, "google")
        self.assertIsNone(r.client)

    def test_word_ran_gives_base_form(self):
        r = online.parse_google(gtx("word_ran"), "word", "ran")
        self.assertEqual(r.main, "побежал")
        self.assertEqual(r.lemma, "run")
        self.assertTrue(r.parts)

    def test_word_news_transcription(self):
        r = online.parse_google(gtx("word_news"), "word", "news")
        self.assertEqual(r.transcription, "no͞oz")
        self.assertEqual(r.main, "новости")

    def test_word_books(self):
        r = online.parse_google(gtx("word_books"), "word", "books")
        self.assertEqual(r.lemma, "books")
        self.assertIsNone(r.transcription)

    def test_phrase_and_sentence(self):
        r = online.parse_google(gtx("phrase_breakout"), "phrase", "break out")
        self.assertEqual(r.main, "разразиться")
        self.assertTrue(r.parts)
        s = online.parse_google(gtx("sentence"), "sentence", FOX)
        self.assertTrue(s.main.startswith("Быстрая"))
        self.assertEqual(s.parts, ())

    def test_nonword_is_not_found_for_word_only(self):
        self.assertReason(gtx("nonword"), "word", "not_found", "xyzzyq")
        r = online.parse_google(gtx("nonword"), "sentence", "xyzzyq")
        self.assertEqual(r.main, "ксиззик")

    def test_echo_is_not_found_for_phrase_and_sentence(self):
        body = json.dumps([[["  Hello  World!", "x"]], None, "en"]).encode()
        self.assertReason(body, "phrase", "not_found", "hello world")
        self.assertReason(body, "sentence", "not_found", "Hello   World.")

    def test_bad_kind(self):
        with self.assertRaises(ValueError):
            online.parse_google(gtx("word_run"), "paragraph")

    def test_blocked_bodies(self):
        for body in (
            b"<html>Sorry...</html>",
            b"  <!DOCTYPE html>",
            b"Our systems have detected unusual traffic... automated queries",
            b"Sorry, something went wrong",
        ):
            with self.subTest(body=body):
                self.assertReason(body, "word", "blocked")

    def test_garbage_bodies(self):
        for body in (
            b"",
            b"not json",
            b"{}",
            b"[]",
            b"[1]",
            b"[[]]",
            b"null",
            b"\xff\xfe\xfa[[",
            b'[[[1, 2, 3]]]',
            b'[[[null, null, "x"]]]',
            b"[" * 50000,
        ):
            with self.subTest(body=body[:20]):
                self.assertReason(body, "word", "bad_response")

    def test_malformed_dictionary_entries_are_skipped(self):
        data = [
            [["книга", "book"]],
            [1, ["noun"], [], ["noun", "x"], ["noun", ["a", 2, "b"], None, "book", 1]],
            "en",
        ]
        r = online.parse_google(json.dumps(data).encode(), "word", "book")
        self.assertEqual(r.parts, (("noun", ("a", "b")),))
        self.assertEqual(r.lemma, "book")

    def test_caps_on_parts_and_terms(self):
        block = [[f"pos{i}", [f"t{j}" for j in range(20)], None, "w", 1] for i in range(20)]
        data = [[["x", "y"]], block, "en"]
        r = online.parse_google(json.dumps(data).encode(), "word", "y")
        self.assertEqual(len(r.parts), 8)
        self.assertTrue(all(len(t) == 5 for _p, t in r.parts))


class ParseMyMemoryTests(unittest.TestCase):
    def assertReason(self, body, kind, reason, text=None):
        with self.assertRaises(TranslateError) as cm:
            online.parse_mymemory(body, kind, text)
        self.assertEqual(cm.exception.reason, reason)

    def test_sentence(self):
        r = online.parse_mymemory(mm("sentence"), "sentence", FOX)
        self.assertEqual(r.main, "Коричневая лиса прыгает через собаку.")
        self.assertEqual(r.provider, "mymemory")
        self.assertEqual(r.parts, ())
        self.assertEqual(r.src_lang, "en")

    def test_phrase(self):
        r = online.parse_mymemory(mm("break_out"), "phrase", "break out")
        self.assertTrue(r.main)

    def test_echo_is_not_found(self):
        self.assertReason(mm("xyzzyq"), "phrase", "not_found", "xyzzyq")

    def test_blocked(self):
        def body(**kw):
            d = {"responseData": {"translatedText": "x"}, "responseStatus": 200}
            d.update(kw)
            return json.dumps(d).encode()

        self.assertReason(body(quotaFinished=True), "phrase", "blocked", "a b")
        self.assertReason(body(responseStatus=429), "phrase", "blocked", "a b")
        self.assertReason(body(responseStatus="403"), "phrase", "blocked", "a b")
        warn = {"translatedText": "MYMEMORY WARNING: YOU USED ALL AVAILABLE FREE TRANSLATIONS"}
        self.assertReason(body(responseData=warn), "phrase", "blocked", "a b")

    def test_bad_response(self):
        def body(rd, status=200):
            return json.dumps({"responseData": rd, "responseStatus": status}).encode()

        self.assertReason(body({}), "phrase", "bad_response", "a b")
        self.assertReason(body({"translatedText": 5}), "phrase", "bad_response", "a b")
        self.assertReason(body({"translatedText": "  "}), "phrase", "bad_response", "a b")
        self.assertReason(body({"translatedText": "ok"}, 500), "phrase", "bad_response", "a b")
        self.assertReason(body(None), "phrase", "bad_response", "a b")
        for raw in (b"", b"nope", b"[]", b"null", b"\xff\xfe"):
            self.assertReason(raw, "phrase", "bad_response", "a b")


class PayloadTests(unittest.TestCase):
    def test_round_trip_both_providers(self):
        g = online.parse_google(gtx("word_news"), "word", "news")
        m = online.parse_mymemory(mm("break_out"), "phrase", "break out")
        for r in (g, m):
            payload = r.to_payload()
            json.dumps(payload)  # must be JSON-serialisable
            self.assertEqual(OnlineResult.from_payload(payload), r)
        import dataclasses

        withclient = dataclasses.replace(g, client="gtx")
        self.assertEqual(OnlineResult.from_payload(withclient.to_payload()), withclient)

    def test_from_payload_rejects_bad_shapes(self):
        good = online.parse_google(gtx("word_news"), "word", "news").to_payload()
        bad = [None, [], "x", 5, {}]
        for key in good:
            d = dict(good)
            del d[key]
            bad.append(d)
        for key, value in (
            ("provider", "bing"),
            ("provider", 3),
            ("client", 3),
            ("main", 3),
            ("main", ""),
            ("parts", "x"),
            ("parts", [["noun"]]),
            ("parts", [["noun", "x"]]),
            ("parts", [["noun", [1]]]),
            ("parts", [[1, ["a"]]]),
            ("transcription", 3),
            ("lemma", 3),
            ("src_lang", None),
        ):
            d = dict(good)
            d[key] = value
            bad.append(d)
        for payload in bad:
            with self.subTest(payload=payload):
                self.assertIsNone(OnlineResult.from_payload(payload))


class PrepareTextTests(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(online.prepare_text("  a \n b\t\tc  "), "a b c")

    def test_cuts_at_word_boundary(self):
        text = " ".join(["word"] * 400)
        out = online.prepare_text(text)
        self.assertLessEqual(len(out), online.ONLINE_MAX_CHARS)
        self.assertTrue(out.endswith("word"))
        self.assertGreater(len(out), online.ONLINE_MAX_CHARS - 10)
        self.assertEqual(set(out.split()), {"word"})

    def test_hard_cut_without_spaces(self):
        out = online.prepare_text("x" * 5000)
        self.assertEqual(len(out), online.ONLINE_MAX_CHARS)

    def test_short_text_untouched(self):
        self.assertEqual(online.prepare_text("run"), "run")


class ErrorTests(unittest.TestCase):
    def test_reason_is_message(self):
        e = TranslateError("blocked")
        self.assertEqual(e.reason, "blocked")
        self.assertEqual(str(e), "blocked")
        self.assertIsInstance(e, RuntimeError)

    def test_unknown_reason(self):
        with self.assertRaises(ValueError):
            TranslateError("other")


if __name__ == "__main__":
    unittest.main()
