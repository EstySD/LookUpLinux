import dataclasses
import json
import os
import unittest
from pathlib import Path
from unittest import mock

from lookup import dicts
from lookup.dicts import Article, SearchResult
from tests._support import make_tempdir


class ArticleTests(unittest.TestCase):
    def test_defaults_and_frozen(self):
        a = Article("n", "h", None, (), "t")
        self.assertIsNone(a.transcription)
        self.assertEqual(a.senses, ())
        self.assertIsNone(a.lemma_of)
        self.assertIsNone(a.form_of)
        self.assertIs(a.pointer_only, False)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            a.text = "x"
        self.assertEqual(dataclasses.replace(a, lemma_of="run").lemma_of, "run")

    def test_search_result(self):
        self.assertFalse(SearchResult())
        self.assertIsNone(SearchResult().lemma)
        a = Article("n", "h", None, (), "t")
        self.assertTrue(SearchResult((a,), "run"))
        self.assertFalse(SearchResult((), "run"))

    def test_dict_error_reason(self):
        e = dicts.DictError("corrupt")
        self.assertEqual(e.reason, "corrupt")
        self.assertEqual(str(e), "corrupt")
        self.assertIsInstance(e, RuntimeError)

    def test_constants(self):
        self.assertEqual(dicts.MAX_ARTICLE_BYTES, 16 << 20)
        self.assertEqual(dicts.MAX_ARTICLE_CHARS, 200_000)
        self.assertEqual(dicts.MAX_INDEX_CACHE_BYTES, 256 << 20)


class FoldKeyTests(unittest.TestCase):
    def test_case(self):
        self.assertEqual(dicts.fold_key("Running"), "running")

    def test_apostrophes_and_dashes(self):
        self.assertEqual(dicts.fold_key("Don’t"), "don't")
        self.assertEqual(dicts.fold_key("well—known"), "well-known")
        self.assertEqual(dicts.fold_key("a–b"), "a-b")

    def test_whitespace(self):
        self.assertEqual(dicts.fold_key("  Break   Out "), "break out")

    def test_nfc(self):
        self.assertEqual(dicts.fold_key("café"), dicts.fold_key("café"))

    def test_idempotent(self):
        for s in ("Don’t  STOP", "café", "Straße", "İstanbul", "a‑b"):
            once = dicts.fold_key(s)
            self.assertEqual(dicts.fold_key(once), once)


class CleanTextTests(unittest.TestCase):
    def test_control_chars(self):
        self.assertEqual(dicts.clean_text("a\x00b\x07c\x1bd\x7fe"), "abcde")

    def test_newline_and_tab_kept(self):
        self.assertEqual(dicts.clean_text("a\tb\nc"), "a\tb\nc")

    def test_bidi_and_zero_width(self):
        self.assertEqual(
            dicts.clean_text("a‮b​c⁦d‏e﻿"), "abcde"
        )

    def test_line_endings(self):
        self.assertEqual(dicts.clean_text("a\r\nb\rc"), "a\nb\nc")

    def test_spaces_and_lines(self):
        self.assertEqual(dicts.clean_text("a    b\n   c   \n"), "a b\nc")

    def test_blank_lines(self):
        self.assertEqual(dicts.clean_text("a\n\n\n\n\nb"), "a\n\nb")
        self.assertEqual(dicts.clean_text("a\n \n \n \nb"), "a\n\nb")

    def test_strip(self):
        self.assertEqual(dicts.clean_text("\n\n  x  \n\n"), "x")

    def test_truncates(self):
        out = dicts.clean_text("x" * (dicts.MAX_ARTICLE_CHARS + 500))
        self.assertEqual(len(out), dicts.MAX_ARTICLE_CHARS)

    def test_truncates_at_line_boundary(self):
        line = "y" * 99 + "\n"
        out = dicts.clean_text(line * 5000)
        self.assertLessEqual(len(out), dicts.MAX_ARTICLE_CHARS)
        self.assertTrue(out.endswith("y" * 99))
        self.assertTrue(all(len(x) == 99 for x in out.split("\n")))


