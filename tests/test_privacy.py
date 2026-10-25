"""Core modules neither print nor log, even on hostile inputs and transport errors."""
import ast
import contextlib
import io
import logging
import os
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from lookup import dicts, config, online, translate
from lookup.store import open_store
from tests._support import make_tempdir

SENTINEL = 'zxqv-secret-word'


class PrivacyTests(unittest.TestCase):
    def setUp(self):
        self.root = make_tempdir(self)

    def test_no_print_or_logging_in_library(self):
        scanned = set()
        for path in (Path(__file__).resolve().parents[1] / 'lookup').glob('*.py'):
            if path.stem == '__main__':
                continue
            scanned.add(path.stem)
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                if isinstance(node, ast.Import):
                    self.assertFalse(any(n.name.split('.')[0] in ('logging', 'warnings') for n in node.names), path.name)
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn((node.module or '').split('.')[0], ('logging', 'warnings'), path.name)
                if isinstance(node, ast.Call):
                    self.assertFalse(isinstance(node.func, ast.Name) and node.func.id == 'print', path.name)
                    if isinstance(node.func, ast.Attribute) and node.func.attr == 'write':
                        self.assertNotIn(ast.unparse(node.func.value), ('sys.stdout', 'sys.stderr'), path.name)
        self.assertTrue(set('stardict dsl mdx lzo ripemd128 dictzip dicts config online translate store normalize'.split()) <= scanned)

    def test_network_failures_do_not_leak(self):
        out, err, logs = io.StringIO(), io.StringIO(), io.StringIO()
        logger = logging.getLogger()
        old_level = logger.level
        handler = logging.StreamHandler(logs)
        logger.addHandler(handler)
        logger.setLevel(1)
        self.addCleanup(logger.setLevel, old_level)
        self.addCleanup(logger.removeHandler, handler)
        conn = open_store()
        self.addCleanup(conn.close)
        fake = mock.Mock()
        fake.find.return_value = dicts.SearchResult()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            for reason in online.REASONS:
                with mock.patch.object(online, 'translate_online', side_effect=online.TranslateError(reason)):
                    result = translate.lookup(SENTINEL, dictset=fake, conn=conn)
                    self.assertEqual(result.online_error, reason)
                    sentence = translate.lookup('zxqv secret sentence for the network test here', conn=conn)
                    self.assertEqual(sentence.online_error, reason)
            http_error = urllib.error.HTTPError('https://example.org/' + SENTINEL, 429, SENTINEL, {}, io.BytesIO())
            self.addCleanup(http_error.close)
            errors = [urllib.error.URLError(SENTINEL), http_error, TimeoutError(SENTINEL), OSError(SENTINEL)]
            for error in errors:
                with mock.patch('urllib.request.OpenerDirector.open', side_effect=error):
                    try:
                        online.translate_online(SENTINEL, 'word')
                    except online.TranslateError as exc:
                        for value in (str(exc), repr(exc), str(exc.args)):
                            self.assertNotIn(SENTINEL, value)
                        self.assertIsNone(exc.__cause__)
                        self.assertTrue(exc.__suppress_context__)
                    else:
                        self.fail('transport error unexpectedly succeeded')
        self.assertEqual((out.getvalue(), err.getvalue(), logs.getvalue()), ('', '', ''))

    def test_corrupt_files_and_cli_warning(self):
        root = Path(os.environ['LOOKUP_DICTS'])
        root.mkdir()
        (root / 'bad.ifo').write_text(SENTINEL, encoding='utf-8')
        with dicts.open_all(config.Config(), [root]) as result:
            self.assertEqual(result.problems, [('bad.ifo', 'corrupt')])
        path = Path(os.environ['LOOKUP_CONFIG'])
        path.parent.mkdir(parents=True)
        path.write_text(SENTINEL, encoding='utf-8')
        self.assertEqual(config.load(), config.Config())
        source = root / 'bad.ifo'
        cache = dicts.index_cache_path(source, 'test')
        cache.parent.mkdir(parents=True)
        cache.write_text(SENTINEL, encoding='utf-8')
        self.assertIsNone(dicts.index_cache_load(source, 'test'))
        db = Path(os.environ['LOOKUP_DB'])
        db.parent.mkdir(parents=True)
        db.write_text(SENTINEL, encoding='utf-8')
        from lookup.__main__ import main
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            main(['--word', 'run', '--offline'])
        self.assertNotIn(SENTINEL, err.getvalue())
        self.assertIn('DatabaseError', err.getvalue())
