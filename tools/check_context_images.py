"""Generate owned public scenes and check production OCR, never synthetic TSV."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lookup import ocr


def accepted(case, selection):
    return bool(selection and selection.word == case['word'] and
                selection.context == case['context'] and
                selection.span == tuple(case['span']) and
                selection.context_complete == case['complete'])


def scenes():
    two = ['They sat on the bank', 'of the quiet river.']
    return [
        dict(name='two-lines', lines=two, target=(0, 'bank')),
        dict(name='three-lines', lines=['They sat on the bank', 'of the river and watched',
                                      'the ducks swim past.'], target=(0, 'bank')),
        dict(name='four-lines', lines=['They sat on the bank', 'of the river and watched',
                                     'the ducks swim past', 'until the sun set.'], target=(1, 'river')),
        dict(name='repeated-first', lines=['The bank of the river', 'stands next to the bank with money.'], target=(0, 'bank')),
        dict(name='repeated-second', lines=['The bank of the river', 'stands next to the bank with money.'], target=(1, 'bank')),
        dict(name='two-sentences', lines=['The bank approved a loan.', 'They sat by the bank of the river.'],
             target=(1, 'bank'), context='They sat by the bank of the river.'),
        dict(name='hyphen-first', lines=['They showed the trans-', 'lation of this word.'],
             target=(0, 'trans-'), context='They showed the translation of this word.', word='translation'),
        dict(name='hyphen-second', lines=['They showed the trans-', 'lation of this word.'],
             target=(1, 'lation'), context='They showed the translation of this word.', word='translation'),
        dict(name='columns', lines=two, target=(0, 'bank'),
             extras=[('Unrelated nearby column.', 700, 20, 18), ('Other unrelated words.', 700, 45, 18)]),
        dict(name='caption', lines=two, target=(0, 'bank'), extras=[('Caption below the scene.', 20, 95, 12)]),
        dict(name='dialogue', lines=['Alice: They reached the bank.', 'Bob: I saw the river.'],
             target=(0, 'bank.'), context='Alice: They reached the bank.', span_text='bank.'),
        dict(name='fragment', lines=['walking near the bank', 'of the river without an end'],
             target=(0, 'bank'), complete=False),
        dict(name='ambiguous-boundary', lines=['They waited near the bank', 'another unrelated fragment'],
             target=(0, 'bank'), offsets=[0, 180], context='They waited near the bank', complete=False),
    ]


def render(scene, path, scale, dark):
    from PyQt6.QtCore import QPointF
    from PyQt6.QtGui import QColor, QFont, QFontMetricsF, QImage, QPainter

    image = QImage(round(1100*scale), round(124*scale), QImage.Format.Format_RGB32)
    image.fill(QColor('#232629' if dark else '#ffffff'))
    painter = QPainter(image)
    painter.scale(scale, scale)
    painter.setPen(QColor('#eff0f1' if dark else '#111111'))
    font = QFont('DejaVu Sans')
    font.setPixelSize(18)
    painter.setFont(font)
    metrics = QFontMetricsF(font)
    target_row, target_token = scene['target']
    point = None
    for row, text in enumerate(scene['lines']):
        x, y = 20 + scene.get('offsets', [0]*len(scene['lines']))[row], 20+row*25
        painter.drawText(QPointF(x, y), text)
        if row == target_row:
            offset = text.index(target_token)
            point = ((x+metrics.horizontalAdvance(text[:offset])+metrics.horizontalAdvance(target_token)/2)*scale,
                     (y-metrics.ascent()/2)*scale)
    for text, x, y, size in scene.get('extras', []):
        extra_font = QFont(font)
        extra_font.setPixelSize(size)
        painter.setFont(extra_font)
        painter.drawText(QPointF(x, y), text)
    painter.end()
    if not image.save(str(path)):
        raise RuntimeError('fixture_write_failed')
    context = scene.get('context', '\n'.join(scene['lines']))
    span_text = scene.get('span_text', scene.get('word', target_token))
    # Fixture expectations are authored from the scene, independent of OCR output.
    start = context.rfind(span_text) if scene['name'] == 'repeated-second' else context.index(span_text)
    return dict(name=scene['name'], scale=scale, theme='dark' if dark else 'light',
                path=path.name, point=point, word=scene.get('word', target_token.rstrip('.')),
                context=context, span=[start, start+len(span_text)], complete=scene.get('complete', True))


def run(output, scales=(1, 1.25, 1.5, 2), themes=('light', 'dark')):
    if not shutil.which('tesseract'):
        raise RuntimeError('missing_tesseract')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PyQt6.QtWidgets import QApplication
    application = QApplication.instance() or QApplication([])
    output.mkdir(parents=True, exist_ok=True)
    cases = []
    for theme in themes:
        for scale in scales:
            for scene in scenes():
                path = output/f"{scene['name']}-{theme}-{scale:g}.png"
                case = render(scene, path, scale, theme == 'dark')
                try:
                    result = ocr.recognize_image(path, case['point'])
                    selected = result.selection
                    case.update(passed=accepted(case, selected), actual=None if not selected else
                                dict(word=selected.word, context=selected.context, span=selected.span,
                                     complete=selected.context_complete), timings=result.timings)
                except ocr.OcrError as error:
                    case.update(passed=False, error=error.reason)
                cases.append(case)
    report = dict(acceptance='agent', total=len(cases),
                  passed=sum(case['passed'] for case in cases),
                  failed=sum(not case['passed'] for case in cases), cases=cases)
    (output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output)
    print(json.dumps({key: report[key] for key in ('acceptance', 'total', 'passed', 'failed')}))
    return bool(report['failed'])


if __name__ == '__main__':
    raise SystemExit(main())