class HtmlToTextTests(unittest.TestCase):
    def test_basic(self):
        out = dicts.html_to_text(
            "<b>run</b> <i>[rʌn]</i><br>1. <span>бежать</span>"
            "<p>2. идти</p>"
        )
        self.assertEqual(
            out, "run [rʌn]\n1. бежать\n2. идти"
        )
        self.assertNotIn("<", out)
        self.assertNotIn(">", out)

    def test_entities(self):
        self.assertEqual(dicts.html_to_text("a &amp; b &lt;c&gt; &#1088;"), "a & b <c> р")

    def test_script_and_style_dropped(self):
        out = dicts.html_to_text(
            "x<script>alert(1)</script>y<style>p{color:red}</style>z"
        )
        self.assertEqual(out, "xyz")

    def test_garbage_never_raises(self):
        for s in ("<<b>x", "<a href=", "<", ">", "</", "<!--", "<![CDATA[", "&", "&#xZZ;", ""):
            out = dicts.html_to_text(s)
            self.assertIsInstance(out, str)
            self.assertNotIn("\x00", out)
        self.assertIn("x", dicts.html_to_text("<<b>x"))

    def test_parser_failure_falls_back(self):
        with mock.patch.object(
            dicts._TextExtractor, "feed", side_effect=RuntimeError("boom")
        ):
            self.assertEqual(dicts.html_to_text("<b>run</b> fast"), "run fast")

    def test_xdxf_fragment(self):
        out = dicts.html_to_text("<k>run</k><tr>rʌn</tr><ex>I run</ex>")
        for part in ("run", "rʌn", "I run"):
            self.assertIn(part, out)
        self.assertNotIn("<", out)

    def test_control_chars_removed(self):
        self.assertEqual(dicts.html_to_text("<b>a‮b\x00c</b>"), "abc")

    def test_no_markup_survives_deep_nesting(self):
        out = dicts.html_to_text("<b>" * 5000 + "deep" + "</b>" * 5000)
        self.assertEqual(out, "deep")


