"""Render public test text with the target's real Qt widget style."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def render(args):
    from PyQt6.QtCore import Qt, QT_VERSION_STR
    from PyQt6.QtGui import QFont, QFontMetricsF, QPalette, QColor, QPixmap, QPainter, QPen, QIcon
    from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QStyleFactory

    app = QApplication([])
    if args.style.lower() not in {s.lower() for s in QStyleFactory.keys()}:
        raise SystemExit('requested Qt style unavailable')
    app.setStyle(args.style)
    dark = args.theme == 'dark'
    palette = app.style().standardPalette()
    for role in (QPalette.ColorRole.Window, QPalette.ColorRole.Base, QPalette.ColorRole.Button):
        palette.setColor(role, QColor('#232629' if dark else '#fcfcfc'))
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        palette.setColor(role, QColor('#eff0f1' if dark else '#232629'))
    app.setPalette(palette)
    widget = QWidget()
    widget.setAutoFillBackground(True)
    widget.resize(640, 250)
    font = QFont('Noto Sans', args.font_size)
    widget.setFont(font)
    metrics = QFontMetricsF(font)
    texts = ['We read clear English words.', 'We break out together.', 'A well-known word appears.']
    labels = []
    for i, text in enumerate(texts):
        label = QLabel(text, widget)
        label.setGeometry(32, 20+i*56, 580, 40)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        labels.append(label)
    icon = QPushButton(widget)
    icon.setGeometry(32, 200, 28, 28)
    drawing = QPixmap(16, 16)
    drawing.fill(Qt.GlobalColor.transparent)
    painter = QPainter(drawing)
    painter.setPen(QPen(palette.color(QPalette.ColorRole.Text), 2))
    painter.drawLine(3, 3, 13, 13)
    painter.drawLine(3, 13, 13, 3)
    painter.end()
    icon.setIcon(QIcon(drawing))
    widget.show()
    app.processEvents()
    image = widget.grab().toImage()
    ratio_x, ratio_y = image.width()/widget.width(), image.height()/widget.height()
    cases = []

    def add(name, row, prefix, token, expected, compound=None):
        label = labels[row]
        x = label.x()+metrics.horizontalAdvance(prefix)+metrics.horizontalAdvance(token)/2
        y = label.y()+label.height()/2
        cases.append({'name': name, 'point': [x*ratio_x, y*ratio_y], 'word': expected,
                      'line_tokens': texts[row].split(), 'compound': compound})

    add('word', 0, 'We read clear ', 'English', 'english')
    # Ink bearings differ from advance widths: derive the actual inter-glyph gap.
    gap_left = 32+metrics.horizontalAdvance('We read ')+metrics.tightBoundingRect('clear').right()
    gap_right = 32+metrics.horizontalAdvance('We read clear ')+metrics.tightBoundingRect('English').left()
    x = gap_left + (gap_right-gap_left)*0.85
    cases.append({'name': 'between', 'point': [x*ratio_x, 40*ratio_y], 'word': 'english',
                  'line_tokens': texts[0].split(), 'compound': None,
                  'layout_gap': [gap_left*ratio_x, gap_right*ratio_x]})
    add('compound', 1, 'We ', 'break', 'break', 'break out')
    add('hyphen', 2, 'A ', 'well-known', 'well-known')
    for name, point in (('blank', (600, 220)), ('icon', (46, 214))):
        cases.append({'name': name, 'point': [point[0]*ratio_x, point[1]*ratio_y],
                      'word': None, 'line_tokens': [], 'compound': None})
    filename = f'images/{args.theme}-{args.scale:g}-{args.font_size}.png'
    target = args.output / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(target)):
        raise SystemExit('fixture image write failed')
    result = {'path': filename, 'theme': args.theme, 'scale': args.scale,
              'font_size': args.font_size, 'font_family': font.family(),
              'qt': QT_VERSION_STR, 'size': [image.width(), image.height()], 'cases': cases}
    widget.close()
    print(json.dumps(result))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--style', default='Breeze')
    parser.add_argument('--scale', type=float)
    parser.add_argument('--theme', choices=('light', 'dark'))
    parser.add_argument('--font-size', type=int)
    args = parser.parse_args()
    if args.scale:
        render(args)
        return
    images = []
    for theme in ('light', 'dark'):
        for scale in (1, 1.25, 1.5, 2):
            for font in (9, 16):
                env = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_SCALE_FACTOR=str(scale))
                run = subprocess.run([sys.executable, __file__, '--output', str(args.output),
                                      '--style', args.style, '--theme', theme, '--scale', str(scale),
                                      '--font-size', str(font)], env=env, capture_output=True,
                                     text=True, timeout=30, check=True)
                images.append(json.loads(run.stdout))
    manifest = {'version': 1, 'source': 'rendered-widget', 'style': args.style,
                'palette': 'explicit Breeze light/dark colors',
                'provenance': 'Qt widget grabs of fixed public text; not live desktop captures',
                'images': images}
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(f'Rendered {len(images)} images, {sum(len(i["cases"]) for i in images)} cases')


if __name__ == '__main__':
    main()
