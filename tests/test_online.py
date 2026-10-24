"""Online translation client: parsers, payload round trip, text preparation (D-13, D-14, D-30, D-31)."""
import dataclasses
import http.client
import json
import socket
import ssl
import unittest
import urllib.error
import urllib.parse
from pathlib import Path
from unittest import mock

from lookup import online
from lookup.online import OnlineResult, TranslateError
from tests._support import forbid_network

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


class FakeClock:
    def __init__(self, now=0.0):
        self.now = now

    def __call__(self):
        return self.now


class FakeResponse:
    """Context-manager response that serves `body` (or `size` zero bytes) in read() chunks."""

    def __init__(self, body=b"", url="https://translate.googleapis.com/x", size=None,
                 clock=None, tick=0.0):
        self.body = body
        self.size = len(body) if size is None else size
        self.url = url
        self.clock = clock
        self.tick = tick
        self.served = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def geturl(self):
        return self.url

    def read(self, n=-1):
        if self.clock is not None:
            self.clock.now += self.tick
        left = self.size - self.served
        n = left if n is None or n < 0 else min(n, left)
        start = self.served
        self.served += n
        if self.body:
            return self.body[start:start + n]
        return b"\0" * n


def fixed_fetch(results):
    """A fake online._fetch: `results` maps a substring of the URL to bytes or a TranslateError reason."""
    calls = []

    def fake(url, timeout, deadline_at, clock, expected_host):
        calls.append((url, timeout, deadline_at, expected_host))
        for key, value in results.items():
            if key in url:
                if isinstance(value, str):
                    raise TranslateError(value)
                return value
        raise AssertionError("unexpected url " + url)

    fake.calls = calls
    return fake


def query_of(url):
    return urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)


class FetchTests(unittest.TestCase):
    URL = "https://translate.googleapis.com/translate_a/single?q=secretword"

    def fetch(self, side_effect=None, response=None, clock=None, deadline_at=100.0, timeout=2.5):
        clock = clock or FakeClock()
        with mock.patch("urllib.request.urlopen", side_effect=side_effect,
                        return_value=response) as m:
            try:
                return online._fetch(self.URL, timeout, deadline_at, clock, online.GOOGLE_HOST), m
            except TranslateError as e:
                return e, m

    def test_returns_body_and_passes_timeout(self):
        body = b"x" * 40000
        got, m = self.fetch(response=FakeResponse(body))
        self.assertEqual(got, body)
        self.assertEqual(m.call_args.kwargs["timeout"], 2.5)
        self.assertEqual(m.call_args.args[0].full_url, self.URL)

    def test_google_url_parameters(self):
        clock = FakeClock()
        resp = FakeResponse(gtx("word_run"))
        with mock.patch("urllib.request.urlopen", return_value=resp) as m:
            r = online.google_translate("run it", "word", "gtx", 3.0, clock)
        url = m.call_args.args[0].full_url
        self.assertTrue(url.startswith("https://translate.googleapis.com/translate_a/single?"))
        q = query_of(url)
        self.assertEqual(q["client"], ["gtx"])
        self.assertEqual((q["sl"], q["tl"]), (["en"], ["ru"]))
        self.assertEqual(q["dt"], ["t", "bd", "rm"])
        self.assertEqual(q["q"], ["run it"])
        self.assertNotIn(" ", url)
        self.assertEqual(m.call_args.kwargs["timeout"], 3.0)
        self.assertEqual(r.client, "gtx")

    def test_http_errors(self):
        for code, reason in ((429, "blocked"), (403, "blocked"), (500, "bad_response"),
                             (404, "bad_response")):
            with self.subTest(code=code):
                err = urllib.error.HTTPError(self.URL, code, "msg", {}, None)
                got, _ = self.fetch(side_effect=err)
                self.assertIsInstance(got, TranslateError)
                self.assertEqual(got.reason, reason)

    def test_transport_errors(self):
        cases = (
            (urllib.error.URLError(socket.gaierror(-2, "name")), "no_network"),
            (urllib.error.URLError(ConnectionRefusedError()), "no_network"),
            (urllib.error.URLError(ssl.SSLCertVerificationError()), "no_network"),
            (urllib.error.URLError(socket.timeout()), "timeout"),
            (urllib.error.URLError(TimeoutError()), "timeout"),
            (TimeoutError(), "timeout"),
            (ConnectionResetError(), "no_network"),
            (OSError(), "no_network"),
            (http.client.IncompleteRead(b"ab"), "bad_response"),
        )
        for exc, reason in cases:
            with self.subTest(exc=repr(exc)):
                got, _ = self.fetch(side_effect=exc)
                self.assertIsInstance(got, TranslateError)
                self.assertEqual(got.reason, reason)

    def test_oversized_body_stops_early(self):
        resp = FakeResponse(size=50 * online.MAX_BODY)
        got, _ = self.fetch(response=resp)
        self.assertEqual(got.reason, "bad_response")
        self.assertLessEqual(resp.served, online.MAX_BODY + 16 * 1024)

    def test_cross_host_redirect(self):
        resp = FakeResponse(b"[]", url="https://evil.example/translate_a/single")
        got, _ = self.fetch(response=resp)
        self.assertEqual(got.reason, "bad_response")

    def test_downgrade_to_http(self):
        resp = FakeResponse(b"[]", url="http://translate.googleapis.com/x")
        got, _ = self.fetch(response=resp)
        self.assertEqual(got.reason, "bad_response")

    def test_deadline_passes_between_chunks(self):
        clock = FakeClock()
        resp = FakeResponse(b"y" * 100000, clock=clock, tick=0.6)
        got, _ = self.fetch(response=resp, clock=clock, deadline_at=1.0)
        self.assertEqual(got.reason, "timeout")
        self.assertLess(resp.served, 100000)

    def test_error_never_carries_the_query(self):
        errors = (
            urllib.error.HTTPError(self.URL, 429, "secretword", {}, None),
            urllib.error.URLError("secretword"),
            OSError("secretword"),
        )
        for exc in errors:
            with self.subTest(exc=type(exc).__name__):
                got, _ = self.fetch(side_effect=exc)
                self.assertIsInstance(got, TranslateError)
                self.assertIsNone(got.__cause__)
                self.assertTrue(got.__suppress_context__)
                self.assertNotIn("secretword", str(got))
                self.assertNotIn("secretword", repr(got))

    def test_no_network_calls_in_pure_functions(self):
        m = forbid_network(self)
        online.parse_google(gtx("word_run"), "word", "run")
        online.parse_mymemory(mm("sentence"), "sentence", FOX)
        online.prepare_text("a b")
        OnlineResult.from_payload(None)
        self.assertEqual(m.call_count, 0)


