"""Independent MDX (MDict) writer for tests, stdlib only (D-34).

Written from the format description (RESEARCH Format Reference 3), not from
lookup/mdx.py, so reader and writer can disagree and the tests notice. It
produces versions 1.2 and 2.0, the encodings UTF-8, UTF-16, GBK and Big5, key
and record blocks stored uncompressed, with zlib, or as a literal-only LZO1X
stream, and the Encrypted=2 key info scheme.

`write_mdx` leaves a description of the byte layout in `LAYOUT` so a test can
damage one precise field.
"""
import html
import struct
import zlib
from pathlib import Path

from lookup.ripemd128 import digest

LAYOUT: dict = {}

_ENCODINGS = {
    "UTF-8": ("utf-8", 1),
    "UTF8": ("utf-8", 1),
    "UTF-16": ("utf-16-le", 2),
    "GBK": ("gbk", 1),
    "BIG5": ("big5", 1),
}


def lzo_literal_stream(data: bytes) -> bytes:
    """A valid LZO1X stream that holds `data` as one literal run (no compression)."""
    n = len(data)
    if n == 0:
        return b"\x11\x00\x00"
    if n <= 238:
        head = bytes([17 + n])
    else:
        k = (n - 19) // 255
        b = n - 18 - 255 * k
        head = b"\x00" * (1 + k) + bytes([b])
    return head + bytes(data) + b"\x11\x00\x00"


def _compress(codec, raw: bytes):
    if callable(codec):
        return codec(raw)
    if codec == "none":
        return 0, raw
    if codec == "zlib":
        return 2, zlib.compress(raw)
    if codec == "lzo":
        return 1, lzo_literal_stream(raw)
    raise ValueError("unknown codec " + repr(codec))


def _block(codec, raw: bytes) -> bytes:
    ctype, comp = _compress(codec, raw)
    return struct.pack("<I", ctype) + struct.pack(">I", zlib.adler32(raw) & 0xFFFFFFFF) + comp


def _encrypt_key_info(block: bytes) -> bytes:
    key = digest(block[4:8] + b"\x95\x36\x00\x00")
    out = bytearray(block[:8])
    prev = 0x36
    for i, p in enumerate(block[8:]):
        t = p ^ prev ^ (i & 0xFF) ^ key[i % len(key)]
        c = ((t & 0x0F) << 4) | (t >> 4)
        out.append(c)
        prev = c
    return bytes(out)


def write_mdx(
    path,
    entries,
    *,
    version="2.0",
    encoding="UTF-8",
    record_codec="zlib",
    key_codec="zlib",
    encrypted=0,
    fmt="Html",
    title="Test",
    keys_per_block=3,
    record_block_size=64,
    append_nul=True,
    corrupt=None,
) -> Path:
    """Write an MDX file and return its path.

    `entries` is a list of (key, text) pairs in record order. A third item
    overrides the record offset; text None stores no record (used to make keys
    that point outside the record data).
    """
    path = Path(path)
    v2 = float(version) >= 2.0
    w = 8 if v2 else 4
    pyenc, unit = _ENCODINGS[encoding.upper()]
    term = b"\x00" * unit

    def num(x, width=w):
        return int(x).to_bytes(width, "big")

    records = bytearray()
    items = []
    for e in entries:
        key, text = e[0], e[1]
        computed = len(records)
        if text is not None:
            records += text.encode(pyenc) + (term if append_nul else b"")
        items.append((key, e[2] if len(e) > 2 else computed))

    order = sorted(items, key=lambda it: it[0])
    chunks = [order[i:i + keys_per_block] for i in range(0, len(order), keys_per_block)]

    def keyfield(k):
        kb = k.encode(pyenc)
        n = len(kb) // unit
        if v2:
            return n.to_bytes(2, "big") + kb + term
        return bytes([min(n, 255)]) + kb

    key_blocks = []
    info = bytearray()
    for ch in chunks:
        raw = b"".join(num(off) + k.encode(pyenc) + term for k, off in ch)
        blk = _block(key_codec, raw)
        key_blocks.append(blk)
        info += num(len(ch)) + keyfield(ch[0][0]) + keyfield(ch[-1][0]) + num(len(blk)) + num(len(raw))
    key_blocks_bytes = b"".join(key_blocks)

    if v2:
        key_info = _block(key_codec, bytes(info))
        if encrypted & 2:
            key_info = _encrypt_key_info(key_info)
        kw = b"".join(
            num(x) for x in (len(chunks), len(items), len(info), len(key_info), len(key_blocks_bytes))
        )
        kw += struct.pack(">I", zlib.adler32(kw) & 0xFFFFFFFF)
    else:
        key_info = bytes(info)
        kw = b"".join(num(x) for x in (len(chunks), len(items), len(key_info), len(key_blocks_bytes)))

    rec_raws = [bytes(records[i:i + record_block_size]) for i in range(0, len(records), record_block_size)]
    rec_blocks = [_block(record_codec, raw) for raw in rec_raws]
    rec_index = b"".join(num(len(b)) + num(len(r)) for b, r in zip(rec_blocks, rec_raws))
    rec_blocks_bytes = b"".join(rec_blocks)
    rec_section = (
        num(len(rec_blocks))
        + num(len(items))
        + num(len(rec_index))
        + num(len(rec_blocks_bytes))
        + rec_index
    )

    xml = (
        '<Dictionary GeneratedByEngineVersion="%s" RequiredEngineVersion="%s" Encrypted="%s" '
        'Encoding="%s" Format="%s" Title="%s" />\r\n'
        % (version, version, encrypted or "No", encoding, fmt, html.escape(title))
    )
    xml_bytes = xml.encode("utf-16-le") + b"\x00\x00"
    header = struct.pack(">I", len(xml_bytes)) + xml_bytes + struct.pack("<I", zlib.adler32(xml_bytes) & 0xFFFFFFFF)

    pos_kw = len(header)
    pos_info = pos_kw + len(kw)
    pos_kblocks = pos_info + len(key_info)
    pos_rec = pos_kblocks + len(key_blocks_bytes)
    pos_rblocks = pos_rec + len(rec_section)
    kb_offsets, p = [], pos_kblocks
    for b in key_blocks:
        kb_offsets.append((p, len(b)))
        p += len(b)
    rb_offsets, p = [], pos_rblocks
    for b in rec_blocks:
        rb_offsets.append((p, len(b)))
        p += len(b)
    LAYOUT.clear()
    LAYOUT.update(
        header_len=len(xml_bytes),
        kw_header=pos_kw,
        key_info=pos_info,
        key_info_size=len(key_info),
        key_blocks=pos_kblocks,
        key_block_list=kb_offsets,
        rec_header=pos_rec,
        rec_blocks=pos_rblocks,
        rec_block_list=rb_offsets,
    )

    data = header + kw + key_info + key_blocks_bytes + rec_section + rec_blocks_bytes
    if corrupt is not None:
        data = corrupt(data)
    path.write_bytes(data)
    return path
