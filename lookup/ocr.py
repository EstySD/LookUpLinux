"""Quiet offline OCR core; optional Qt and tesseract are loaded only on use."""
import math
from dataclasses import dataclass

from lookup.normalize import normalize
from lookup.dicts import DictError

MAX_TSV_BYTES = 4 << 20
MAX_ROWS = 10000
MAX_TEXT = 1024
MIN_CONFIDENCE = 50
NEAR_X = 0.75
NEAR_Y = 0.25
HYPHEN_GAP = 0.5
PAIR_GAP = 1.5
_HEADER = 'level page_num block_num par_num line_num word_num left top width height conf text'.split()
_REASONS = frozenset(('bad_output', 'invalid_point', 'missing_qt', 'missing_tesseract',
                      'missing_eng', 'invalid_image', 'too_large', 'timeout', 'process_failed'))


class OcrError(RuntimeError):
    def __init__(self, reason):
        if reason not in _REASONS:
            raise ValueError('unknown reason')
        super().__init__(reason)
        self.reason = reason


def _fail(reason):
    raise OcrError(reason) from None


def _point(point):
    try:
        x, y = point
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
                   for v in (x, y)):
            _fail('invalid_point')
        return x, y
    except (TypeError, ValueError):
        _fail('invalid_point')


@dataclass(frozen=True)
class Word:
    text: str
    box: tuple[float, float, float, float]
    confidence: float
    line_id: tuple[int, int, int, int]
    order: int


@dataclass(frozen=True)
class Transform:
    left: float = 0
    top: float = 0
    scale_x: float = 1
    scale_y: float = 1
    border: float = 0

    def __post_init__(self):
        _point((self.left, self.top))
        _point((self.scale_x, self.scale_y))
        if self.scale_x <= 0 or self.scale_y <= 0 or not math.isfinite(self.border) or self.border < 0:
            _fail('invalid_point')

    def original_xy(self, x, y):
        return (self.left + (x - self.border) / self.scale_x,
                self.top + (y - self.border) / self.scale_y)

    def original_box(self, box):
        x, y, w, h = box
        left, top = self.original_xy(x, y)
        return left, top, w / self.scale_x, h / self.scale_y


@dataclass(frozen=True)
class Selection:
    word: str
    line: str
    candidates: tuple[str, ...]
    box: tuple[float, float, float, float]
    confidence: float


def parse_tsv(data: bytes, transform: Transform | None = None) -> tuple[Word, ...]:
    if not isinstance(data, bytes) or len(data) > MAX_TSV_BYTES:
        _fail('bad_output')
    transform = transform or Transform()
    try:
        rows = data.decode('utf-8').splitlines()
        if not rows or rows[0].split('\t') != _HEADER or len(rows) > MAX_ROWS + 1:
            _fail('bad_output')
        words = []
        for row in rows[1:]:
            values = row.split('\t')
            if len(values) != 12:
                _fail('bad_output')
            level = int(values[0])
            if level not in range(1, 6):
                _fail('bad_output')
            if level != 5:
                continue
            ids = tuple(int(v) for v in values[1:6])
            box = tuple(float(v) for v in values[6:10])
            confidence = float(values[10])
            text = values[11]
            if (min(ids) <= 0 or not all(math.isfinite(v) for v in (*box, confidence))
                    or min(box[:2]) < 0 or min(box[2:]) <= 0 or not 0 <= confidence <= 100
                    or len(text) > MAX_TEXT or not text or any(ord(c) < 32 for c in text)):
                _fail('bad_output')
            words.append(Word(text, transform.original_box(box), confidence, ids[:4], ids[4]))
        return tuple(words)
    except (UnicodeError, ValueError, OverflowError):
        _fail('bad_output')


def _key(word):
    key = normalize(word.text)
    return key if key and ' ' not in key and word.confidence >= MIN_CONFIDENCE else None


def _gap(a, b):
    return b.box[0] - (a.box[0] + a.box[2])


def _union(parts, text):
    left = min(w.box[0] for w in parts)
    top = min(w.box[1] for w in parts)
    right = max(w.box[0] + w.box[2] for w in parts)
    bottom = max(w.box[1] + w.box[3] for w in parts)
    return Word(text, (left, top, right-left, bottom-top), min(w.confidence for w in parts),
                parts[0].line_id, parts[0].order)


def _units(line):
    units = []
    i = 0
    while i < len(line):
        current = line[i]
        if _key(current):
            while i + 1 < len(line):
                end = i + 1
                if line[end].text in ('-', '‐', '‑'):
                    end += 1
                elif not current.text.endswith(('-', '‐', '‑')):
                    break
                if end >= len(line) or not _key(line[end]):
                    break
                parts = [current, *line[i+1:end+1]]
                height = min(w.box[3] for w in (current, line[end]))
                if (any(w.confidence < MIN_CONFIDENCE for w in parts)
                        or any(not -height * 0.25 <= _gap(a, b) <= height * HYPHEN_GAP
                               for a, b in zip(parts, parts[1:]))):
                    break
                joined = _key(current).rstrip('-') + '-' + _key(line[end])
                current = _union(parts, joined)
                i = end
        units.append(current)
        i += 1
    return units


def _distance(word, x, y):
    left, top, width, height = word.box
    return max(left-x, 0, x-left-width), max(top-y, 0, y-top-height)


def select_word(words, point) -> Selection | None:
    x, y = _point(point)
    lines = {}
    for word in words:
        lines.setdefault(word.line_id, []).append(word)
    all_units = []
    for line_id, line in lines.items():
        line.sort(key=lambda w: (w.box[0], w.order))
        all_units.extend(_units(line))
    # Invalid text stays positioned so a rejected hit cannot jump to a neighbor.
    hits = [w for w in all_units if _distance(w, x, y) == (0, 0)]
    if hits:
        selected = min(hits, key=lambda w: (w.line_id, w.order))
        if not _key(selected):
            return None
    else:
        nearby = []
        for w in all_units:
            dx, dy = _distance(w, x, y)
            if _key(w) and dx <= NEAR_X*w.box[3] and dy <= NEAR_Y*w.box[3]:
                nearby.append((dx*dx + dy*dy, w.line_id, w.order, w))
        if not nearby:
            return None
        selected = min(nearby, key=lambda item: item[:3])[3]
    units = [w for w in all_units if w.line_id == selected.line_id]
    index = units.index(selected)
    candidates = []
    for a, b in ((index, index+1), (index-1, index)):
        if a < 0 or b >= len(units):
            continue
        first, second = units[a], units[b]
        if (not _key(first) or not _key(second)
                or not first.text[-1].isalpha() or not second.text[0].isalpha()
                or not 0 <= _gap(first, second) <= PAIR_GAP*min(first.box[3], second.box[3])):
            continue
        candidates.append(_key(first) + ' ' + _key(second))
    line = ' '.join(w.text for w in lines[selected.line_id])
    return Selection(_key(selected), line, tuple(candidates), selected.box, selected.confidence)


def choose_query(selection: Selection, dictset=None) -> str:
    if dictset is not None:
        for candidate in selection.candidates:
            try:
                if dictset.find(candidate):
                    return candidate
            except (DictError, OSError, ValueError):
                break
    return selection.word
