"""Discovery, ordering and failure isolation through real dictionary readers."""
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lookup import dicts
from lookup.config import Config
from tests._dsl_writer import write_dsl
from tests._mdx_writer import write_mdx
from tests._stardict_writer import write_stardict


class RootTests(unittest.TestCase):
    def test_environment_and_xdg(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            cases = [
                ({'LOOKUP_DICTS': os.pathsep.join(['one', '', 'two'])}, [Path('one'), Path('two')]),
                ({'XDG_DATA_HOME': tmp}, [home / 'lookup/dicts', dicts.SYSTEM_DICT_ROOT]),
                ({'XDG_DATA_HOME': 'relative', 'LOOKUP_DICTS': ''}, [home / '.local/share/lookup/dicts', dicts.SYSTEM_DICT_ROOT]),
                ({}, [home / '.local/share/lookup/dicts', dicts.SYSTEM_DICT_ROOT]),
            ]
            for env, expected in cases:
                with self.subTest(env=env), mock.patch.dict(os.environ, env, clear=True), mock.patch.object(Path, 'home', return_value=home):
                    self.assertEqual(dicts.dict_roots(), expected)
            self.assertEqual(list(home.iterdir()), [])


class DictionaryCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cache = mock.patch.dict(os.environ, {'LOOKUP_CACHE': str(self.root / 'cache')})
        self.cache.start()
        self.addCleanup(self.cache.stop)

    def open(self, config=Config(), roots=None):
        result = dicts.open_all(config=config, roots=roots or [self.root])
        self.addCleanup(result.close)
        return result

    def star(self, stem, name=None):
        return write_stardict(self.root / stem, stem, [('run', '_v. бежать')], bookname=name or stem)


class DiscoveryTests(DictionaryCase):
    def test_formats_depth_hidden_and_duplicate_roots(self):
        self.star('a')
        write_dsl(self.root / 'b.dsl', [(['run'], ['бежать'])])
        (self.root / 'b.dsl.dz').touch()
        write_mdx(self.root / 'c.mdx', [('run', 'бежать')])
        for name in ['.hidden.ifo', 'other.mdd', 'swap.dsl.swp']:
            (self.root / name).touch()
        (self.root / '.hidden').mkdir()
        (self.root / '.hidden/x.ifo').touch()
        deep = self.root.joinpath(*(['deep'] * (dicts.MAX_WALK_DEPTH + 1)))
        deep.mkdir(parents=True)
        (deep / 'no.ifo').touch()
        second = self.root / 'second'
        second.mkdir()
        (second / 'b.dsl').touch()
        found = dicts.discover([self.root, second, self.root / 'missing'])
        self.assertEqual({f.id for f in found}, {'a/a.ifo', 'b.dsl', 'c.mdx', 'second/b.dsl'})
        self.assertEqual(next(f.path for f in found if f.id == 'b.dsl'), self.root / 'b.dsl')
        with mock.patch.object(dicts, 'MAX_DISCOVERED', 2):
            self.assertEqual(len(dicts.discover([self.root])), 2)

    @unittest.skipIf(os.name == 'nt', 'POSIX symlink semantics')
    def test_symlinks_do_not_escape_root(self):
        with tempfile.TemporaryDirectory() as outside:
            target = write_stardict(outside, 'secret', [('run', 'secret')])
            (self.root / 'link').symlink_to(outside, target_is_directory=True)
            (self.root / 'secret.ifo').symlink_to(target)
            self.assertEqual(dicts.discover([self.root]), [])


class OrderTests(DictionaryCase):
    def test_config_order_disable_and_all_articles(self):
        self.star('a', 'Zulu')
        self.star('z', 'Alpha')
        result = self.open()
        self.assertEqual([a.dict_name for a in result.lookup_exact('RUN')], ['Alpha', 'Zulu'])
        result = self.open(Config(dictionaries=(('a/a.ifo', True), ('z/z.ifo', True))))
        self.assertEqual([a.dict_name for a in result.lookup_exact('run')], ['Zulu', 'Alpha'])
        with mock.patch('lookup.stardict.open_stardict', wraps=__import__('lookup.stardict', fromlist=['open_stardict']).open_stardict) as opener:
            result = self.open(Config(dictionaries=(('z/z.ifo', False), ('../outside.ifo', True), ('/outside.ifo', True), ('a\\a.ifo', True), ('\x00', True))))
            self.assertEqual([call.args[0] for call in opener.call_args_list], [self.root / 'a/a.ifo'])
        self.assertEqual(result.disabled, ['z/z.ifo'])
        self.assertEqual([(i.status, i.order) for i in result.info()], [('disabled', None), ('ok', 1)])
        self.assertGreaterEqual(result.open_ms, 0)
        self.assertTrue(result.has('run'))

    def test_roots_precede_names_and_close_is_idempotent(self):
        self.star('a', 'Zulu')
        other = self.root / 'system'
        write_stardict(other, 'z', [('run', 'бег')], bookname='Alpha')
        result = self.open(roots=[self.root / 'a', other])
        self.assertEqual([r.name for r in result.info()], ['Zulu', 'Alpha'])
        with mock.patch.object(result.dicts[0], 'close', wraps=result.dicts[0].close) as closer:
            with result:
                pass
            result.close()
            self.assertEqual(closer.call_count, 1)
        empty = self.open(roots=[self.root / 'missing'])
        self.assertFalse(empty.find('run'))


class BrokenDictionaryTests(DictionaryCase):
    def test_errors_preserve_healthy_readers_and_info(self):
        self.star('good')
        (self.root / 'bad.ifo').write_text('garbage', encoding='utf-8')
        missing = self.star('missing')
        missing.with_suffix('.dict').unlink()
        (self.root / 'short.mdx').write_bytes(b'123')
        (self.root / 'empty.dsl').touch()
        write_mdx(self.root / 'locked.mdx', [('run', 'x')], encrypted=1)
        write_mdx(self.root / 'checksum.mdx', [('run', 'x')], corrupt=lambda b: b[:4] + bytes([b[4] ^ 1]) + b[5:])
        result = self.open()
        problems = dict(result.problems)
        for ident, reason in [('bad.ifo', 'corrupt'), ('missing/missing.ifo', 'missing_files'), ('empty.dsl', 'empty'), ('locked.mdx', 'encrypted_registration'), ('checksum.mdx', 'checksum')]:
            self.assertEqual(problems[ident], reason)
        self.assertIn(problems['short.mdx'], ('corrupt', 'checksum'))
        self.assertTrue(result.find('run'))
        healthy = next(i for i in result.info() if i.status == 'ok')
        self.assertEqual((healthy.entries, healthy.skipped), (1, 0))

    def test_unexpected_open_and_lookup_errors_are_isolated(self):
        self.star('a')
        self.star('b')
        for exc in (ValueError(), struct.error()):
            with self.subTest(exc=type(exc)), mock.patch('lookup.stardict.open_stardict', side_effect=exc):
                self.assertEqual(self.open().problems, [('a/a.ifo', 'corrupt'), ('b/b.ifo', 'corrupt')])
        result = self.open()
        with mock.patch.object(result.dicts[0], 'lookup', side_effect=ValueError()):
            self.assertEqual(len(result.lookup_exact('run')), 1)
        with mock.patch('lookup.stardict.open_stardict', side_effect=MemoryError):
            with self.assertRaises(MemoryError):
                self.open()
