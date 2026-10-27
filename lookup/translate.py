"""Orchestrator for word, phrase and sentence lookup.

Dictionary first, then validated cache and online translation. Nothing prints
or logs; online failures are returned as fixed reason codes only.
"""
import json
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass, field, replace
from itertools import islice

from lookup import online as _online
from lookup import context as _contextual
from lookup.dicts import SearchResult
from lookup.normalize import normalize
from lookup.store import upsert_word, enrich_word_context

MAX_PHRASE_WORDS = 4
SENTENCE_CACHE_LIMIT = 1000
SHORT_MAX_CHARS = 200
CONTEXT_JOIN_S = _online.DEADLINE_S + 0.5
META_GOOGLE_CLIENT = "google_client"
_KINDS = ("word", "phrase", "sentence")
_MEANING_SLOT = threading.BoundedSemaphore(1)


@dataclass(frozen=True)
class Query:
    kind: str
    key: str | None


def classify(text) -> Query:
    if not isinstance(text, str):
        raise TypeError("text must be str")
    tokens = text.split()
    if not tokens:
        return Query("invalid", None)
    if len(tokens) > MAX_PHRASE_WORDS:
        return Query("sentence", " ".join(tokens))
    key = normalize(text)
    return Query("word" if len(tokens) == 1 else "phrase", key) if key else Query("invalid", None)


def short_translation(articles, online_result) -> str | None:
    for article in articles:
        if article.senses:
            values = islice((value for _pos, terms in article.senses for value in terms), 3)
            return "; ".join(values)[:SHORT_MAX_CHARS] or None
    if articles:
        lines = articles[0].text.splitlines()
        return (lines[0][:80] or None) if lines else None
    if online_result is None:
        return None
    values = [online_result.main] if online_result.main else []
    if online_result.parts:
        for value in online_result.parts[0][1]:
            if value and value not in values:
                values.append(value)
            if len(values) >= 3:
                break
    return "; ".join(values)[:SHORT_MAX_CHARS] or None


def _check_kind(kind):
    if kind not in _KINDS:
        raise ValueError("bad kind")


def cache_get(conn, key, kind) -> _online.OnlineResult | None:
    _check_kind(kind)
    row = conn.execute("SELECT payload FROM translations WHERE text=? AND kind=?", (key, kind)).fetchone()
    if row is None:
        return None
    try:
        return _online.OnlineResult.from_payload(json.loads(row[0]))
    except (ValueError, TypeError, RecursionError):
        return None


def cache_put(conn, key, kind, result, now=None) -> None:
    _check_kind(kind)
    conn.execute(
        "INSERT INTO translations (text, kind, provider, payload, fetched_at) VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(text, kind) DO UPDATE SET provider=excluded.provider, "
        "payload=excluded.payload, fetched_at=excluded.fetched_at",
        (key, kind, result.provider, json.dumps(result.to_payload()),
         int(time.time() if now is None else now)),
    )
    if kind == "sentence":
        conn.execute(
            "DELETE FROM translations WHERE kind=? AND rowid NOT IN "
            "(SELECT rowid FROM translations WHERE kind=? "
            "ORDER BY fetched_at DESC, rowid DESC LIMIT ?)",
            (kind, kind, SENTENCE_CACHE_LIMIT),
        )


def get_meta(conn, key) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row[0] if row and isinstance(row[0], str) else None


