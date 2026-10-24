"""StarDict reader tests: layouts, validation, field types (D-02, D-05, D-06, D-08, D-33)."""
import os
import struct
import unittest
from unittest import mock

from lookup import stardict
from lookup.dicts import Article, DictError
from lookup.stardict import open_stardict
from tests._stardict_writer import write_stardict
from tests._support import make_tempdir


class _Base(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)
        self.dir = self.root / "dicts"

    def write(self, stem="book", entries=None, **kw):
        if entries is None:
            entries = [("run", "to move fast"), ("walk", "to go on foot"), ("sit", "to rest")]
        return write_stardict(self.dir, stem, entries, **kw)

    def open(self, ifo):
        d = open_stardict(ifo)
        self.addCleanup(d.close)  # closed before the temp dir goes (Windows)
        return d


class StarDictReaderTests(_Base):
    def test_open_and_lookup(self):
        d = self.open(self.write(bookname="Test Dict"))
        self.assertEqual(d.name, "Test Dict")
        self.assertEqual(d.fmt, "stardict")
        self.assertEqual(d.entry_count, 3)
        self.assertEqual(d.skipped_entries, 0)
        arts = d.lookup("run")
        self.assertEqual(len(arts), 1)
        a = arts[0]
        self.assertIsInstance(a, Article)
        self.assertEqual((a.dict_name, a.headword, a.text), ("Test Dict", "run", "to move fast"))
        self.assertTrue(d.has("run"))
        self.assertFalse(d.has("nope"))
        self.assertEqual(d.lookup("nope"), [])

    def test_keys_are_folded_not_the_query(self):
        d = self.open(self.write(entries=[("Run", "x one"), ("Ёлка", "y two")]))
        self.assertTrue(d.has("run"))
        self.assertEqual(d.lookup("run")[0].headword, "Run")
        self.assertTrue(d.has("ёлка"))
        self.assertFalse(d.has("RUN"))

    def test_bookname_falls_back_to_stem(self):
        ifo = self.write(stem="fallback")
        text = ifo.read_text(encoding="utf-8").replace("bookname=fallback\n", "")
        ifo.write_text(text, encoding="utf-8")
        self.assertEqual(self.open(ifo).name, "fallback")

    def test_bom_and_crlf_in_ifo(self):
        ifo = self.write(bookname="Crlf Book")
        raw = ifo.read_bytes().replace(b"\n", b"\r\n")
        ifo.write_bytes(b"\xef\xbb\xbf" + raw)
        d = self.open(ifo)
        self.assertEqual((d.name, d.entry_count), ("Crlf Book", 3))

    def test_compressed_layout_returns_identical_articles(self):
        entries = [("w%03d" % i, ("definition number %d " % i) * 40) for i in range(30)]
        plain = self.open(self.write("plain", entries, bookname="B"))
        packed = self.open(self.write("packed", entries, bookname="B", dz=True, plain_dict=False, gz_idx=True))
        self.assertEqual(packed.entry_count, 30)
        for i in (0, 7, 29):
            self.assertEqual(packed.lookup("w%03d" % i), plain.lookup("w%03d" % i))

    def test_plain_dict_wins_over_garbage_dz(self):
        ifo = self.write("both", dz=True, plain_dict=True)
        (self.dir / "both.dict.dz").write_bytes(b"this is not gzip at all")
        d = self.open(ifo)
        self.assertEqual(d.lookup("run")[0].text, "to move fast")

    def test_dotfiles_and_other_suffixes_are_never_data(self):
        ifo = self.write("only", plain_dict=False, dz=False)
        (self.dir / ".only.dict").write_bytes(b"to move fastto go on footto rest")
        (self.dir / "only.dict.bak").write_bytes(b"x")
        (self.dir / "only.dict.swp").write_bytes(b"x")
        with self.assertRaises(DictError) as cm:
            open_stardict(ifo)
        self.assertEqual(cm.exception.reason, "missing_files")

    def test_missing_index_or_data(self):
        ifo = self.write("noidx")
        os.remove(self.dir / "noidx.idx")
        with self.assertRaises(DictError) as cm:
            open_stardict(ifo)
        self.assertEqual(cm.exception.reason, "missing_files")
        ifo = self.write("nodata")
        os.remove(self.dir / "nodata.dict")
        with self.assertRaises(DictError) as cm:
            open_stardict(ifo)
        self.assertEqual(cm.exception.reason, "missing_files")
        with self.assertRaises(DictError) as cm:
            open_stardict(self.dir / "absent.ifo")
        self.assertEqual(cm.exception.reason, "missing_files")

    def test_dz_read_is_random_access(self):
        entries = [("w%03d" % i, ("definition number %d " % i) * 40) for i in range(30)]
        ifo = self.write("rand", entries, dz=True, plain_dict=False)
        d = self.open(ifo)
        with mock.patch.object(stardict.DictzipFile, "read_all", side_effect=AssertionError("inflated all")):
            self.assertTrue(d.lookup("w017")[0].text.startswith("definition number 17"))

    def test_offset_bits_64(self):
        d = self.open(self.write(version="3.0.0", offset_bits=64))
        self.assertEqual(d.entry_count, 3)
        self.assertEqual(d.lookup("walk")[0].text, "to go on foot")

    def test_unsupported_ifo_variants(self):
        cases = {
            "bits64_old": dict(version="2.4.2", offset_bits=64),
            "bits48": dict(version="3.0.0", offset_bits=48),
        }
        for stem, kw in cases.items():
            with self.subTest(stem):
                ifo = self.write(stem, **kw)
                with self.assertRaises(DictError) as cm:
                    open_stardict(ifo)
                self.assertIn(cm.exception.reason, ("corrupt", "unsupported"))

    def test_bad_magic_and_oversized_ifo(self):
        ifo = self.write("magic")
        ifo.write_bytes(ifo.read_bytes().replace(b"StarDict's dict ifo file", b"Something else"))
        with self.assertRaises(DictError) as cm:
            open_stardict(ifo)
        self.assertIn(cm.exception.reason, ("corrupt", "unsupported"))
        ifo = self.write("bigifo")
        ifo.write_bytes(ifo.read_bytes() + b"#" * stardict.MAX_IFO_BYTES)
        with self.assertRaises(DictError) as cm:
            open_stardict(ifo)
        self.assertIn(cm.exception.reason, ("corrupt", "unsupported"))

    def test_error_reason_carries_no_file_content(self):
        ifo = self.write("secret")
        ifo.write_bytes(b"TOPSECRET-CONTENT\nversion=1\n")
        with self.assertRaises(DictError) as cm:
            open_stardict(ifo)
        self.assertNotIn("TOPSECRET", str(cm.exception))
        self.assertNotIn("TOPSECRET", cm.exception.reason)


