"""DSL reader tests: encodings, headword groups, markup, index cache, hostile input (D-02, D-05, D-06, D-08, D-33)."""
import json
import os
import time
import unittest
from unittest import mock

from lookup import dsl
from lookup.dictzip import DictzipFile
from lookup.dicts import Article, DictError, fold_key, index_cache_path
from lookup.dsl import MAX_VARIANTS, expand_headword, open_dsl
from tests._dsl_writer import write_dsl
from tests._support import make_tempdir

TWO = [
    (["run"], ["[m1]to move fast[/m]"]),
    (["Сон"], ["[m1]sleep[/m]"]),
]


class ExpandHeadwordTests(unittest.TestCase):
    def test_optional_suffix(self):
        self.assertEqual(expand_headword("word{s}"), ["word", "words"])

    def test_optional_in_the_middle(self):
        self.assertEqual(expand_headword("colo{u}r"), ["color", "colour"])

    def test_no_braces(self):
        self.assertEqual(expand_headword("run"), ["run"])

    def test_two_groups_in_stable_order(self):
        self.assertEqual(expand_headword("a{b}{c}"), ["a", "ab", "ac", "abc"])
        self.assertEqual(expand_headword("a{b}{c}"), expand_headword("a{b}{c}"))

    def test_hard_cap(self):
        ten = "a{1}b{2}c{3}d{4}e{5}f{6}g{7}h{8}i{9}j{0}"
        self.assertEqual(len(expand_headword(ten)), MAX_VARIANTS)
        self.assertEqual(MAX_VARIANTS, 32)
        forty = "".join("x{%d}" % i for i in range(40))
        self.assertEqual(len(expand_headword(forty)), MAX_VARIANTS)

    def test_primary_spelling_comes_first(self):
        self.assertEqual(expand_headword("a{1}b{2}c{3}d{4}e{5}f{6}g{7}")[0], "abcdefg")

    def test_escaped_braces_are_literal(self):
        self.assertEqual(expand_headword("\\{x\\}"), ["{x}"])

    def test_escaped_backslash_and_other_characters(self):
        self.assertEqual(expand_headword("a\\\\b"), ["a\\b"])
        self.assertEqual(expand_headword("a\\(b\\)"), ["a(b)"])

    def test_trailing_backslash_and_unclosed_brace_are_literal(self):
        self.assertEqual(expand_headword("ab\\"), ["ab\\"])
        self.assertEqual(expand_headword("ab{c"), ["ab{c"])

    def test_whitespace_stripped_and_empty_dropped(self):
        self.assertEqual(expand_headword("  run  "), ["run"])
        self.assertEqual(expand_headword("   "), [])
        self.assertEqual(expand_headword(""), [])
        self.assertEqual(expand_headword("{x}"), ["x"])
        self.assertEqual(expand_headword("run{ }"), ["run"])

    def test_duplicates_removed(self):
        self.assertEqual(expand_headword("a{}"), ["a"])


class _Base(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)
        self.dir = self.root / "dicts"

    def write(self, entries=TWO, stem="book.dsl", **kw):
        return write_dsl(self.dir / stem, entries, **kw)

    def open(self, path):
        d = open_dsl(path)
        self.addCleanup(d.close)  # closed before the temp dir goes (Windows)
        return d


