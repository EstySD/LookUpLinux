"""MDX reader tests: format, checksums, encryption, redirects, cache, hostile input (D-02, D-06, D-07, D-08, D-33, D-34).

No real MDX file is available, so the files come from an independent writer
(tests/_mdx_writer.py) plus real liblzo2 vectors; real-file acceptance is a UAT item.
"""
import base64
import json
import os
import random
import struct
import time
import unittest
import zlib
from unittest import mock

from lookup import mdx
from lookup.dicts import Article, DictError, fold_key, index_cache_path
from lookup.lzo import LzoError, decompress
from lookup.mdx import MAX_LINK_HOPS, MAX_MDX_BLOCK, open_mdx
from lookup.ripemd128 import digest
from tests import _mdx_writer
from tests._mdx_writer import lzo_literal_stream, write_mdx
from tests._support import make_tempdir

LONG = "x" * 10 + " слово" * 30

ENTRIES = [
    ("run", "<b>run</b><br>бежать"),
    ("Сон", "<i>sleep</i> сон"),
    ("apple", "яблоко"),
    ("zebra", "зебра"),
    ("cat", "кошка"),
    ("dog", "собака"),
    ("bird", "птица"),
    ("LONG", LONG),
    ("fish", "рыба"),
]
EXPECTED = {
    "run": "run\nбежать",
    "сон": "sleep сон",
    "apple": "яблоко",
    "zebra": "зебра",
    "cat": "кошка",
    "dog": "собака",
    "bird": "птица",
    "long": LONG,
    "fish": "рыба",
}

with open(os.path.join(os.path.dirname(__file__), "fixtures", "lzo", "vectors.json"), encoding="utf-8") as _fh:
    VECTORS = json.load(_fh)


def vector(name, algo):
    for v in VECTORS:
        if v["name"] == name and v["algo"] == algo:
            return base64.b64decode(v["comp_b64"])
    raise KeyError(name)


def flip(path, offset):
    data = bytearray(path.read_bytes())
    data[offset] ^= 0xFF
    path.write_bytes(bytes(data))


def rewrite_header(path, xml):
    """Replace the header of a written file with `xml` (length and checksum recomputed)."""
    data = path.read_bytes()
    (length,) = struct.unpack(">I", data[:4])
    rest = data[8 + length:]
    body = xml.encode("utf-16-le") + b"\x00\x00"
    path.write_bytes(
        struct.pack(">I", len(body)) + body + struct.pack("<I", zlib.adler32(body) & 0xFFFFFFFF) + rest
    )


def patch_keyword_header(path, index, value):
    """Set one of the five keyword header numbers of a version 2.0 file; the checksum follows."""
    data = bytearray(path.read_bytes())
    at = _mdx_writer.LAYOUT["kw_header"]
    data[at + 8 * index:at + 8 * index + 8] = value.to_bytes(8, "big")
    data[at + 40:at + 44] = struct.pack(">I", zlib.adler32(bytes(data[at:at + 40])) & 0xFFFFFFFF)
    path.write_bytes(bytes(data))


class MdxTestCase(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)

    def build(self, name="d.mdx", entries=ENTRIES, **kw):
        return write_mdx(self.root / name, entries, **kw)

    def open(self, path):
        d = open_mdx(path)
        self.addCleanup(d.close)
        return d

    def reason(self, path):
        with self.assertRaises(DictError) as cm:
            open_mdx(path).close()
        return cm.exception.reason

    def check_all(self, d, expected=EXPECTED):
        for key, text in expected.items():
            arts = d.lookup(key)
            self.assertEqual(len(arts), 1, key)
            self.assertIsInstance(arts[0], Article)
            self.assertEqual(arts[0].text, text, key)
            self.assertTrue(d.has(key))


