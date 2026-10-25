"""Online translation: Google translate_a/single, MyMemory fallback, one shared deadline (D-13..D-16, D-30, D-31).

Privacy rule (V7): this module never prints or logs. Exceptions carry only a
fixed reason code and the transport exception is suppressed, so the query text
can never leak through messages or tracebacks. Only the word, phrase or
sentence is sent; no identity, key or e-mail parameter ever is.
"""
import dataclasses
import http.client
import json
import re
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

GOOGLE_HOST = "translate.googleapis.com"
MYMEMORY_HOST = "api.mymemory.translated.net"
DEFAULT_CLIENTS = ("gtx", "dict-chrome-ex", "at")
DEADLINE_S = 3.0
MIN_ATTEMPT_S = 0.5
MAX_BODY = 1 << 20
ONLINE_MAX_CHARS = 1000
REASONS = ("no_network", "timeout", "blocked", "bad_response", "not_found")

_KINDS = ("word", "phrase", "sentence")
_MAX_PARTS = 8
_MAX_TERMS = 5
_SNIFF_CHARS = 2000


class TranslateError(RuntimeError):
    """Online translation failed; the message is one of REASONS and never carries user text."""

    def __init__(self, reason: str):
        if reason not in REASONS:
            raise ValueError("unknown reason")
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class OnlineResult:
    provider: str  # "google" or "mymemory"
    client: str | None  # Google client= value that answered
    main: str
    parts: tuple[tuple[str, tuple[str, ...]], ...]  # (part of speech, terms)
    transcription: str | None
    lemma: str | None
    src_lang: str

    def to_payload(self) -> dict:
        return {
            "provider": self.provider,
            "client": self.client,
            "main": self.main,
            "parts": [[pos, list(terms)] for pos, terms in self.parts],
            "transcription": self.transcription,
            "lemma": self.lemma,
            "src_lang": self.src_lang,
        }

    @classmethod
    def from_payload(cls, d) -> "OnlineResult | None":
        """Rebuild a result from a cached payload; None on any shape mismatch (the cache is untrusted)."""
        if not isinstance(d, dict):
            return None
        try:
            provider, client, main = d["provider"], d["client"], d["main"]
            raw_parts, transcription = d["parts"], d["transcription"]
            lemma, src_lang = d["lemma"], d["src_lang"]
        except KeyError:
            return None
        if provider not in ("google", "mymemory"):
            return None
        if not (client is None or isinstance(client, str)):
            return None
        if not (isinstance(main, str) and main):
            return None
        for opt in (transcription, lemma):
            if not (opt is None or isinstance(opt, str)):
                return None
        if not isinstance(src_lang, str):
            return None
        if not isinstance(raw_parts, list):
            return None
        parts = []
        for item in raw_parts:
            if not (isinstance(item, list) and len(item) == 2):
                return None
            pos, terms = item
            if not isinstance(pos, str) or not isinstance(terms, list):
                return None
            if not all(isinstance(t, str) for t in terms):
                return None
            parts.append((pos, tuple(terms)))
        return cls(provider, client, main, tuple(parts), transcription, lemma, src_lang)


def prepare_text(text: str) -> str:
    """Collapse whitespace; cut at ONLINE_MAX_CHARS on a word boundary."""
    text = " ".join(text.split())
    if len(text) <= ONLINE_MAX_CHARS:
        return text
    cut = text[:ONLINE_MAX_CHARS]
    if text[ONLINE_MAX_CHARS] != " ":
        head, sep, _tail = cut.rpartition(" ")
        if sep:
            cut = head
    return cut.rstrip()


def _norm(text: str) -> str:
    return " ".join(text.split()).casefold().rstrip(".!? ")


def _at(seq, *path):
    """Safe nested index: None when any step has the wrong type or is out of range."""
    cur = seq
    for i in path:
        if not isinstance(cur, list) or not (0 <= i < len(cur)):
            return None
        cur = cur[i]
    return cur


