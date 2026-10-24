"""Test-only dictzip writer, shared by the StarDict and DSL test plans (stdlib only).

make_dictzip() produces a real gzip stream (gzip.decompress reads it back) whose
FEXTRA field carries the 'RA' chunk table. assemble_dictzip() is the low-level
builder the dictzip tests use to make deliberately broken files.
"""
import struct
import zlib


def assemble_dictzip(
    chunks,
    chunk_len,
    isize,
    crc=0,
    *,
    ver=1,
    count=None,
    sizes=None,
    fname=None,
    comment=None,
    hcrc=False,
    subfield=b"RA",
):
    """Join already compressed chunks into a dictzip file; every header field can be forced."""
    if sizes is None:
        sizes = [len(c) for c in chunks]
    if count is None:
        count = len(chunks)
    body = struct.pack("<HHH", ver, chunk_len, count) + struct.pack("<%dH" % len(sizes), *sizes)
    sub = subfield + struct.pack("<H", len(body)) + body
    if len(sub) > 0xFFFF:
        raise ValueError("chunk table does not fit in the gzip extra field")
    flags = 4
    if fname is not None:
        flags |= 8
    if comment is not None:
        flags |= 16
    if hcrc:
        flags |= 2
    head = b"\x1f\x8b\x08" + bytes([flags]) + b"\x00\x00\x00\x00\x00\x03"
    head += struct.pack("<H", len(sub)) + sub
    if fname is not None:
        head += fname.encode("latin-1") + b"\x00"
    if comment is not None:
        head += comment.encode("latin-1") + b"\x00"
    if hcrc:
        head += struct.pack("<H", zlib.crc32(head) & 0xFFFF)
    return head + b"".join(chunks) + struct.pack("<II", crc & 0xFFFFFFFF, isize & 0xFFFFFFFF)


def make_dictzip(data: bytes, chunk_len: int = 4096, fname: str | None = "x.dict") -> bytes:
    """Compress data into dictzip: independent chunks, each ending on a full flush."""
    if not data:
        raise ValueError("empty input is not supported")
    if not 0 < chunk_len <= 0xFFFF:
        raise ValueError("chunk_len out of range")
    pieces = [data[i:i + chunk_len] for i in range(0, len(data), chunk_len)]
    comp = zlib.compressobj(9, zlib.DEFLATED, -15)
    chunks = []
    for i, piece in enumerate(pieces):
        last = i == len(pieces) - 1
        chunks.append(comp.compress(piece) + comp.flush(zlib.Z_FINISH if last else zlib.Z_FULL_FLUSH))
    return assemble_dictzip(chunks, chunk_len, len(data), zlib.crc32(data), fname=fname)
