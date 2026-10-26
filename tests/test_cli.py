"""Observable CLI behavior, including database and network degradation."""
import contextlib
import io
import json
import os
import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from lookup.__main__ import main
from lookup.online import OnlineResult, TranslateError
from lookup.store import open_store
from tests._stardict_writer import write_stardict
from tests._support import make_tempdir, forbid_network


def answer(text):
    return OnlineResult('google', 'gtx', text, (), None, None, 'en')


class CliCase(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)
        self.network = forbid_network(self)
        write_stardict(self.root / 'dicts', 'mueller', [
            ('run', '[rʌn] 1. _n. бег 2. _v. бежать'),
            ('ran', '[ræn] _p. от run 2'), ('book', '_n. книга'),
        ], bookname='Mueller')

    def call(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(args))
        return code, out.getvalue(), err.getvalue()

    def rows(self):
        with contextlib.closing(open_store()) as conn:
            return conn.execute('SELECT word, count, lemma, context FROM words').fetchall()


class CliLookupTests(CliCase):
    def test_gui_actions_dispatch_before_dictionary_database_work(self):
        for action in ('--app','--trigger'):
            with mock.patch('lookup.gui.run',return_value=0) as gui, \
                 mock.patch('lookup.__main__.dicts.open_all') as dictionaries, \
                 mock.patch('lookup.__main__.open_store') as database:
                self.assertEqual(self.call(action),(0,'',''))
                gui.assert_called_once_with(trigger=action=='--trigger')
                dictionaries.assert_not_called()
                database.assert_not_called()
        for extra in (('--offline',),('--no-save',),('--context','private'),('--at','1,2')):
            with mock.patch('lookup.gui.run') as gui:
                self.assertEqual(self.call('--trigger',*extra)[0],2)
                gui.assert_not_called()

    def test_gui_startup_errors_are_fixed_and_private(self):
        for error,expected in ((ImportError('private path'),'python-pyqt6'),(RuntimeError('private token'),'KDE Wayland')):
            with mock.patch('lookup.gui.run',side_effect=error):
                code,out,err=self.call('--trigger')
            self.assertEqual((code,out),(1,''))
            self.assertIn(expected,err)
            self.assertNotIn('private',err)

    def test_offline_article_lemma_count_and_no_save(self):
        code, out, err = self.call('--word', 'run', '--offline')
        self.assertEqual((code, err), (0, ''))
        for part in ['Mueller', 'run', 'rʌn', 'n:', 'v:', 'бежать', 'Записано: искали 1 раз']:
            self.assertIn(part, out)
        self.assertEqual(tuple(self.rows()[0])[:3], ('run', 1, None))
        code, out, _ = self.call('--word', 'ran', '--offline')
        self.assertEqual(code, 0)
        self.assertIn('ran → run', out)
        self.assertIn(('ran', 1, 'run', None), [tuple(r) for r in self.rows()])
        self.assertEqual(self.call('--word', 'books', '--offline', '--no-save')[0], 0)
        self.assertEqual(len(self.rows()), 2)
        self.network.assert_not_called()

    def test_missing_invalid_sentence_and_usage(self):
        code, out, _ = self.call('--word', 'zzzz', '--offline')
        self.assertEqual(code, 1)
        self.assertIn('Не найдено', out)
        self.assertIn('выключен', out)
        self.assertEqual(len(self.rows()), 1)
        self.assertEqual(self.call('--word', '12345')[0], 1)
        self.assertIn('Не слово', self.call('--word', '12345')[1])
        self.assertEqual(len(self.rows()), 1)
        for args in [(), ('--word', 'run', '--text', 'other'), ('--word', 'one two three four five'), ('--unknown',)]:
            code, out, err = self.call(*args)
            self.assertEqual((code, out), (2, ''))
            self.assertIn('usage:', err)
        with mock.patch('lookup.online.translate_online', return_value=answer('быстрая лиса')):
            code, out, err = self.call('--text', 'The quick brown fox jumps.')
        self.assertEqual((code, err), (0, ''))
        self.assertIn('быстрая лиса', out)
        self.assertEqual(len(self.rows()), 1)

    def test_online_cache_and_reasons(self):
        with mock.patch('lookup.online.translate_online', return_value=answer('перевод')) as online:
            code, out, _ = self.call('--word', 'other')
            self.assertEqual(code, 0)
            self.assertIn('Онлайн', out)
            self.assertIn('перевод', out)
            online.assert_called_once()
        with mock.patch('lookup.online.translate_online', side_effect=AssertionError('cache missed')):
            self.assertIn('из кэша', self.call('--word', 'other')[1])
        for reason, message in [('no_network', 'нет сети'), ('timeout', 'онлайн-перевод не ответил вовремя'), ('blocked', 'онлайн-перевод заблокирован'), ('bad_response', 'онлайн-перевод вернул непонятный ответ'), ('not_found', 'Не найдено')]:
            with mock.patch('lookup.online.translate_online', side_effect=TranslateError(reason)):
                code, out, _ = self.call('--word', 'unknown')
            self.assertEqual(code, 1)
            self.assertIn(message, out)

    def test_context_config_and_timing(self):
        sentence = 'I run fast every day.'
        with mock.patch('lookup.online.translate_online', return_value=answer('Я бегаю быстро.')):
            code, out, _ = self.call('--word', 'run', '--context', sentence)
        self.assertEqual(code, 0)
        self.assertIn('Предложение: Я бегаю быстро.', out)
        self.assertEqual(self.rows()[0][3], sentence)
        with mock.patch('lookup.online.translate_online', side_effect=TranslateError('blocked')):
            code, out, _ = self.call('--word', 'run', '--context', 'Another sentence is used here.')
        self.assertEqual(code, 0)
        self.assertIn('бежать', out)
        self.assertIn('перевод недоступен (онлайн-перевод заблокирован)', out)
        self.assertIn('выключен', self.call('--word', 'run', '--context', sentence, '--offline')[1])
        path = Path(os.environ['LOOKUP_CONFIG'])
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'online': False}), encoding='utf-8')
        with mock.patch('lookup.online.translate_online', side_effect=AssertionError('disabled')):
            self.assertEqual(self.call('--word', 'run')[0], 0)
        with mock.patch.dict(os.environ, {'LOOKUP_TIMING': '1'}):
            err = self.call('--word', 'run', '--offline')[2]
        self.assertEqual(len(err.splitlines()), 1)
        self.assertTrue(err.startswith('timing:'))
        for key in ['open_dicts', 'open_db', 'dicts', 'online', 'cache', 'context', 'db', 'total']:
            self.assertIn(key + '=', err)

    def test_database_errors_do_not_hide_dictionary(self):
        path = Path(os.environ['LOOKUP_DB'])
        path.parent.mkdir(parents=True)
        path.write_text('private-sentinel', encoding='utf-8')
        code, out, err = self.call('--word', 'run', '--offline')
        self.assertEqual(code, 0)
        self.assertIn('бежать', out)
        self.assertIn('DatabaseError', err)
        self.assertNotIn('private-sentinel', err)
        path.unlink()
        with contextlib.closing(sqlite3.connect(path)) as conn:
            conn.execute('PRAGMA user_version=999')
        code, out, err = self.call('--word', 'run', '--offline')
        self.assertEqual(code, 0)
        self.assertIn('нов', err)