class DslReaderTests(_Base):
    def test_open_and_lookup(self):
        d = self.open(self.write(name="Test Dict"))
        self.assertEqual((d.name, d.fmt), ("Test Dict", "dsl"))
        self.assertEqual((d.entry_count, d.skipped_entries), (2, 0))
        self.assertEqual(d.path, self.dir / "book.dsl")
        arts = d.lookup("run")
        self.assertEqual(len(arts), 1)
        a = arts[0]
        self.assertIsInstance(a, Article)
        self.assertEqual((a.dict_name, a.headword), ("Test Dict", "run"))
        self.assertIn("to move fast", a.text)
        self.assertTrue(d.has("run"))
        self.assertFalse(d.has("nope"))
        self.assertEqual(d.lookup("nope"), [])

    def test_every_common_encoding_opens_the_same(self):
        for encoding, bom in (
            ("utf-16", True),
            ("utf-16", False),
            ("utf-16-be", True),
            ("utf-16-be", False),
            ("utf-8", True),
            ("utf-8", False),
        ):
            for newline in ("\r\n", "\n"):
                with self.subTest(encoding=encoding, bom=bom, newline=newline):
                    path = self.write(stem="%s-%s-%d.dsl" % (encoding, bom, len(newline)), name="Enc",
                                      encoding=encoding, bom=bom, newline=newline)
                    d = self.open(path)
                    self.assertEqual((d.name, d.entry_count), ("Enc", 2))
                    self.assertIn("to move fast", d.lookup("run")[0].text)
                    self.assertEqual(d.lookup("сон")[0].headword, "Сон")
                    self.assertIn("sleep", d.lookup("сон")[0].text)

    def test_utf16_without_bom_starts_with_a_bare_hash(self):
        le = self.write(stem="le.dsl", bom=False).read_bytes()
        be = self.write(stem="be.dsl", bom=False, encoding="utf-16-be").read_bytes()
        self.assertEqual(le[:2], b"\x23\x00")
        self.assertEqual(be[:2], b"\x00\x23")

    def test_header_values(self):
        d = self.open(self.write(index_language="English", contents_language="Russian"))
        self.assertEqual((d.index_language, d.contents_language), ("English", "Russian"))
        d2 = self.open(self.write(stem="bare.dsl", index_language=None, contents_language=None))
        self.assertEqual((d2.index_language, d2.contents_language), (None, None))

    def test_name_falls_back_to_the_file_stem(self):
        self.assertEqual(self.open(self.write(stem="plain.dsl", name=None)).name, "plain")
        self.assertEqual(self.open(self.write(stem="packed.dsl", name=None, dz=True)).name, "packed")

    def test_consecutive_headwords_share_one_article(self):
        d = self.open(self.write([(["colour", "color"], ["[m1]a hue[/m]"]), (["zed"], ["[m1]z[/m]"])]))
        self.assertEqual(d.entry_count, 2)
        for key, head in (("colour", "colour"), ("color", "color")):
            arts = d.lookup(key)
            self.assertEqual(len(arts), 1)
            self.assertEqual(arts[0].headword, head)
            self.assertIn("a hue", arts[0].text)

    def test_blank_lines_inside_an_article_do_not_end_it(self):
        d = self.open(self.write([(["run"], ["[m1]first[/m]", "", "", "[m1]second[/m]"]), (["sit"], ["[m1]x[/m]"])]))
        text = d.lookup("run")[0].text
        self.assertIn("first", text)
        self.assertIn("second", text)
        self.assertEqual(d.entry_count, 2)

    def test_headword_without_a_body_is_ignored(self):
        d = self.open(self.write([(["run"], ["[m1]x[/m]"]), (["orphan"], [])]))
        self.assertEqual(d.entry_count, 1)
        self.assertFalse(d.has("orphan"))

    def test_tab_indented_body(self):
        d = self.open(self.write([(["run"], ["\t[m1]tabbed[/m]"])]))
        self.assertIn("tabbed", d.lookup("run")[0].text)

    def test_lookup_uses_the_folded_key_not_the_query(self):
        d = self.open(self.write([(["Run"], ["[m1]x[/m]"])]))
        self.assertTrue(d.has("run"))
        self.assertEqual(d.lookup("run")[0].headword, "Run")
        self.assertFalse(d.has("Run"))

    def test_optional_parts_register_both_spellings(self):
        d = self.open(self.write([(["word{s}"], ["[m1]x[/m]"])]))
        self.assertEqual(d.entry_count, 1)
        self.assertEqual(d.lookup("word")[0].headword, "word")
        self.assertEqual(d.lookup("words")[0].headword, "word")

    def test_same_key_from_two_headword_lines_of_one_article_is_returned_once(self):
        d = self.open(self.write([(["Run", "run"], ["[m1]x[/m]"])]))
        self.assertEqual(len(d.lookup("run")), 1)

    def test_oversized_articles_are_skipped_and_counted(self):
        entries = [(["small"], ["[m1]ok[/m]"]), (["big"], ["[m1]" + "x" * 300 + "[/m]"]), (["after"], ["[m1]ok[/m]"])]
        path = self.write(entries)
        with mock.patch.object(dsl, "MAX_ARTICLE_BYTES", 100):
            d = self.open(path)
        self.assertEqual((d.entry_count, d.skipped_entries), (2, 1))
        self.assertEqual(d.lookup("big"), [])
        self.assertFalse(d.has("big"))
        self.assertTrue(d.has("after"))

    def test_dictzip_returns_the_same_articles_as_plain(self):
        entries = [(["w%03d" % i], ["[m1]definition number %d [/m]" % i * 40]) for i in range(60)]
        plain = self.open(self.write(entries, stem="plain.dsl", name="B"))
        orig = DictzipFile.read_all
        with mock.patch.object(DictzipFile, "read_all", autospec=True, side_effect=orig) as read_all:
            packed = self.open(self.write(entries, stem="packed.dsl", name="B", dz=True, chunk_len=512))
            self.assertEqual(read_all.call_count, 1)  # the cold index decompresses once
            self.assertEqual(packed.entry_count, 60)
            for i in (0, 17, 59):
                self.assertEqual(packed.lookup("w%03d" % i), plain.lookup("w%03d" % i))
            self.assertEqual(read_all.call_count, 1)  # articles are random access afterwards

    def test_non_bmp_and_a_0a_byte_never_split_lines(self):
        # U+0A41 is 41 0A in LE; followed by U+0100 (00 01) it shows the bytes 0A 00 at an odd
        # offset; in BE, U+0100 then U+0A41 shows 00 0A at an odd offset
        tricky = "ਁĀ and Āਁ \U0001F600 end"
        for encoding in ("utf-16", "utf-16-be"):
            with self.subTest(encoding=encoding):
                entries = [
                    (["first" + tricky], ["[m1]" + tricky + " Привет[/m]", "[m1]second line[/m]"]),
                    (["later"], ["[m1]body[/m]"]),
                ]
                d = self.open(self.write(entries, stem=encoding + ".dsl", encoding=encoding))
                self.assertEqual(d.entry_count, 2)
                art = d.lookup(fold_key("first" + tricky))[0]
                self.assertIn(tricky + " Привет", art.text)
                self.assertIn("second line", art.text)
                self.assertIn("body", d.lookup("later")[0].text)

    def test_a_file_above_the_size_cap_is_refused(self):
        path = self.write()
        with mock.patch.object(dsl, "MAX_DSL_BYTES", 100):
            with self.assertRaises(DictError) as cm:
                open_dsl(path)
        self.assertEqual(cm.exception.reason, "too_large")
        packed = self.write(stem="packed.dsl", dz=True)
        with mock.patch.object(dsl, "MAX_DSL_BYTES", 100):
            with self.assertRaises(DictError) as cm:
                open_dsl(packed)
        self.assertEqual(cm.exception.reason, "too_large")

    def test_no_articles_is_empty(self):
        for stem, entries in (("header.dsl", []), ("orphan.dsl", [(["lonely"], [])])):
            with self.subTest(stem=stem):
                with self.assertRaises(DictError) as cm:
                    open_dsl(self.write(entries, stem=stem))
                self.assertEqual(cm.exception.reason, "empty")

    def test_empty_files_are_empty(self):
        self.dir.mkdir(parents=True)
        for stem, raw in (("zero.dsl", b""), ("bom.dsl", b"\xff\xfe")):
            with self.subTest(stem=stem):
                (self.dir / stem).write_bytes(raw)
                with self.assertRaises(DictError) as cm:
                    open_dsl(self.dir / stem)
                self.assertEqual(cm.exception.reason, "empty")

    def test_missing_file_is_unreadable(self):
        with self.assertRaises(DictError) as cm:
            open_dsl(self.dir / "absent.dsl")
        self.assertEqual(cm.exception.reason, "unreadable")

    def test_broken_dictzip_is_corrupt(self):
        self.dir.mkdir(parents=True)
        bad = self.dir / "bad.dsl.dz"
        bad.write_bytes(b"this is not gzip at all")
        with self.assertRaises(DictError) as cm:
            open_dsl(bad)
        self.assertEqual(cm.exception.reason, "corrupt")

    def test_close_is_idempotent(self):
        d = self.open(self.write())
        d.close()
        d.close()


