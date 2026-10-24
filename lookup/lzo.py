"""LZO1X decompressor (decompress only), written from the LZO1X stream format.

MDX dictionary blocks may be LZO-compressed and the stdlib has no LZO codec
(D-07). The caller must pass the exact decompressed size (MDX records it), so
the output is bounded before any work is done. Malformed, truncated or
oversized input raises LzoError and nothing else (T-02-04, T-02-06).
No compression function exists: MDX is read-only here. The module never prints
or logs.
"""

# Largest block accepted. MDX blocks are small; this only stops absurd sizes
# declared by a hostile file from reaching the allocator.
MAX_OUT = 64 << 20

_MAIN, _FIRST_LIT, _MATCH_NEXT, _MATCH, _MATCH_DONE = range(5)


class LzoError(ValueError):
    """Raised for malformed, truncated or oversized LZO1X data."""


def decompress(data: bytes, out_len: int) -> bytes:
    """Decompress one LZO1X stream that must expand to exactly out_len bytes."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data must be bytes-like, got " + type(data).__name__)
    if not isinstance(out_len, int) or isinstance(out_len, bool):
        raise TypeError("out_len must be int, got " + type(out_len).__name__)
    if out_len < 0 or out_len > MAX_OUT:
        raise LzoError("declared output size out of range")
    src = bytes(data)
    n = len(src)
    if n == 0:
        raise LzoError("empty input")
    try:
        return _run(src, n, out_len)
    except IndexError:
        raise LzoError("truncated input") from None


def _run(src: bytes, n: int, out_len: int) -> bytes:
    out = bytearray()

    def literals(ip: int, count: int) -> int:
        if ip + count > n:
            raise LzoError("truncated input")
        if len(out) + count > out_len:
            raise LzoError("output exceeds declared size")
        out.extend(src[ip:ip + count])
        return ip + count

    def copy_back(dist: int, length: int) -> None:
        if dist == 0 or dist > len(out):
            raise LzoError("lookbehind out of range")
        if len(out) + length > out_len:
            raise LzoError("output exceeds declared size")
        start = len(out) - dist
        if dist >= length:
            out.extend(out[start:start + length])
        else:
            chunk = out[start:]
            reps, rem = divmod(length, dist)
            out.extend(chunk * reps + chunk[:rem])

    ip = 0
    lits = 0
    t = 0
    if src[0] > 17:
        t = src[0] - 17
        ip = 1
        if t < 4:
            state, lits = _MATCH_NEXT, t
        else:
            ip = literals(ip, t)
            state = _FIRST_LIT
    else:
        state = _MAIN
    while True:
        if state == _MAIN:
            t = src[ip]
            ip += 1
            if t >= 16:
                state = _MATCH
                continue
            if t == 0:
                while src[ip] == 0:
                    t += 255
                    ip += 1
                t += 15 + src[ip]
                ip += 1
            ip = literals(ip, t + 3)
            state = _FIRST_LIT
        elif state == _FIRST_LIT:
            t = src[ip]
            ip += 1
            if t >= 16:
                state = _MATCH
                continue
            copy_back(1 + 0x800 + (t >> 2) + (src[ip] << 2), 3)
            ip += 1
            state = _MATCH_DONE
        elif state == _MATCH_NEXT:
            ip = literals(ip, lits)
            t = src[ip]
            ip += 1
            state = _MATCH
        elif state == _MATCH:
            if t >= 64:  # M2
                dist = 1 + ((t >> 2) & 7) + (src[ip] << 3)
                ip += 1
                length = (t >> 5) + 1
            elif t >= 32:  # M3
                t &= 31
                if t == 0:
                    while src[ip] == 0:
                        t += 255
                        ip += 1
                    t += 31 + src[ip]
                    ip += 1
                dist = 1 + (src[ip] >> 2) + (src[ip + 1] << 6)
                ip += 2
                length = t + 2
            elif t >= 16:  # M4, or the end-of-stream marker
                hi = (t & 8) << 11
                t &= 7
                if t == 0:
                    while src[ip] == 0:
                        t += 255
                        ip += 1
                    t += 7 + src[ip]
                    ip += 1
                back = (src[ip] >> 2) + (src[ip + 1] << 6)
                ip += 2
                if hi + back == 0:
                    break
                dist = hi + back + 0x4000
                length = t + 2
            else:  # M1: two bytes copied after a literal run
                dist = 1 + (t >> 2) + (src[ip] << 2)
                ip += 1
                copy_back(dist, 2)
                state = _MATCH_DONE
                continue
            copy_back(dist, length)
            state = _MATCH_DONE
        else:  # _MATCH_DONE
            s = src[ip - 2] & 3
            if s == 0:
                state = _MAIN
            else:
                lits = s
                state = _MATCH_NEXT
    if ip != n:
        raise LzoError("trailing bytes after end marker")
    if len(out) != out_len:
        raise LzoError("output shorter than declared size")
    return bytes(out)
