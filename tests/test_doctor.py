"""Diagnostics read data without lookup, GUI, network or cache persistence."""
import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from lookup import doctor,config,dicts,lifecycle
from tests._support import make_tempdir,forbid_network
from tests._stardict_writer import write_stardict
from tests._dsl_writer import write_dsl
from tests._mdx_writer import write_mdx


class DoctorTests(unittest.TestCase):
    def setUp(self):
        self.root=make_tempdir(self);forbid_network(self)

    def test_real_readonly_parsers_never_construct_cached_readers(self):
        root=self.root/'dicts'
        write_stardict(root,'public',[('bank','берег')])
        write_dsl(root/'public.dsl',[(['bank'],['берег'])])
        write_mdx(root/'public.mdx',[('bank','берег')])
        before={p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with mock.patch('lookup.dsl.open_dsl',side_effect=AssertionError('cached constructor')), \
             mock.patch('lookup.mdx.open_mdx',side_effect=AssertionError('cached constructor')), \
             mock.patch('lookup.dicts.index_cache_save',side_effect=AssertionError('cache write')):
            for found in dicts.discover([root]):
                result=doctor._probe(found.path,found.fmt)
                self.assertEqual(result['entries'],1)
        self.assertEqual(before,{p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        self.assertFalse(Path(os.environ['LOOKUP_DB']).exists())
        self.assertFalse(Path(os.environ['LOOKUP_CACHE']).exists())

    def test_bounded_child_probes_and_disabled_missing_corrupt_status(self):
        root=self.root/'dicts';root.mkdir()
        (root/'bad.mdx').write_bytes(b'private malformed bytes')
        result=doctor._dictionary_checks(config.Config(),[root])
        self.assertTrue(any(not row.ok and 'поврежд' in row.message for row in result))
        self.assertNotIn('private',' '.join(row.message for row in result))
        result=doctor._dictionary_checks(config.Config(dictionaries=(('bad.mdx',False),('missing.dsl',True))),[root])
        self.assertTrue(any('выключен' in row.message for row in result))
        self.assertTrue(any('не найден' in row.message for row in result))

    def test_healthy_checks_readonly_and_run_exit_status(self):
        root=self.root/'dicts';write_stardict(root,'public',[('bank','берег')])
        with mock.patch.object(doctor,'_tool_checks',return_value=[doctor.Diagnostic('tools',True,'Инструменты доступны.')]), \
             mock.patch.object(doctor,'_session_checks',return_value=[doctor.Diagnostic('session',True,'Сеанс доступен.')]), \
             mock.patch('lookup.store.open_store',side_effect=AssertionError('database')), \
             mock.patch('lookup.platform.read_primary',side_effect=AssertionError('clipboard')), \
             mock.patch('lookup.capture.capture_monitor',side_effect=AssertionError('capture')), \
             mock.patch('lookup.dicts.open_all',side_effect=AssertionError('cached readers')):
            out=io.StringIO()
            self.assertEqual(doctor.run(out,roots=[root]),0)
            self.assertIn('OK',out.getvalue())
        self.assertFalse(Path(os.environ['LOOKUP_DB']).exists())

    def test_missing_tools_and_session_are_actionable_and_private(self):
        with mock.patch('lookup.platform.run',side_effect=FileNotFoundError('private path')), \
             mock.patch('lookup.platform.session_env',side_effect=RuntimeError('private session')):
            rows=doctor._tool_checks()+doctor._session_checks()
        self.assertTrue(any(not row.ok for row in rows))
        self.assertIn('tesseract',' '.join(row.message for row in rows))
        self.assertNotIn('private',' '.join(row.message for row in rows))

    def test_cli_is_lazy_exclusive_and_does_not_open_history(self):
        from lookup.__main__ import main
        with mock.patch.object(doctor,'run',return_value=0) as run, \
             mock.patch('lookup.__main__.open_store',side_effect=AssertionError('history')):
            self.assertEqual(main(['--doctor']),0)
            run.assert_called_once()
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(['--doctor','--word','bank']),2)
                self.assertEqual(main(['--doctor','--offline']),2)
