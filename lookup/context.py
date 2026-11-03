"""Occurrence-specific meanings from marked Google sentence translation.

The public gtx endpoint is undocumented. Recorded examples establish feasibility,
not universal alignment: malformed/unsuitable responses are refused, never guessed.
Only bounded source text crosses the existing private TLS transport.
"""
from dataclasses import dataclass
import html
import json
import re
import time
import unicodedata
from urllib.parse import urlencode

from . import online
from .normalize import normalize
from .store import CONTEXT_MAX_CHARS

PROVIDER = 'google-marked-v2'
MAX_BODY = 65536
MAX_MEANING = 200
MAX_TRANSLATED = 4000
CACHE_LIMIT = 1000


def _bad():
    raise online.TranslateError('bad_response') from None


def _controls(text):
    return any(unicodedata.category(c).startswith('C') and c not in '\t\r\n' for c in text)


@dataclass(frozen=True)
class ContextRequest:
    context: str
    start: int
    end: int
    word: str
    provider: str = PROVIDER
    target: str = 'ru'

    def __post_init__(self):
        if (not isinstance(self.context, str) or not 0 < len(self.context) <= CONTEXT_MAX_CHARS
                or '<' in self.context or '>' in self.context or _controls(self.context)
                or any(isinstance(v, bool) or not isinstance(v, int) for v in (self.start,self.end))
                or not 0 <= self.start < self.end <= len(self.context)
                or not isinstance(self.word, str) or not self.word
                or normalize(self.context[self.start:self.end]) != self.word
                or any(not isinstance(v,str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}',v)
                       for v in (self.provider,self.target))):
            _bad()


@dataclass(frozen=True)
class ContextResult:
    meaning: str
    provider: str


def _meaning(value):
    if (not isinstance(value,str) or not value.strip() or len(value) > MAX_MEANING
            or _controls(value) or '<' in value or '>' in value
            or not any('а' <= c.lower() <= 'я' or c.lower() == 'ё' for c in value)
            or any(c.isalpha() and not ('а' <= c.lower() <= 'я' or c.lower() == 'ё') for c in value)):
        _bad()
    return value.strip()


def _parse(body):
    if not isinstance(body,bytes) or len(body) > MAX_BODY:
        _bad()
    try:
        data = json.loads(body.decode('utf-8'))
        if not isinstance(data,list) or not data or not isinstance(data[0],list) or not 0 < len(data[0]) <= 100:
            _bad()
        parts = data[0]
        if any(not isinstance(part,list) or not part or not isinstance(part[0],str) for part in parts):
            _bad()
        translated = ''.join(part[0] for part in parts)
        if len(translated) > MAX_TRANSLATED or _controls(translated):
            _bad()
        # Exact syntax intentionally rejects HTMLParser's tolerant repairs.
        match = re.fullmatch(r'[^<>]*<b>([^<>]*)</b>[^<>]*', translated)
        if match is None:
            _bad()
        return _meaning(html.unescape(match[1]))
    except (UnicodeError, ValueError, TypeError, RecursionError):
        _bad()


def translate_context(request):
    if not isinstance(request,ContextRequest) or request.provider != PROVIDER or request.target != 'ru':
        _bad()
    source = request.context
    marked = (html.escape(source[:request.start])+'<b>'+
              html.escape(source[request.start:request.end])+'</b>'+html.escape(source[request.end:]))
    clock = time.monotonic
    deadline = clock()+online.DEADLINE_S
    failures = set()
    for client in online.DEFAULT_CLIENTS:
        remaining = deadline-clock()
        if remaining < online.MIN_ATTEMPT_S:
            failures.add('timeout')
            break
        query = urlencode(dict(client=client,sl='en',tl='ru',dt='t',q=marked))
        try:
            body = online._fetch('https://'+online.GOOGLE_HOST+'/translate_a/single?'+query,
                                 remaining,deadline,clock,online.GOOGLE_HOST)
        except online.TranslateError as error:
            if error.reason not in online._PRIORITY:
                raise
            failures.add(error.reason)
            continue
        return ContextResult(_parse(body), request.provider)
    raise online.TranslateError(next(reason for reason in online._PRIORITY if reason in failures)) from None


def _identity(request):
    if not isinstance(request,ContextRequest):
        _bad()
    request.__post_init__()
    return (request.provider,request.target,request.word,request.context,request.start,request.end)


def cache_get(conn, request):
    identity = _identity(request)
    row = conn.execute(
        'SELECT payload FROM contextual_translations '
        'WHERE provider=? AND target=? AND word=? AND context=? AND start=? AND end=?',identity).fetchone()
    if row is None or not isinstance(row[0],str) or len(row[0]) > 2048:
        return None
    try:
        payload = json.loads(row[0])
        if not isinstance(payload,dict) or payload.get('provider') != request.provider:
            return None
        return ContextResult(_meaning(payload.get('meaning')),request.provider)
    except (ValueError,TypeError,RecursionError,online.TranslateError):
        return None


def cache_put(conn, request, result, now=None):
    identity = _identity(request)
    if not isinstance(result,ContextResult) or result.provider != request.provider:
        _bad()
    meaning = _meaning(result.meaning)
    conn.execute(
        'INSERT INTO contextual_translations (provider,target,word,context,start,end,payload,fetched_at) '
        'VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(provider,target,word,context,start,end) '
        'DO UPDATE SET payload=excluded.payload,fetched_at=excluded.fetched_at',
        identity+(json.dumps(dict(meaning=meaning,provider=result.provider)),int(time.time() if now is None else now)))
    conn.execute(
        'DELETE FROM contextual_translations WHERE rowid NOT IN '
        '(SELECT rowid FROM contextual_translations ORDER BY fetched_at DESC,rowid DESC LIMIT ?)',(CACHE_LIMIT,))
