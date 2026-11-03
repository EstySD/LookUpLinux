"""Dictionary layer foundation: the Article model, plain-text helpers, index cache.

Dictionary text comes from third-party files and is shown in a popup, so it is
exposed as plain text only (D-06): control and format characters removed,
markup flattened. Nothing here prints or logs (V7), and no error message
carries file content.

Open failures use stable reason codes: corrupt, unsupported,
encrypted_registration, missing_files, too_large, empty and checksum.
One failing dictionary never prevents searches in the others.
"""
import hashlib
import html.parser
import json
import os
import re
import tempfile
import time
import unicodedata as ud
from dataclasses import dataclass, replace
from functools import lru_cache
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


# -------------------------------------------------------- discovery and search

DICTS_ENV = "LOOKUP_DICTS"
SYSTEM_DICT_ROOT = Path("/usr/share/lookup/dicts")
MAX_DISCOVERED = 200
MAX_WALK_DEPTH = 6


@dataclass(frozen=True)
class Found:
    id: str
    path: Path
    fmt: str
    root_index: int


@dataclass(frozen=True)
class DictInfo:
    order: int | None
    id: str
    name: str
    fmt: str
    entries: int
    skipped: int
    status: str
    reason: str | None


def dict_roots() -> list[Path]:
    explicit = os.environ.get(DICTS_ENV)
    if explicit:
        return [Path(part) for part in explicit.split(os.pathsep) if part]
    xdg = os.environ.get("XDG_DATA_HOME")
    user = Path(xdg) if xdg and os.path.isabs(xdg) else Path.home() / ".local/share"
    return [user / "lookup/dicts", SYSTEM_DICT_ROOT]


def discover(roots=None) -> list[Found]:
    found = []
    seen = set()
    for root_index, root in enumerate(dict_roots() if roots is None else roots):
        root = Path(root)
        try:
            for directory, dirs, files in os.walk(root, followlinks=False):
                directory = Path(directory)
                depth = len(directory.relative_to(root).parts)
                dirs[:] = sorted(d for d in dirs if not d.startswith('.') and
                                 depth < MAX_WALK_DEPTH and not (directory / d).is_symlink())
                plain_dsl = {f.casefold() for f in files if f.casefold().endswith('.dsl')}
                for name in sorted(files):
                    path = directory / name
                    if name.startswith('.') or path.is_symlink():
                        continue
                    lower = name.casefold()
                    if lower.endswith('.ifo'):
                        fmt = 'stardict'
                    elif lower.endswith(('.dsl', '.dsl.dz')):
                        if lower.endswith('.dz') and lower[:-3] in plain_dsl:
                            continue
                        fmt = 'dsl'
                    elif lower.endswith('.mdx'):
                        fmt = 'mdx'
                    elif lower.endswith('.zip'):
                        fmt = 'yomitan'
                    else:
                        continue
                    ident = path.relative_to(root).as_posix()
                    if ident in seen:
                        continue
                    seen.add(ident)
                    found.append(Found(ident, path, fmt, root_index))
                    if len(found) >= MAX_DISCOVERED:
                        return found
        except OSError:
            continue
    return found


