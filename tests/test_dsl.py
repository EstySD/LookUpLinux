"""DSL reader tests: encodings, headword groups, markup, index cache, hostile input (D-02, D-05, D-06, D-08, D-33)."""
import unittest
from unittest import mock

from lookup import dsl
from lookup.dictzip import DictzipFile
from lookup.dicts import Article, DictError, fold_key
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


if __name__ == "__main__":
    unittest.main()
