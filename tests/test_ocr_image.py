"""Image/process boundary tests, separate from real target calibration."""
import json
import math
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from lookup import ocr
from tests._support import make_tempdir
from tests.test_ocr import tsv

try:
    from PyQt6.QtGui import QImage, QColor
except ImportError:
    QImage = None


@unittest.skipIf(QImage is None, 'PyQt6 unavailable')
class ImageTests(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)
        self.image = self.root / 'test.png'
        image = QImage(200, 80, QImage.Format.Format_RGB32)
        image.fill(QColor('white'))
        image.save(str(self.image))

    def recognize(self, **kwargs):
        return ocr.recognize_image(self.image, (25, 25), **kwargs)

    def test_memory_png_process_and_transform(self):
        output = tsv((5, 1, 1, 1, 1, 1, 48, 48, 60, 20, 95, 'run'))
        with mock.patch('lookup.ocr.subprocess.run', return_value=subprocess.CompletedProcess([], 0, output, b'')) as run:
            result = self.recognize(enlarge=2)
        self.assertEqual(result.selection.word, 'run')
        self.assertEqual(result.selection.box, (20, 20, 30, 10))
        argv = run.call_args.args[0]
        self.assertEqual(argv[:6], ['tesseract', 'stdin', 'stdout', '-l', 'eng', '--psm'])
        self.assertEqual(argv[-1], 'tsv')
        self.assertFalse(run.call_args.kwargs['shell'])
        self.assertEqual(run.call_args.kwargs['env']['OMP_THREAD_LIMIT'], '1')
        self.assertEqual(run.call_args.kwargs['timeout'], 3)
        self.assertTrue(run.call_args.kwargs['input'].startswith(b'\x89PNG'))
        self.assertEqual(set(result.timings), {'prepare_image', 'ocr', 'select', 'total'})
        self.assertEqual(list(self.root.glob('*.png')), [self.image])

    def test_invalid_input_before_process(self):
        for point, reason in (((math.nan, 1), 'invalid_point'), ((-1, 1), 'invalid_point'),
                              ((200, 1), 'invalid_point'), ((1, 80), 'invalid_point')):
            with mock.patch('lookup.ocr.subprocess.run') as run:
                with self.assertRaises(ocr.OcrError) as error:
                    ocr.recognize_image(self.image, point)
                self.assertEqual(error.exception.reason, reason)
                run.assert_not_called()
        self.image.write_bytes(b'secret-invalid-image')
        with self.assertRaises(ocr.OcrError) as error:
            self.recognize()
        self.assertEqual(error.exception.reason, 'invalid_image')

    def test_transport_errors_are_fixed_and_private(self):
        cases = [(FileNotFoundError('secret'), 'missing_tesseract'),
                 (subprocess.TimeoutExpired('secret', 3, b'secret', b'secret'), 'timeout'),
                 (subprocess.CompletedProcess([], 1, b'secret', b'secret'), 'process_failed'),
                 (subprocess.CompletedProcess([], 1, b'', b'Error opening data file eng.traineddata'), 'missing_eng'),
                 (subprocess.CompletedProcess([], 0, b'secret', b''), 'bad_output')]
        for outcome, reason in cases:
            options = {'side_effect': outcome} if isinstance(outcome, Exception) else {'return_value': outcome}
            with mock.patch('lookup.ocr.subprocess.run', **options):
                with self.assertRaises(ocr.OcrError) as caught:
                    self.recognize()
            self.assertEqual(str(caught.exception), reason)
            self.assertTrue(caught.exception.__suppress_context__)

    def test_dark_crop_edge_and_no_word(self):
        image = QImage(5000, 400, QImage.Format.Format_RGB32)
        image.fill(QColor('black'))
        image.save(str(self.image))
        with mock.patch('lookup.ocr.subprocess.run', return_value=subprocess.CompletedProcess([], 0, tsv(), b'')):
            result = ocr.recognize_image(self.image, (4999, 399), enlarge=2)
        self.assertIsNone(result.selection)
        self.assertGreaterEqual(result.timings['ocr'], 0)

    def test_resource_caps(self):
        with mock.patch.object(ocr, 'MAX_SOURCE_BYTES', 1):
            with self.assertRaises(ocr.OcrError) as caught:
                self.recognize()
        self.assertEqual(caught.exception.reason, 'too_large')
        with mock.patch.object(ocr, 'MAX_PREPARED_PIXELS', 10):
            with self.assertRaises(ocr.OcrError) as caught:
                self.recognize()
        self.assertEqual(caught.exception.reason, 'too_large')

    def test_dimensions_checked_before_decode(self):
        from PyQt6.QtCore import QSize
        reader = mock.Mock()
        reader.size.return_value = QSize(16385, 10)
        with mock.patch('PyQt6.QtGui.QImageReader', return_value=reader):
            with self.assertRaises(ocr.OcrError) as caught:
                self.recognize()
        self.assertEqual(caught.exception.reason, 'too_large')
        reader.read.assert_not_called()

    def test_transparency_is_flattened_in_memory(self):
        transparent = QImage(200, 80, QImage.Format.Format_ARGB32)
        transparent.fill(0)
        transparent.save(str(self.image))
        png, transform = ocr._prepare_image(self.image, (25, 25), 2, 'auto')
        prepared = QImage.fromData(png)
        color = prepared.pixelColor(30, 30)
        self.assertEqual((color.red(), color.alpha()), (255, 255))
        self.assertEqual(transform.original_xy(58, 58), (25, 25))

    def test_at_2x_filename_keeps_physical_pixels(self):
        from PyQt6.QtGui import QPainter
        source = QImage(200, 80, QImage.Format.Format_RGB32)
        source.fill(QColor('white'))
        painter = QPainter(source)
        painter.fillRect(100, 20, 20, 20, QColor('black'))
        painter.end()
        path = self.root/'sample@2x.png'
        source.save(str(path))
        png, transform = ocr._prepare_image(path, (110, 30), 1, 'never')
        prepared = QImage.fromData(png)
        self.assertEqual(prepared.pixelColor(118, 38).red(), 0)
        self.assertEqual(prepared.pixelColor(63, 23).red(), 255)
        self.assertEqual(transform.original_xy(118, 38), (110, 30))


