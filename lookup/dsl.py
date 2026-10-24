"""Lingvo DSL reader (.dsl, .dsl.dz), stdlib only.

A DSL file is text in UTF-16 (LE or BE, with or without a BOM) or UTF-8: a `#KEY "value"`
header, then articles made of unindented headword lines and indented body lines.
The headword index is one sequential scan over the raw bytes, kept in memory as
`folded key -> entries` of (byte offset, size, headword) and cached as validated JSON
(D-08); article bodies are read lazily by offset, from an mmap or from a dictzip file.

The file is untrusted (D-33): a size cap, an article size cap (skipped and counted), a hard
cap on `{}` variants per headword (T-02-22), a cache that is range-checked against the real
source before it is believed (T-02-25), and markup conversion without recursion (T-02-23).
Article text is exposed as plain text only (D-06). Never prints or logs (V7); DictError
reasons are short codes, never file content. Not thread-safe (dictzip uses one handle).
"""
import mmap
import os
import re
from pathlib import Path

from lookup.dictzip import DictzipError, DictzipFile
from lookup.dicts import (
    MAX_ARTICLE_BYTES,
    Article,
    DictError,
    clean_text,
    fold_key,
    index_cache_load,
    index_cache_save,
)

MAX_DSL_BYTES = 512 << 20
MAX_VARIANTS = 32
INDEX_TAG = "dsl-1"

_NEWLINE = {"utf-8": b"\n", "utf-16-le": b"\n\x00", "utf-16-be": b"\x00\n"}
_HEADER_RE = re.compile(r'#([A-Za-z_]+)[ \t]*"((?:\\.|[^"\\])*)"')
_UNESCAPE_RE = re.compile(r"\\(.)", re.S)
_NAME_CHARS = 200


# ---------------------------------------------------------------- headwords


def expand_headword(text: str) -> list:
    """Spellings of one headword line: `{}` parts are optional, a backslash escapes.

    The spelling without any optional part comes first; at most MAX_VARIANTS results,
    stripped, non-empty and without duplicates (D-08, T-02-22).
    """
    parts = []  # (text, optional)
    literal = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == "\\":
            literal.append(text[i + 1] if i + 1 < n else "\\")
            i += 2
        elif c == "{":
            j = i + 1
            optional = []
            while j < n and text[j] != "}":
                if text[j] == "\\" and j + 1 < n:
                    j += 1
                optional.append(text[j])
                j += 1
            if j >= n:  # unclosed: the brace is an ordinary character
                literal.append(c)
                i += 1
                continue
            if literal:
                parts.append(("".join(literal), False))
                literal = []
            parts.append(("".join(optional), True))
            i = j + 1
        else:
            literal.append(c)
            i += 1
    if literal:
        parts.append(("".join(literal), False))

    variants = [""]
    for piece, optional in parts:
        if optional:
            variants = (variants + [v + piece for v in variants])[:MAX_VARIANTS]
        else:
            variants = [v + piece for v in variants]
    out = []
    for v in variants:
        v = v.strip()
        if v and v not in out:
            out.append(v)
    return out


# ------------------------------------------------------------------ scanning


def _detect(head: bytes):
    """Return (encoding, BOM length) from the first bytes of the file."""
    if head[:2] == b"\xff\xfe":
        return "utf-16-le", 2
    if head[:2] == b"\xfe\xff":
        return "utf-16-be", 2
    if head[:3] == b"\xef\xbb\xbf":
        return "utf-8", 3
    if head[:2] == b"#\x00":
        return "utf-16-le", 0
    if head[:2] == b"\x00#":
        return "utf-16-be", 0
    return "utf-8", 0


def _scan(data, start: int, enc: str) -> dict:
    """One pass over the raw bytes; return the index payload (the shape that is cached)."""
    nl = _NEWLINE[enc]
    wide = enc != "utf-8"
    n = len(data)
    limit = MAX_ARTICLE_BYTES
    header = {}
    entries = []
    keys = {}
    stats = [0, 0]  # registered articles, skipped articles

    def flush(heads, b0, b1):
        size = b1 - b0
        if size > limit:
            stats[1] += 1
            return
        seen = set()
        registered = False
        for h in heads:
            variants = expand_headword(h)
            if not variants:
                continue
            num = len(entries)
            used = False
            for v in variants:
                k = fold_key(v)
                if k and k not in seen:
                    seen.add(k)
                    keys.setdefault(k, []).append(num)
                    used = True
            if used:
                entries.append([b0, size, variants[0]])
                registered = True
        if registered:
            stats[0] += 1

    in_header = True
    heads = []
    b0 = b1 = None
    pos = start
    while pos < n:
        i = data.find(nl, pos)
        if wide:
            while i >= 0 and (i - start) & 1:  # a 0x0A byte inside a character, not a newline
                i = data.find(nl, i + 1)
        if i < 0:
            end = n - ((n - start) & 1) if wide else n
            nxt = n
        else:
            end = i
            nxt = i + len(nl)
        line = data[pos:end].decode(enc, "replace").rstrip("\r")
        if not line.strip():
            pass
        elif line[0] in " \t":
            if heads:
                if b0 is None:
                    b0 = pos
                b1 = end
        elif in_header and line[0] == "#":
            m = _HEADER_RE.match(line)
            if m:
                header.setdefault(m.group(1).upper(), _UNESCAPE_RE.sub(r"\1", m.group(2)))
        else:
            in_header = False
            if b0 is not None:
                flush(heads, b0, b1)
                heads = []
                b0 = b1 = None
            heads.append(line.strip())
        pos = nxt
    if b0 is not None:
        flush(heads, b0, b1)
    return {
        "enc": enc,
        "bom": start,
        "name": header.get("NAME"),
        "il": header.get("INDEX_LANGUAGE"),
        "cl": header.get("CONTENTS_LANGUAGE"),
        "count": stats[0],
        "skipped": stats[1],
        "entries": entries,
        "keys": keys,
    }


