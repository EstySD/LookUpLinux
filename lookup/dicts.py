"""Dictionary layer foundation: the Article model, plain-text helpers, index cache.

Dictionary text comes from third-party files and is shown in a popup, so it is
exposed as plain text only (D-06): control and format characters removed,
markup flattened. Nothing here prints or logs (V7), and no error message
carries file content.

Later plans append dictionary discovery, ordering and search to this module.
"""
import hashlib
import html.parser
import json
import os
import re
import tempfile
import unicodedata as ud
from dataclasses import dataclass
from pathlib import Path

from lookup import config
from lookup.normalize import _APOS, _DASH

MAX_ARTICLE_BYTES = 16 << 20
MAX_ARTICLE_CHARS = 200_000
MAX_INDEX_CACHE_BYTES = 256 << 20

_CACHE_FORMAT = 1
_TAG_RE = re.compile(r"[A-Za-z0-9._-]{1,32}\Z")


class DictError(RuntimeError):
    """A dictionary file is unusable; `reason` is a short code, never file content."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class Article:
    """One dictionary entry as the UI and the orchestrator see it.

    senses is a tuple of (pos_or_None, tuple_of_value_strings). Fields a
    dictionary lacks stay None or empty, never invented (D-28). form_of and
    pointer_only are set by readers ("от X" pointers); lemma_of only by the
    search layer.
    """

    dict_name: str
    headword: str
    transcription: str | None
    senses: tuple
    text: str
    lemma_of: str | None = None
    form_of: str | None = None
    pointer_only: bool = False


@dataclass(frozen=True)
class SearchResult:
    """What the search layer hands to the translate orchestrator (D-05, D-12)."""

    articles: tuple = ()
    lemma: str | None = None

    def __bool__(self) -> bool:
        return bool(self.articles)


# ---------------------------------------------------------------- text helpers


def fold_key(text: str) -> str:
    """Case, apostrophe, dash, whitespace and Unicode-form insensitive key."""
    t = ud.normalize("NFC", text).translate(_APOS).translate(_DASH)
    t = ud.normalize("NFC", t.casefold())
    return " ".join(t.split())


_SPACES_RE = re.compile(r" {2,}")
_NEWLINES_RE = re.compile(r"\n{3,}")


def _keep_char(c: str) -> bool:
    if c in "\n\t":
        return True
    return ud.category(c) not in ("Cc", "Cf", "Cs")


def clean_text(text: str) -> str:
    """Reduce text to safe, tidy plain text (D-06, T-02-10)."""
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = t.replace(" ", "\n").replace(" ", "\n")
    t = "".join(c if ud.category(c) != "Zs" else " " for c in t if _keep_char(c))
    t = _SPACES_RE.sub(" ", t)
    t = "\n".join(line.strip() for line in t.split("\n"))
    t = _NEWLINES_RE.sub("\n\n", t).strip()
    if len(t) > MAX_ARTICLE_CHARS:
        cut = t[:MAX_ARTICLE_CHARS]
        nl = cut.rfind("\n")
        t = (cut[:nl] if nl > MAX_ARTICLE_CHARS // 2 else cut).strip()
    return t


_BLOCK_TAGS = frozenset(
    "br p div li tr table ul ol h1 h2 h3 h4 h5 h6 dt dd hr".split()
)
_SKIP_TAGS = frozenset(("script", "style"))
_WS_RE = re.compile(r"\s+")
_TAG_STRIP_RE = re.compile(r"<[^>]*>?")


class _TextExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip: str | None = None

    def handle_starttag(self, tag, attrs):
        if self._skip is None:
            if tag in _SKIP_TAGS:
                self._skip = tag
            elif tag in _BLOCK_TAGS:
                self.parts.append("\n")

    def handle_endtag(self, tag):
        if self._skip is not None:
            if tag == self._skip:
                self._skip = None
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._skip is None:
            self.parts.append(_WS_RE.sub(" ", data))


def html_to_text(markup: str) -> str:
    """Flatten HTML, XDXF or Pango-style markup to plain text. Never raises."""
    try:
        parser = _TextExtractor()
        parser.feed(markup)
        parser.close()
        return clean_text("".join(parser.parts))
    except Exception:
        try:
            return clean_text(_TAG_STRIP_RE.sub(" ", markup))
        except Exception:
            return ""


# ----------------------------------------------------------------- index cache


def index_cache_path(src, tag: str) -> Path:
    """Cache file for the index built from `src` (D-08). Creates nothing."""
    if not _TAG_RE.match(tag):
        raise ValueError("bad cache tag")
    digest = hashlib.sha256(os.path.abspath(src).encode("utf-8", "surrogatepass")).hexdigest()
    return config.cache_dir() / "index" / (digest[:32] + "-" + tag + ".json")


def _is_int(value, expected: int) -> bool:
    return type(value) is int and value == expected


def index_cache_save(src, tag: str, payload) -> bool:
    """Store `payload` (JSON-able) for `src`; False on any problem, never raises."""
    tmp_name = None
    try:
        st = os.stat(src)
        target = index_cache_path(src, tag)
        blob = json.dumps(
            {
                "format": _CACHE_FORMAT,
                "tag": tag,
                "path": os.path.abspath(src),
                "size": st.st_size,
                "mtime_ns": st.st_mtime_ns,
                "data": payload,
            },
            ensure_ascii=False,
        ).encode("utf-8", "surrogatepass")
        if len(blob) > MAX_INDEX_CACHE_BYTES:
            return False
        directory = target.parent
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name == "posix":
            os.chmod(directory, 0o700)
        fd, tmp_name = tempfile.mkstemp(dir=directory, prefix=".tmp-", suffix=".json")
        with os.fdopen(fd, "wb") as fh:  # mkstemp creates the file with mode 0600
            fh.write(blob)
        os.replace(tmp_name, target)
        tmp_name = None
        return True
    except (OSError, TypeError, ValueError, RecursionError):
        return False
    finally:
        if tmp_name is not None:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def index_cache_load(src, tag: str):
    """Return the cached payload for `src`, or None on any mismatch (a miss)."""
    try:
        target = index_cache_path(src, tag)
        st = os.stat(src)
        with open(target, "rb") as fh:
            raw = fh.read(MAX_INDEX_CACHE_BYTES + 1)
        if len(raw) > MAX_INDEX_CACHE_BYTES:
            return None
        wrapper = json.loads(raw.decode("utf-8", "surrogatepass"))
    except (OSError, ValueError, RecursionError):
        return None
    if not isinstance(wrapper, dict) or "data" not in wrapper:
        return None
    if (
        _is_int(wrapper.get("format"), _CACHE_FORMAT)
        and wrapper.get("tag") == tag
        and wrapper.get("path") == os.path.abspath(src)
        and _is_int(wrapper.get("size"), st.st_size)
        and _is_int(wrapper.get("mtime_ns"), st.st_mtime_ns)
    ):
        return wrapper["data"]
    return None