class CalibrationTests(unittest.TestCase):
    def test_line_check_preserves_order_and_repeated_words(self):
        from tools.calibrate_ocr import evaluate
        image = {'path': 'public.png', 'cases': [
            {'name': 'repeated', 'point': [1, 1], 'word': 'go',
             'line_tokens': ['go', 'go', 'now'], 'compound': None}]}
        for actual in ('go now', 'now go go'):
            recognition = ocr.Recognition(ocr.Selection('go', actual, (), (0, 0, 2, 2), 90), {'total': 1})
            with mock.patch('lookup.ocr.recognize_image', return_value=recognition):
                result = evaluate(Path('.'), [image], 6, 2, 'auto')
            self.assertEqual(result['passed'], 0)


class FixtureManifestTests(unittest.TestCase):
    def test_manifest_integrity(self):
        root = Path(__file__).parent / 'fixtures' / 'ocr'
        manifest = root / 'manifest.json'
        if not manifest.exists():
            self.skipTest('target Breeze fixtures not generated yet')
        data = json.loads(manifest.read_text(encoding='utf-8'))
        self.assertEqual(data['source'], 'rendered-widget')
        self.assertEqual(data['style'].lower(), 'breeze')
        images = data['images']
        combinations = {(row['theme'], row['scale'], row['font_size']) for row in images}
        self.assertEqual(len(combinations), 16)
        for row in images:
            self.assertTrue((root / row['path']).is_file())
            self.assertGreaterEqual(len(row['cases']), 6)
            for case in row['cases']:
                self.assertEqual(len(case['point']), 2)
                if case['name'] == 'between':
                    left, right = case['layout_gap']
                    self.assertLess(left, case['point'][0])
                    self.assertLess(case['point'][0], right)
                    self.assertGreater(case['point'][0], (left+right)/2)