def convert(*lines, head="run"):
    """Run the markup converter on body lines the way a reader hands them over."""
    return dsl._convert("D", head, "\n".join(" " + line for line in lines))


class DslMarkupTests(unittest.TestCase):
    def test_fixture_article(self):
        a = convert(
            "[m1][t]rʌn[/t][/m]",
            "[m1][p]v[/p] [trn]бежать[/trn]; [trn]бегать[/trn][/m]",
            "[m1][p]n[/p] [trn]бег[/trn][/m]",
        )
        self.assertEqual((a.dict_name, a.headword), ("D", "run"))
        self.assertEqual(a.transcription, "rʌn")
        self.assertEqual(a.senses, (("v", ("бежать", "бегать")), ("n", ("бег",))))
        self.assertTrue(a.text.startswith("[rʌn]"))
        self.assertIn("бежать", a.text)
        self.assertIn("бег", a.text)
        self.assertNotRegex(a.text[len("[rʌn]"):], r"[\[\]]")
        self.assertIsNone(a.form_of)
        self.assertFalse(a.pointer_only)
        self.assertIsNone(a.lemma_of)

    def test_examples_and_comments_stay_in_text_but_are_not_values(self):
        a = convert("[m1][p]n[/p] [trn]бег[/trn][/m]", "[m2][ex]I run daily[/ex][/m]", "[m2][com]rare[/com][/m]")
        self.assertEqual(a.senses, (("n", ("бег",)),))
        self.assertIn("I run daily", a.text)
        self.assertIn("rare", a.text)

    def test_media_and_comments_are_dropped(self):
        a = convert("[m1]word [s]a.wav[/s][video]x.mp4[/video] more {{secret}}end[/m]")
        self.assertEqual(a.text, "word more end")
        self.assertNotIn("a.wav", a.text)
        self.assertNotIn("secret", a.text)

    def test_multiline_comment_is_dropped(self):
        a = convert("[m1]before {{a", "comment}} after[/m]")
        self.assertNotIn("comment", a.text)
        self.assertIn("before", a.text)
        self.assertIn("after", a.text)

    def test_references_keep_their_word(self):
        self.assertEqual(convert("[m1][ref]word[/ref] and <<other>>[/m]").text, "word and other")

    def test_formatting_and_unknown_tags_are_stripped(self):
        a = convert(
            "[m1][c]a[/c] [c green]b[/c] [b]c[/b] [i]d[/i] [u]e[/u] [sub]f[/sub] [sup]g[/sup] "
            "[lang id=1]h[/lang] [*]i[/*] [foo]j[/foo] [!trs]k[/!trs][/m]"
        )
        self.assertEqual(a.text, "a b c d e f g h i j k")

    def test_margin_tags_start_new_lines(self):
        self.assertEqual(convert("[m1]one[/m][m2]two[/m][m]three[/m]").text, "one\ntwo\nthree")
        self.assertEqual(convert("[m1]one", "[m1]two").text, "one\ntwo")

    def test_escaped_characters_are_literal(self):
        self.assertEqual(convert("[m1]\\[not a tag\\] ok[/m]").text, "[not a tag] ok")
        self.assertEqual(convert("[m1]\\{x\\} and a\\\\b[/m]").text, "{x} and a\\b")
        self.assertEqual(convert("[m1]\\{\\{x\\}\\}[/m]").text, "{{x}}")

    def test_unclosed_and_stray_tags_keep_the_text(self):
        self.assertEqual(convert("[m1][b]text").text, "text")
        self.assertEqual(convert("[/b]stray [/m] text").text, "stray text")
        self.assertEqual(convert("[m1][trn]open value").senses, ((None, ("open value",)),))
        self.assertEqual(convert("[m1]a [ b").text, "a [ b")

    def test_plain_brackets_that_are_not_tags_stay(self):
        self.assertEqual(convert("[m1]see [1] and [2][/m]").text, "see [1] and [2]")

    def test_without_trn_plain_lines_are_values(self):
        a = convert("[m1][t]rʌn[/t][/m]", "[m1][p]v[/p] бежать[/m]", "[m1]бегать[/m]", "[m2][ex]example[/ex][/m]", "[m2][com]c[/com][/m]")
        self.assertEqual(a.senses, (("v", ("бежать", "бегать")),))

    def test_without_p_values_go_to_none(self):
        self.assertEqual(convert("[m1][trn]a[/trn] [trn]b[/trn][/m]").senses, ((None, ("a", "b")),))
        self.assertEqual(convert("[m1]first[/m]", "[m1]second[/m]").senses, ((None, ("first", "second")),))

    def test_values_are_capped_by_length_and_count(self):
        many = " ".join("[trn]v%d[/trn]" % i for i in range(9))
        self.assertEqual(convert("[m1][p]n[/p] " + many + "[/m]").senses, (("n", ("v0", "v1", "v2", "v3", "v4")),))
        lines = ["[m1]line%d[/m]" % i for i in range(9)]
        self.assertEqual(convert(*lines).senses, ((None, ("line0", "line1", "line2", "line3", "line4")),))
        ((pos, values),) = convert("[m1][p]n[/p] [trn]" + "x" * 200 + "[/trn][/m]").senses
        self.assertEqual(len(values[0]), 80)

    def test_empty_groups_are_dropped(self):
        a = convert("[m1][p]adj[/p] [p]n[/p] [trn]x[/trn][/m]")
        self.assertEqual(a.senses, (("n", ("x",)),))

    def test_first_transcription_wins(self):
        a = convert("[m1][t]one[/t] [t]two[/t][/m]", "[m1]body[/m]")
        self.assertEqual(a.transcription, "one")
        self.assertNotIn("two", a.text)
        self.assertEqual(a.text, "[one]\nbody")

    def test_transcription_inside_other_tags(self):
        a = convert("[m1][c][t]rʌn[/t][/c][/m]", "[m1]x[/m]")
        self.assertEqual(a.transcription, "rʌn")

    def test_no_transcription(self):
        a = convert("[m1]just text[/m]")
        self.assertIsNone(a.transcription)
        self.assertEqual(a.text, "just text")

    def test_control_characters_are_removed(self):
        a = convert("[m1]a\x00b\x07c‮d[/m]")
        self.assertEqual(a.text, "abcd")

    def test_private_use_characters_from_the_file_do_not_confuse_escapes(self):
        a = convert("[m1] \\[x\\][/m]")
        self.assertIn("[x]", a.text)

    def test_lookup_returns_converted_articles(self):
        root = make_tempdir(self)
        path = write_dsl(root / "d" / "x.dsl", [(["run"], ["[m1][t]rʌn[/t][/m]", "[m1][p]v[/p] [trn]бежать[/trn][/m]"])])
        d = open_dsl(path)
        self.addCleanup(d.close)
        a = d.lookup("run")[0]
        self.assertEqual((a.transcription, a.senses), ("rʌn", (("v", ("бежать",)),)))


