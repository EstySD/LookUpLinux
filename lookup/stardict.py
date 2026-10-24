"""StarDict reader (the format of the default Mueller 7 dictionary), stdlib only.

A dictionary is X.ifo plus X.idx or X.idx.gz, X.dict or X.dict.dz and an optional
X.syn. All of them are untrusted (D-33): the .ifo counts are ignored, every index
entry is validated against the real data length and MAX_ARTICLE_BYTES, an invalid
entry is skipped and counted in `skipped_entries` instead of failing the
dictionary, and index files are read through hard size bounds. Article text is
exposed as plain text only (D-06).

Dictionary contract shared with the other readers: name, fmt, path, entry_count,
skipped_entries, lookup(key), has(key), close(); keys are already `fold_key`ed.
Never prints or logs (V7); DictError reasons are short codes, never file content.
Not thread-safe: one open data handle with seeks.
"""
import gzip
import re
import struct
import zlib
from pathlib import Path
from typing import NamedTuple

from lookup.dictzip import DictzipError, DictzipFile
from lookup.dicts import (
    MAX_ARTICLE_BYTES,
    Article,
    DictError,
    clean_text,
    fold_key,
    html_to_text,
)

MAX_IDX_BYTES = 256 << 20
MAX_IFO_BYTES = 64 << 10

_MAGIC = "StarDict's dict ifo file"
_BIG_ENDIAN_U32 = struct.Struct(">I")
_TR_RE = re.compile(r"<tr\b[^>]{0,100}>(.{0,200}?)</tr\s*>", re.S | re.I)


# ------------------------------------------------------------------- .ifo / files


def _read_ifo(path: Path) -> dict:
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_IFO_BYTES + 1)
    except FileNotFoundError:
        raise DictError("missing_files") from None
    except OSError:
        raise DictError("unreadable") from None
    if len(raw) > MAX_IFO_BYTES:
        raise DictError("corrupt")
    text = raw.decode("utf-8-sig", "replace").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    if lines[0].strip() != _MAGIC:
        raise DictError("corrupt")
    fields = {}
    for line in lines[1:]:
        key, sep, value = line.partition("=")
        if sep:
            fields[key.strip().lower()] = value.strip()
    return fields


def _offset_bytes(fields: dict) -> int:
    raw = fields.get("idxoffsetbits")
    if raw is None:
        return 4
    try:
        bits = int(raw)
    except ValueError:
        raise DictError("unsupported") from None
    if bits == 32:
        return 4
    if bits == 64 and fields.get("version") == "3.0.0":
        return 8
    raise DictError("unsupported")


def _read_capped(path: Path, gz: bool) -> bytes:
    """Whole index file, refusing more than MAX_IDX_BYTES (also after gunzip)."""
    limit = MAX_IDX_BYTES
    try:
        with (gzip.open(path, "rb") if gz else open(path, "rb")) as fh:
            data = fh.read(limit + 1)
    except FileNotFoundError:
        raise DictError("missing_files") from None
    except (OSError, EOFError, zlib.error):
        raise DictError("corrupt") from None
    if len(data) > limit:
        raise DictError("too_large")
    return data


def _read_syn(path: Path) -> bytes:
    try:
        with open(path, "rb") as fh:
            return fh.read(MAX_IDX_BYTES)
    except OSError:
        return b""


def _parse_idx(idx: bytes, data_len: int, offset_bytes: int):
    """Return (entries, skipped); entries has one slot per index record, None when invalid."""
    entries = []
    skipped = 0
    offset_struct = struct.Struct(">I" if offset_bytes == 4 else ">Q")
    pos = 0
    n = len(idx)
    while pos < n:
        j = idx.find(b"\x00", pos)
        if j < 0 or j + 1 + offset_bytes + 4 > n:
            skipped += 1  # index ends inside an entry
            break
        word = idx[pos:j]
        offset = offset_struct.unpack_from(idx, j + 1)[0]
        size = _BIG_ENDIAN_U32.unpack_from(idx, j + 1 + offset_bytes)[0]
        pos = j + 1 + offset_bytes + 4
        if not word or size == 0 or size > MAX_ARTICLE_BYTES or offset + size > data_len:
            entries.append(None)
            skipped += 1
            continue
        entries.append((word.decode("utf-8", "replace"), offset, size))
    return entries, skipped


# ---------------------------------------------------------------- Mueller articles

_SCAN_CHARS = 20000  # parse_mueller looks at no more than this (T-02-20)
_POINTER_CHARS = 600  # and the "от X" pointer test at no more than this
_MAX_VALUES = 5
_MAX_VALUE_CHARS = 80
_MAX_SENSES = 64