class MdxFormatTests(MdxTestCase):
    def test_version_2_utf8_zlib(self):
        path = self.build()
        layout = _mdx_writer.LAYOUT
        self.assertGreater(len(layout["key_block_list"]), 1)
        self.assertGreater(len(layout["rec_block_list"]), 1)
        d = self.open(path)
        self.assertEqual(d.name, "Test")
        self.assertEqual(d.fmt, "mdx")
        self.assertEqual(d.version, "2.0")
        self.assertEqual(d.entry_count, len(ENTRIES))
        self.assertEqual(d.skipped_entries, 0)
        self.assertEqual(d.path, path)
        self.check_all(d)

    def test_headword_keeps_original_spelling(self):
        d = self.open(self.build())
        self.assertEqual(d.lookup("long")[0].headword, "LONG")
        self.assertEqual(d.lookup("сон")[0].headword, "Сон")
        art = d.lookup("run")[0]
        self.assertEqual(art.dict_name, "Test")
        self.assertIsNone(art.transcription)
        self.assertEqual(art.senses, ())

    def test_uncompressed_blocks_give_the_same_lookups(self):
        d = self.open(self.build(record_codec="none", key_codec="none"))
        self.check_all(d)

    def test_has_and_unknown_key(self):
        d = self.open(self.build())
        self.assertTrue(d.has("run"))
        self.assertFalse(d.has("walk"))
        self.assertEqual(d.lookup("walk"), [])

    def test_record_spanning_two_blocks_is_complete(self):
        d = self.open(self.build(record_block_size=16))
        self.check_all(d)
        d = self.open(self.build("e.mdx", record_block_size=1))
        self.check_all(d)

    def test_last_record_and_key_order_differs_from_offset_order(self):
        order = [("zeta", "последний"), ("alpha", "первый"), ("mid", "средний")]
        d = self.open(self.build(entries=order, record_block_size=7))
        self.assertEqual(d.lookup("zeta")[0].text, "последний")
        self.assertEqual(d.lookup("alpha")[0].text, "первый")
        self.assertEqual(d.lookup("mid")[0].text, "средний")

    def test_duplicate_keys_return_all_records(self):
        d = self.open(self.build(entries=[("run", "один"), ("other", "x"), ("run", "два")]))
        self.assertEqual(sorted(a.text for a in d.lookup("run")), ["два", "один"])

    def test_text_format_keeps_text(self):
        d = self.open(self.build(entries=[("a", "<b>x</b>")], fmt="Text"))
        self.assertEqual(d.lookup("a")[0].text, "<b>x</b>")

    def test_header_attribute_order_single_quotes_and_entities(self):
        path = self.build()
        rewrite_header(
            path,
            "<Dictionary Title='Tom &amp; Jerry' Format=\"Html\" Encoding = 'UTF-8' Encrypted='No' "
            "RequiredEngineVersion=\"2.0\" GeneratedByEngineVersion='2.0'/>\r\n",
        )
        d = self.open(path)
        self.assertEqual(d.name, "Tom & Jerry")
        self.check_all(d)

    def test_name_falls_back_to_file_stem(self):
        path = self.build("my dict.mdx", title="")
        self.assertEqual(self.open(path).name, "my dict")

    def test_version_12_codecs(self):
        for rc in ("zlib", "none", "lzo"):
            for kc in ("zlib", "none", "lzo"):
                with self.subTest(record=rc, key=kc):
                    path = self.build("v12-%s-%s.mdx" % (rc, kc), version="1.2", record_codec=rc, key_codec=kc)
                    d = self.open(path)
                    self.assertEqual(d.version, "1.2")
                    self.check_all(d)

    def test_version_2_lzo_blocks(self):
        d = self.open(self.build(record_codec="lzo", key_codec="lzo"))
        self.check_all(d)

    def test_long_literal_lzo_blocks(self):
        entries = [("k%03d" % i, "слово " * 20 + str(i)) for i in range(40)]
        d = self.open(self.build(entries=entries, record_codec="lzo", record_block_size=400, keys_per_block=10))
        for i in (0, 17, 39):
            self.assertEqual(d.lookup("k%03d" % i)[0].text, ("слово " * 20 + str(i)).strip())

    def test_real_liblzo2_record_block(self):
        for algo in ("lzo1x_1_compress", "lzo1x_999_compress"):
            with self.subTest(algo=algo):
                comp = vector("run_1000", algo)

                def codec(raw, comp=comp):
                    self.assertEqual(raw, b"a" * 1000)
                    return 1, comp

                path = self.build(
                    "lzo-%s.mdx" % algo,
                    entries=[("run", "a" * 1000)],
                    fmt="Text",
                    append_nul=False,
                    record_block_size=10**6,
                    record_codec=codec,
                )
                self.assertEqual(self.open(path).lookup("run")[0].text, "a" * 1000)

    def test_corrupted_real_lzo_block_is_skipped_others_served(self):
        comp = bytearray(vector("run_1000", "lzo1x_999_compress"))
        comp[len(comp) // 2] ^= 0x55

        def codec(raw):
            if raw == b"a" * 1000:
                return 1, bytes(comp)
            return 2, zlib.compress(raw)

        path = self.build(
            entries=[("bad", "a" * 1000), ("good", "hello")],
            fmt="Text",
            append_nul=False,
            record_block_size=1000,
            record_codec=codec,
        )
        d = self.open(path)
        self.assertEqual(d.lookup("bad"), [])
        self.assertEqual(d.lookup("good")[0].text, "hello")

    def test_utf16(self):
        entries = [("слово", "перевод"), ("word", "a"), ("字", "字典 entry")]
        d = self.open(self.build(entries=entries, encoding="UTF-16"))
        self.assertEqual(d.lookup("слово")[0].text, "перевод")
        self.assertEqual(d.lookup("word")[0].text, "a")
        self.assertEqual(d.lookup("字")[0].text, "字典 entry")
        self.assertEqual(d.encoding, "utf-16-le")

    def test_utf16_record_ending_in_a_zero_byte_is_not_damaged(self):
        # "a" is 61 00 in UTF-16LE; the terminator is 00 00 and must be removed as one unit only
        d = self.open(self.build(entries=[("one", "ba"), ("two", "a")], encoding="UTF-16", record_block_size=3))
        self.assertEqual(d.lookup("one")[0].text, "ba")
        self.assertEqual(d.lookup("two")[0].text, "a")
        d = self.open(
            self.build("nonul.mdx", entries=[("one", "ba"), ("two", "a")], encoding="UTF-16", append_nul=False)
        )
        self.assertEqual(d.lookup("one")[0].text, "ba")
        self.assertEqual(d.lookup("two")[0].text, "a")

    def test_utf16_version_12(self):
        d = self.open(self.build(version="1.2", encoding="UTF-16"))
        self.check_all(d)

    def test_gbk_and_big5(self):
        entries = [("你好", "問候語"), ("hello", "你好 world"), ("書", "book 書籍")]
        for enc in ("GBK", "Big5"):
            with self.subTest(enc=enc):
                d = self.open(self.build("%s.mdx" % enc, entries=entries, encoding=enc))
                self.assertEqual(d.lookup("你好")[0].text, "問候語")
                self.assertEqual(d.lookup("hello")[0].text, "你好 world")
                self.assertEqual(d.lookup("書")[0].text, "book 書籍")

    def test_gbk_cyrillic(self):
        d = self.open(self.build(encoding="GBK"))
        self.check_all(d)

    def test_checksum_failures_at_open(self):
        def damaged(offset_of):
            path = self.build()
            layout = dict(_mdx_writer.LAYOUT)
            flip(path, offset_of(layout))
            return path

        cases = {
            "header": lambda lay: 8,
            "keyword header": lambda lay: lay["kw_header"] + 2,
            "key info": lambda lay: lay["key_info"] + 5,
            "key block": lambda lay: lay["key_block_list"][1][0] + 5,
        }
        for name, where in cases.items():
            with self.subTest(name):
                self.assertEqual(self.reason(damaged(where)), "checksum")

    def test_data_byte_flips_in_uncompressed_blocks_are_checksum_errors(self):
        for name, where in {
            "key info": lambda lay: lay["key_info"] + 8 + 3,
            "key block": lambda lay: lay["key_block_list"][0][0] + 12,
        }.items():
            with self.subTest(name):
                path = self.build(key_codec="none")
                flip(path, where(_mdx_writer.LAYOUT))
                self.assertEqual(self.reason(path), "checksum")

    def test_record_block_checksum_skips_that_record_only(self):
        path = self.build()
        layout = _mdx_writer.LAYOUT
        self.assertGreater(len(layout["rec_block_list"]), 2)
        flip(path, layout["rec_block_list"][0][0] + 5)
        d = self.open(path)
        self.assertEqual(d.lookup("run"), [])
        self.assertEqual(d.lookup("fish")[0].text, "рыба")
        self.assertEqual(d.lookup("dog")[0].text, "собака")

    def test_record_block_data_flip_is_skipped(self):
        path = self.build(record_codec="none")
        flip(path, _mdx_writer.LAYOUT["rec_block_list"][0][0] + 9)
        d = self.open(path)
        self.assertEqual(d.lookup("run"), [])
        self.assertEqual(d.lookup("fish")[0].text, "рыба")

    def test_unusable_files_raise_dict_error_with_a_reason(self):
        path = self.build()
        rewrite_header(path, path_header("abc", "No", "UTF-8"))
        self.assertEqual(self.reason(path), "corrupt")

        for value in ("1", "Yes"):
            path = self.build()
            rewrite_header(path, path_header("2.0", value, "UTF-8"))
            self.assertEqual(self.reason(path), "encrypted_registration", value)

        path = self.build()
        rewrite_header(path, path_header("2.0", "No", "EBCDIC"))
        self.assertEqual(self.reason(path), "unsupported")

        path = self.build()
        rewrite_header(path, path_header("3.0", "No", "UTF-8"))
        self.assertEqual(self.reason(path), "unsupported")

        data = self.build().read_bytes()
        cut = self.root / "cut.mdx"
        cut.write_bytes(data[:10])
        self.assertEqual(self.reason(cut), "corrupt")
        cut.write_bytes(data[: _mdx_writer.LAYOUT["kw_header"] + 5])
        self.assertEqual(self.reason(cut), "corrupt")
        cut.write_bytes(data[: _mdx_writer.LAYOUT["rec_blocks"] - 3])
        self.assertEqual(self.reason(cut), "corrupt")

        empty = self.root / "empty.mdx"
        empty.write_bytes(b"")
        self.assertEqual(self.reason(empty), "empty")

        rnd = self.root / "random.mdx"
        rnd.write_bytes(b"\xff" + random.Random(7).randbytes(3000))
        self.assertEqual(self.reason(rnd), "corrupt")
        rnd.write_bytes(b"\x00\x00\x00\x10" + random.Random(8).randbytes(3000))
        self.assertIn(self.reason(rnd), ("checksum", "corrupt"))

        missing = self.root / "missing.mdx"
        self.assertEqual(self.reason(missing), "unreadable")

    def test_close_is_idempotent_and_lookup_after_close_is_empty(self):
        d = open_mdx(self.build())
        d.close()
        d.close()
        self.assertEqual(d.lookup("run"), [])


def path_header(version, encrypted, encoding):
    return (
        '<Dictionary GeneratedByEngineVersion="%s" RequiredEngineVersion="%s" Encrypted="%s" '
        'Encoding="%s" Format="Html" Title="T" />\r\n' % (version, version, encrypted, encoding)
    )


class MdxEncryptionTests(MdxTestCase):
    def test_encrypted_key_info_gives_the_same_lookups(self):
        plain = self.open(self.build("plain.mdx"))
        enc = self.open(self.build("enc.mdx", encrypted=2))
        self.check_all(enc)
        self.assertEqual(enc.entry_count, plain.entry_count)
        for key in EXPECTED:
            self.assertEqual(enc.lookup(key), plain.lookup(key))

    def test_other_key_codecs_with_encryption(self):
        for kc in ("none", "lzo"):
            with self.subTest(kc):
                self.check_all(self.open(self.build("e-%s.mdx" % kc, encrypted=2, key_codec=kc)))

    def test_key_derivation_matches_an_independent_decryption(self):
        path = self.build(encrypted=2)
        lay = _mdx_writer.LAYOUT
        data = path.read_bytes()
        block = data[lay["key_info"]:lay["key_info"] + lay["key_info_size"]]
        key = digest(block[4:8] + bytes([0x95, 0x36, 0x00, 0x00]))
        plain = bytearray()
        prev = 0x36
        for i, c in enumerate(block[8:]):
            swapped = ((c & 0x0F) << 4) | (c >> 4)
            plain.append(swapped ^ prev ^ (i % 256) ^ key[i % len(key)])
            prev = c
        raw = zlib.decompress(bytes(plain))
        self.assertEqual(zlib.adler32(raw), int.from_bytes(block[4:8], "big"))
        with self.assertRaises(zlib.error):
            zlib.decompress(block[8:])

    def test_flipped_byte_in_encrypted_key_info_is_a_checksum_error(self):
        for delta in (8, 12, 20):
            with self.subTest(delta):
                path = self.build("f%d.mdx" % delta, encrypted=2)
                flip(path, _mdx_writer.LAYOUT["key_info"] + delta)
                self.assertEqual(self.reason(path), "checksum")

    def test_registration_encryption_is_reported(self):
        for value in (1, 3):
            with self.subTest(value):
                self.assertEqual(self.reason(self.build("r%d.mdx" % value, encrypted=value)), "encrypted_registration")

    def test_key_info_encryption_needs_version_2(self):
        self.assertEqual(self.reason(self.build(version="1.2", encrypted=2)), "unsupported")


class MdxRecordTests(MdxTestCase):
    def links(self, extra=()):
        return [
            ("run", "бежать"),
            ("go", "@@@LINK=run"),
            ("a", "@@@LINK=b"),
            ("b", "@@@LINK=c"),
            ("c", "@@@LINK=d"),
            ("d", "конец"),
            ("p1", "@@@LINK=p2"),
            ("p2", "@@@LINK=p3"),
            ("p3", "@@@LINK=p4"),
            ("p4", "@@@LINK=p5"),
            ("p5", "дно"),
            ("self", "@@@LINK=self"),
            ("c1", "@@@LINK=c2"),
            ("c2", "@@@LINK=c1"),
            ("lost", "@@@LINK=nowhere"),
            ("Mixed", "@@@LINK=  RUN \r\nignored second line"),
            *extra,
        ]

    def test_link_is_followed(self):
        d = self.open(self.build(entries=self.links()))
        art = d.lookup("go")[0]
        self.assertEqual(art.text, "бежать")
        self.assertEqual(art.headword, "go")

    def test_three_hops_resolve_four_do_not(self):
        self.assertEqual(MAX_LINK_HOPS, 3)
        d = self.open(self.build(entries=self.links()))
        self.assertEqual(d.lookup("a")[0].text, "конец")
        self.assertEqual(d.lookup("p2")[0].text, "дно")
        self.assertEqual(d.lookup("p1"), [])

    def test_self_link_cycle_and_missing_target(self):
        d = self.open(self.build(entries=self.links()))
        for key in ("self", "c1", "c2", "lost"):
            self.assertEqual(d.lookup(key), [], key)

    def test_link_targets_are_folded_and_first_line_only(self):
        d = self.open(self.build(entries=self.links()))
        self.assertEqual(d.lookup("mixed")[0].text, "бежать")

    def test_html_is_flattened(self):
        d = self.open(self.build(entries=[("run", "<b>run</b><br>бежать")]))
        self.assertEqual(d.lookup("run")[0].text.split("\n"), ["run", "бежать"])

    def test_script_and_control_characters_are_dropped(self):
        d = self.open(self.build(entries=[("x", "<script>evil()</script>ok\x07")]))
        self.assertEqual(d.lookup("x")[0].text, "ok")

    def test_text_format_is_kept(self):
        d = self.open(self.build(entries=[("run", "run\nбежать")], fmt="Text"))
        self.assertEqual(d.lookup("run")[0].text, "run\nбежать")

    def test_empty_record_gives_no_article(self):
        d = self.open(self.build(entries=[("a", ""), ("b", "x")]))
        self.assertEqual(d.lookup("a"), [])
        self.assertEqual(d.lookup("b")[0].text, "x")


class MdxIndexCacheTests(MdxTestCase):
    def test_second_open_does_not_parse_the_key_blocks(self):
        path = self.build()
        self.open(path)
        self.assertTrue(index_cache_path(path, mdx.INDEX_TAG).exists())
        with mock.patch.object(mdx, "_build_index", side_effect=AssertionError("parsed")):
            d = self.open(path)
        self.check_all(d)

    def test_skipped_entries_survive_a_cache_hit(self):
        path = self.build(entries=ENTRIES + [("ghost", None, 10**6)])
        self.assertEqual(self.open(path).skipped_entries, 1)
        with mock.patch.object(mdx, "_build_index", side_effect=AssertionError("parsed")):
            d = self.open(path)
        self.assertEqual(d.skipped_entries, 1)
        self.assertEqual(d.entry_count, len(ENTRIES))

    def rebuilt_after(self, path, change):
        self.open(path)
        change()
        with mock.patch.object(mdx, "_build_index", wraps=mdx._build_index) as spy:
            d = self.open(path)
        self.assertEqual(spy.call_count, 1)
        self.check_all(d)

    def test_size_change_rebuilds(self):
        path = self.build()

        def grow():
            with open(path, "ab") as fh:
                fh.write(b"\x00")

        self.rebuilt_after(path, grow)

    def test_mtime_change_rebuilds(self):
        path = self.build()
        st = path.stat()
        self.rebuilt_after(path, lambda: os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000)))

    def test_poisoned_caches_are_ignored(self):
        path = self.build()
        cache = index_cache_path(path, mdx.INDEX_TAG)

        def poison(mutate):
            def run():
                wrapper = json.loads(cache.read_text(encoding="utf-8"))
                mutate(wrapper["data"])
                cache.write_text(json.dumps(wrapper), encoding="utf-8")

            return run

        def set_item(container, key, value):
            container[key] = value

        mutations = {
            "entry offset not in offsets": lambda p: p["entries"][0].__setitem__(0, 10**9),
            "block outside the file": lambda p: p["blocks"][0].__setitem__(0, 10**9),
            "block size over the cap": lambda p: p["blocks"][0].__setitem__(2, MAX_MDX_BLOCK + 1),
            "wrong key type": lambda p: set_item(p["keys"], "run", ["x"]),
            "key target out of range": lambda p: set_item(p["keys"], "run", [10**6]),
            "offsets out of range": lambda p: set_item(p, "offsets", [10**9]),
            "entries not a list": lambda p: set_item(p, "entries", "boom"),
            "negative skipped": lambda p: set_item(p, "skipped", -1),
            "wrong count": lambda p: set_item(p, "count", 99),
            "other encoding": lambda p: set_item(p, "enc", "gb18030"),
        }
        for name, mutate in mutations.items():
            with self.subTest(name):
                self.rebuilt_after(path, poison(mutate))


