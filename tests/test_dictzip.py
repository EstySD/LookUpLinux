"""dictzip random-access reader (D-08, D-33, T-02-05, T-02-06)."""
import gzip
import struct
import unittest
import zlib

from lookup.dictzip import DictzipError, DictzipFile
from tests._dictzip_writer import assemble_dictzip, make_dictzip
from tests._support import make_tempdir

DATA = bytes((i * 7 + i // 13) % 251 for i in range(1000)) + b"tail-bytes-here"


def _raw(chunk_bytes):
    c = zlib.compressobj(9, zlib.DEFLATED, -15)
    return c.compress(chunk_bytes) + c.flush(zlib.Z_FINISH)


class DictzipBase(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)
        self.root.mkdir(parents=True, exist_ok=True)
        self.n = 0

    def write(self, blob):
        self.n += 1
        p = self.root / ("f%d.dz" % self.n)
        p.write_bytes(blob)
        return p

    def open(self, blob):
        f = DictzipFile(self.write(blob))
        self.addCleanup(f.close)
        return f


class ReadTests(DictzipBase):
    def test_read_all_and_geometry(self):
        blob = make_dictzip(DATA, 100)
        self.assertEqual(gzip.decompress(blob), DATA)
        f = self.open(blob)
        self.assertEqual(f.read_all(), DATA)
        self.assertEqual(f.size, len(DATA))
        self.assertEqual(f.chunk_len, 100)
        self.assertEqual(f.chunk_count, -(-len(DATA) // 100))

    def test_ranges(self):
        f = self.open(make_dictzip(DATA, 100))
        cases = {
            "inside one chunk": (110, 30),
            "two chunks": (90, 20),
            "many chunks": (50, 700),
            "first byte": (0, 1),
            "last byte": (len(DATA) - 1, 1),
            "whole file": (0, len(DATA)),
            "chunk boundary": (100, 100),
            "zero length": (500, 0),
            "zero length at end": (len(DATA), 0),
        }
        for name, (off, ln) in cases.items():
            with self.subTest(name):
                self.assertEqual(f.read(off, ln), DATA[off:off + ln])

    def test_single_chunk_file(self):
        f = self.open(make_dictzip(b"hello", 4096))
        self.assertEqual(f.read(1, 3), b"ell")
        self.assertEqual(f.chunk_count, 1)

    def test_only_covering_chunks_are_inflated(self):
        # corrupt chunk 0; a read that does not touch it must still work
        blob = bytearray(make_dictzip(DATA, 100))
        f0 = self.open(bytes(blob))
        start = f0._starts[0]
        for i in range(start, start + 4):
            blob[i] ^= 0xFF
        f = self.open(bytes(blob))
        self.assertEqual(f.read(250, 20), DATA[250:270])
        with self.assertRaises(DictzipError):
            f.read(0, 10)

    def test_invalid_ranges(self):
        f = self.open(make_dictzip(DATA, 100))
        for off, ln in [(len(DATA) - 1, 2), (len(DATA) + 1, 0), (-1, 5), (5, -1), (0, len(DATA) + 1)]:
            with self.subTest(off=off, ln=ln):
                with self.assertRaises(DictzipError):
                    f.read(off, ln)

    def test_max_out(self):
        f = self.open(make_dictzip(DATA, 100))
        with self.assertRaises(DictzipError):
            f.read(0, 200, max_out=199)
        self.assertEqual(f.read(0, 200, max_out=200), DATA[:200])

    def test_read_all_cap(self):
        f = self.open(make_dictzip(DATA, 100))
        with self.assertRaises(DictzipError):
            f.read_all(max_total=len(DATA) - 1)

    def test_fname_variants(self):
        for fname in ("x.dict", None):
            with self.subTest(fname=fname):
                f = self.open(make_dictzip(DATA, 128, fname=fname))
                self.assertEqual(f.read_all(), DATA)

    def test_comment_and_header_crc_flags(self):
        chunks = [_raw(DATA[:500]), _raw(DATA[500:])]
        blob = assemble_dictzip(
            chunks, 500, len(DATA), zlib.crc32(DATA), fname="n", comment="c", hcrc=True
        )
        f = self.open(blob)
        self.assertEqual(f.read_all(), DATA)

    def test_context_manager(self):
        p = self.write(make_dictzip(DATA, 100))
        with DictzipFile(p) as f:
            self.assertEqual(f.read(0, 4), DATA[:4])
        with self.assertRaises(DictzipError):
            f.read(0, 4)


class MalformedHeaderTests(DictzipBase):
    def bad(self, blob):
        p = self.write(blob)
        with self.assertRaises(DictzipError):
            DictzipFile(p).close()

    def test_wrong_magic(self):
        good = make_dictzip(DATA, 100)
        self.bad(b"PK" + good[2:])
        self.bad(b"")
        self.bad(b"\x1f")

    def test_plain_gzip_without_ra(self):
        self.bad(gzip.compress(DATA))

    def test_other_subfield(self):
        chunks = [_raw(DATA)]
        self.bad(assemble_dictzip(chunks, 2000, len(DATA), subfield=b"XX"))

    def test_wrong_version(self):
        self.bad(assemble_dictzip([_raw(DATA)], 2000, len(DATA), ver=2))

    def test_zero_chunk_len(self):
        self.bad(assemble_dictzip([_raw(DATA)], 0, len(DATA)))

    def test_chunk_count_larger_than_table(self):
        self.bad(assemble_dictzip([_raw(DATA)], 2000, len(DATA), count=1000))

    def test_chunk_count_smaller_than_table(self):
        self.bad(assemble_dictzip([_raw(DATA)], 2000, len(DATA), count=0))

    def test_sizes_exceed_file(self):
        chunks = [_raw(DATA)]
        self.bad(assemble_dictzip(chunks, 2000, len(DATA), sizes=[60000]))

    def test_isize_inconsistent_with_geometry(self):
        chunks = [_raw(DATA[:500]), _raw(DATA[500:])]
        self.bad(assemble_dictzip(chunks, 500, 10_000_000))
        self.bad(assemble_dictzip(chunks, 500, 500))

    def test_every_truncation_is_dictzip_error(self):
        blob = make_dictzip(DATA, 300)
        for cut in range(len(blob)):
            with self.subTest(cut=cut):
                self.bad(blob[:cut])

    def test_unterminated_name(self):
        good = make_dictzip(DATA, 300, fname="abc")
        i = good.index(b"abc\x00")
        self.bad(good[:i] + b"abc" + good[i + 4:])


class BombTests(DictzipBase):
    def test_chunk_inflating_past_declared_length(self):
        bomb = _raw(b"a" * 1000)
        blob = assemble_dictzip([bomb], 10, 10)
        f = self.open(blob)
        with self.assertRaises(DictzipError):
            f.read(0, 5)

    def test_short_non_final_chunk(self):
        chunks = [_raw(DATA[:50]), _raw(DATA[100:150])]
        blob = assemble_dictzip(chunks, 100, 150)
        f = self.open(blob)
        with self.assertRaises(DictzipError):
            f.read(0, 10)

    def test_garbage_deflate_data(self):
        blob = assemble_dictzip([b"\xff" * 20], 100, 50)
        f = self.open(blob)
        with self.assertRaises(DictzipError):
            f.read(0, 10)

    def test_dictzip_error_is_valueerror(self):
        self.assertTrue(issubclass(DictzipError, ValueError))
        self.assertIsInstance(struct.calcsize("<H"), int)


if __name__ == "__main__":
    unittest.main()