class DictSet:
    def __init__(self):
        self.dicts = []
        self.problems = []
        self.disabled = []
        self.open_ms = 0.0
        self._info = []
        self._closed = False

    def info(self) -> list[DictInfo]:
        return list(self._info)

    def lookup_exact(self, key) -> list[Article]:
        key = fold_key(key)
        articles = []
        for reader in self.dicts:
            try:
                articles.extend(reader.lookup(key))
            except MemoryError:
                raise
            except Exception:
                continue
        return articles

    def has(self, key) -> bool:
        key = fold_key(key)
        for reader in self.dicts:
            try:
                if reader.has(key):
                    return True
            except MemoryError:
                raise
            except Exception:
                continue
        return False

    def find(self, text) -> SearchResult:
        key = fold_key(text)
        if not key:
            return SearchResult()
        articles = self.lookup_exact(key)
        if articles:
            return self._resolve(articles, key)
        if ' ' not in key:
            for candidate in form_candidates(key):
                articles = self.lookup_exact(candidate)
                if articles:
                    result = self._resolve(articles, candidate)
                    return SearchResult(tuple(replace(a, lemma_of=a.lemma_of or candidate)
                                              for a in result.articles), result.lemma or candidate)
        return SearchResult()

    def _resolve(self, articles, key):
        out = []
        seen = set()
        lemma = None
        for article in articles:
            resolved = [article]
            base = fold_key(article.form_of) if article.form_of else None
            if base and article.pointer_only:
                targets = [a for a in self.lookup_exact(base) if not a.pointer_only]
                if targets:
                    resolved = [replace(a, lemma_of=base) for a in targets]
            elif base and base != key and self.has(base):
                resolved = [replace(article, lemma_of=base)]
            for item in resolved:
                ident = (item.dict_name, item.headword, item.text)
                if ident not in seen:
                    seen.add(ident)
                    out.append(item)
                    lemma = lemma or item.lemma_of
        return SearchResult(tuple(out), lemma)

    def close(self):
        if self._closed:
            return
        self._closed = True
        for reader in self.dicts:
            try:
                reader.close()
            except MemoryError:
                raise
            except Exception:
                continue

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def open_all(config=None, roots=None) -> DictSet:
    from lookup.config import load
    from lookup.stardict import open_stardict
    from lookup.dsl import open_dsl
    from lookup.mdx import open_mdx
    from lookup.yomitan import open_yomitan

    started = time.perf_counter()
    settings = load() if config is None else config
    result = DictSet()
    candidates = discover(roots)
    by_id = {f.id: f for f in candidates}
    enabled = {}
    for ident, on in settings.dictionaries:
        if ident in by_id and ident not in enabled:
            enabled[ident] = on
    records = []
    openers = {'stardict': open_stardict, 'dsl': open_dsl, 'mdx': open_mdx,
               'yomitan': open_yomitan}
    try:
        for candidate in candidates:
            name = candidate.path.name
            name = name[:-7] if name.casefold().endswith('.dsl.dz') else candidate.path.stem
            reader = None
            reason = None
            status = 'ok'
            if enabled.get(candidate.id, True) is False:
                status = 'disabled'
            else:
                try:
                    reader = openers[candidate.fmt](candidate.path)
                    name = reader.name
                    # Track immediately so exceptional termination closes earlier readers.
                    result.dicts.append(reader)
                except MemoryError:
                    raise
                except DictError as exc:
                    status, reason = 'error', exc.reason
                except Exception:
                    status, reason = 'error', 'corrupt'
            records.append((candidate, name, reader, status, reason))
        ranks = {ident: n for n, ident in enumerate(enabled)}
        records.sort(key=lambda r: (0, ranks[r[0].id]) if r[0].id in ranks else
                     (1, r[0].root_index, r[1].casefold(), r[0].id))
        result.dicts = []
        for candidate, name, reader, status, reason in records:
            order = None
            if reader is not None:
                result.dicts.append(reader)
                order = len(result.dicts)
            elif status == 'disabled':
                result.disabled.append(candidate.id)
            else:
                result.problems.append((candidate.id, reason))
            result._info.append(DictInfo(order, candidate.id, name, candidate.fmt,
                                        reader.entry_count if reader else 0,
                                        reader.skipped_entries if reader else 0, status, reason))
    except BaseException:
        result.close()
        raise
    result.open_ms = (time.perf_counter() - started) * 1000
    return result


_IRREGULAR_PATH = Path(__file__).with_name('data') / 'irregular.txt'
_FORM_RE = re.compile(r"[a-z][a-z'-]*\Z")


@lru_cache(maxsize=1)
def load_irregular() -> dict[str, tuple[str, ...]]:
    try:
        with open(_IRREGULAR_PATH, 'rb') as fh:
            raw = fh.read((4 << 20) + 1)
        if len(raw) > 4 << 20:
            return {}
        forms = {}
        for line in raw.decode('utf-8').splitlines():
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            fields = line.split()
            if len(fields) >= 2 and all(_FORM_RE.fullmatch(f) for f in fields):
                forms[fields[0]] = tuple(fields[1:])
        return forms
    except (OSError, UnicodeError):
        return {}


def form_candidates(word) -> list[str]:
    if not isinstance(word, str):
        raise TypeError('word must be str')
    word = word.lower()
    if not word or any(c.isspace() for c in word):
        return []
    candidates = list(load_irregular().get(word, ()))

    def undouble(stem):
        if len(stem) > 1 and stem[-1] == stem[-2] and stem[-1].isalpha() and stem[-1] not in 'aeiou':
            candidates.append(stem[:-1])

    for suffix in ('ies', 'ied', 'ier', 'iest'):
        if word.endswith(suffix):
            candidates.append(word[:-len(suffix)] + 'y')
    if word.endswith('ing') and len(word) > 4:
        stem = word[:-3]
        candidates.extend((stem + 'e', stem))
        undouble(stem)
    if word.endswith('ed') and len(word) > 3:
        candidates.extend((word[:-1], word[:-2]))
        undouble(word[:-2])
    if word.endswith('es'):
        candidates.extend((word[:-1], word[:-2]))
    elif word.endswith('s') and not word.endswith(('ss', 'us')):
        candidates.append(word[:-1])
    if word.endswith('est'):
        candidates.extend((word[:-2], word[:-3]))
        undouble(word[:-3])
    elif word.endswith('er'):
        candidates.extend((word[:-1], word[:-2]))
        undouble(word[:-2])
    return list(dict.fromkeys(c for c in candidates if len(c) >= 2 and c != word))