class CliListDictsTests(CliCase):
    def test_listing_never_opens_database(self):
        (self.root / 'dicts/broken.mdx').write_bytes(b'bad')
        config = Path(os.environ['LOOKUP_CONFIG'])
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({'dictionaries': [{'id': 'mueller.ifo', 'enabled': False}]}), encoding='utf-8')
        code, out, err = self.call('--list-dicts')
        self.assertEqual((code, err), (0, ''))
        for part in ['mueller.ifo', 'stardict', 'выключен', 'повреждён', str(self.root / 'dicts')]:
            self.assertIn(part, out)
        self.assertFalse(Path(os.environ['LOOKUP_DB']).exists())
        with mock.patch.dict(os.environ, {'LOOKUP_DICTS': str(self.root / 'missing')}):
            self.assertIn('не найдены', self.call('--list-dicts')[1])


class CliSubprocessTests(CliCase):
    def test_utf8_and_stdlib_entrypoint(self):
        for flags in [[], ['-S']]:
            proc = subprocess.run([sys.executable, *flags, '-m', 'lookup', '--word', 'run', '--offline', '--no-save'], capture_output=True, timeout=30)
            self.assertEqual((proc.returncode, proc.stderr), (0, b''))
            self.assertIn('rʌn', proc.stdout.decode('utf-8'))
            self.assertIn('бежать', proc.stdout.decode('utf-8'))
        proc = subprocess.run([sys.executable, '-m', 'lookup'], capture_output=True, timeout=30)
        self.assertEqual(proc.returncode, 2)
