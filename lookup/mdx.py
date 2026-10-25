"""MDict MDX reader (.mdx), stdlib only.

An MDX file is a header (UTF-16 XML attributes), a keyword section (key info, key
blocks) and a record section (record blocks). Versions 1.2 (4-byte numbers) and 2.0
(8-byte numbers) are read, blocks may be stored plain, with zlib or with LZO (through
lookup.lzo), text may be UTF-8, UTF-16, GBK or Big5, and key info encrypted with the
RIPEMD-128 derived key (Encrypted=2) is decrypted (lookup.ripemd128). Registration
encryption (Encrypted=1) is not supported and is reported, not crashed on (D-07).
The layout is read from the format description (RESEARCH Format Reference 3); no code of
the GPL reference reader is used. MDD resource files are ignored (D-02).

The file is untrusted (D-33): every declared size, count and offset is bounds-checked
before it is used, decompression is capped at the declared size (T-02-26, T-02-27), every
Adler-32 is verified (T-02-28), redirects follow at most MAX_LINK_HOPS hops (T-02-29), and
the index cache is range-checked against the real file before it is believed (D-08).
Record text is exposed as plain text only (D-06). Never prints or logs (V7); DictError
reasons are short codes, never file content. Not thread-safe (one file handle).
"""
import bisect
import html
import itertools
import os
import re
import struct
import zlib
from pathlib import Path

from lookup import lzo, ripemd128
from lookup.dicts import (
    MAX_ARTICLE_BYTES,
    Article,
    DictError,
    clean_text,
    fold_key,
    html_to_text,
    index_cache_load,
    index_cache_save,
)
from lookup.lzo import LzoError

MAX_MDX_BLOCK = 64 << 20
MAX_KEY_INFO = 64 << 20
MAX_HEADER = 1 << 20
MAX_BLOCKS = 2_000_000
MAX_LINK_HOPS = 3
INDEX_TAG = "mdx-1"

MAX_ENTRIES = 8_000_000
MAX_KEY_TOTAL = 512 << 20  # all decompressed key blocks together
_MAX_KEY_CHARS = 500
_MAX_MARKUP_CHARS = 1_200_000
_NAME_CHARS = 200
_LINK = "@@@LINK="

# normalised Encoding attribute -> (python codec, terminator width in bytes)
_ENCODINGS = {
    "": ("utf-8", 1),
    "utf8": ("utf-8", 1),
    "utf16": ("utf-16-le", 2),
    "gbk": ("gb18030", 1),
    "gb2312": ("gb18030", 1),
    "gb18030": ("gb18030", 1),
    "big5": ("big5", 1),
}
# \w is bounded and anchored at a word start so hostile text cannot cause backtracking
_ATTR_RE = re.compile(r"""(?<!\w)(\w{1,64})\s{0,32}=\s{0,32}(?:"([^"]*)"|'([^']*)')""")
_VERSION_RE = re.compile(r"[0-9]{1,3}(?:\.[0-9]{1,3})?")
_ENCRYPTED_RE = re.compile(r"[0-9]{1,3}")


