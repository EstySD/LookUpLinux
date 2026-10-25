"""Quiet offline OCR core; optional Qt and tesseract are loaded only on use."""
import math
import os
import stat
import subprocess
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

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
_REASONS = frozenset(('bad_output', 'invalid_point', 'missing_pyqt6', 'missing_tesseract',
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
            if not row:
                continue
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
                    or len(text) > MAX_TEXT or not text
                    or any(unicodedata.category(c) in ('Cc', 'Cf', 'Cs') for c in text)):
                _fail('bad_output')
            words.append(Word(text, transform.original_box(box), confidence, ids[:4], ids[4]))
        return tuple(words)
    except (UnicodeError, ValueError, OverflowError):
        _fail('bad_output')


def _key(word):
    key = normalize(word.text)
    return key if key and ' ' not in key and word.confidence >= MIN_CONFIDENCE else None


def _fragment(word):
    if word.confidence < MIN_CONFIDENCE:
        return None
    raw = word.text.replace('‐', '-').replace('‑', '-')
    if not all(c in "'-" or (c.isalpha() and unicodedata.name(c, '').startswith('LATIN')) for c in raw):
        return None
    key = normalize(raw)
    if key and ' ' not in key:
        return key
    stem = raw.rstrip('-')
    return stem.casefold() if len(stem) == 1 and stem.isalpha() else None


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
        if _fragment(current):
            while i + 1 < len(line):
                end = i + 1
                if line[end].text in ('-', '‐', '‑'):
                    end += 1
                elif not current.text.endswith(('-', '‐', '‑')):
                    break
                if end >= len(line) or not _fragment(line[end]):
                    break
                parts = [current, *line[i+1:end+1]]
                height = min(w.box[3] for w in (current, line[end]))
                if (any(w.confidence < MIN_CONFIDENCE for w in parts)
                        or any(not -height * 0.25 <= _gap(a, b) <= height * HYPHEN_GAP
                               for a, b in zip(parts, parts[1:]))):
                    break
                joined = _fragment(current).rstrip('-') + '-' + _fragment(line[end])
                if line[end].text.endswith(('-', '‐', '‑')):
                    joined += '-'
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


DEFAULT_PSM = 6
DEFAULT_ENLARGE = 2
DEFAULT_INVERT = 'auto'
MAX_SOURCE_BYTES = 64 << 20
MAX_SOURCE_DIMENSION = 16384
MAX_SOURCE_PIXELS = 64_000_000
MAX_PREPARED_PIXELS = 8_000_000
OCR_TIMEOUT = 3


@dataclass(frozen=True)
class Recognition:
    selection: Selection | None
    timings: dict[str, float]


def _prepare_image(path, point, enlarge, invert):
    x, y = _point(point)
    try:
        from PyQt6.QtCore import QBuffer, QIODevice, Qt
        from PyQt6.QtGui import QImage, QImageReader, QPainter, QColor
    except ImportError:
        _fail('missing_pyqt6')
    try:
        info = Path(path).stat()
        if not stat.S_ISREG(info.st_mode):
            _fail('invalid_image')
        if info.st_size > MAX_SOURCE_BYTES:
            _fail('too_large')
        reader = QImageReader(str(path))
        reader.setAutoTransform(False)
        size = reader.size()
        width, height = size.width(), size.height()
        if width <= 0 or height <= 0:
            _fail('invalid_image')
        if max(width, height) > MAX_SOURCE_DIMENSION or width*height > MAX_SOURCE_PIXELS:
            _fail('too_large')
        if not 0 <= x < width or not 0 <= y < height:
            _fail('invalid_point')
        image = reader.read()
        if image.isNull():
            _fail('invalid_image')
        # QImageReader interprets @2x filenames; this API always uses physical pixels.
        image.setDevicePixelRatio(1.0)
        crop_w, crop_h = min(width, 4096), min(height, 256)
        left = min(max(int(x)-crop_w//2, 0), width-crop_w)
        top = min(max(int(y)-crop_h//2, 0), height-crop_h)
        image = image.copy(left, top, crop_w, crop_h)
        # Sample the background without importing numpy or reading individual glyphs.
        samples = [image.pixelColor(px, py) for px in range(0, crop_w, max(1, crop_w//16))
                   for py in range(0, crop_h, max(1, crop_h//8))]
        background = sorted(samples, key=lambda c: c.lightness())[len(samples)//2]
        if background.alpha() < 128:
            background = QColor('white')
        flattened = QImage(crop_w, crop_h, QImage.Format.Format_RGB32)
        flattened.fill(background)
        painter = QPainter(flattened)
        painter.drawImage(0, 0, image)
        painter.end()
        if invert == 'auto' and background.lightness() < 128:
            flattened.invertPixels()
        scaled_w, scaled_h = round(crop_w*enlarge), round(crop_h*enlarge)
        border = 8
        if (scaled_w+2*border)*(scaled_h+2*border) > MAX_PREPARED_PIXELS:
            _fail('too_large')
        scaled = flattened.scaled(scaled_w, scaled_h, Qt.AspectRatioMode.IgnoreAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
        prepared = QImage(scaled_w+2*border, scaled_h+2*border, QImage.Format.Format_RGB32)
        prepared.fill(QColor('white'))
        painter = QPainter(prepared)
        painter.drawImage(border, border, scaled)
        painter.end()
        if scaled.isNull() or prepared.isNull():
            _fail('too_large')
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        if not prepared.save(buffer, 'PNG'):
            _fail('invalid_image')
        png = bytes(buffer.data())
        buffer.close()
        return png, Transform(left, top, scaled_w/crop_w, scaled_h/crop_h, border)
    except (OSError, TypeError, ValueError):
        _fail('invalid_image')


def recognize_image(path, point, *, psm=DEFAULT_PSM, enlarge=DEFAULT_ENLARGE,
                    invert=DEFAULT_INVERT) -> Recognition:
    if psm not in (6, 11) or enlarge not in (1, 2) or invert not in ('never', 'auto'):
        _fail('invalid_image')
    start = time.perf_counter()
    png, transform = _prepare_image(path, point, enlarge, invert)
    prepared_at = time.perf_counter()
    try:
        process = subprocess.run(['tesseract', 'stdin', 'stdout', '-l', 'eng', '--psm', str(psm), 'tsv'],
                                 input=png, capture_output=True, timeout=OCR_TIMEOUT,
                                 shell=False, check=False, env=dict(os.environ, OMP_THREAD_LIMIT='1'))
    except FileNotFoundError:
        _fail('missing_tesseract')
    except subprocess.TimeoutExpired:
        _fail('timeout')
    except OSError:
        _fail('process_failed')
    recognized_at = time.perf_counter()
    if process.returncode:
        if b'eng.traineddata' in process.stderr or b"Failed loading language 'eng'" in process.stderr:
            _fail('missing_eng')
        _fail('process_failed')
    words = parse_tsv(process.stdout, transform)
    selection = select_word(words, point)
    finished = time.perf_counter()
    return Recognition(selection, {'prepare_image': (prepared_at-start)*1000,
                                   'ocr': (recognized_at-prepared_at)*1000,
                                   'select': (finished-recognized_at)*1000,
                                   'total': (finished-start)*1000})