class IndexCacheTests(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)
        self.src = self.root / "d.dsl"
        self.src.write_bytes(b"hello")

    def test_round_trip(self):
        payload = {"keys": ["a", "b"], "n": 3, "t": "б"}
        self.assertTrue(dicts.index_cache_save(self.src, "dsl", payload))
        self.assertEqual(dicts.index_cache_load(self.src, "dsl"), payload)

    def test_path_under_cache_dir(self):
        p = dicts.index_cache_path(self.src, "dsl")
        self.assertEqual(p.parent, Path(os.environ["LOOKUP_CACHE"]) / "index")
        self.assertTrue(p.name.endswith("-dsl.json"))
        self.assertEqual(len(p.name), 32 + len("-dsl.json"))
        self.assertFalse(p.parent.exists())

    def test_bad_tag(self):
        with self.assertRaises(ValueError):
            dicts.index_cache_path(self.src, "../x")
        self.assertFalse(dicts.index_cache_save(self.src, "../x", {}))
        self.assertIsNone(dicts.index_cache_load(self.src, "../x"))

    def test_miss_without_cache(self):
        self.assertIsNone(dicts.index_cache_load(self.src, "dsl"))

    def test_size_change_is_miss(self):
        dicts.index_cache_save(self.src, "dsl", [1])
        st = os.stat(self.src)
        self.src.write_bytes(b"hello!")
        os.utime(self.src, ns=(st.st_atime_ns, st.st_mtime_ns))
        self.assertIsNone(dicts.index_cache_load(self.src, "dsl"))

    def test_mtime_change_is_miss(self):
        dicts.index_cache_save(self.src, "dsl", [1])
        st = os.stat(self.src)
        os.utime(self.src, ns=(st.st_atime_ns, st.st_mtime_ns + 2_000_000_000))
        self.assertIsNone(dicts.index_cache_load(self.src, "dsl"))

    def test_missing_source_is_miss(self):
        dicts.index_cache_save(self.src, "dsl", [1])
        self.src.unlink()
        self.assertIsNone(dicts.index_cache_load(self.src, "dsl"))

    def test_tags_are_separate(self):
        dicts.index_cache_save(self.src, "dsl", [1])
        self.assertIsNone(dicts.index_cache_load(self.src, "mdx"))

    def _rewrite(self, **changes):
        path = dicts.index_cache_path(self.src, "dsl")
        wrapper = json.loads(path.read_text(encoding="utf-8"))
        wrapper.update(changes)
        path.write_text(json.dumps(wrapper), encoding="utf-8")

    def test_tampered_fields_are_misses(self):
        dicts.index_cache_save(self.src, "dsl", [1])
        self.assertEqual(dicts.index_cache_load(self.src, "dsl"), [1])
        for field, bad in (
            ("format", 2),
            ("format", True),
            ("tag", "mdx"),
            ("path", str(self.root / "other.dsl")),
            ("size", 999),
            ("mtime_ns", 1),
        ):
            dicts.index_cache_save(self.src, "dsl", [1])
            self._rewrite(**{field: bad})
            self.assertIsNone(dicts.index_cache_load(self.src, "dsl"), field)

    def test_missing_data_key_is_miss(self):
        dicts.index_cache_save(self.src, "dsl", [1])
        path = dicts.index_cache_path(self.src, "dsl")
        wrapper = json.loads(path.read_text(encoding="utf-8"))
        del wrapper["data"]
        path.write_text(json.dumps(wrapper), encoding="utf-8")
        self.assertIsNone(dicts.index_cache_load(self.src, "dsl"))

    def test_corrupt_files_are_misses(self):
        dicts.index_cache_save(self.src, "dsl", [1])
        path = dicts.index_cache_path(self.src, "dsl")
        for blob in (b"{not json", b"[1, 2]", b"\xff\xfe", b"", b"null"):
            path.write_bytes(blob)
            self.assertIsNone(dicts.index_cache_load(self.src, "dsl"))

    def test_oversized_cache_is_miss(self):
        dicts.index_cache_save(self.src, "dsl", ["x" * 200])
        with mock.patch.object(dicts, "MAX_INDEX_CACHE_BYTES", 50):
            self.assertIsNone(dicts.index_cache_load(self.src, "dsl"))

    def test_oversized_payload_not_saved(self):
        with mock.patch.object(dicts, "MAX_INDEX_CACHE_BYTES", 50):
            self.assertFalse(dicts.index_cache_save(self.src, "dsl", ["x" * 200]))
        self.assertFalse(dicts.index_cache_path(self.src, "dsl").exists())

    def test_save_failure_returns_false(self):
        blocker = self.root / "blocker"
        blocker.write_text("file", encoding="utf-8")
        with mock.patch.dict(os.environ, {"LOOKUP_CACHE": str(blocker / "sub")}):
            self.assertFalse(dicts.index_cache_save(self.src, "dsl", [1]))
            self.assertIsNone(dicts.index_cache_load(self.src, "dsl"))

    def test_unserialisable_payload_returns_false(self):
        self.assertFalse(dicts.index_cache_save(self.src, "dsl", {1, 2}))
        self.assertFalse(dicts.index_cache_save(self.src, "dsl", object()))

    def test_missing_source_save_returns_false(self):
        self.assertFalse(dicts.index_cache_save(self.root / "nope.dsl", "dsl", [1]))

    def test_no_temp_files_left(self):
        dicts.index_cache_save(self.src, "dsl", [1])
        dicts.index_cache_save(self.src, "dsl", [2])
        names = [p.name for p in dicts.index_cache_path(self.src, "dsl").parent.iterdir()]
        self.assertEqual(len(names), 1)
        self.assertFalse(names[0].startswith(".tmp-"))

    @unittest.skipIf(os.name != "posix", "POSIX modes")
    def test_modes(self):
        dicts.index_cache_save(self.src, "dsl", [1])
        path = dicts.index_cache_path(self.src, "dsl")
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)

    def test_json_only(self):
        dicts.index_cache_save(self.src, "dsl", {"a": 1})
        path = dicts.index_cache_path(self.src, "dsl")
        self.assertEqual(path.read_bytes()[:1], b"{")
        source = Path(dicts.__file__).read_text(encoding="utf-8").lower()
        self.assertNotIn("pickle", source)
        self.assertNotIn("marshal", source)


if __name__ == "__main__":
    unittest.main()
