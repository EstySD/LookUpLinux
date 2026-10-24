"""RIPEMD-128 for MDX format compatibility only (Encrypted=2 key info).

Not a security primitive: it only derives the key that MDX files use to scramble
their key-info block, and hashlib has no ripemd128 (D-34). Written from the
RIPEMD-128 specification (two parallel lines of four 16-step rounds, 32-bit
words, little-endian, MD-style padding). Stdlib only; never prints or logs.
"""
import struct

_MASK = 0xFFFFFFFF

# Message word order, rotation amounts: left line then right line, 64 steps each.
_R_L = (
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
    7, 4, 13, 1, 10, 6, 15, 3, 12, 0, 9, 5, 2, 14, 11, 8,
    3, 10, 14, 4, 9, 15, 8, 1, 2, 7, 0, 6, 13, 11, 5, 12,
    1, 9, 11, 10, 0, 8, 12, 4, 13, 3, 7, 15, 14, 5, 6, 2,
)
_R_R = (
    5, 14, 7, 0, 9, 2, 11, 4, 13, 6, 15, 8, 1, 10, 3, 12,
    6, 11, 3, 7, 0, 13, 5, 10, 14, 15, 8, 12, 4, 9, 1, 2,
    15, 5, 1, 3, 7, 14, 6, 9, 11, 8, 12, 2, 10, 0, 4, 13,
    8, 6, 4, 1, 3, 11, 15, 0, 5, 12, 2, 13, 9, 7, 10, 14,
)
_S_L = (
    11, 14, 15, 12, 5, 8, 7, 9, 11, 13, 14, 15, 6, 7, 9, 8,
    7, 6, 8, 13, 11, 9, 7, 15, 7, 12, 15, 9, 11, 7, 13, 12,
    11, 13, 6, 7, 14, 9, 13, 15, 14, 8, 13, 6, 5, 12, 7, 5,
    11, 12, 14, 15, 14, 15, 9, 8, 9, 14, 5, 6, 8, 6, 5, 12,
)
_S_R = (
    8, 9, 9, 11, 13, 15, 15, 5, 7, 7, 8, 11, 14, 14, 12, 6,
    9, 13, 15, 7, 12, 8, 9, 11, 7, 7, 12, 7, 6, 15, 13, 11,
    9, 7, 15, 11, 8, 6, 6, 14, 12, 13, 5, 14, 13, 13, 7, 5,
    15, 5, 8, 11, 14, 14, 6, 14, 6, 9, 12, 9, 12, 5, 15, 8,
)
_K_L = (0x00000000, 0x5A827999, 0x6ED9EBA1, 0x8F1BBCDC)
_K_R = (0x50A28BE6, 0x5C4DD124, 0x6D703EF3, 0x00000000)


def _f(n: int, x: int, y: int, z: int) -> int:
    if n == 0:
        return x ^ y ^ z
    if n == 1:
        return (x & y) | (~x & _MASK & z)
    if n == 2:
        return (x | (~y & _MASK)) ^ z
    return (x & z) | (y & (~z & _MASK))


def _rol(x: int, n: int) -> int:
    return ((x << n) | (x >> (32 - n))) & _MASK


def _compress(h: list, block: bytes) -> None:
    x = struct.unpack("<16I", block)
    al, bl, cl, dl = h
    ar, br, cr, dr = h
    for j in range(64):
        rnd = j >> 4
        t = _rol((al + _f(rnd, bl, cl, dl) + x[_R_L[j]] + _K_L[rnd]) & _MASK, _S_L[j])
        al, dl, cl, bl = dl, cl, bl, t
        t = _rol((ar + _f(3 - rnd, br, cr, dr) + x[_R_R[j]] + _K_R[rnd]) & _MASK, _S_R[j])
        ar, dr, cr, br = dr, cr, br, t
    t = (h[1] + cl + dr) & _MASK
    h[1] = (h[2] + dl + ar) & _MASK
    h[2] = (h[3] + al + br) & _MASK
    h[3] = (h[0] + bl + cr) & _MASK
    h[0] = t


def digest(data: bytes) -> bytes:
    """Return the 16-byte RIPEMD-128 digest of bytes-like data."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data must be bytes-like, got " + type(data).__name__)
    raw = bytes(data)
    h = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476]
    padded = raw + b"\x80" + b"\x00" * ((55 - len(raw)) % 64)
    padded += struct.pack("<Q", (len(raw) * 8) & 0xFFFFFFFFFFFFFFFF)
    for i in range(0, len(padded), 64):
        _compress(h, padded[i:i + 64])
    return struct.pack("<4I", *h)


def hexdigest(data: bytes) -> str:
    """Return the digest as 32 lowercase hex characters."""
    return digest(data).hex()
