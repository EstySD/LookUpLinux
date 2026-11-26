"""Portable SteamOS install: ownership, XDG paths and private-data preservation."""
import io
import os
import tarfile
import unittest
from unittest import mock

from lookup import portable
from tests._support import make_tempdir


class PortableTests(unittest.TestCase):
    def setUp(self):
        self.root=make_tempdir(self)
        self.env={'XDG_DATA_HOME':str(self.root/'data'),
                  'XDG_CONFIG_HOME':str(self.root/'config'),
                  'XDG_BIN_HOME':str(self.root/'bin')}
        patcher=mock.patch.dict(os.environ,self.env)
        patcher.start();self.addCleanup(patcher.stop)

    def _source(self):
        source=self.root/'source'/'lookup'
        source.mkdir(parents=True)
        (source/'__init__.py').write_text('VALUE=1\n',encoding='utf-8')
        return source.parent

    def test_trigger_entry_is_owned_and_trusts_screenshot2(self):
        text=portable.desktop_text(self.root/'bin/lookup','Meta+Shift+D','trigger')
        self.assertIn(portable.MARKER,text.splitlines())
        self.assertIn(portable.RESTRICTED,text.splitlines())
        self.assertIn('X-KDE-Shortcuts=Meta+Shift+D',text)
        self.assertIn('--trigger',text)
        self.assertIn('NoDisplay=true',text)
        autostart=portable.desktop_text(self.root/'bin/lookup','Meta+Shift+D','autostart')
        self.assertIn('OnlyShowIn=KDE;',autostart)
        self.assertIn('--autostart',autostart)

    def test_systemd_unit_is_owned_and_starts_the_daemon(self):
        text=portable.service_text(self.root)
        self.assertIn('# '+portable.MARKER,text)
        self.assertIn('--background',text)
        self.assertIn('WantedBy=default.target',text)
        self.assertIn('lookup',text)

    def test_install_launch_files_and_uninstall_preserves_user_data(self):
        paths=portable.install(source=self._source(),home=self.root)
        self.assertTrue((paths['app']/'lookup'/'__init__.py').is_file())
        self.assertTrue((paths['app']/portable.OWNED_FILE).is_file())
        self.assertIn(portable.MARKER,paths['wrapper'].read_text(encoding='utf-8'))
        self.assertTrue(all(portable.status(home=self.root).values()))
        self.assertIn(portable.RESTRICTED,paths['applications'].read_text(encoding='utf-8'))
        data=self.root/'.local/share/lookup'
        data.mkdir(parents=True)
        (data/'lookup.db').write_text('private',encoding='utf-8')
        settings=self.root/'.config/lookup'
        settings.mkdir(parents=True)
        (settings/'config.json').write_text('{}',encoding='utf-8')
        portable.uninstall(home=self.root)
        self.assertFalse(any(portable.status(home=self.root).values()))
        self.assertEqual((data/'lookup.db').read_text(encoding='utf-8'),'private')
        self.assertEqual((settings/'config.json').read_text(encoding='utf-8'),'{}')

    def test_unowned_collision_is_refused(self):
        target=self.root/'data/applications/org.lookup.Linux.desktop'
        target.parent.mkdir(parents=True)
        target.write_text('[Desktop Entry]\nExec=other\n',encoding='utf-8')
        with self.assertRaises(portable.PortableError) as error:
            portable.install(source=self._source(),home=self.root)
        self.assertEqual(error.exception.reason,'unowned_file')

    def test_bundle_rejects_path_traversal_and_symlinks(self):
        bundle=self.root/'bundle.tar.gz'
        with tarfile.open(bundle,'w:gz') as archive:
            info=tarfile.TarInfo('../escaped')
            info.size=1
            archive.addfile(info,io.BytesIO(b'x'))
        target=self.root/'target'
        with self.assertRaises(portable.PortableError) as error:
            portable.extract_bundle(bundle,target)
        self.assertEqual(error.exception.reason,'unsafe_bundle')
        self.assertFalse((self.root/'escaped').exists())

    def test_bundle_install_extracts_bounded_files(self):
        bundle=self.root/'bundle.tar.gz'
        with tarfile.open(bundle,'w:gz') as archive:
            for name,payload in (('lookup/__init__.py',b'VALUE=2\n'),('runtime/bin/helper',b'#!/bin/sh\n')):
                info=tarfile.TarInfo(name);info.size=len(payload)
                archive.addfile(info,io.BytesIO(payload))
        paths=portable.install(bundle=bundle,home=self.root)
        self.assertIn('VALUE=2',(paths['app']/'lookup/__init__.py').read_text(encoding='utf-8'))
        self.assertTrue((paths['app']/'runtime/bin/helper').is_file())


if __name__=='__main__':
    unittest.main()
