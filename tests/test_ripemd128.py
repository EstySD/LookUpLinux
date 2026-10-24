"""RIPEMD-128 against reference and boundary vectors (D-07, D-34)."""
import unittest

from lookup.ripemd128 import digest, hexdigest

VECTORS = [
    (b"", "cdf26213a150dc3ecb610f18f6b38b46"),
    (b"The quick brown fox jumps over the lazy dog", "3fa9b57f053c053fbe2735b2380db596"),
    (b"a", "86be7afa339d0fc7cfc785e72f578d33"),
    (b"abc", "c14a12199c66e4ba84636b0f69144c77"),
    (b"message digest", "9e327b3d6e523062afc1132d7df9d1b8"),
    (b"abcdefghijklmnopqrstuvwxyz", "fd2aa607f71dc8f510714922b371834e"),
    (
        b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
        "a1aa0689d0fafa2ddc22e88b49133a06",
    ),
    (b"1234567890" * 8, "3f45ef194732c2dbb2c4a2c769795fa3"),
    # padding boundaries
    (b"x" * 55, "939ea8b9c8a62aa6c18f47b65743dce8"),
    (b"x" * 56, "01b3ed3753c897abadee8a09b85760a6"),
    (b"x" * 63, "ed06e22b7b84ee5c0bfe7047af24ba9c"),
    (b"x" * 64, "0411681595c303a45bdc9eeefb73b666"),
    (b"x" * 65, "3259405c889aa6e7be938a4d1f73256b"),
]


class Ripemd128Tests(unittest.TestCase):
    def test_vectors(self):
        for data, hexed in VECTORS:
            with self.subTest(length=len(data), head=data[:8]):
                self.assertEqual(hexdigest(data), hexed)
                self.assertEqual(digest(data).hex(), hexed)

    def test_digest_is_16_bytes(self):
        self.assertEqual(len(digest(b"abc")), 16)
        self.assertIsInstance(digest(b"abc"), bytes)

    def test_str_rejected(self):
        with self.assertRaises(TypeError):
            digest("abc")
        with self.assertRaises(TypeError):
            hexdigest("abc")

    def test_bytearray_and_memoryview(self):
        want = digest(b"message digest")
        self.assertEqual(digest(bytearray(b"message digest")), want)
        self.assertEqual(digest(memoryview(b"message digest")), want)


if __name__ == "__main__":
    unittest.main()