def _load_json(body: bytes):
    try:
        return json.loads(body.decode("utf-8"))
    except (ValueError, RecursionError):
        raise TranslateError("bad_response") from None


def _check_kind(kind: str) -> None:
    if kind not in _KINDS:
        raise ValueError("bad kind")


def parse_google(body: bytes, kind: str, text: str | None = None) -> OnlineResult:
    """Parse a translate_a/single answer (dt=t, dt=bd, dt=rm) into an OnlineResult."""
    _check_kind(kind)
    head = body[:_SNIFF_CHARS].decode("utf-8", errors="replace").lstrip().lower()
    if head.startswith("<") or head.startswith("sorry"):
        raise TranslateError("blocked")
    if not head.startswith("[") and "automated queries" in head:
        raise TranslateError("blocked")
    data = _load_json(body)
    segments = _at(data, 0)
    if not isinstance(segments, list):
        raise TranslateError("bad_response")
    main = "".join(s[0] for s in segments if isinstance(s, list) and s and isinstance(s[0], str))
    if not main.strip():
        raise TranslateError("bad_response")
    transcription = None
    for s in segments:
        tr = _at(s, 3)
        if isinstance(s, list) and s and s[0] is None and isinstance(tr, str) and tr:
            transcription = tr
            break
    parts = []
    lemma = None
    block = _at(data, 1)
    for entry in block if isinstance(block, list) else ():
        pos, terms = _at(entry, 0), _at(entry, 1)
        if not (isinstance(pos, str) and pos and isinstance(terms, list)):
            continue
        clean = tuple(t for t in terms if isinstance(t, str) and t)[:_MAX_TERMS]
        if not clean:
            continue
        if len(parts) >= _MAX_PARTS:
            break
        parts.append((pos, clean))
        source = _at(entry, 3)
        if lemma is None and isinstance(source, str) and source:
            lemma = source
    src = _at(data, 2)
    src_lang = src if isinstance(src, str) else ""
    if kind == "word" and not parts:
        raise TranslateError("not_found")  # a transliteration is not a translation (D-30)
    if text is not None and _norm(main) == _norm(text):
        raise TranslateError("not_found")
    return OnlineResult("google", None, main, tuple(parts), transcription, lemma, src_lang)