class MdxHostileInputTests(MdxTestCase):
    def test_declared_counts_and_sizes_above_the_caps_fail_at_open(self):
        for name, value in (
            ("MAX_BLOCKS", 1),
            ("MAX_KEY_INFO", 10),
            ("MAX_MDX_BLOCK", 20),
        ):
            # a fresh, never opened file each time: an index cache would hide the parse
            with self.subTest(name), mock.patch.object(mdx, name, value):
                self.assertEqual(self.reason(self.build("%s.mdx" % name)), "corrupt")
        self.check_all(self.open(self.build("fine.mdx")))

    def test_record_block_above_the_cap_fails_at_open(self):
        entries = [(k, "v" * 50) for k in "abcdef"]
        path = self.build(entries=entries, keys_per_block=6, record_block_size=120)
        with mock.patch.object(mdx, "MAX_MDX_BLOCK", 70):
            self.assertEqual(self.reason(path), "corrupt")

    def test_absurd_keyword_header_numbers(self):
        for index in (0, 1, 2, 3, 4):
            with self.subTest(index):
                path = self.build("h%d.mdx" % index)
                patch_keyword_header(path, index, 2**40)
                self.assertEqual(self.reason(path), "corrupt")
        path = self.build("sum.mdx")
        patch_keyword_header(path, 1, 5)
        self.assertEqual(self.reason(path), "corrupt")

    def test_offsets_beyond_the_record_data_are_skipped_and_counted(self):
        path = self.build(entries=ENTRIES + [("ghost", None, 10**6), ("ghost2", None, 10**9)])
        d = self.open(path)
        self.assertEqual(d.skipped_entries, 2)
        self.assertEqual(d.entry_count, len(ENTRIES))
        self.assertFalse(d.has("ghost"))
        self.check_all(d)

    def test_no_usable_entry_is_empty(self):
        self.assertEqual(self.reason(self.build(entries=[("ghost", None, 10**6)])), "empty")

    def test_over_long_key_is_skipped(self):
        path = self.build(entries=[("k" * 600, "x"), ("ok", "y")])
        d = self.open(path)
        self.assertEqual(d.skipped_entries, 1)
        self.assertEqual(d.lookup("ok")[0].text, "y")

    def test_zlib_key_block_that_inflates_beyond_its_declared_size(self):
        calls = []

        def bomb(raw):
            calls.append(raw)
            if len(calls) == 1:
                return 2, zlib.compress(raw * 1000)
            return 2, zlib.compress(raw)

        self.assertEqual(self.reason(self.build(key_codec=bomb)), "corrupt")

    def test_zlib_record_block_that_inflates_beyond_its_declared_size(self):
        calls = []

        def bomb(raw):
            calls.append(raw)
            if len(calls) == 1:
                return 2, zlib.compress(raw * 1000)
            return 2, zlib.compress(raw)

        d = self.open(self.build(record_codec=bomb))
        self.assertEqual(d.lookup("run"), [])
        self.assertEqual(d.lookup("fish")[0].text, "рыба")

    def test_lzo_block_with_a_wrong_declared_size_is_skipped(self):
        comp = vector("run_1000", "lzo1x_1_compress")

        def codec(raw):
            if raw == b"a" * 999:
                return 1, comp
            return 2, zlib.compress(raw)

        path = self.build(
            entries=[("bad", "a" * 999), ("good", "hello")],
            fmt="Text",
            append_nul=False,
            record_block_size=999,
            record_codec=codec,
        )
        d = self.open(path)
        self.assertEqual(d.lookup("bad"), [])
        self.assertEqual(d.lookup("good")[0].text, "hello")

    def test_lzo_lookbehind_past_the_start_is_skipped(self):
        bad = bytes([18, 0x61, 0xFF, 0xFF, 0x11, 0, 0])
        with self.assertRaises(LzoError):
            decompress(bad, 5)

        def codec(raw):
            if raw == b"hello":
                return 1, bad
            return 2, zlib.compress(raw)

        path = self.build(
            entries=[("bad", "hello"), ("good", "world")],
            fmt="Text",
            append_nul=False,
            record_block_size=5,
            record_codec=codec,
        )
        d = self.open(path)
        self.assertEqual(d.lookup("bad"), [])
        self.assertEqual(d.lookup("good")[0].text, "world")

    def test_hundred_thousand_identical_keys_open_quickly(self):
        entries = [("same", "x")] * 100_000
        path = self.build(
            entries=entries, keys_per_block=5000, record_block_size=1 << 20, record_codec="none", key_codec="none"
        )
        start = time.monotonic()
        d = self.open(path)
        self.assertLess(time.monotonic() - start, 5.0)
        self.assertEqual(d.entry_count, 100_000)
        d.close()
        start = time.monotonic()
        d = self.open(path)
        self.assertLess(time.monotonic() - start, 5.0)
        self.assertTrue(d.has("same"))

    def test_control_characters_in_keys_and_titles_are_cleaned(self):
        path = self.build(entries=[("a\x07b", "x")], title="Ti\x07tle")
        d = self.open(path)
        self.assertEqual(d.name, "Title")
        self.assertEqual(d.lookup(fold_key("ab"))[0].headword, "ab")

    def test_attribute_regex_is_linear_on_hostile_headers(self):
        path = self.build()
        rewrite_header(path, "a" * 250_000 + " " * 250_000)
        start = time.monotonic()
        self.assertEqual(self.reason(path), "corrupt")
        self.assertLess(time.monotonic() - start, 3.0)


if __name__ == "__main__":
    unittest.main()
