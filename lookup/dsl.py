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

_MAX_MARKUP_CHARS = 1_200_000  # the converter reads no more of one article (T-02-23)
_MAX_TEXT_CHARS = 250_000  # clean_text trims to its own limit after this
_MAX_VALUES = 5
_MAX_VALUE_CHARS = 80
_MAX_POS_CHARS = 40

# Characters that matter to the converter are swapped for private-use ones while a
# backslash protects them, and swapped back at the end.
_PROTECTED = "[]{}<>\\"
_PROTECT = {c: chr(0xE000 + i) for i, c in enumerate(_PROTECTED)}
_RESTORE = {ord(v): k for k, v in _PROTECT.items()}
_DROP_PRIVATE = {ord(v): None for v in _PROTECT.values()}
_ESCAPE_RE = re.compile(r"\\(.)", re.S)
_TAG_RE = re.compile(r"\[(/?)([A-Za-z!*][^\[\]]{0,100})\]")
_MEDIA_RE = re.compile(r"\[(s|video)\b[^\[\]]{0,100}\][^\[\]]{0,300}\[/\1\]", re.I)
_BRACKETS_RE = re.compile(r"\[[^\[\]]{0,100}\]")


def _protect(m) -> str:
    c = m.group(1)
    return _PROTECT.get(c, c)


def _strip_comments(text: str) -> str:
    """Remove {{...}} comments in one linear pass; an unclosed {{ stays as text."""
    if "{{" not in text:
        return text
    out = []
    i = 0
    while True:
        start = text.find("{{", i)
        if start < 0:
            break
        end = text.find("}}", start + 2)
        if end < 0:
            break
        out.append(text[i:start])
        i = end + 2
    out.append(text[i:])
    return "".join(out)


def _collapse(parts) -> str:
    return " ".join("".join(parts).split())


class _Converter:
    """One pass over the tags of an article; keeps flags, never recurses (T-02-23)."""

    def __init__(self):
        self.lines = []  # (full text, value text, part of speech at line end)
        self.full = []
        self.val = []
        self.t_buf = None
        self.p_buf = None
        self.trn_buf = None
        self.ex = 0
        self.transcription = None
        self.cur_pos = None
        self.group = None
        self.groups = []
        self.trn_seen = 0

    def add(self, part: str) -> None:
        if not part:
            return
        if self.t_buf is not None:
            self.t_buf.append(part)
            return
        self.full.append(part)
        if self.p_buf is not None:
            self.p_buf.append(part)
        elif not self.ex:
            self.val.append(part)
        if self.trn_buf is not None:
            self.trn_buf.append(part)

    def feed(self, seg: str) -> None:
        if "\n" not in seg:
            self.add(seg)
            return
        pieces = seg.split("\n")
        self.add(pieces[0])
        for piece in pieces[1:]:
            self.newline()
            self.add(piece)

    def newline(self) -> None:
        self.end_t()  # transcription and part of speech never span lines
        self.end_p()
        if self.trn_buf is not None:
            self.trn_buf.append(" ")
        full = "".join(self.full).strip()
        if full:
            self.lines.append((full, _collapse(self.val), self.cur_pos))
        self.full = []
        self.val = []

    def end_t(self) -> None:
        if self.t_buf is not None:
            tr = _collapse(self.t_buf)
            self.t_buf = None
            if tr and self.transcription is None:
                self.transcription = tr

    def end_p(self) -> None:
        if self.p_buf is not None:
            pos = _collapse(self.p_buf)[:_MAX_POS_CHARS].strip()
            self.p_buf = None
            if pos:
                self.cur_pos = pos
                self.group = [pos, []]
                self.groups.append(self.group)

    def end_trn(self) -> None:
        if self.trn_buf is not None:
            value = _collapse(self.trn_buf).strip(" ;,")
            self.trn_buf = None
            self.trn_seen += 1
            if value:
                if self.group is None:
                    self.group = [None, []]
                    self.groups.append(self.group)
                if len(self.group[1]) < _MAX_VALUES:
                    self.group[1].append(value[:_MAX_VALUE_CHARS].rstrip())

    def tag(self, closing: bool, name: str) -> None:
        if name == "t":
            if closing:
                self.end_t()
            elif self.t_buf is None:
                self.t_buf = []
        elif name == "p":
            if closing:
                self.end_p()
            elif self.p_buf is None:
                self.p_buf = []
        elif name == "trn":
            if closing:
                self.end_trn()
            elif self.trn_buf is None:
                self.trn_buf = []
        elif name == "ex" or name == "com":
            self.ex = max(0, self.ex - 1) if closing else self.ex + 1
        elif not closing and name[0] == "m" and (len(name) == 1 or name[1:].isdigit()):
            self.newline()
        # every other tag is stripped, its text stays

    def fallback_groups(self) -> list:
        groups = []
        for _full, val, pos in self.lines:
            val = val.strip(" ;,")
            if not any(c.isalnum() for c in val):
                continue
            if not groups or groups[-1][0] != pos:
                groups.append([pos, []])
            if len(groups[-1][1]) < _MAX_VALUES:
                groups[-1][1].append(val[:_MAX_VALUE_CHARS].rstrip())
        return groups


def _restore(text: str) -> str:
    return text.translate(_RESTORE)


def _convert_markup(text: str):
    """Return (transcription, senses, plain_text) for one decoded DSL article body."""
    text = text[:_MAX_MARKUP_CHARS].translate(_DROP_PRIVATE)
    text = _ESCAPE_RE.sub(_protect, text)
    text = _strip_comments(text)
    text = _MEDIA_RE.sub("", text).replace("<<", "").replace(">>", "")
    conv = _Converter()
    pos = 0
    for m in _TAG_RE.finditer(text):
        conv.feed(text[pos:m.start()])
        pos = m.end()
        conv.tag(m.group(1) == "/", m.group(2).split(None, 1)[0].lower())
    conv.feed(text[pos:])
    conv.newline()
    conv.end_trn()
    groups = conv.groups if conv.trn_seen else conv.fallback_groups()
    senses = tuple(
        (_restore(pos) if pos else None, tuple(_restore(v) for v in values))
        for pos, values in groups
        if values
    )
    body = [full for full, _val, _pos in conv.lines]
    transcription = _restore(conv.transcription) if conv.transcription else None
    if transcription:
        body.insert(0, "[" + transcription + "]")
    plain = clean_text(_restore("\n".join(body))[:_MAX_TEXT_CHARS])
    return transcription, senses, plain


def _convert(dict_name: str, headword: str, text: str) -> Article:
    """Decoded article body to an Article of plain text; never raises (D-05, D-06)."""
    try:
        transcription, senses, plain = _convert_markup(text)
        return Article(dict_name, headword, transcription, senses, plain)
    except Exception:
        try:
            plain = clean_text(_BRACKETS_RE.sub("", text[:_MAX_MARKUP_CHARS])[:_MAX_TEXT_CHARS])
        except Exception:
            plain = ""
        return Article(dict_name, headword, None, (), plain)


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
