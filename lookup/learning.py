"""Offline card snapshots, history queries, deterministic review and file export.

Connections belong to the calling thread. Errors carry fixed codes, never text
from a word, context, translation or destination.
"""
import csv
import html
import math
import os
from pathlib import Path
import sqlite3
import tempfile
import time
import unicodedata

from .normalize import normalize
from .store import CONTEXT_MAX_CHARS, get_word_context

REASONS = ('invalid_snapshot','missing_translation','invalid_state','invalid_rating',
           'invalid_sort','invalid_time','invalid_search','export_failed')
_WORD_FIELDS = 'word translation context count first_seen last_seen lemma'.split()
_CARD_FIELDS = ('word translation context context_start context_end provider created_at due '
                'repetitions interval_days ease review_version').split()
_SORTS = frozenset(_WORD_FIELDS)
_MAX_TIME = (1 << 63)-1


class LearningError(ValueError):
    def __init__(self, reason):
        if reason not in REASONS:
            reason = 'invalid_state'
        self.reason = reason
        super().__init__(reason)


def _text(value, limit):
    return (isinstance(value,str) and len(value) <= limit and
            not any(unicodedata.category(c).startswith('C') and c not in '\t\r\n' for c in value))


def _word(value):
    if (not _text(value,500) or not value or len(value.split()) > 4 or normalize(value) != value):
        raise LearningError('invalid_snapshot')
    return value


def _now(value):
    if value is None:
        return int(time.time())
    if (isinstance(value,bool) or not isinstance(value,(int,float)) or
            (isinstance(value,float) and not math.isfinite(value)) or not 0 <= value <= _MAX_TIME):
        raise LearningError('invalid_time')
    return int(value)


def list_words(conn, search='', sort='count', descending=True):
    if not isinstance(sort,str) or sort not in _SORTS or not isinstance(descending,bool):
        raise LearningError('invalid_sort')
    if not _text(search,500):
        raise LearningError('invalid_search')
    search = search.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
    rows = conn.execute(
        'SELECT '+','.join(_WORD_FIELDS)+' FROM words '
        "WHERE word LIKE ? ESCAPE '\\' OR translation LIKE ? ESCAPE '\\' "
        'ORDER BY '+sort+(' DESC' if descending else ' ASC')+',word ASC',
        ('%'+search+'%','%'+search+'%')).fetchall()
    return [dict(zip(_WORD_FIELDS,row)) for row in rows]


def delete_word(conn, word):
    if not _text(word,500) or not word:
        raise LearningError('invalid_snapshot')
    return conn.execute('DELETE FROM words WHERE word=?',(word,)).rowcount == 1


def _card(row):
    result = dict(zip(_CARD_FIELDS,row))
    start, end = result.pop('context_start'), result.pop('context_end')
    result['span'] = (start,end) if start is not None and end is not None else None
    return result


def get_card(conn, word):
    row = conn.execute('SELECT '+','.join(_CARD_FIELDS)+' FROM cards WHERE word=?',(_word(word),)).fetchone()
    return _card(row) if row is not None else None


def list_cards(conn):
    return [_card(row) for row in conn.execute('SELECT '+','.join(_CARD_FIELDS)+' FROM cards ORDER BY word').fetchall()]


def add_card(conn, snapshot, now=None):
    if not isinstance(snapshot,dict):
        raise LearningError('invalid_snapshot')
    word = _word(snapshot.get('word'))
    meaning = snapshot.get('meaning')
    translation = meaning or snapshot.get('translation')
    if not _text(translation,8000) or not translation.strip():
        raise LearningError('missing_translation')
    context = snapshot.get('context')
    if context is not None and not _text(context,CONTEXT_MAX_CHARS):
        raise LearningError('invalid_snapshot')
    span = snapshot.get('span')
    start = end = provider = None
    if span is not None:
        if (not isinstance(span,(tuple,list)) or len(span) != 2 or not isinstance(context,str)
                or any(isinstance(v,bool) or not isinstance(v,int) for v in span)
                or not 0 <= span[0] < span[1] <= len(context)
                or normalize(context[span[0]:span[1]]) != word):
            raise LearningError('invalid_snapshot')
        start,end = span
    if meaning:
        provider = snapshot.get('provider')
        if span is None or not _text(provider,64) or not provider:
            raise LearningError('invalid_snapshot')
    created = _now(now)
    cursor = conn.execute(
        'INSERT INTO cards (word,translation,context,context_start,context_end,provider,created_at,due) '
        'VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(word) DO NOTHING',
        (word,translation,context,start,end,provider,created,created))
    return 'created' if cursor.rowcount == 1 else 'already_present'