class StarDictValidationTests(_Base):
    def test_mueller_like_index_defects_are_skipped_and_counted(self):
        entries = [("", "x"), ("run", "to move fast"), ("walk", "to go on foot")]
        extra = [
            (b"", 11835175, 1667331443),
            (b"zero", 0, 0),
            (b"beyond", 0, 10 ** 6),
            (b"huge", 0, 1667331443),
        ]
        ifo = self.write(entries=entries, extra_idx=extra, wordcount=46231)
        d = self.open(ifo)
        self.assertEqual(d.skipped_entries, 5)
        self.assertEqual(d.entry_count, 2)
        self.assertEqual(d.lookup("run")[0].text, "to move fast")
        self.assertEqual(d.lookup("walk")[0].text, "to go on foot")
        for bad in ("zero", "beyond", "huge", ""):
            self.assertFalse(d.has(bad))

    def test_wordcount_is_never_trusted(self):
        d = self.open(self.write(wordcount=999999))
        self.assertEqual((d.entry_count, d.skipped_entries), (3, 0))

    def test_size_above_max_article_bytes_is_skipped(self):
        ifo = self.write(extra_idx=[(b"big", 0, 5)])
        with mock.patch.object(stardict, "MAX_ARTICLE_BYTES", 4):
            d = self.open(ifo)
        self.assertFalse(d.has("big"))
        self.assertEqual(d.entry_count, 0)
        self.assertEqual(d.skipped_entries, 4)

    def test_duplicates_in_index_order(self):
        d = self.open(self.write(entries=[("Walk", "first"), ("run", "r"), ("walk", "second"), ("WALK", "third")]))
        self.assertEqual([a.text for a in d.lookup("walk")], ["first", "second", "third"])
        self.assertEqual([a.headword for a in d.lookup("walk")], ["Walk", "walk", "WALK"])

    def test_syn_counts_over_all_entries_including_skipped(self):
        entries = [("", "skipped"), ("alpha", "A text"), ("beta", "B text")]
        syn = [("Sprint", 1), ("ghost", 0), ("hop", 77), ("Zed", 2), ("beta", 2)]
        d = self.open(self.write(entries=entries, syn=syn))
        self.assertEqual(d.lookup("sprint")[0].headword, "alpha")
        self.assertFalse(d.has("ghost"))
        self.assertFalse(d.has("hop"))
        self.assertEqual(d.lookup("zed")[0].headword, "beta")
        self.assertEqual(len(d.lookup("beta")), 1)  # deduplicated

    def test_idx_cut_inside_an_entry(self):
        ifo = self.write("cut")
        p = self.dir / "cut.idx"
        p.write_bytes(p.read_bytes()[:-3])
        d = self.open(ifo)
        self.assertEqual(d.entry_count, 2)
        self.assertEqual(d.skipped_entries, 1)
        self.assertTrue(d.has("run"))
        self.assertTrue(d.has("walk"))
        self.assertFalse(d.has("sit"))

    def test_idx_too_large(self):
        ifo = self.write("large")
        with mock.patch.object(stardict, "MAX_IDX_BYTES", 10):
            with self.assertRaises(DictError) as cm:
                open_stardict(ifo)
        self.assertEqual(cm.exception.reason, "too_large")
        ifo = self.write("largegz", gz_idx=True)
        with mock.patch.object(stardict, "MAX_IDX_BYTES", 10):
            with self.assertRaises(DictError) as cm:
                open_stardict(ifo)
        self.assertEqual(cm.exception.reason, "too_large")

    def test_corrupt_gz_index_and_dz_data(self):
        ifo = self.write("badgz", gz_idx=True)
        (self.dir / "badgz.idx.gz").write_bytes(b"\x1f\x8b\x08garbage")
        with self.assertRaises(DictError) as cm:
            open_stardict(ifo)
        self.assertEqual(cm.exception.reason, "corrupt")
        ifo = self.write("baddz", dz=True, plain_dict=False)
        (self.dir / "baddz.dict.dz").write_bytes(b"not a dictzip file")
        with self.assertRaises(DictError) as cm:
            open_stardict(ifo)
        self.assertEqual(cm.exception.reason, "corrupt")

    def test_lookup_survives_truncated_plain_data(self):
        ifo = self.write("trunc", entries=[("aa", "first article"), ("bb", "second article")])
        d = self.open(ifo)
        with open(self.dir / "trunc.dict", "r+b") as fh:
            fh.truncate(len("first article"))
        self.assertEqual(d.lookup("aa")[0].text, "first article")
        self.assertEqual(d.lookup("bb"), [])

    def test_lookup_survives_truncated_dz_data(self):
        entries = [("w%03d" % i, ("definition number %d " % i) * 40) for i in range(30)]
        ifo = self.write("dztrunc", entries, dz=True, plain_dict=False)
        d = self.open(ifo)
        p = self.dir / "dztrunc.dict.dz"
        with open(p, "r+b") as fh:
            fh.truncate(len(p.read_bytes()) // 2)
        d.lookup("w029")  # must not raise
        self.assertEqual(d.lookup("w029"), [])

    def test_close_is_idempotent_and_lookup_after_close_is_empty(self):
        d = self.open(self.write())
        d.close()
        d.close()
        self.assertEqual(d.lookup("run"), [])


class FieldTypeTests(_Base):
    def one(self, data, seq="m", word="w"):
        d = self.open(self.write("ft", entries=[(word, data)], sametypesequence=seq))
        arts = d.lookup(word)
        self.assertEqual(len(arts), 1)
        return arts[0]

    def test_t_then_m(self):
        a = self.one("rʌn\0".encode() + "бег".encode(), seq="tm")
        self.assertEqual(a.transcription, "rʌn")
        self.assertEqual(a.text, "бег")

    def test_y_is_a_transcription(self):
        a = self.one("ping".encode(), seq="y")
        self.assertEqual(a.transcription, "ping")
        self.assertEqual(a.text, "")

    def test_xdxf_is_flattened_and_gives_transcription(self):
        xdxf = "<k>run</k><tr>rʌn</tr><def><deftext>to <b>move</b> fast</deftext></def>"
        a = self.one(xdxf, seq="x")
        self.assertEqual(a.transcription, "rʌn")
        self.assertNotIn("<", a.text)
        self.assertIn("to move fast", a.text)

    def test_t_beats_xdxf_tr(self):
        data = "TT\0".encode() + "<tr>XX</tr><def>body</def>".encode()
        a = self.one(data, seq="tx")
        self.assertEqual(a.transcription, "TT")

    def test_h_and_g_markup_is_flattened(self):
        a = self.one("<p>Hello <b>world</b></p><script>evil()</script>", seq="h")
        self.assertNotIn("<", a.text)
        self.assertNotIn("evil", a.text)
        self.assertIn("Hello world", a.text)
        a = self.one('<span foreground="red">red <i>word</i></span>', seq="g")
        self.assertEqual(a.text, "red word")

    def test_k_and_l_and_w(self):
        a = self.one("<k>x</k><dtrn>translation</dtrn>", seq="k")
        self.assertIn("translation", a.text)
        self.assertNotIn("<", a.text)
        self.assertEqual(self.one("plain locale text", seq="l").text, "plain locale text")
        self.assertEqual(self.one("wiki text", seq="w").text, "wiki text")

    def test_resource_and_unknown_types_are_ignored(self):
        data = b"text\0" + b"file.png\0" + struct.pack(">I", 3) + b"abc" + b"zzz"
        a = self.one(data, seq="mrWP")
        self.assertEqual(a.text, "text")
        self.assertEqual(self.one(b"text\0unknown", seq="mq").text, "text")

    def test_no_sametypesequence_layout(self):
        data = b"m" + "text one".encode() + b"\0" + b"t" + "tr".encode() + b"\0" + b"W" + struct.pack(">I", 2) + b"zz"
        a = self.one(data, seq=None)
        self.assertEqual(a.text, "text one")
        self.assertEqual(a.transcription, "tr")

    def test_no_sametypesequence_matches_sametypesequence(self):
        with_seq = self.one("rʌn\0".encode() + "бег".encode(), seq="tm")
        data = b"t" + "rʌn".encode() + b"\0" + b"m" + "бег".encode() + b"\0"
        without = self.one(data, seq=None)
        self.assertEqual((without.transcription, without.text), (with_seq.transcription, with_seq.text))

    def test_malformed_fields_fall_back_to_whole_data(self):
        # missing NUL after the t field
        self.assertEqual(self.one(b"abc", seq="tm").text, "abc")
        # length prefix past the end
        a = self.one(b"\x00\x00\x00\xffxy", seq="Wm")
        self.assertEqual(a.text, "�xy")  # control bytes dropped, 0xff replaced
        # type byte layout without a terminating NUL
        self.assertEqual(self.one(b"mfoo", seq=None).text, "mfoo")
        # invalid UTF-8 is replaced, never raised
        self.assertIn("�", self.one(b"ab\xffcd", seq="tm").text)

    def test_text_is_cleaned(self):
        a = self.one("a\x00b".encode() + b"\x07 c", seq="m")
        self.assertNotIn("\x07", a.text)
        self.assertNotIn("\x00", a.text)


class MuellerParseTests(_Base):
    def parse(self, text):
        return stardict.parse_mueller(text)

    def test_numbered_pos_blocks_with_sense_markers(self):
        r = self.parse("[rʌn] 1. _n. 1> бег 2> ход 2. _v. 1> бежать 2> управлять")
        self.assertEqual(r.transcription, "rʌn")
        self.assertEqual(r.senses, (("n", ("бег", "ход")), ("v", ("бежать", "управлять"))))
        self.assertIsNone(r.form_of)
        self.assertFalse(r.pointer_only)

    def test_segment_without_markers_is_one_value_cut_at_80(self):
        r = self.parse("[ˈbetə] _n. держащий пари")
        self.assertEqual(r.transcription, "ˈbetə")
        self.assertEqual(r.senses, (("n", ("держащий пари",)),))
        long = self.parse("[x] _n. " + "ы" * 200)
        self.assertEqual(long.senses, (("n", ("ы" * 80,)),))

    def test_at_most_five_values_per_pos(self):
        r = self.parse("[x] _n. " + " ".join("%d> v%d" % (i, i) for i in range(1, 10)))
        self.assertEqual(r.senses, (("n", ("v1", "v2", "v3", "v4", "v5")),))

    def test_letter_sense_markers(self):
        r = self.parse("[x] _v. а> выламывать; б> убежать")
        self.assertEqual(r.senses, (("v", ("выламывать", "убежать")),))

    def test_pure_pointers(self):
        cases = {
            "[ræn] _p. от run 2": "run",
            "[men] _pl. от man 1": "man",
            "[went] _p. от go 1": "go",
            "[tiːθ] _pl. от tooth 1": "tooth",
            "_pl. от man 1": "man",
            "[ræn] _p. от run": "run",
            "[x] _p. от run 2;": "run",
        }
        for text, lemma in cases.items():
            with self.subTest(text):
                r = self.parse(text)
                self.assertEqual(r.form_of, lemma)
                self.assertTrue(r.pointer_only)
                self.assertEqual(r.senses, ())
        self.assertEqual(self.parse("[ræn] _p. от run 2").transcription, "ræn")
        self.assertIsNone(self.parse("_pl. от man 1").transcription)

    def test_mixed_articles(self):
        r = self.parse("[ˈrʌnıŋ] 1. _pres-p. от run 2 2. _n. бег")
        self.assertEqual((r.form_of, r.pointer_only), ("run", False))
        self.assertEqual(r.senses, (("n", ("бег",)),))
        r = self.parse("[gɔn] 1. _p-p. от go 1; 2. _a. ушедший")
        self.assertEqual((r.form_of, r.pointer_only), ("go", False))
        self.assertEqual(r.senses, (("a", ("ушедший",)),))

    def test_ordinary_articles_are_not_pointers(self):
        cases = [
            "[ˈbetə] _n. держащий пари _II [ˈbetə] 1. _a. (_comp. от good 1) лучший",
            "[wəːs] 1. _a. (_comp. от bad 1) худший",
            "[ˈdeıtə] _n. _pl. 1> _pl. от datum",
            "[njuːz] _n. _pl. (употр. как sing) 1> новости",
        ]
        for text in cases:
            with self.subTest(text):
                r = self.parse(text)
                self.assertIsNone(r.form_of)
                self.assertFalse(r.pointer_only)

    def test_homograph_blocks_become_separate_senses(self):
        r = self.parse("[ˈbetə] _n. держащий пари _II [ˈbetə] 1. _a. (_comp. от good 1) лучший")
        self.assertEqual(r.transcription, "ˈbetə")
        self.assertEqual(r.senses, (("n", ("держащий пари",)), ("a", ("лучший",))))

    def test_usage_labels_and_homograph_markers_are_not_senses(self):
        r = self.parse("[x] _I _n. _разг. слово _ам. тоже _лат. verbum")
        self.assertEqual([pos for pos, _ in r.senses], ["n"])
        self.assertNotIn("_I", " ".join(v for _, vals in r.senses for v in vals))

    def test_unstructured_text(self):
        r = self.parse("just a word")
        self.assertEqual(r, stardict.MuellerParts(None, (), None, False))
        self.assertEqual(self.parse(""), stardict.MuellerParts(None, (), None, False))

    def test_pathological_input_is_bounded(self):
        import time

        for text in ("_n. от [" * 150000, "[" * 1_000_000, "_n. от " * 150000, " " * 1_000_000 + "x"):
            with self.subTest(text[:12]):
                t0 = time.perf_counter()
                r = self.parse(text)
                self.assertLess(time.perf_counter() - t0, 1.0)
                self.assertIsInstance(r, stardict.MuellerParts)

    def test_integration_through_open_stardict(self):
        entries = [
            ("ran", "[ræn] _p. от run 2"),
            ("run", "[rʌn] 1. _n. 1> бег 2. _v. 1> бежать"),
            ("plain", "just a word"),
        ]
        d = self.open(write_stardict(self.dir, "mu", entries, bookname="Mu"))
        ran = d.lookup("ran")[0]
        self.assertEqual((ran.transcription, ran.form_of, ran.pointer_only), ("ræn", "run", True))
        self.assertEqual(ran.text, "[ræn] _p. от run 2")
        run = d.lookup("run")[0]
        self.assertEqual(run.transcription, "rʌn")
        self.assertEqual(run.senses, (("n", ("бег",)), ("v", ("бежать",))))
        self.assertFalse(run.pointer_only)
        self.assertIn("бег", run.text)
        plain = d.lookup("plain")[0]
        self.assertIsNone(plain.transcription)
        self.assertEqual((plain.senses, plain.form_of, plain.pointer_only), ((), None, False))

    def test_t_field_wins_and_multi_field_entry_is_not_pointer_only(self):
        data = "TT\0".encode() + "[ræn] _p. от run 2".encode()
        d = self.open(write_stardict(self.dir, "mt", [("ran", data)], sametypesequence="tm"))
        a = d.lookup("ran")[0]
        self.assertEqual(a.transcription, "TT")
        self.assertEqual(a.form_of, "run")
        self.assertFalse(a.pointer_only)


if __name__ == "__main__":
    unittest.main()
