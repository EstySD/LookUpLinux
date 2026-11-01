"""Dependency I/O failures must not skip later owned-clone cleanup actions."""
import ast
import hashlib
import io
import json
from contextlib import redirect_stderr
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch


class CleanupDependencyTests(unittest.TestCase):
    def execute(self,root,record,calls):
        source=Path('.planning/phases/08-vm/08-07-controller.py').read_text(encoding='utf-8')
        tree=ast.parse(source)
        helpers=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('save','attempt')]
        final=next(node for node in tree.body if isinstance(node,ast.Try)).finalbody
        def info(identity):
            calls.append(('info',identity));return dict(UUID='"'+identity+'"',VMState='"poweroff"')
        env=dict(root=root,record=record,calls=calls,hashlib=hashlib,json=json,
            adapter=dict(inputs=lambda *a,**k:calls.append(('input',)),guest=lambda *a,**k:calls.append(('guest',a[0]))),
            info=info,run=lambda *a:calls.append(a),clone='clone',original='external',vbox='VBox',actions=[],
            prior=dict(accelerate3d='"on"',clipboard='"bidirectional"'),time=types.SimpleNamespace(monotonic=lambda:0,sleep=lambda _:None))
        exec(compile(ast.Module(body=helpers+final,type_ignores=[]),'owned-cleanup-dependency','exec'),env)

    def test_source_read_error_still_runs_shutdown_restore_and_readbacks(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'08-07-guest-cleanup.py').write_text('pass');record={};calls=[]
            original=Path.read_text
            def read(path,*args,**kwargs):
                if path.name=='08-07-guest-cleanup.py':raise OSError('controlled source read')
                return original(path,*args,**kwargs)
            with patch.object(Path,'read_text',read):self.execute(root,record,calls)
            self.assertTrue(any('modifyvm' in call for call in calls))
            self.assertFalse(record['guest_cleanup']['ok'])
            self.assertTrue(any(call[0]=='guest' and 'poweroff' in call[1] for call in calls))
            self.assertTrue((root/'08-07-controller-state.json').exists())

    def test_report_write_error_does_not_prevent_shutdown_or_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'08-07-guest-cleanup.py').write_text('pass');record={};calls=[]
            errors=io.StringIO()
            with patch.object(Path,'write_text',side_effect=OSError('controlled persistence')),redirect_stderr(errors):
                try:self.execute(root,record,calls)
                except (OSError,RuntimeError):pass
            self.assertTrue(any('modifyvm' in call for call in calls))
            self.assertTrue(any(call[0]=='guest' and 'poweroff' in call[1] for call in calls))
            self.assertTrue(record.get('persistence_errors'))
            self.assertIn('evidence persistence error',errors.getvalue())
