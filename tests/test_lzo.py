"""LZO1X decompressor against real liblzo2 2.10 output (D-07, T-02-04, T-02-06)."""
import base64
import hashlib
import json
import unittest
from pathlib import Path

from lookup import lzo
from lookup.lzo import LzoError, decompress

VECTORS = json.loads(
    (Path(__file__).parent / "fixtures" / "lzo" / "vectors.json").read_text(encoding="utf-8")
)


def _comp(v):
    return base64.b64decode(v["comp_b64"])


class VectorTests(unittest.TestCase):
    def test_every_vector_roundtrips(self):
        self.assertGreaterEqual(len(VECTORS), 14)
        for v in VECTORS:
            with self.subTest(name=v["name"], algo=v["algo"]):
                out = decompress(_comp(v), v["raw_len"])
                self.assertEqual(len(out), v["raw_len"])
                self.assertEqual(hashlib.sha256(out).hexdigest(), v["raw_sha256"])

    def test_both_algos_present(self):
        self.assertEqual(
            {v["algo"] for v in VECTORS}, {"lzo1x_1_compress", "lzo1x_999_compress"}
        )

    def test_accepts_bytearray_and_memoryview(self):
        v = next(x for x in VECTORS if x["name"] == "run_1000")
        data = _comp(v)
        self.assertEqual(decompress(bytearray(data), v["raw_len"]), b"a" * 1000)
        self.assertEqual(decompress(memoryview(data), v["raw_len"]), b"a" * 1000)


class MalformedTests(unittest.TestCase):
    def test_truncated_input_raises_lzoerror(self):
        tested = 0
        for v in VECTORS:
            comp = _comp(v)
            if v["raw_len"] < 100:
                continue
            with self.subTest(name=v["name"], algo=v["algo"]):
                with self.assertRaises(LzoError):
                    decompress(comp[: len(comp) // 2], v["raw_len"])
                tested += 1
        self.assertGreater(tested, 0)

    def test_truncated_at_every_length_never_leaks_other_errors(self):
        v = next(
            x for x in VECTORS if x["name"] == "period2_10000" and x["algo"] == "lzo1x_999_compress"
        )
        comp = _comp(v)
        for cut in range(len(comp)):
            with self.subTest(cut=cut):
                with self.assertRaises(LzoError):
                    decompress(comp[:cut], v["raw_len"])

    def test_out_len_too_small(self):
        v = next(x for x in VECTORS if x["name"] == "run_1000")
        with self.assertRaises(LzoError):
            decompress(_comp(v), v["raw_len"] - 1)

    def test_out_len_too_large(self):
        v = next(x for x in VECTORS if x["name"] == "run_1000")
        with self.assertRaises(LzoError):
            decompress(_comp(v), v["raw_len"] + 1)

    def test_out_len_above_max_out_or_negative(self):
        self.assertEqual(lzo.MAX_OUT, 64 << 20)
        v = next(x for x in VECTORS if x["name"] == "abc")
        with self.assertRaises(LzoError):
            decompress(_comp(v), lzo.MAX_OUT + 1)
        with self.assertRaises(LzoError):
            decompress(_comp(v), -1)

    def test_lookbehind_beyond_start_raises(self):
        # three literals, then an M3 match with distance 128 while only 3 bytes exist
        with self.assertRaises(LzoError):
            decompress(bytes([0x14, 0x61, 0x62, 0x63, 0x21, 0xFC, 0x01]), 6)

    def test_trailing_bytes_after_end_marker(self):
        v = next(x for x in VECTORS if x["name"] == "abc")
        with self.assertRaises(LzoError):
            decompress(_comp(v) + b"\x00", v["raw_len"])

    def test_runaway_literal_length_is_bounded(self):
        # a long run of zero length-extension bytes must not allocate or hang
        data = bytes([0x00]) + b"\x00" * 100000 + b"\x01"
        with self.assertRaises(LzoError):
            decompress(data, 1000)

    def test_empty_input(self):
        with self.assertRaises(LzoError):
            decompress(b"", 0)

    def test_non_bytes_input(self):
        with self.assertRaises(TypeError):
            decompress("abc", 3)
        with self.assertRaises(TypeError):
            decompress(None, 0)

    def test_lzoerror_is_valueerror(self):
        self.assertTrue(issubclass(LzoError, ValueError))


if __name__ == "__main__":
    unittest.main()