class _BlockError(Exception):
    """One block is unusable; `reason` is a DictError reason code."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


# ------------------------------------------------------------------- blocks


def _decode_block(raw, dec_size: int) -> bytes:
    """Decode one block: 4 bytes type (LE), 4 bytes Adler-32 (BE) of the result, data."""
    if dec_size < 0 or dec_size > MAX_MDX_BLOCK or len(raw) < 8:
        raise _BlockError("corrupt")
    ctype = int.from_bytes(raw[:4], "little")
    stored = int.from_bytes(raw[4:8], "big")
    body = memoryview(raw)[8:]
    if ctype == 0:
        if len(body) != dec_size:
            raise _BlockError("corrupt")
        out = bytes(body)
    elif ctype == 1:
        try:
            out = lzo.decompress(body, dec_size)
        except LzoError:
            raise _BlockError("corrupt") from None
    elif ctype == 2:
        try:
            out = zlib.decompressobj().decompress(body, dec_size + 1)
        except zlib.error:
            raise _BlockError("corrupt") from None
        if len(out) != dec_size:
            raise _BlockError("corrupt")
    else:
        raise _BlockError("unsupported")
    if zlib.adler32(out) & 0xFFFFFFFF != stored:
        raise _BlockError("checksum")
    return out


def _decrypt_key_info(block) -> bytes:
    """Undo the Encrypted=2 scheme on bytes 8.. of the key info block."""
    key = ripemd128.digest(bytes(block[4:8]) + b"\x95\x36\x00\x00")
    klen = len(key)
    prev = 0x36
    out = bytearray(len(block) - 8)
    for i, c in enumerate(block[8:]):
        out[i] = ((c >> 4) | ((c & 0x0F) << 4)) ^ prev ^ (i & 0xFF) ^ key[i % klen]
        prev = c
    return bytes(out)


# ------------------------------------------------------------------- header


class _Header:
    __slots__ = ("version", "ver", "width", "py_enc", "unit", "fmt", "title", "encrypted", "end")


def _read_at(fh, size: int, pos: int, n: int) -> bytes:
    if n < 0 or pos < 0 or pos + n > size:
        raise DictError("corrupt")
    fh.seek(pos)
    data = fh.read(n)
    if len(data) != n:
        raise DictError("corrupt")
    return data


def _read_header(fh, size: int) -> _Header:
    if size < 8:
        raise DictError("corrupt")
    fh.seek(0)
    (length,) = struct.unpack(">I", fh.read(4))
    if length > MAX_HEADER or length % 2 or 8 + length > size:
        raise DictError("corrupt")
    body = fh.read(length)
    stored = fh.read(4)
    if len(body) != length or len(stored) != 4:
        raise DictError("corrupt")
    if zlib.adler32(body) & 0xFFFFFFFF != int.from_bytes(stored, "little"):
        raise DictError("checksum")
    text = body.decode("utf-16-le", "replace")
    attrs = {}
    for m in _ATTR_RE.finditer(text):
        value = m.group(2) if m.group(2) is not None else m.group(3)
        attrs.setdefault(m.group(1), html.unescape(value))

    version = attrs.get("GeneratedByEngineVersion", "").strip()
    if not _VERSION_RE.fullmatch(version):
        raise DictError("corrupt")
    ver = float(version)
    if ver < 1.0 or ver >= 3.0:
        raise DictError("unsupported")

    raw = attrs.get("Encrypted", "").strip().lower()
    if raw in ("", "no"):
        encrypted = 0
    elif raw == "yes":
        encrypted = 1
    elif _ENCRYPTED_RE.fullmatch(raw) and int(raw) <= 3:
        encrypted = int(raw)
    else:
        raise DictError("unsupported")
    if encrypted & 1:
        raise DictError("encrypted_registration")
    if encrypted & 2 and ver < 2.0:
        raise DictError("unsupported")

    enc_key = re.sub(r"[\s_-]", "", attrs.get("Encoding", "")).lower()
    if enc_key not in _ENCODINGS:
        raise DictError("unsupported")

    title = html.unescape(attrs.get("Title", ""))
    if "<" in title:
        title = html_to_text(title)

    h = _Header()
    h.version = version
    h.ver = ver
    h.width = 8 if ver >= 2.0 else 4
    h.py_enc, h.unit = _ENCODINGS[enc_key]
    h.fmt = "Text" if attrs.get("Format", "").strip().lower() == "text" else "Html"
    h.title = clean_text(title)[:_NAME_CHARS]
    h.encrypted = encrypted
    h.end = 8 + length
    return h


# -------------------------------------------------------------------- index


def _parse_key_info(info: bytes, nblocks: int, w: int, v2: bool, unit: int) -> list:
    """Return [(entry_count, comp_size, decomp_size)] for every key block."""
    pos = 0
    n = len(info)
    out = []
    for _ in range(nblocks):
        count = int.from_bytes(info[pos:pos + w], "big")
        pos += w
        for _key in (0, 1):  # first and last key: skipped, only their length matters
            if v2:
                ln = int.from_bytes(info[pos:pos + 2], "big")
                pos += 2 + (ln + 1) * unit
            else:
                if pos >= n:
                    raise DictError("corrupt")
                ln = info[pos]
                pos += 1 + ln * unit
        comp = int.from_bytes(info[pos:pos + w], "big")
        dec = int.from_bytes(info[pos + w:pos + 2 * w], "big")
        pos += 2 * w
        if pos > n:
            raise DictError("corrupt")
        out.append((count, comp, dec))
    return out


def _split_keys(data: bytes, count: int, w: int, unit: int, py_enc: str) -> list:
    """Split one decompressed key block into (record offset, key text) pairs."""
    pos = 0
    n = len(data)
    out = []
    nul = b"\x00" * unit
    for _ in range(count):
        if pos + w > n:
            raise DictError("corrupt")
        off = int.from_bytes(data[pos:pos + w], "big")
        pos += w
        end = data.find(nul, pos)
        if unit == 2:
            while end >= 0 and (end - pos) % 2:
                end = data.find(nul, end + 1)
        if end < 0:
            raise DictError("corrupt")
        out.append((off, data[pos:end].decode(py_enc, "replace")))
        pos = end + unit
    return out


def _build_index(fh, size: int, hdr: _Header) -> dict:
    """Parse key info, key blocks and the record block table into a cacheable payload."""
    w = hdr.width
    v2 = hdr.ver >= 2.0
    pos = hdr.end
    if v2:
        raw = _read_at(fh, size, pos, 44)
        if zlib.adler32(raw[:40]) & 0xFFFFFFFF != int.from_bytes(raw[40:44], "big"):
            raise DictError("checksum")
        nblocks, nentries, ki_dec, ki_size, kb_size = (
            int.from_bytes(raw[i:i + 8], "big") for i in range(0, 40, 8)
        )
        pos += 44
    else:
        raw = _read_at(fh, size, pos, 16)
        nblocks, nentries, ki_size, kb_size = (int.from_bytes(raw[i:i + 4], "big") for i in range(0, 16, 4))
        ki_dec = ki_size
        pos += 16
    if (
        nblocks > MAX_BLOCKS
        or nentries > MAX_ENTRIES
        or ki_size > MAX_KEY_INFO
        or ki_dec > MAX_KEY_INFO
        or kb_size > size
    ):
        raise DictError("corrupt")

    ki_raw = _read_at(fh, size, pos, ki_size)
    if v2:
        encrypted = bool(hdr.encrypted & 2)
        try:
            if encrypted:
                if len(ki_raw) < 8:
                    raise _BlockError("corrupt")
                ki_raw = ki_raw[:8] + _decrypt_key_info(ki_raw)
            info = _decode_block(ki_raw, ki_dec)
        except _BlockError as e:
            # a damaged or wrongly decrypted key info is an integrity failure
            raise DictError("checksum" if encrypted else e.reason) from None
    else:
        info = ki_raw
    blocks = _parse_key_info(info, nblocks, w, v2, hdr.unit)
    if (
        sum(b[0] for b in blocks) != nentries
        or sum(b[1] for b in blocks) != kb_size
        or sum(b[2] for b in blocks) > MAX_KEY_TOTAL
        or any(b[1] < 8 or b[2] > MAX_MDX_BLOCK for b in blocks)
    ):
        raise DictError("corrupt")
    kb_pos = pos + ki_size

    rec_pos = kb_pos + kb_size
    rec_hdr = _read_at(fh, size, rec_pos, 4 * w)
    nb, _ne, index_len, _blocks_len = (int.from_bytes(rec_hdr[i:i + w], "big") for i in range(0, 4 * w, w))
    if nb > MAX_BLOCKS or index_len != 2 * w * nb:
        raise DictError("corrupt")
    idx = _read_at(fh, size, rec_pos + 4 * w, index_len)
    foff = rec_pos + 4 * w + index_len
    rec_blocks = []
    total = 0
    for comp, dec in struct.iter_unpack(">QQ" if w == 8 else ">II", idx):
        if comp < 8 or dec > MAX_MDX_BLOCK:
            raise DictError("corrupt")
        rec_blocks.append([foff, comp, dec])
        foff += comp
        total += dec
    if foff > size:
        raise DictError("corrupt")

    entries = []
    keys = {}
    skipped = 0
    pos = kb_pos
    for count, comp, dec in blocks:
        raw = _read_at(fh, size, pos, comp)
        pos += comp
        try:
            data = _decode_block(raw, dec)
        except _BlockError as e:
            raise DictError(e.reason) from None
        for off, key in _split_keys(data, count, w, hdr.unit, hdr.py_enc):
            if len(key) > _MAX_KEY_CHARS:
                skipped += 1
                continue
            head = key.strip()
            if not head.isprintable():
                head = clean_text(head)
            folded = fold_key(head)
            if not folded or off >= total:
                skipped += 1
                continue
            keys.setdefault(folded, []).append(len(entries))
            entries.append([off, head])
    return {
        "ver": hdr.version,
        "enc": hdr.py_enc,
        "fmt": hdr.fmt,
        "title": hdr.title,
        "count": nentries,
        "skipped": skipped,
        "blocks": rec_blocks,
        "offsets": sorted({e[0] for e in entries}),
        "entries": entries,
        "keys": keys,
    }


def _valid_payload(p, size: int, hdr: _Header) -> bool:
    """True when a cached payload matches the live header and every range lies in the file."""
    try:
        if type(p) is not dict:
            return False
        if (
            p["ver"] != hdr.version
            or p["enc"] != hdr.py_enc
            or p["fmt"] != hdr.fmt
            or p["title"] != hdr.title
        ):
            return False
        count, skipped = p["count"], p["skipped"]
        if type(count) is not int or type(skipped) is not int or count < 0 or skipped < 0:
            return False
        blocks, offsets, entries, keys = p["blocks"], p["offsets"], p["entries"], p["keys"]
        if (
            type(blocks) is not list
            or type(offsets) is not list
            or type(entries) is not list
            or type(keys) is not dict
            or len(blocks) > MAX_BLOCKS
            or not entries
        ):
            return False
        total = 0
        for b in blocks:
            if type(b) is not list or len(b) != 3:
                return False
            foff, comp, dec = b
            if type(foff) is not int or type(comp) is not int or type(dec) is not int:
                return False
            if foff < 0 or comp < 8 or foff + comp > size or not 0 <= dec <= MAX_MDX_BLOCK:
                return False
            total += dec
        prev = -1
        for o in offsets:
            if type(o) is not int or not prev < o < total:
                return False
            prev = o
        known = set(offsets)
        if len(entries) + skipped != count:
            return False
        for e in entries:
            if type(e) is not list or len(e) != 2:
                return False
            off, head = e
            if type(off) is not int or type(head) is not str or off not in known:
                return False
        n = len(entries)
        for k, nums in keys.items():
            if type(k) is not str or type(nums) is not list:
                return False
            for num in nums:
                if type(num) is not int or not 0 <= num < n:
                    return False
        return True
    except (KeyError, TypeError, ValueError):
        return False


# --------------------------------------------------------------- dictionary


def _stem(path: Path) -> str:
    name = path.name
    return name[:-4] if name.lower().endswith(".mdx") else name


class MdxDictionary:
    """An open MDX dictionary. Attributes: name, fmt, path, entry_count, skipped_entries,
    version, encoding. lookup() takes a folded key (fold_key)."""

    fmt = "mdx"

    def __init__(self, path, fh, hdr, payload):
        self.path = path
        self.name = hdr.title or _stem(path)
        self.version = hdr.version
        self.encoding = hdr.py_enc
        self.entry_count = len(payload["entries"])
        self.skipped_entries = payload["skipped"]
        self._fh = fh
        self._unit = hdr.unit
        self._html = hdr.fmt == "Html"
        self._blocks = payload["blocks"]
        self._starts = [0]
        self._starts.extend(itertools.accumulate(b[2] for b in self._blocks))
        self._total = self._starts.pop()
        self._offsets = payload["offsets"]
        self._entries = payload["entries"]
        self._keys = payload["keys"]
        self._last = (-1, b"")

    def has(self, key: str) -> bool:
        return key in self._keys

    def lookup(self, key: str) -> list:
        out = []
        for n in self._keys.get(key, ()):
            art = self._article(n)
            if art is not None:
                out.append(art)
        return out

    # -- records

    def _article(self, n: int):
        try:
            text = self._resolve(n, 0, set())
        except (OSError, ValueError, zlib.error, struct.error, IndexError, MemoryError, RecursionError):
            return None
        if not text:
            return None
        return Article(self.name, self._entries[n][1], None, (), text)

    def _resolve(self, n: int, hops: int, seen: set):
        s = self._record_str(n)
        if s is None:
            return None
        if not s.startswith(_LINK):
            return self._to_text(s) or None
        if hops >= MAX_LINK_HOPS or n in seen:
            return None
        seen.add(n)
        target = fold_key(s[len(_LINK):].strip().split("\n", 1)[0])
        for m in self._keys.get(target, ()):
            text = self._resolve(m, hops + 1, seen)
            if text:
                return text
        return None

    def _to_text(self, s: str) -> str:
        s = s[:_MAX_MARKUP_CHARS]
        return html_to_text(s) if self._html else clean_text(s)

    def _record_str(self, n: int):
        offset = self._entries[n][0]
        i = bisect.bisect_right(self._offsets, offset)
        end = self._offsets[i] if i < len(self._offsets) else self._total
        need = end - offset
        if need <= 0 or need > MAX_ARTICLE_BYTES:
            return None
        starts = self._starts
        b = bisect.bisect_right(starts, offset) - 1
        pos = offset
        chunks = []
        while need > 0:
            if b < 0 or b >= len(self._blocks):
                return None
            data = self._block(b)
            if data is None:
                return None
            local = pos - starts[b]
            take = data[local:local + need]
            if take:
                chunks.append(take)
                pos += len(take)
                need -= len(take)
            b += 1
        rec = b"".join(chunks)
        unit = self._unit
        nul = b"\x00" * unit
        while len(rec) >= unit and len(rec) % unit == 0 and rec.endswith(nul):
            rec = rec[:-unit]
        return rec.decode(self.encoding, "replace")

    def _block(self, b: int):
        if self._last[0] == b:
            return self._last[1]
        fh = self._fh
        if fh is None:
            return None
        foff, comp, dec = self._blocks[b]
        try:
            fh.seek(foff)
            raw = fh.read(comp)
            if len(raw) != comp:
                return None
            data = _decode_block(raw, dec)
        except (OSError, ValueError, _BlockError):
            return None
        self._last = (b, data)
        return data

    def close(self) -> None:
        fh, self._fh = self._fh, None
        self._last = (-1, b"")
        if fh is not None:
            try:
                fh.close()
            except OSError:
                pass


def open_mdx(path) -> MdxDictionary:
    """Open the MDX dictionary at `path`; raise DictError with a reason code."""
    path = Path(path)
    try:
        fh = open(path, "rb")
    except OSError:
        raise DictError("unreadable") from None
    try:
        size = os.fstat(fh.fileno()).st_size
        if size == 0:
            raise DictError("empty")
        hdr = _read_header(fh, size)
        payload = index_cache_load(path, INDEX_TAG)
        if payload is not None and not _valid_payload(payload, size, hdr):
            payload = None
        if payload is None:
            payload = _build_index(fh, size, hdr)
            if not payload["entries"]:
                raise DictError("empty")
            index_cache_save(path, INDEX_TAG, payload)
        return MdxDictionary(path, fh, hdr, payload)
    except DictError:
        fh.close()
        raise
    except MemoryError:
        fh.close()
        raise DictError("too_large") from None
    except (OSError, struct.error, zlib.error, LzoError, ValueError, OverflowError, IndexError):
        fh.close()
        raise DictError("corrupt") from None
    except BaseException:
        fh.close()
        raise
