"""Image CLI side effects, real dictionary/counting, optional target OCR."""
import contextlib
import io
import json
import os
import sqlite3
import unittest
from pathlib import Path
from unittest import mock

from lookup import ocr, translate
from lookup.__main__ import main
from tests._stardict_writer import write_stardict
from tests._support import make_tempdir, forbid_network


class OcrCliTests(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)
        self.network = forbid_network(self)
        write_stardict(self.root/'dicts', 'test', [('break', 'ломать'), ('break out', 'вырваться'),
                                                ('english', 'английский'), ('well-known', 'известный')])

    def call(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(args))
        return code, out.getvalue(), err.getvalue()

    def selection(self, word='break', candidates=('break out',)):
        return ocr.Recognition(ocr.Selection(word, 'We break out together.', candidates,
                                             (10, 10, 30, 12), 90),
                               {'prepare_image': 1, 'ocr': 2, 'select': 1, 'total': 4})

    def rows(self):
        with contextlib.closing(sqlite3.connect(os.environ['LOOKUP_DB'])) as conn:
            return conn.execute('SELECT word,count,context FROM words ORDER BY word').fetchall()

    def test_compound_saved_once_and_repeated(self):
        with mock.patch('lookup.__main__.ocr.recognize_image', return_value=self.selection()):
            with mock.patch('lookup.__main__.translate.lookup', wraps=translate.lookup) as lookup:
                for count in (1, 2):
                    code, out, err = self.call('--image', 'shot.png', '--at', '15,15', '--offline')
                    self.assertEqual((code, err), (0, ''))
                    self.assertIn('вырваться', out)
                    self.assertIn('Строка: We break out together.', out)
                    self.assertEqual(self.rows(), [('break out', count, 'We break out together.')])
                self.assertEqual(lookup.call_count, 2)
                self.assertTrue(all(c.args == ('break out',) for c in lookup.call_args_list))
        self.network.assert_not_called()

    def test_fallback_hyphen_no_save_and_timing(self):
        for word, candidates, expected in (('break', ('break away',), 'ломать'),
                                           ('well-known', (), 'известный')):
            with mock.patch('lookup.__main__.ocr.recognize_image', return_value=self.selection(word, candidates)):
                with mock.patch.dict(os.environ, LOOKUP_TIMING='1'):
                    code, out, err = self.call('--image', 'shot.png', '--at', '15,15', '--offline', '--no-save')
            self.assertEqual(code, 0)
            self.assertIn(expected, out)
            self.assertIn('prepare_image=', err)
            self.assertIn('ocr=', err)
            self.assertIn('compound=', err)
            self.assertEqual(self.rows(), [])

    def test_rejected_ocr_has_no_database_dictionary_or_network_side_effect(self):
        recognition = ocr.Recognition(None, {'prepare_image': 1, 'ocr': 2, 'select': 1, 'total': 4})
        with mock.patch('lookup.__main__.ocr.recognize_image', return_value=recognition):
            with mock.patch('lookup.__main__.open_store') as store, mock.patch('lookup.__main__.dicts.open_all') as dictionaries:
                code, out, err = self.call('--image', 'shot.png', '--at', '15,15')
                store.assert_not_called()
                dictionaries.assert_not_called()
        self.assertEqual((code, out, err), (1, 'Не найдено.\n', ''))
        self.assertFalse(Path(os.environ['LOOKUP_DB']).exists())
        self.network.assert_not_called()

    def test_usage_and_fixed_ocr_errors(self):
        for args in (('--image', 'shot.png'), ('--word', 'break', '--at', '1,2'),
                     ('--image', 'shot.png', '--at', 'nan,2'),
                     ('--image', 'shot.png', '--at', '1,2,3'),
                     ('--image', 'shot.png', '--at', '1,2', '--context', 'override')):
            self.assertEqual(self.call(*args)[0], 2)
        for reason in ('timeout', 'missing_tesseract', 'missing_pyqt6', 'missing_eng', 'bad_output',
                       'invalid_image', 'invalid_point', 'process_failed', 'too_large'):
            with mock.patch('lookup.__main__.ocr.recognize_image', side_effect=ocr.OcrError(reason)):
                code, out, err = self.call('--image', 'private-secret.png', '--at', '1,2')
            self.assertEqual(code, 2 if reason == 'invalid_point' else 1)
            self.assertNotIn('private-secret', out+err)
            self.assertNotIn('Traceback', err)
            self.assertFalse(Path(os.environ['LOOKUP_DB']).exists())

    @unittest.skipUnless(os.environ.get('LOOKUP_TEST_OCR') == '1', 'opt-in target OCR fixture gate')
    def test_actual_breeze_fixture_cli(self):
        root = Path(__file__).parent/'fixtures'/'ocr'
        manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
        for image in manifest['images']:
            for case in image['cases']:
                with self.subTest(image=image['path'], case=case['name']):
                    x, y = case['point']
                    with mock.patch.dict(os.environ, LOOKUP_TIMING='1'):
                        code, out, err = self.call('--image', str(root/image['path']), '--at',
                                                   f'{x},{y}', '--offline', '--no-save')
                    self.assertEqual(code, 0 if case['word'] else 1, out+err)
                    if case['word']:
                        self.assertIn(case['compound'] or case['word'], out)
                        self.assertIn('Строка:', out)
                    self.assertIn('ocr=', err)
        self.network.assert_not_called()
