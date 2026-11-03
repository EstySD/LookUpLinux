"""Yomitan reader and normal offline dictionary workflow contracts."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile

from lookup import dicts, doctor, translate, yomitan
from lookup.config import Config


def row(word='cat', definitions=None):
    return [word, '', '', '', 0, ['кот'] if definitions is None else definitions, 0, '']


def write(path, rows=None, index=None, banks=None):
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('index.json', json.dumps(index if index is not None else {'format': 3, 'title': 'Test'}))
        for name, value in (banks if banks is not None else {'term_bank_1.json': [row()] if rows is None else rows}).items():
            archive.writestr(name, json.dumps(value))


class YomitanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'test.zip'

    def test_structured_content_and_duplicates(self):
        write(self.path, [row(definitions=[{'type': 'structured-content', 'content': [
            {'tag': 'div', 'content': ['кот', {'tag': 'span', 'content': ' домашний'}]},
            {'tag': 'div', 'content': 'кошка'},
            {'tag': 'img', 'path': '../../secret'},
            {'tag': 'script', 'content': 'evil()'}]}]), row(definitions=['<b>котик</b>'])])
        reader = yomitan.open_yomitan(self.path)
        self.addCleanup(reader.close)
        self.assertEqual(reader.entry_count, 2)
        self.assertEqual(reader.skipped_entries, 0)
        self.assertTrue(reader.has('CAT'))
        articles = reader.lookup(' CAT ')
        self.assertEqual([a.text for a in articles], ['кот домашний\n\nкошка', 'котик'])
        self.assertEqual(reader.lookup('missing'), [])
        self.assertEqual(doctor._probe(self.path, 'yomitan'), {'entries': 2, 'skipped': 0})

    def test_invalid_archives(self):
        cases = [({'index': {'format': 2, 'title': 'Test'}}, 'unsupported'),
                 ({'index': {'format': 3, 'title': ''}}, 'corrupt'),
                 ({'rows': []}, 'empty'), ({'rows': [['cat']]}, 'corrupt'),
                 ({'banks': {'term_bank_2.json': [row()]}}, 'corrupt'),
                 ({'rows': [row(definitions=[{'type': 'future'}])]}, 'unsupported'),
                 ({'banks': {}}, 'empty')]
        for args, reason in cases:
            with self.subTest(args=args):
                write(self.path, **args)
                with self.assertRaises(dicts.DictError) as error:
                    yomitan.open_yomitan(self.path)
                self.assertEqual(error.exception.reason, reason)
        self.path.write_bytes(b'not zip')
        with self.assertRaises(dicts.DictError):
            yomitan.open_yomitan(self.path)

    def test_limits_and_duplicate_members(self):
        write(self.path)
        for constant in ('MAX_ARCHIVE_BYTES', 'MAX_TOTAL_BYTES', 'MAX_BANK_BYTES', 'MAX_ENTRIES', 'MAX_MEMBERS'):
            with self.subTest(constant=constant), mock.patch.object(yomitan, constant, 0):
                with self.assertRaises(dicts.DictError) as error:
                    yomitan.open_yomitan(self.path)
                self.assertEqual(error.exception.reason, 'too_large')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with zipfile.ZipFile(self.path, 'a') as archive:
                archive.writestr('index.json', '{}')
        with self.assertRaises(dicts.DictError):
            yomitan.open_yomitan(self.path)

    def test_normal_lookup_reconnect_disable_and_isolation(self):
        write(self.path)
        other = self.root / 'other.zip'
        write(other, [row('dog', ['собака'])])
        (self.root / 'bad.zip').write_bytes(b'bad')
        cfg = Config(dictionaries=(('test.zip', True), ('other.zip', True)))
        with dicts.open_all(config=cfg, roots=[self.root]) as dictionaries:
            self.assertEqual(dictionaries.problems, [('bad.zip', 'corrupt')])
            self.assertEqual(translate.lookup('Cat', dictset=dictionaries, online=False, save=False).articles[0].text, 'кот')
            self.assertEqual([r.id for r in dictionaries.info() if r.status == 'ok'], ['test.zip', 'other.zip'])
        write(self.path, [row(definitions=['кошка'])])
        with dicts.open_all(config=cfg, roots=[self.root]) as dictionaries:
            self.assertEqual(dictionaries.find('cat').articles[0].text, 'кошка')
            self.assertEqual(dictionaries.find('dog').articles[0].text, 'собака')
        with dicts.open_all(config=Config(dictionaries=(('test.zip', False),)), roots=[self.root]) as dictionaries:
            self.assertFalse(dictionaries.find('cat'))
            self.assertTrue(dictionaries.find('dog'))
        self.path.write_bytes(b'broken replacement')
        with dicts.open_all(config=cfg, roots=[self.root]) as dictionaries:
            self.assertTrue(dictionaries.find('dog'))
            self.assertFalse(dictionaries.find('cat'))

    def test_settings_show_archive_error(self):
        from lookup.settings_gui import _dictionary_rows
        self.path.write_bytes(b'broken')
        with mock.patch.object(dicts, 'dict_roots', return_value=[self.root]), mock.patch('lookup.config.load', return_value=Config()):
            rows = _dictionary_rows()
        self.assertEqual(rows[0]['id'], 'test.zip')
        self.assertIn('повреждён', rows[0]['name'])

    def test_source_cross_reference_uses_existing_resolution(self):
        write(self.path, [row('hello', ['= hallo']), row('hallo', ['привет'])])
        with dicts.open_all(config=Config(), roots=[self.root]) as dictionaries:
            result = translate.lookup('hello', dictset=dictionaries, online=False, save=False)
            self.assertEqual(result.articles[0].text, 'привет')
            self.assertEqual(result.articles[0].lemma_of, 'hallo')


if __name__ == '__main__':
    unittest.main()