def _valid_payload(p, data_len: int) -> bool:
    """True when a cached payload is well formed and every range lies inside the source."""
    try:
        if type(p) is not dict or p["enc"] not in _NEWLINE:
            return False
        if type(p["bom"]) is not int or not 0 <= p["bom"] <= 3:
            return False
        for field in ("name", "il", "cl"):
            if p[field] is not None and type(p[field]) is not str:
                return False
        for field in ("count", "skipped"):
            if type(p[field]) is not int or p[field] < 0:
                return False
        entries, keys = p["entries"], p["keys"]
        if type(entries) is not list or type(keys) is not dict or not entries or p["count"] == 0:
            return False
        for e in entries:
            if type(e) is not list or len(e) != 3:
                return False
            off, size, head = e
            if (
                type(off) is not int
                or type(size) is not int
                or type(head) is not str
                or off < 0
                or not 0 < size <= MAX_ARTICLE_BYTES
                or off + size > data_len
            ):
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


# ------------------------------------------------------------ article markup


def _convert(dict_name: str, headword: str, text: str) -> Article:
    """Minimal converter: the decoded lines as text (replaced by the markup converter)."""
    lines = [line.strip() for line in text.replace("\r", "").split("\n")]
    return Article(dict_name, headword, None, (), clean_text("\n".join(lines)))


# ---------------------------------------------------------------- dictionary


def _stem(path: Path) -> str:
    name = path.name
    if name.lower().endswith(".dz"):
        name = name[:-3]
    if name.lower().endswith(".dsl"):
        name = name[:-4]
    return name


class DslDictionary:
    """An open DSL dictionary. Attributes: name, fmt, path, entry_count, skipped_entries,
    index_language, contents_language."""

    fmt = "dsl"

    def __init__(self, path, payload, mm, dz):
        self.path = path
        self.name = clean_text(payload["name"] or "")[:_NAME_CHARS] or _stem(path)
        self.index_language = clean_text(payload["il"] or "")[:80] or None
        self.contents_language = clean_text(payload["cl"] or "")[:80] or None
        self.entry_count = payload["count"]
        self.skipped_entries = payload["skipped"]
        self._enc = payload["enc"]
        self._entries = payload["entries"]
        self._keys = payload["keys"]
        self._mm = mm
        self._dz = dz

    def has(self, key: str) -> bool:
        return key in self._keys

    def lookup(self, key: str) -> list:
        out = []
        for num in self._keys.get(key, ()):
            art = self._article(num)
            if art is not None:
                out.append(art)
        return out

    def _article(self, num: int):
        offset, size, headword = self._entries[num]
        raw = self._read(offset, size)
        if raw is None:
            return None
        return _convert(self.name, headword, raw.decode(self._enc, "replace"))

    def _read(self, offset: int, size: int):
        try:
            if self._mm is not None:
                raw = self._mm[offset:offset + size]
            elif self._dz is not None:
                raw = self._dz.read(offset, size, max_out=MAX_ARTICLE_BYTES)
            else:
                return None
        except (OSError, ValueError, DictzipError):
            return None
        return raw if len(raw) == size else None

    def close(self) -> None:
        mm, dz = self._mm, self._dz
        self._mm = self._dz = None
        _close_quietly(mm, dz)


def _close_quietly(*handles) -> None:
    for h in handles:
        if h is not None:
            try:
                h.close()
            except (OSError, ValueError, BufferError):
                pass


def _open_source(path: Path):
    """Return (mmap or None, DictzipFile or None, size); raise DictError."""
    if path.name.lower().endswith(".dz"):
        try:
            dz = DictzipFile(path)
        except DictzipError:
            raise DictError("corrupt") from None
        except OSError:
            raise DictError("unreadable") from None
        return None, dz, dz.size
    try:
        with open(path, "rb") as fh:
            size = os.fstat(fh.fileno()).st_size
            if size == 0 or size > MAX_DSL_BYTES:
                return None, None, size
            mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
    except (OSError, ValueError):
        raise DictError("unreadable") from None
    return mm, None, size


def open_dsl(path) -> DslDictionary:
    """Open the DSL dictionary at `path`; raise DictError with a reason code."""
    path = Path(path)
    mm, dz, size = _open_source(path)
    try:
        if size > MAX_DSL_BYTES:
            raise DictError("too_large")
        if size == 0:
            raise DictError("empty")
        payload = index_cache_load(path, INDEX_TAG)
        if payload is not None and not _valid_payload(payload, size):
            payload = None
        if payload is None:
            data = dz.read_all(MAX_DSL_BYTES) if dz is not None else mm
            enc, bom = _detect(bytes(data[:4]))
            payload = _scan(data, bom, enc)
            if not payload["entries"]:
                raise DictError("empty")
            index_cache_save(path, INDEX_TAG, payload)
        return DslDictionary(path, payload, mm, dz)
    except DictError:
        _close_quietly(mm, dz)
        raise
    except MemoryError:
        _close_quietly(mm, dz)
        raise DictError("too_large") from None
    except (OSError, ValueError, DictzipError):
        _close_quietly(mm, dz)
        raise DictError("corrupt") from None
    except BaseException:
        _close_quietly(mm, dz)
        raise