class DslIndexCacheTests(_Base):
    def cache_file(self, path):
        return index_cache_path(path, dsl.INDEX_TAG)

    def scanning(self):
        return mock.patch.object(dsl, "_scan", autospec=True, side_effect=dsl._scan)

    def test_first_open_writes_the_cache_and_the_second_skips_the_scan(self):
        path = self.write()
        first = self.open(path)
        self.assertTrue(self.cache_file(path).is_file())
        expected = [first.lookup(k) for k in ("run", "сон", "absent")]
        with mock.patch.object(dsl, "_scan", side_effect=AssertionError("scanner must not run")):
            second = self.open(path)
        self.assertEqual([second.lookup(k) for k in ("run", "сон", "absent")], expected)
        self.assertEqual((second.name, second.entry_count), (first.name, first.entry_count))

    def test_dictzip_cache_skips_decompressing_the_whole_file(self):
        path = self.write(dz=True)
        self.open(path)
        with mock.patch.object(DictzipFile, "read_all", side_effect=AssertionError("cold path")):
            d = self.open(path)
        self.assertIn("to move fast", d.lookup("run")[0].text)

    def test_changed_size_rescans(self):
        path = self.write()
        self.open(path).close()
        self.write(TWO + [(["extra"], ["[m1]more[/m]"])])
        with self.scanning() as scan:
            d = self.open(path)
        self.assertEqual(scan.call_count, 1)
        self.assertTrue(d.has("extra"))

    def test_changed_mtime_rescans(self):
        path = self.write()
        self.open(path).close()
        st = path.stat()
        os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
        with self.scanning() as scan:
            self.open(path)
        self.assertEqual(scan.call_count, 1)

    def test_damaged_cache_is_rebuilt(self):
        path = self.write()
        self.open(path).close()
        self.cache_file(path).write_bytes(b'{"format": 1, "tag": "dsl-1", "da')
        with self.scanning() as scan:
            d = self.open(path)
        self.assertEqual(scan.call_count, 1)
        self.assertIn("to move fast", d.lookup("run")[0].text)
        d.close()
        with mock.patch.object(dsl, "_scan", side_effect=AssertionError("cache must be healed")):
            self.open(path)

    def tamper(self, path, edit):
        target = self.cache_file(path)
        wrapper = json.loads(target.read_text(encoding="utf-8"))
        edit(wrapper["data"])
        target.write_text(json.dumps(wrapper, ensure_ascii=False), encoding="utf-8")

    def test_offsets_outside_the_file_are_ignored(self):
        path = self.write()
        self.open(path).close()
        self.tamper(path, lambda data: data["entries"][0].__setitem__(0, 10**9))
        with self.scanning() as scan:
            d = self.open(path)
        self.assertEqual(scan.call_count, 1)
        self.assertIn("to move fast", d.lookup("run")[0].text)

    def test_malformed_payloads_are_ignored(self):
        edits = {
            "negative offset": lambda data: data["entries"][0].__setitem__(0, -1),
            "zero size": lambda data: data["entries"][0].__setitem__(1, 0),
            "huge size": lambda data: data["entries"][0].__setitem__(1, 1 << 40),
            "string offset": lambda data: data["entries"][0].__setitem__(0, "0"),
            "key to missing entry": lambda data: data["keys"].__setitem__("run", [99]),
            "key to bool": lambda data: data["keys"].__setitem__("run", [True]),
            "bad encoding": lambda data: data.__setitem__("enc", "latin-1"),
            "bad bom": lambda data: data.__setitem__("bom", 99),
            "entries not a list": lambda data: data.__setitem__("entries", {}),
            "no entries": lambda data: data.__setitem__("entries", []),
            "missing field": lambda data: data.pop("keys"),
        }
        for label, edit in edits.items():
            with self.subTest(label):
                path = self.write(stem=label.replace(" ", "-") + ".dsl")
                self.open(path).close()
                self.tamper(path, edit)
                with self.scanning() as scan:
                    d = self.open(path)
                self.assertEqual(scan.call_count, 1)
                self.assertIn("to move fast", d.lookup("run")[0].text)


