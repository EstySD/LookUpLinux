"""Opt-in real Mueller 7 verification; third-party files stay outside the repo."""
import os
import unittest
from pathlib import Path

from lookup.config import Config
from lookup.dicts import open_all

ROOT = os.environ.get('LOOKUP_TEST_DICTS')
AVAILABLE = bool(ROOT and Path(ROOT).is_dir() and next(Path(ROOT).rglob('mueller7.ifo'), None))


@unittest.skipUnless(AVAILABLE, 'Set LOOKUP_TEST_DICTS to a directory containing mueller7.ifo')
class MuellerSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dictionaries = open_all(Config(), [Path(ROOT)])
        cls.addClassCleanup(cls.dictionaries.close)

    def test_metadata_and_run(self):
        row = next(i for i in self.dictionaries.info() if i.id.endswith('mueller7.ifo'))
        self.assertEqual((row.entries, row.skipped, row.status), (46231, 1, 'ok'))
        article = self.dictionaries.find('run').articles[0]
        self.assertEqual(article.transcription, 'rʌn')
        self.assertTrue({'n', 'v'} <= {pos for pos, _ in article.senses})

    def test_base_forms(self):
        for word, lemma in [('ran', 'run'), ('went', 'go'), ('men', 'man'), ('running', 'run'), ('books', 'book'), ('stopped', 'stop'), ('boxes', 'box')]:
            with self.subTest(word=word):
                self.assertEqual(self.dictionaries.find(word).lemma, lemma)
        for word in ('better', 'news'):
            self.assertIsNone(self.dictionaries.find(word).lemma)
        self.assertFalse(self.dictionaries.find('break out'))
