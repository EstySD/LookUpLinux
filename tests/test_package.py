"""Deterministic, restricted local package staging and installed entry contracts."""
import hashlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

from tools import stage_package

ROOT=Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_staging_is_deterministic_and_excludes_private_runtime_files(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot=Path(directory)/'source'
            shutil.copytree(ROOT/'lookup',snapshot/'lookup')
            shutil.copytree(ROOT/'packaging',snapshot/'packaging')
            shutil.copyfile(ROOT/'PKGBUILD',snapshot/'PKGBUILD')
            for name in ('LICENSE','COPYING.md'):
                shutil.copyfile(ROOT/name,snapshot/name)
            first,second=(Path(directory)/name for name in ('first','second'))
            a=stage_package.stage(first,root=snapshot)
            for path in (snapshot/'lookup').rglob('*.py'):
                path.write_bytes(path.read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
            launcher=snapshot/'packaging/lookup'
            launcher.write_bytes(launcher.read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
            b=stage_package.stage(second,root=snapshot)
            self.assertEqual(a['archive_sha256'],b['archive_sha256'])
            self.assertEqual((first/'lookup-source.tar.gz').read_bytes(),(second/'lookup-source.tar.gz').read_bytes())
            with tarfile.open(first/'lookup-source.tar.gz') as archive:
                names=archive.getnames()
                self.assertEqual(names,sorted(names))
                self.assertIn('lookup-source/lookup/data/irregular.txt',names)
                self.assertIn('lookup-source/packaging/lookup',names)
                self.assertTrue(all(name.startswith(('lookup-source/lookup/','lookup-source/packaging/')) or name in ('lookup-source/LICENSE','lookup-source/COPYING.md') for name in names))
                self.assertFalse(any('/tests/' in name or '.planning' in name or name.endswith(('.pyc','.db')) for name in names))
                self.assertTrue(all(info.mtime==0 and info.uid==info.gid==0 for info in archive.getmembers()))
            build=(first/'PKGBUILD').read_text()
            self.assertIn(a['archive_sha256'],build)
            self.assertNotIn('@LOCAL_SOURCE_SHA256@',build)
            self.assertNotIn('SKIP',build)
            self.assertEqual(json.loads((first/'SOURCE.json').read_text())['archive_sha256'],hashlib.sha256((first/'lookup-source.tar.gz').read_bytes()).hexdigest())

    def test_nonempty_or_symlink_target_is_refused_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'existing';target.mkdir()
            (target/'private').write_text('untouched')
            with self.assertRaises(ValueError):stage_package.stage(target)
            self.assertEqual((target/'private').read_text(),'untouched')

    def test_public_package_excludes_uncleared_dictionary_and_preserves_licenses(self):
        with tempfile.TemporaryDirectory() as directory:
            record=stage_package.stage(Path(directory)/'public',public=True)
            build=(Path(directory)/'public/PKGBUILD').read_text()
            self.assertNotIn('mueller',build.lower())
            self.assertEqual(set(record['upstream']),{'kdotool'})
            self.assertIn('lookup-source/LICENSE',record['files'])
            self.assertIn('lookup-source/COPYING.md',record['files'])
            self.assertIn('GPL-3.0-or-later',build)

    def test_installed_wrapper_imports_without_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);build=root/'build';stage_package.stage(build)
            with tarfile.open(build/'lookup-source.tar.gz') as archive:archive.extractall(root,filter='data')
            wrapper=root/'run.py'
            wrapper.write_text((ROOT/'packaging/lookup').read_text().replace('/usr/lib/lookup/app',(root/'lookup-source').as_posix()),encoding='utf-8')
            cfg=root/'config.json';cfg.write_text('{"autostart":false}')
            result=subprocess.run([sys.executable,str(wrapper),'--autostart'],cwd=root,
                env=dict(os.environ,PYTHONPATH='',LOOKUP_CONFIG=str(cfg)),capture_output=True,timeout=5)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_desktop_and_package_identity_paths_and_attribution(self):
        desktop=(ROOT/'packaging/org.lookup.Linux.desktop').read_text()
        autostart=(ROOT/'packaging/org.lookup.Linux.autostart.desktop').read_text()
        self.assertIn('Exec=/usr/bin/lookup --trigger',desktop)
        self.assertIn('X-KDE-DBUS-Restricted-Interfaces=org.kde.KWin.ScreenShot2',desktop)
        self.assertIn('X-KDE-Shortcuts=Meta+Shift+D',desktop)
        self.assertNotIn('\nPath=',desktop)
        self.assertIn('Exec=/usr/bin/lookup --autostart',autostart)
        self.assertIn('TryExec=/usr/bin/lookup',autostart)
        self.assertIn('OnlyShowIn=KDE;',autostart)
        build=(ROOT/'PKGBUILD').read_text()
        for text in ('/usr/lib/lookup/kdotool','/usr/lib/lookup/app','/usr/share/lookup/dicts/mueller7',
                     '2079cc1d492b6e83e04def4d9376e34fcb36a4e3bdc637c8c2ee6fa547ce90ff',
                     '1c5e19b857eaa5fc98f77173e8baeb22cb654c407586465b4270e4286bf070ed'):
            self.assertIn(text,build)
        self.assertIn('unspecified',(ROOT/'packaging/THIRD-PARTY.md').read_text())