def _status(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def parse_mymemory(body: bytes, kind: str, text: str | None = None) -> OnlineResult:
    """Parse a MyMemory /get answer; phrases and sentences only (D-31)."""
    _check_kind(kind)
    data = _load_json(body)
    if not isinstance(data, dict):
        raise TranslateError("bad_response")
    status = _status(data.get("responseStatus"))
    if data.get("quotaFinished") is True or status in (403, 429):
        raise TranslateError("blocked")
    rd = data.get("responseData")
    translated = rd.get("translatedText") if isinstance(rd, dict) else None
    if not isinstance(translated, str):
        raise TranslateError("bad_response")
    if "mymemory warning" in translated.lower():
        raise TranslateError("blocked")
    if status != 200 or not translated.strip():
        raise TranslateError("bad_response")
    if text is not None and _norm(translated) == _norm(text):
        raise TranslateError("not_found")
    return OnlineResult("mymemory", None, translated.strip(), (), None, None, "en")


_CHUNK = 16 * 1024
_CLIENT_RE = re.compile(r"[A-Za-z0-9._-]{1,32}")
# When every attempt failed, report the most actionable reason first.
_PRIORITY = ("blocked", "bad_response", "timeout", "no_network")


def _fail(reason: str):
    raise TranslateError(reason) from None


def _fetch(url: str, timeout: float, deadline_at: float, clock, expected_host: str) -> bytes:
    """GET url over default-verified TLS and return the body, or raise TranslateError(reason).

    urlopen is looked up by attribute so tests can patch it. urllib's timeout
    is per socket operation, so the wall clock is checked between chunks.
    """
    request = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            final = urllib.parse.urlsplit(resp.geturl())
            if final.scheme != "https" or final.hostname != expected_host:
                _fail("bad_response")
            chunks = []
            total = 0
            while True:
                chunk = resp.read(_CHUNK)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_BODY:
                    _fail("bad_response")
                chunks.append(chunk)
                if clock() > deadline_at:
                    _fail("timeout")
            return b"".join(chunks)
    except TranslateError:
        raise
    except urllib.error.HTTPError as e:
        e.close()
        _fail("blocked" if e.code in (403, 429) else "bad_response")
    except urllib.error.URLError as e:
        _fail("timeout" if isinstance(e.reason, TimeoutError) else "no_network")
    except TimeoutError:
        _fail("timeout")
    except http.client.HTTPException:
        _fail("bad_response")
    except (ssl.SSLError, OSError):
        _fail("no_network")


def google_translate(text: str, kind: str, client: str, deadline_at: float, clock) -> OnlineResult:
    query = urllib.parse.urlencode(
        [("client", client), ("sl", "en"), ("tl", "ru"), ("dt", "t"), ("dt", "bd"), ("dt", "rm"), ("q", text)]
    )
    url = f"https://{GOOGLE_HOST}/translate_a/single?{query}"
    timeout = max(MIN_ATTEMPT_S, deadline_at - clock())
    body = _fetch(url, timeout, deadline_at, clock, GOOGLE_HOST)
    return dataclasses.replace(parse_google(body, kind, text), client=client)


def mymemory_translate(text: str, kind: str, deadline_at: float, clock) -> OnlineResult:
    """Fallback for phrases and sentences only; a single word never leaves for MyMemory (D-31)."""
    _check_kind(kind)
    if kind == "word":
        raise TranslateError("not_found")
    # Only q and langpair: no `de` (e-mail) and no `key` (T-02-16).
    query = urllib.parse.urlencode([("q", text), ("langpair", "en|ru")])
    url = f"https://{MYMEMORY_HOST}/get?{query}"
    timeout = max(MIN_ATTEMPT_S, deadline_at - clock())
    body = _fetch(url, timeout, deadline_at, clock, MYMEMORY_HOST)
    return parse_mymemory(body, kind, text)


def translate_online(
    text: str,
    kind: str,
    *,
    clients=None,
    first_client=None,
    deadline_s: float = DEADLINE_S,
    clock=time.monotonic,
) -> OnlineResult:
    """Translate through the ordered Google clients, then MyMemory for phrases and sentences.

    All attempts share one deadline. Returns the first success or raises
    TranslateError with exactly one of REASONS; not_found ends the chain at once.
    """
    _check_kind(kind)
    if not isinstance(text, str) or not text.strip():
        raise ValueError("empty text")
    text = prepare_text(text)
    names = []
    for name in clients or ():
        if isinstance(name, str) and _CLIENT_RE.fullmatch(name) and name not in names:
            names.append(name)
    if not names:
        names = list(DEFAULT_CLIENTS)
    if first_client in names:
        names.remove(first_client)
        names.insert(0, first_client)
    deadline_at = clock() + deadline_s
    failures = set()

    def time_left() -> bool:
        if deadline_at - clock() < MIN_ATTEMPT_S:
            failures.add("timeout")
            return False
        return True

    for client in names:
        if not time_left():
            break
        try:
            return google_translate(text, kind, client, deadline_at, clock)
        except TranslateError as e:
            if e.reason == "not_found":
                raise
            failures.add(e.reason)
    else:
        if kind != "word" and time_left():
            try:
                return mymemory_translate(text, kind, deadline_at, clock)
            except TranslateError as e:
                if e.reason == "not_found":
                    raise
                failures.add(e.reason)
    for reason in _PRIORITY:
        if reason in failures:
            raise TranslateError(reason) from None
    raise TranslateError("bad_response") from None