def set_meta(conn, key, value) -> None:
    conn.execute("INSERT INTO meta (key, value) VALUES (?, ?) "
                 "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))


@dataclass
class Result:
    kind: str
    key: str | None
    articles: tuple = ()
    lemma: str | None = None
    online: _online.OnlineResult | None = None
    online_attempted: bool = False
    online_enabled: bool = True
    online_error: str | None = None
    from_cache: bool = False
    context_translation: str | None = None
    context_error: str | None = None
    context_from_cache: bool = False
    translation: str | None = None
    saved: bool = False
    count: int | None = None
    context_pending: bool = False
    cache_error: str | None = None
    timings: dict = field(default_factory=lambda: dict.fromkeys(
        ("classify", "dicts", "cache", "online", "context", "db", "total", "first_useful", "meaning_ready"), 0.0))
    context_meaning: str | None = None
    meaning_provider: str | None = None
    meaning_error: str | None = None
    meaning_pending: bool = False
    meaning_from_cache: bool = False
    context_complete: bool = False
    meaning_save_error: bool = False


def _context_request(holder, key, clients, first_client, gate=None):
    # Only this holder crosses the thread boundary; the connection stays local.
    try:
        holder["result"] = _online.translate_online(
            key, "sentence", clients=clients, first_client=first_client)
    except _online.TranslateError as error:
        holder["error"] = error.reason
    except Exception:
        holder["error"] = "bad_response"
    finally:
        if gate is not None:
            gate.release()


def _meaning_request(holder, request, start, gate):
    try:
        value = _contextual.translate_context(request)
        if not isinstance(value, _contextual.ContextResult) or value.provider != request.provider:
            raise _online.TranslateError('bad_response')
        holder['result'] = _contextual.ContextResult(_contextual._meaning(value.meaning), value.provider)
    except _online.TranslateError as error:
        holder['error'] = error.reason
    except Exception:
        holder['error'] = 'bad_response'
    finally:
        holder['ready'] = (time.perf_counter()-start)*1000
        gate.release()


def lookup(text, *, dictset=None, conn=None, context=None, online=True,
           save=True, clients=None, now=None, on_ready=None, context_gate=None,
           context_span=None, context_complete=False, meaning_gate=None) -> Result:
    start = time.perf_counter()
    query = classify(text)
    result = Result(query.kind, query.key, online_enabled=online,
                    context_complete=context_complete is True,
                    meaning_error=('disabled' if not online else 'no_context')
                                  if query.kind in ('word','phrase') else None)
    result.timings["classify"] = (time.perf_counter() - start) * 1000
    if query.kind == "invalid":
        result.timings["total"] = (time.perf_counter() - start) * 1000
        return result

    def cached(key, kind):
        began = time.perf_counter()
        try:
            value = cache_get(conn, key, kind) if conn is not None else None
        except sqlite3.Error:
            result.cache_error = 'unavailable'
            value = None
        result.timings["cache"] += (time.perf_counter() - began) * 1000
        return value

    def remember(key, kind, value):
        if conn is not None:
            began = time.perf_counter()
            try:
                cache_put(conn, key, kind, value, now=now)
                if value.client:
                    set_meta(conn, META_GOOGLE_CLIENT, value.client)
            except sqlite3.Error:
                result.cache_error = 'unavailable'
            result.timings["db"] += (time.perf_counter() - began) * 1000

    try:
        first_client = get_meta(conn, META_GOOGLE_CLIENT) if conn is not None and online else None
    except sqlite3.Error:
        result.cache_error = 'unavailable'
        first_client = None
    thread = None
    holder = {}
    if context and online and query.kind != "sentence":
        ctx_key = _online.prepare_text(context)
        if ctx_key and ctx_key.casefold() != query.key.casefold():
            value = cached(ctx_key, "sentence")
            if value is not None:
                result.context_translation = value.main
                result.context_from_cache = True
            elif context_gate is not None and not context_gate.acquire(blocking=False):
                result.context_error = 'busy'
            else:
                context_start = time.perf_counter()
                thread = threading.Thread(target=_context_request,
                                          args=(holder, ctx_key, clients, first_client, context_gate), daemon=True)
                try:
                    thread.start()
                except (RuntimeError, OSError):
                    if context_gate is not None:
                        context_gate.release()
                    thread = None
                    result.context_error = 'bad_response'

    request = None
    if query.kind in ('word', 'phrase') and isinstance(context_span, (tuple, list)) and len(context_span) == 2:
        try:
            request = _contextual.ContextRequest(context, context_span[0], context_span[1], query.key)
        except _online.TranslateError:
            pass
    meaning_thread = None
    meaning_holder = {}
    meaning_collected = False
    if online and request is not None and result.context_complete and normalize(context) != query.key:
        result.meaning_error = None
        try:
            value = _contextual.cache_get(conn, request) if conn is not None else None
        except sqlite3.Error:
            result.cache_error = 'unavailable'
            value = None
        if value is not None:
            result.context_meaning, result.meaning_provider = value.meaning, value.provider
            result.meaning_from_cache = True
            result.timings['meaning_ready'] = (time.perf_counter()-start)*1000
        else:
            gate = meaning_gate if meaning_gate is not None else _MEANING_SLOT
            if not gate.acquire(blocking=False):
                result.meaning_error = 'busy'
            else:
                meaning_start = time.perf_counter()
                meaning_thread = threading.Thread(target=_meaning_request,
                    args=(meaning_holder, request, start, gate), daemon=True)
                try:
                    meaning_thread.start()
                except (RuntimeError, OSError):
                    gate.release()
                    meaning_thread = None
                    result.meaning_error = 'bad_response'

    def collect_meaning():
        nonlocal meaning_collected
        if meaning_collected or meaning_thread is None or meaning_thread.is_alive():
            return
        meaning_collected = True
        result.timings['meaning_ready'] = meaning_holder.get('ready', (time.perf_counter()-start)*1000)
        value = meaning_holder.get('result')
        if value is None:
            result.meaning_error = meaning_holder.get('error', 'bad_response')
        else:
            result.context_meaning, result.meaning_provider = value.meaning, value.provider
            if conn is not None:
                try:
                    _contextual.cache_put(conn, request, value, now)
                except sqlite3.Error:
                    result.cache_error = 'unavailable'

    began = time.perf_counter()
    search = SearchResult()
    if dictset is not None and query.kind != "sentence":
        try:
            search = dictset.find(query.key)
        except Exception:
            pass  # A damaged dictionary must not prevent online fallback.
    result.articles, result.lemma = search.articles, search.lemma
    result.timings["dicts"] = (time.perf_counter() - began) * 1000

    if not result.articles and online:
        key = _online.prepare_text(query.key) if query.kind == "sentence" else query.key
        result.online = cached(key, query.kind)
        result.from_cache = result.online is not None
        if result.online is None:
            began = time.perf_counter()
            result.online_attempted = True
            try:
                result.online = _online.translate_online(
                    key, query.kind, clients=clients, first_client=first_client)
            except _online.TranslateError as error:
                result.online_error = error.reason
            result.timings["online"] = (time.perf_counter() - began) * 1000
            if result.online is not None:
                remember(key, query.kind, result.online)

    if result.lemma is None and query.kind == "word" and result.online is not None:
        lemma = result.online.lemma
        if lemma and lemma.casefold() != query.key.casefold():
            result.lemma = lemma
    result.translation = short_translation(result.articles, result.online)
    token = None
    if query.kind in ("word", "phrase") and conn is not None and save and result.online_error != "not_found":
        began = time.perf_counter()
        token = uuid.uuid4().hex
        pair = dict(context_span=(request.start, request.end), context_token=token) if request is not None else {}
        result.count = upsert_word(conn, query.key, result.translation, context, now, lemma=result.lemma, **pair)
        result.saved = True
        result.timings["db"] += (time.perf_counter() - began) * 1000

    meaning_save_attempted = False
    def persist_meaning():
        nonlocal meaning_save_attempted
        if meaning_save_attempted or not result.saved or request is None or result.context_meaning is None:
            return
        meaning_save_attempted = True
        try:
            matched = enrich_word_context(conn, query.key, token, request.context, (request.start, request.end),
                                          _contextual.ContextResult(result.context_meaning, result.meaning_provider))
            result.meaning_save_error = not matched
        except (sqlite3.Error, OSError):
            result.meaning_save_error = True

    collect_meaning()
    persist_meaning()
    result.meaning_pending = meaning_thread is not None and not meaning_collected
    result.context_pending = thread is not None and thread.is_alive()
    if result.articles or result.online is not None:
        result.timings['first_useful'] = (time.perf_counter()-start)*1000
    if on_ready is not None:
        result.timings['total'] = (time.perf_counter()-start)*1000
        on_ready(replace(result, timings=dict(result.timings)))
    if thread is not None:
        began = time.perf_counter()
        thread.join(timeout=max(0.0, CONTEXT_JOIN_S - (began - context_start)))
        result.timings["context"] = (time.perf_counter() - began) * 1000
        if thread.is_alive():
            result.context_error = "timeout"
        elif "result" in holder:
            value = holder["result"]
            result.context_translation = value.main
            remember(ctx_key, "sentence", value)
        else:
            result.context_error = holder["error"]
    if meaning_thread is not None:
        meaning_thread.join(timeout=max(0.0, CONTEXT_JOIN_S - (time.perf_counter()-meaning_start)))
        if meaning_thread.is_alive():
            result.meaning_error = 'timeout'
        else:
            collect_meaning()
    result.meaning_pending = False
    persist_meaning()
    result.context_pending = False
    result.timings["total"] = (time.perf_counter() - start) * 1000
    return result