class DslHostileInputTests(_Base):
    def timed(self, fn, limit=1.0):
        t = time.perf_counter()
        result = fn()
        self.assertLess(time.perf_counter() - t, limit)
        return result

    def test_one_megabyte_line_without_a_newline(self):
        a = self.timed(lambda: convert("[m1]" + "x" * 1_000_000 + "[/m]"))
        self.assertTrue(a.text.startswith("xxxx"))
        self.assertLessEqual(len(a.text), 200_000)

    def test_deeply_nested_tags(self):
        a = self.timed(lambda: convert("[b]" * 100_000 + "text" + "[/b]" * 100_000))
        self.assertEqual(a.text, "text")

    def test_pathological_repetitions(self):
        cases = {
            "open comments": "{{" * 200_000,
            "brackets": "[" * 300_000,
            "closing brackets": "[/" * 150_000,
            "escapes": "\\" * 300_000,
            "tag soup": "[trn][p][t][ex][m1]" * 20_000,
            "unclosed s": "[s]" * 100_000 + "text",
            "refs": "<<" * 200_000,
        }
        for label, body in cases.items():
            with self.subTest(label):
                self.timed(lambda: convert(body))

    def test_hostile_article_through_a_real_file(self):
        path = self.write([(["big"], ["[m1]" + "[b]" * 50_000 + "x" * 500_000 + "[/m]"]), (["small"], ["[m1]ok[/m]"])])
        d = self.open(path)
        a = self.timed(lambda: d.lookup("big"))
        self.assertEqual(len(a), 1)
        self.assertIn("ok", d.lookup("small")[0].text)

    def test_converter_failure_falls_back_to_stripped_text(self):
        with mock.patch.object(dsl, "_convert_markup", side_effect=RuntimeError("boom")):
            a = convert("[m1][b]text[/b] here[/m]")
        self.assertEqual(a.text, "text here")
        self.assertEqual((a.transcription, a.senses), (None, ()))

    def test_headword_variant_flood_is_capped_in_the_index(self):
        head = "".join("x{%d}" % i for i in range(60))
        d = self.open(self.write([([head], ["[m1]x[/m]"])]))
        self.assertEqual(d.entry_count, 1)
        self.assertLessEqual(len(d._keys), MAX_VARIANTS)


if __name__ == "__main__":
    unittest.main()
