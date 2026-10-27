"""Actual image acceptance is distinct from portable geometry tests."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

from lookup.ocr import Selection


def harness():
    spec = importlib.util.spec_from_file_location('context_images', Path(__file__).parents[1]/'tools/check_context_images.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AcceptanceTests(unittest.TestCase):
    def test_wrong_context_occurrence_and_fragment_fail(self):
        check = harness().accepted
        case = dict(word='bank', context='The bank by the bank.', span=[16,20], complete=True)
        good = Selection('bank', '', (), (0,0,1,1), 90, case['context'], (16,20), True)
        self.assertTrue(check(case, good))
        for result in (None,
                       Selection('bank', '', (), (0,0,1,1), 90, case['context'], (4,8), True),
                       Selection('bank', '', (), (0,0,1,1), 90, 'The bank.', (4,8), True),
                       Selection('bank', '', (), (0,0,1,1), 90, case['context'], (16,20), False)):
            self.assertFalse(check(case, result))

    @unittest.skipUnless(shutil.which('tesseract') and importlib.util.find_spec('PyQt6'),
                         'actual OCR requires Tesseract and PyQt6')
    def test_actual_control_images(self):
        with tempfile.TemporaryDirectory() as output:
            report = harness().run(Path(output), scales=(1,), themes=('light',))
        self.assertGreaterEqual(report['total'], 10)
        self.assertEqual(report['failed'], 0, report['cases'])