def add_history_card(conn, word, now=None):
    return add_card(conn,get_word_context(conn,word),now=now)


def due_cards(conn, now=None):
    rows = conn.execute('SELECT '+','.join(_CARD_FIELDS)+' FROM cards WHERE due<=? ORDER BY due,word',
                        (_now(now),)).fetchall()
    return [_card(row) for row in rows]


def preview(state, rating):
    """Selected SM-2-derived rule, shared by interval labels and persisted grades."""
    if not isinstance(rating,str) or rating not in ('Again','Hard','Good','Easy'):
        raise LearningError('invalid_rating')
    try:
        repetitions, days, ease = state['repetitions'],state['interval_days'],state['ease']
        if (any(isinstance(v,bool) or not isinstance(v,int) or not 0 <= v < (1 << 31)
                for v in (repetitions,days)) or (repetitions == 0) != (days == 0)
                or isinstance(ease,bool) or not isinstance(ease,(int,float))):
            raise LearningError('invalid_state')
        ease = float(ease)
        if not math.isfinite(ease) or ease < 1.3:
            raise LearningError('invalid_state')
        if rating == 'Again':
            return dict(repetitions=0,interval_days=0,ease=ease,delay=600)
        quality = {'Hard':3,'Good':4,'Easy':5}[rating]
        following_days = 1 if repetitions == 0 else 6 if repetitions == 1 else math.ceil(days*ease)
        following_ease = max(1.3,ease+0.1-(5-quality)*(0.08+(5-quality)*0.02))
        if following_days >= (1 << 31) or repetitions+1 >= (1 << 31) or not math.isfinite(following_ease):
            raise LearningError('invalid_state')
        return dict(repetitions=repetitions+1,interval_days=following_days,
                    ease=following_ease,delay=following_days*86400)
    except (KeyError,TypeError,ValueError,OverflowError):
        raise LearningError('invalid_state') from None


def grade_card(conn, word, expected_version, rating, now=None):
    if isinstance(expected_version,bool) or not isinstance(expected_version,int) or not 0 <= expected_version < _MAX_TIME:
        raise LearningError('invalid_state')
    answered = _now(now)
    if not isinstance(rating,str) or rating not in ('Again','Hard','Good','Easy'):
        raise LearningError('invalid_rating')
    card = get_card(conn,word)
    if card is None or card['review_version'] != expected_version or _now(card['due']) > answered:
        return 'stale'
    transition = preview(card,rating)
    due = answered+transition['delay']
    if due > _MAX_TIME:
        raise LearningError('invalid_time')
    cursor = conn.execute(
        'UPDATE cards SET repetitions=?,interval_days=?,ease=?,due=?,review_version=review_version+1 '
        'WHERE word=? AND review_version=? AND due<=?',
        (transition['repetitions'],transition['interval_days'],transition['ease'],due,
         word,expected_version,answered))
    return 'applied' if cursor.rowcount == 1 else 'stale'


def _html_field(value):
    return html.escape(value or '',quote=True).replace('\r\n','\n').replace('\r','\n').replace('\n','<br>').replace('\t','&#9;')


def _export(conn, path, anki):
    temporary = None
    try:
        # One SELECT materializes a consistent snapshot before destination I/O.
        cards = list_cards(conn)
        path = Path(path)
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',newline='',dir=path.parent,
                                         prefix='.'+path.name+'.',suffix='.tmp',delete=False) as stream:
            temporary = Path(stream.name)
            writer = csv.writer(stream,delimiter='\t' if anki else ',',lineterminator='\n' if anki else '\r\n')
            if anki:
                stream.write('#separator:Tab\n#html:true\n#columns:Front\tBack\n')
                for card in cards:
                    back = _html_field(card['translation'])
                    if card['context']:
                        back += '<hr>'+_html_field(card['context'])
                    writer.writerow((_html_field(card['word']),back))
            else:
                writer.writerow(('word','translation','context'))
                writer.writerows((card['word'],card['translation'],card['context'] or '') for card in cards)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary,path)
    except (OSError,TypeError,ValueError,sqlite3.Error):
        raise LearningError('export_failed') from None
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def export_csv(conn, path):
    _export(conn,path,False)


def export_anki(conn, path):
    _export(conn,path,True)
