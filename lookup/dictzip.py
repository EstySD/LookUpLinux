"""Random-access reader for dictzip files (.dict.dz, .dsl.dz), stdlib only (D-08).

A dictzip file is a gzip file whose FEXTRA field holds an 'RA' chunk table: the
data is split into equal chunks, each one an independent raw deflate stream.
Reading a byte range inflates only the chunks that cover it.

The file is untrusted (D-33, T-02-05): the header geometry is validated at open,
every chunk is inflated with a hard output bound of chunk_len + 1 and must come
out at exactly its expected length, and every failure is a DictzipError. The
trailer CRC is not checked (that would inflate the whole file).
Not thread-safe: one file handle with seeks. Never prints or logs; messages
carry no file content.
"""
import struct
import zlib

_NAME_MAX = 1 << 16  # longest FNAME/FCOMMENT accepted


class DictzipError(ValueError):
    """Raised for a malformed dictzip file or an invalid read request."""


def _need(f, n: int, what: str) -> bytes:
    b = f.read(n)
    if len(b) != n:
        raise DictzipError("truncated " + what)
    return b


def _skip_cstring(f) -> None:
    taken = 0
    while True:
        block = f.read(256)
        if not block:
            raise DictzipError("truncated header string")
        i = block.find(b"\x00")
        if i >= 0:
            f.seek(i + 1 - len(block), 1)
            return
        taken += len(block)
        if taken > _NAME_MAX:
            raise DictzipError("header string too long")


class DictzipFile:
    """Open dictzip file. Attributes: chunk_len, chunk_count, size (uncompressed bytes)."""

    def __init__(self, path):
        self._f = open(path, "rb")
        try:
            self._parse()
        except DictzipError:
            self._f.close()
            raise
        except (OSError, struct.error, zlib.error, OverflowError) as exc:
            self._f.close()
            if isinstance(exc, OSError):
                raise
            raise DictzipError("malformed dictzip header") from None

    def _parse(self) -> None:
        f = self._f
        head = _need(f, 10, "header")
        if head[:2] != b"\x1f\x8b":
            raise DictzipError("not a gzip file")
        if head[2] != 8:
            raise DictzipError("unsupported gzip method")
        flags = head[3]
        if not flags & 4:
            raise DictzipError("no extra field, not dictzip")
        (xlen,) = struct.unpack("<H", _need(f, 2, "extra length"))
        extra = _need(f, xlen, "extra field")
        body = None
        pos = 0
        while pos < xlen:
            if pos + 4 > xlen:
                raise DictzipError("malformed extra field")
            si = extra[pos:pos + 2]
            (ln,) = struct.unpack_from("<H", extra, pos + 2)
            if pos + 4 + ln > xlen:
                raise DictzipError("subfield overruns extra field")
            if si == b"RA" and body is None:
                body = extra[pos + 4:pos + 4 + ln]
            pos += 4 + ln
        if body is None:
            raise DictzipError("no RA subfield, not dictzip")
        if len(body) < 6:
            raise DictzipError("RA subfield too short")
        ver, chunk_len, count = struct.unpack_from("<HHH", body, 0)
        if ver != 1:
            raise DictzipError("unsupported dictzip version")
        if chunk_len == 0:
            raise DictzipError("zero chunk length")
        if count == 0:
            raise DictzipError("zero chunk count")
        if len(body) != 6 + 2 * count:
            raise DictzipError("chunk table does not match chunk count")
        sizes = struct.unpack_from("<%dH" % count, body, 6)
        if flags & 8:
            _skip_cstring(f)
        if flags & 16:
            _skip_cstring(f)
        if flags & 2:
            _need(f, 2, "header crc")
        data_start = f.tell()
        file_size = f.seek(0, 2)
        if data_start + sum(sizes) + 8 > file_size:
            raise DictzipError("chunk sizes exceed file size")
        f.seek(file_size - 4)
        (isize,) = struct.unpack("<I", _need(f, 4, "trailer"))
        if not chunk_len * (count - 1) < isize <= chunk_len * count:
            raise DictzipError("uncompressed size does not match chunk geometry")
        starts = [data_start]
        for s in sizes:
            starts.append(starts[-1] + s)
        self.chunk_len = chunk_len
        self.chunk_count = count
        self.size = isize
        self._sizes = sizes
        self._starts = starts

    def _chunk(self, index: int) -> bytes:
        f = self._f
        if f is None or f.closed:
            raise DictzipError("file is closed")
        f.seek(self._starts[index])
        raw = f.read(self._sizes[index])
        if len(raw) != self._sizes[index]:
            raise DictzipError("truncated chunk")
        try:
            out = zlib.decompressobj(-15).decompress(raw, self.chunk_len + 1)
        except zlib.error:
            raise DictzipError("corrupt chunk") from None
        if index < self.chunk_count - 1:
            expected = self.chunk_len
        else:
            expected = self.size - self.chunk_len * (self.chunk_count - 1)
        if len(out) != expected:
            raise DictzipError("chunk length differs from the chunk table")
        return out

    def read(self, offset: int, length: int, max_out: int = 16 << 20) -> bytes:
        """Return uncompressed bytes [offset, offset + length), inflating only covering chunks."""
        if offset < 0 or length < 0:
            raise DictzipError("negative offset or length")
        if length > max_out:
            raise DictzipError("requested range exceeds max_out")
        if offset + length > self.size:
            raise DictzipError("range outside the file")
        if length == 0:
            return b""
        first = offset // self.chunk_len
        last = (offset + length - 1) // self.chunk_len
        buf = b"".join(self._chunk(i) for i in range(first, last + 1))
        start = offset - first * self.chunk_len
        return buf[start:start + length]

    def read_all(self, max_total: int = 512 << 20) -> bytes:
        """Return the whole uncompressed content; refuse files larger than max_total."""
        if self.size > max_total:
            raise DictzipError("file exceeds max_total")
        return b"".join(self._chunk(i) for i in range(self.chunk_count))

    def close(self) -> None:
        f = getattr(self, "_f", None)
        if f is not None:
            f.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False