class ChainTests(unittest.TestCase):
    def run_chain(self, results, text="run", kind="word", **kw):
        fake = fixed_fetch(results)
        with mock.patch.object(online, "_fetch", fake):
            try:
                out = online.translate_online(text, kind, clock=FakeClock(), **kw)
            except TranslateError as e:
                out = e
        return out, fake

    def clients_called(self, fake):
        return [query_of(c[0]).get("client", ["mm"])[0] for c in fake.calls]

    def test_first_success_short_circuits(self):
        out, fake = self.run_chain({"client=": gtx("word_run")})
        self.assertEqual(out.client, "gtx")
        self.assertEqual(self.clients_called(fake), ["gtx"])
        self.assertEqual(fake.calls[0][3], online.GOOGLE_HOST)

    def test_blocked_then_next_client(self):
        out, fake = self.run_chain({"client=gtx": "blocked", "client=dict-chrome-ex": gtx("word_run")})
        self.assertEqual(out.client, "dict-chrome-ex")
        self.assertEqual(self.clients_called(fake), ["gtx", "dict-chrome-ex"])

    def test_first_client_goes_first_without_repeat(self):
        out, fake = self.run_chain(
            {"client=at": "bad_response", "client=gtx": "timeout", "client=dict-chrome-ex": "blocked"},
            first_client="at")
        self.assertEqual(self.clients_called(fake), ["at", "gtx", "dict-chrome-ex"])
        self.assertEqual(out.reason, "blocked")

    def test_unknown_first_client_ignored(self):
        _out, fake = self.run_chain({"client=": "blocked"}, first_client="nope")
        self.assertEqual(self.clients_called(fake), ["gtx", "dict-chrome-ex", "at"])

    def test_client_names_are_sanitised(self):
        bad = ["a b", "a/b", "x&y=1", "c" * 40, "", 5]
        _out, fake = self.run_chain({"client=": "blocked"}, clients=bad + ["ok", "ok"])
        self.assertEqual(self.clients_called(fake), ["ok"])
        for url, *_ in fake.calls:
            self.assertNotIn("&y=1", url)
        _out, fake = self.run_chain({"client=": "blocked"}, clients=[])
        self.assertEqual(self.clients_called(fake), list(online.DEFAULT_CLIENTS))
        _out, fake = self.run_chain({"client=": "blocked"}, clients=bad)
        self.assertEqual(self.clients_called(fake), list(online.DEFAULT_CLIENTS))

    def test_not_found_ends_chain(self):
        out, fake = self.run_chain({"client=gtx": gtx("nonword")}, text="xyzzyq")
        self.assertEqual(out.reason, "not_found")
        self.assertEqual(len(fake.calls), 1)

    def test_nonword_transliteration_is_fine_for_a_phrase(self):
        out, fake = self.run_chain({"client=gtx": gtx("nonword")}, text="xyzzyq", kind="phrase")
        self.assertIsInstance(out, OnlineResult)
        self.assertEqual(len(fake.calls), 1)

    def test_phrase_falls_through_to_mymemory(self):
        out, fake = self.run_chain(
            {"client=": "blocked", "api.mymemory": mm("break_out")}, text="break out", kind="phrase")
        self.assertEqual(out.provider, "mymemory")
        self.assertEqual(len(fake.calls), 4)
        self.assertEqual(fake.calls[-1][3], online.MYMEMORY_HOST)

    def test_sentence_reason_priority_includes_mymemory(self):
        out, _ = self.run_chain(
            {"client=": "timeout", "api.mymemory": "blocked"}, text=FOX, kind="sentence")
        self.assertEqual(out.reason, "blocked")

    def test_word_never_reaches_mymemory(self):
        out, fake = self.run_chain({"client=": "blocked"})
        self.assertEqual(out.reason, "blocked")
        self.assertTrue(all("mymemory" not in c[0] for c in fake.calls))

    def test_mymemory_word_is_not_found_without_transport(self):
        m = forbid_network(self)
        with self.assertRaises(TranslateError) as cm:
            online.mymemory_translate("run", "word", 3.0, FakeClock())
        self.assertEqual(cm.exception.reason, "not_found")
        self.assertEqual(m.call_count, 0)

    def test_mymemory_url_carries_no_identity(self):
        fake = fixed_fetch({"api.mymemory": mm("break_out")})
        with mock.patch.object(online, "_fetch", fake):
            online.mymemory_translate("break out", "phrase", 3.0, FakeClock())
        url = fake.calls[0][0]
        self.assertTrue(url.startswith("https://api.mymemory.translated.net/get?"))
        q = query_of(url)
        self.assertEqual(q["q"], ["break out"])
        self.assertEqual(q["langpair"], ["en|ru"])
        self.assertEqual(sorted(q), ["langpair", "q"])

    def test_reason_priority(self):
        cases = (
            (("blocked", "bad_response", "timeout"), "blocked"),
            (("timeout", "bad_response", "no_network"), "bad_response"),
            (("no_network", "timeout", "no_network"), "timeout"),
            (("no_network", "no_network", "no_network"), "no_network"),
        )
        for reasons, expected in cases:
            with self.subTest(reasons=reasons):
                results = dict(zip(("client=gtx", "client=dict-chrome-ex", "client=at"), reasons))
                out, _ = self.run_chain(results)
                self.assertEqual(out.reason, expected)

    def test_argument_validation(self):
        for args in (("", "word"), ("  ", "word"), ("run", "paragraph")):
            with self.assertRaises(ValueError):
                online.translate_online(*args)

    def test_long_text_is_cut_before_sending(self):
        fake = fixed_fetch({"client=": gtx("sentence")})
        with mock.patch.object(online, "_fetch", fake):
            online.translate_online("word " * 1000, "sentence", clock=FakeClock())
        self.assertLessEqual(len(query_of(fake.calls[0][0])["q"][0]), online.ONLINE_MAX_CHARS)