_TRANS_RE = re.compile(r"\s*\[([^\[\]]{1,200})\]")
_POS_NAMES = (
    "n|a|v|adv|pl|p-p|pres-p|p|attr|comp|sup|pred|predic|prep|conj|pron|num|interj|int|art|aux"
)
_TOKEN_RE = re.compile(
    r"(?<![\w(])_(?P<pos>" + _POS_NAMES + r")\."
    r"|(?P<brk>(?<!\w)_(?:I{1,3}|IV|VI{0,3}|IX|X)(?![\w.])(?:\s*\[[^\[\]]{0,200}\])?)"
)
_SPLIT_RE = re.compile(r"(?<!\w)(?:\d{1,2}|[^\W\d_])>|(?<![\w.,])\d{1,2}\.(?=\s|$)")
_PAREN_POINTER_RE = re.compile(r"\(\s*_[\w-]{1,12}\.\s+от\s+[^()]{0,60}\)")
_POINTER_VALUE_RE = re.compile(r"от\s+[A-Za-z'’ \-]{1,60}(?:\s+\d{1,2})?\s*[;.]?")
_PAREN_ONLY_RE = re.compile(r"\([^()]*\)")
_POINTER_RE = re.compile(
    r"\s*(?:\d{1,2}\.\s*)?_[\w-]{1,12}\.\s+от\s+"
    r"([A-Za-z][A-Za-z'’-]*(?:\s+[A-Za-z][A-Za-z'’-]*){0,2})"
)
_HOMOGRAPH_NUMBER_RE = re.compile(r"\d{1,2}")


class MuellerParts(NamedTuple):
    transcription: str | None
    senses: tuple
    form_of: str | None
    pointer_only: bool


def _values(segment: str) -> tuple:
    values = []
    for piece in _SPLIT_RE.split(_PAREN_POINTER_RE.sub(" ", segment)):
        v = " ".join(piece.split()).strip(" ;,")
        if not v or _POINTER_VALUE_RE.fullmatch(v) or _PAREN_ONLY_RE.fullmatch(v):
            continue
        values.append(v[:_MAX_VALUE_CHARS].rstrip())
        if len(values) == _MAX_VALUES:
            break
    return tuple(values)


def parse_mueller(text: str) -> MuellerParts:
    """Best-effort parse of a Mueller 7 style article; the full text always stays in Article.text.

    Pure and bounded: only the first _SCAN_CHARS characters are read, the pointer
    test sees _POINTER_CHARS, and no pattern nests unbounded quantifiers (T-02-20).
    """
    whole = len(text) <= _SCAN_CHARS
    text = text[:_SCAN_CHARS]

    transcription = None
    start = 0
    m = _TRANS_RE.match(text)
    if m:
        transcription = m.group(1).strip() or None
        start = m.end()

    senses = []
    matches = list(_TOKEN_RE.finditer(text))
    for i, tok in enumerate(matches):
        pos = tok.group("pos")
        if pos is None:  # homograph marker: only ends the previous segment
            continue
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        values = _values(text[tok.end():end])
        if values:
            senses.append((pos, values))
            if len(senses) == _MAX_SENSES:
                break

    form_of = None
    pointer_only = False
    p = _POINTER_RE.match(text, start, min(len(text), start + _POINTER_CHARS))
    if p:
        form_of = p.group(1)
        tail = text[p.end():].strip()
        number = _HOMOGRAPH_NUMBER_RE.match(tail)
        if number:
            tail = tail[number.end():]
        pointer_only = whole and all(c.isspace() or c in ";." for c in tail)
    return MuellerParts(transcription, tuple(senses), form_of, pointer_only)


# ------------------------------------------------------------------ field decoding


class _Malformed(Exception):
    pass


def _split_fields(raw: bytes, seq):
    """Split an article into (type, bytes) fields; raise _Malformed on a broken layout."""
    fields = []
    pos = 0
    n = len(raw)

    def take(t: str) -> bytes:
        nonlocal pos
        if t.isupper():
            if pos + 4 > n:
                raise _Malformed
            (length,) = _BIG_ENDIAN_U32.unpack_from(raw, pos)
            pos += 4
            if pos + length > n:
                raise _Malformed
            chunk = raw[pos:pos + length]
            pos += length
            return chunk
        end = raw.find(b"\x00", pos)
        if end < 0:
            raise _Malformed
        chunk = raw[pos:end]
        pos = end + 1
        return chunk

    if seq:
        for i, t in enumerate(seq):
            if i == len(seq) - 1:
                fields.append((t, raw[pos:]))
            else:
                fields.append((t, take(t)))
    else:
        while pos < n:
            t = chr(raw[pos])
            pos += 1
            fields.append((t, take(t)))
    return fields


