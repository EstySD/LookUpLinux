"""Deterministic offline SteamOS bundle with checksums and license notices."""
import json
import os
from pathlib import Path
import sys
import tarfile
import unittest
from unittest import mock

from lookup import portable
from tests._support import make_tempdir

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_steamos_bundle as builder


class SteamOSBundleTests(unittest.TestCase):
    def setUp(self):
        self.root=make_tempdir(self)
        self.env={'XDG_DATA_HOME':str(self.root/'data'),
                  'XDG_CONFIG_HOME':str(self.root/'config'),
                  'XDG_BIN_HOME':str(self.root/'bin')}
        patcher=mock.patch.dict(os.environ,self.env)
        patcher.start();self.addCleanup(patcher.stop)
        self.runtime=self.root/'runtime'
        for name,payload in (('bin/kdotool',b'#!/bin/sh\n'),
                             ('share/tessdata/eng.traineddata',b'eng'),
                             ('lib/python/pyqt6.marker',b'pyqt6')):
            path=self.runtime/name;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(payload)

    def _build(self,name):
        output=self.root/name
        manifest=builder.build(output,runtime=self.runtime)
        return output,manifest

    def test_bundle_is_deterministic_and_contains_licenses_and_runtime(self):
        first,manifest=self._build('first.tar.gz')
        second,_=self._build('second.tar.gz')
        self.assertEqual(first.read_bytes(),second.read_bytes())
        self.assertTrue(manifest['offline_runtime'])
        with tarfile.open(first,'r:gz') as archive:
            names=set(archive.getnames())
            self.assertIn('MANIFEST.json',names)
            self.assertIn('SHA256SUMS',names)
            self.assertIn('LICENSE',names)
            self.assertIn('COPYING.md',names)
            self.assertIn('packaging/THIRD-PARTY.md',names)
            self.assertIn('docs/STEAMOS.md',names)
            self.assertIn('tools/install_steamos.py',names)
            self.assertIn('runtime/bin/kdotool',names)
            meta=json.loads(archive.extractfile('MANIFEST.json').read())
            self.assertEqual(meta['license_notices'][0],'GPL-3.0-or-later')
            sums=archive.extractfile('SHA256SUMS').read().decode()
            self.assertIn('runtime/bin/kdotool',sums)

    def test_bundle_installs_offline_without_root(self):
        bundle,_=self._build('install.tar.gz')
        paths=portable.install(bundle=bundle,home=self.root)
        self.assertTrue((paths['app']/'runtime/share/tessdata/eng.traineddata').is_file())
        self.assertIn(portable.RESTRICTED,paths['applications'].read_text(encoding='utf-8'))
        self.assertTrue(all(portable.status(home=self.root).values()))


if __name__=='__main__':
    unittest.main()