class DeadlineTests(unittest.TestCase):
    def failing_fetch(self, clock, step, reason="timeout"):
        calls = []

        def fake(url, timeout, deadline_at, clk, expected_host):
            calls.append((url, timeout, deadline_at))
            clock.now += step
            raise TranslateError(reason)

        fake.calls = calls
        return fake

    def test_shared_budget_stops_the_chain(self):
        clock = FakeClock()
        fake = self.failing_fetch(clock, 1.4)
        with mock.patch.object(online, "_fetch", fake):
            with self.assertRaises(TranslateError) as cm:
                online.translate_online("run", "word", clock=clock)
        self.assertEqual(cm.exception.reason, "timeout")
        self.assertEqual(len(fake.calls), 2)
        self.assertAlmostEqual(fake.calls[0][1], 3.0)
        self.assertAlmostEqual(fake.calls[1][1], 1.6)
        for _url, timeout, _d in fake.calls:
            self.assertGreaterEqual(timeout, online.MIN_ATTEMPT_S)
        self.assertLessEqual(clock.now, online.DEADLINE_S + online.MIN_ATTEMPT_S)

    def test_mymemory_skipped_when_time_is_gone(self):
        clock = FakeClock()
        fake = self.failing_fetch(clock, 1.0)
        with mock.patch.object(online, "_fetch", fake):
            with self.assertRaises(TranslateError) as cm:
                online.translate_online("break out", "phrase", clock=clock, clients=["a", "b", "c"])
        self.assertEqual(cm.exception.reason, "timeout")
        self.assertEqual(len(fake.calls), 3)
        self.assertTrue(all("mymemory" not in c[0] for c in fake.calls))

    def test_tiny_budget_makes_no_request(self):
        clock = FakeClock()
        fake = self.failing_fetch(clock, 0.0)
        with mock.patch.object(online, "_fetch", fake):
            with self.assertRaises(TranslateError) as cm:
                online.translate_online("run", "word", clock=clock, deadline_s=0.2)
        self.assertEqual(cm.exception.reason, "timeout")
        self.assertEqual(fake.calls, [])

    def test_earlier_blocked_wins_over_timeout_stop(self):
        clock = FakeClock()
        calls = []

        def fake(url, timeout, deadline_at, clk, expected_host):
            calls.append(timeout)
            clock.now += 2.8
            raise TranslateError("blocked")

        with mock.patch.object(online, "_fetch", fake):
            with self.assertRaises(TranslateError) as cm:
                online.translate_online("run", "word", clock=clock)
        self.assertEqual(cm.exception.reason, "blocked")
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