def _decode_entry(dict_name: str, headword: str, raw: bytes, seq) -> Article:
    try:
        fields = _split_fields(raw, seq)
    except _Malformed:
        return Article(dict_name, headword, None, (), clean_text(raw.decode("utf-8", "replace")))
    transcription = None
    xdxf_tr = None
    mueller = None
    texts = []
    for t, chunk in fields:
        s = chunk.decode("utf-8", "replace")
        if t in ("m", "l", "w"):
            piece = clean_text(s)
            texts.append(piece)
            if t == "m" and mueller is None:
                mueller = parse_mueller(piece)
        elif t in ("t", "y"):
            if transcription is None:
                transcription = " ".join(clean_text(s).split()) or None
        elif t in ("x", "h", "g", "k"):
            texts.append(html_to_text(s))
            if t == "x" and xdxf_tr is None:
                m = _TR_RE.search(s)
                if m:
                    xdxf_tr = " ".join(html_to_text(m.group(1)).split()) or None
        # r, W, P and unknown types carry no text (D-05)
    text = clean_text("\n".join(x for x in texts if x))
    if transcription is None:
        transcription = xdxf_tr
    if mueller is None:
        return Article(dict_name, headword, transcription, (), text)
    if transcription is None:
        transcription = mueller.transcription
    only = len(fields) == 1 and fields[0][0] == "m" and mueller.pointer_only
    return Article(dict_name, headword, transcription, mueller.senses, text, None, mueller.form_of, only)


# -------------------------------------------------------------------- dictionary


class StarDictDictionary:
    """An open StarDict dictionary. Attributes: name, fmt, path, entry_count, skipped_entries."""

    fmt = "stardict"

    def __init__(self, name, path, keys, entries, entry_count, skipped, seq, plain, dz):
        self.name = name
        self.path = path
        self.entry_count = entry_count
        self.skipped_entries = skipped
        self._keys = keys
        self._entries = entries
        self._seq = seq
        self._plain = plain
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
        word, offset, size = self._entries[num]
        raw = self._read(offset, size)
        if raw is None:
            return None
        return _decode_entry(self.name, word, raw, self._seq)

    def _read(self, offset: int, size: int):
        try:
            if self._plain is not None:
                self._plain.seek(offset)
                raw = self._plain.read(size)
            elif self._dz is not None:
                raw = self._dz.read(offset, size, max_out=MAX_ARTICLE_BYTES)
            else:
                return None
        except (OSError, ValueError, DictzipError):
            return None
        return raw if len(raw) == size else None

    def close(self) -> None:
        plain, dz = self._plain, self._dz
        self._plain = self._dz = None
        if plain is not None:
            plain.close()
        if dz is not None:
            dz.close()


def open_stardict(ifo_path) -> StarDictDictionary:
    """Open the dictionary described by `ifo_path`; raise DictError with a reason code."""
    ifo = Path(ifo_path)
    fields = _read_ifo(ifo)
    offset_bytes = _offset_bytes(fields)
    base = ifo.with_suffix("")

    def sibling(suffix: str) -> Path:
        return base.with_name(base.name + suffix)

    if sibling(".idx").is_file():
        idx_path, idx_gz = sibling(".idx"), False
    elif sibling(".idx.gz").is_file():
        idx_path, idx_gz = sibling(".idx.gz"), True
    else:
        raise DictError("missing_files")
    plain_path, dz_path = sibling(".dict"), sibling(".dict.dz")
    if not plain_path.is_file() and not dz_path.is_file():
        raise DictError("missing_files")

    plain = dz = None
    try:
        if plain_path.is_file():
            plain = open(plain_path, "rb")
            data_len = plain.seek(0, 2)
        else:
            dz = DictzipFile(dz_path)
            data_len = dz.size
        entries, skipped = _parse_idx(_read_capped(idx_path, idx_gz), data_len, offset_bytes)
        keys: dict = {}
        for num, entry in enumerate(entries):
            if entry is None:
                continue
            key = fold_key(entry[0])
            if not key:
                entries[num] = None
                skipped += 1
                continue
            keys.setdefault(key, []).append(num)
        entry_count = sum(1 for e in entries if e is not None)
        syn_path = sibling(".syn")
        if syn_path.is_file():
            _add_synonyms(keys, entries, _read_syn(syn_path))
    except DictzipError:
        _close_quietly(plain, dz)
        raise DictError("corrupt") from None
    except OSError:
        _close_quietly(plain, dz)
        raise DictError("unreadable") from None
    except BaseException:
        _close_quietly(plain, dz)
        raise
    name = clean_text(fields.get("bookname", ""))[:200] or base.name
    return StarDictDictionary(name, ifo, keys, entries, entry_count, skipped, fields.get("sametypesequence") or None, plain, dz)


def _add_synonyms(keys: dict, entries: list, syn: bytes) -> None:
    pos = 0
    n = len(syn)
    while pos < n:
        j = syn.find(b"\x00", pos)
        if j < 0 or j + 5 > n:
            return
        word = syn[pos:j].decode("utf-8", "replace")
        (num,) = _BIG_ENDIAN_U32.unpack_from(syn, j + 1)
        pos = j + 5
        if num >= len(entries) or entries[num] is None:
            continue
        key = fold_key(word)
        if key:
            nums = keys.setdefault(key, [])
            if num not in nums:
                nums.append(num)
                nums.sort()


def _close_quietly(*handles) -> None:
    for h in handles:
        if h is not None:
            try:
                h.close()
            except OSError:
                pass
