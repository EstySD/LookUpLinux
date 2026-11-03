"""Owned KDE lifecycle contracts; session mutations use an injected registry."""
import os
from pathlib import Path
import unittest
from unittest import mock

from lookup import lifecycle
from tests._support import make_tempdir


class Registry:
    def __init__(self):
        self.action=[lifecycle.DESKTOP,'_launch','Actual component label','Actual action label']
        self.keys=[123]
        self.available=True
        self.writes=[]
        self.ignore_next=False
        self.fail_restore=False
    def __call__(self,method,*args):
        if method=='allActionsForComponent':return [self.action]
        if method=='shortcut':
            if list(args[0])!=self.action:raise RuntimeError('wrong friendly identity')
            return list(self.keys)
        if method=='isGlobalShortcutAvailable':
            if args[1]!=lifecycle.DESKTOP:raise RuntimeError('wrong component')
            return self.available
        if method=='setForeignShortcut':
            if list(args[0])!=self.action:raise RuntimeError('wrong identity')
            self.writes.append(tuple(args[1]))
            if self.fail_restore and len(self.writes)>1:raise RuntimeError('private detail')
            if self.ignore_next:self.ignore_next=False
            else:self.keys=list(args[1])
            return None
        raise AssertionError(method)


class ShortcutTests(unittest.TestCase):
    def test_startup_preserves_active_binding(self):
        bus=Registry()
        lifecycle.ensure_shortcut(lifecycle.ShortcutRegistry(bus))
        self.assertEqual(bus.keys,[123])
        self.assertEqual(bus.writes,[])

    def test_startup_assigns_empty_binding_and_refuses_conflicts(self):
        for available in (True,False):
            bus=Registry();bus.keys=[];bus.available=available
            with mock.patch.object(lifecycle.config,'load',return_value=lifecycle.config.Config()):
                if available:
                    lifecycle.ensure_shortcut(lifecycle.ShortcutRegistry(bus))
                    self.assertTrue(bus.keys)
                else:
                    with self.assertRaises(lifecycle.LifecycleError):
                        lifecycle.ensure_shortcut(lifecycle.ShortcutRegistry(bus))
                    self.assertEqual(bus.writes,[])

    def test_single_chord_and_canonical_key(self):
        text,key=lifecycle.parse_shortcut('Alt+Q')
        self.assertEqual(text,'Alt+Q')
        self.assertGreater(key,0)
        for invalid in ('','garbage','Ctrl+X, Ctrl+S',None,'Alt+Q\n'):
            with self.subTest(invalid=invalid):
                with self.assertRaises(lifecycle.LifecycleError):lifecycle.parse_shortcut(invalid)

    def test_actual_identity_explicit_edit_commit_and_restore(self):
        bus=Registry()
        registry=lifecycle.ShortcutRegistry(bus)
        binding=registry.inspect()
        self.assertEqual(binding.action,tuple(bus.action))
        transaction=registry.change('Alt+Q')
        self.assertEqual(transaction.before.keys,(123,))
        self.assertEqual(tuple(bus.keys),transaction.desired)
        transaction.rollback()
        self.assertEqual(bus.keys,[123])
        transaction=registry.change('Alt+Q')
        transaction.commit()
        transaction.rollback()
        self.assertNotEqual(bus.keys,[123])

    def test_conflict_never_writes_and_unknown_identity_is_refused(self):
        bus=Registry();bus.available=False
        with self.assertRaises(lifecycle.LifecycleError) as raised:
            lifecycle.ShortcutRegistry(bus).change('Alt+Q')
        self.assertEqual(raised.exception.reason,'shortcut_conflict')
        self.assertEqual(bus.writes,[])
        bus.action[0]='unrelated.desktop'
        with self.assertRaises(lifecycle.LifecycleError) as raised:
            lifecycle.ShortcutRegistry(bus).inspect()
        self.assertEqual(raised.exception.reason,'not_registered')

    def test_readback_mismatch_restores_and_rollback_failure_is_distinct(self):
        bus=Registry();bus.ignore_next=True
        with self.assertRaises(lifecycle.LifecycleError) as raised:
            lifecycle.ShortcutRegistry(bus).change('Alt+Q')
        self.assertEqual(raised.exception.reason,'apply_failed')
        self.assertEqual(bus.keys,[123])
        self.assertEqual(bus.writes[-1],(123,))
        bus=Registry()
        transaction=lifecycle.ShortcutRegistry(bus).change('Alt+Q')
        bus.fail_restore=True
        with self.assertRaises(lifecycle.LifecycleError) as raised:transaction.rollback()
        self.assertEqual(raised.exception.reason,'rollback_failed')


class EntryTests(unittest.TestCase):
    def setUp(self):
        self.root=make_tempdir(self)
        patcher=mock.patch.dict(os.environ,{'XDG_CONFIG_HOME':str(self.root/'config'),
            'XDG_DATA_HOME':str(self.root/'data')})
        patcher.start();self.addCleanup(patcher.stop)

    def test_source_entries_are_owned_quoted_and_ordinary_registration_keeps_override(self):
        bus=Registry()
        with mock.patch.object(lifecycle,'is_installed',return_value=False), \
             mock.patch('lookup.platform.run',return_value=b'') as run:
            paths=lifecycle.ensure_entries(python=self.root/'python $%',directory=self.root/'my checkout')
            self.assertEqual(len(paths),2)
            self.assertEqual(run.call_args.args[0],['kbuildsycoca6'])
            self.assertIn('X-LookUpLinux-Owned=true',paths[0].read_text())
            self.assertIn('python \\$%%" -m lookup --trigger',paths[0].read_text())
            self.assertIn('--autostart',paths[1].read_text())
            home=paths[0].with_name(lifecycle.HOME_DESKTOP).read_text()
            self.assertIn('--app',home)
            self.assertNotIn('X-KDE-Shortcuts',home)
            self.assertIn('NoDisplay=true',paths[0].read_text())
            self.assertIn('OnlyShowIn=KDE;',paths[1].read_text())
        self.assertEqual(lifecycle.ShortcutRegistry(bus).inspect().keys,(123,))
        self.assertEqual(bus.writes,[])

    def test_unowned_collision_refuses_before_creating_other_entries(self):
        desktop=self.root/'data/applications'/lifecycle.DESKTOP
        desktop.parent.mkdir(parents=True)
        desktop.write_text('[Desktop Entry]\nName=Other\n')
        with mock.patch.object(lifecycle,'is_installed',return_value=False):
            with self.assertRaises(lifecycle.LifecycleError) as raised:lifecycle.ensure_entries()
        self.assertEqual(raised.exception.reason,'unowned_file')
        self.assertEqual(desktop.read_text(),'[Desktop Entry]\nName=Other\n')
        self.assertFalse((self.root/'config/autostart'/lifecycle.DESKTOP).exists())

    def test_installed_uses_package_entries_without_user_shadow(self):
        with mock.patch.object(lifecycle,'is_installed',return_value=True), \
             mock.patch('lookup.platform.run') as run:
            paths=lifecycle.ensure_entries()
        self.assertEqual(paths,(lifecycle.INSTALLED_DESKTOP,lifecycle.INSTALLED_AUTOSTART))
        self.assertFalse((self.root/'data').exists())
        self.assertFalse((self.root/'config').exists())
        run.assert_not_called()
        text=lifecycle.desktop_text(installed=True)
        self.assertIn('Exec=/usr/bin/lookup --trigger',text)
        self.assertNotIn('Path=',text)
        text=lifecycle.desktop_text(installed=True,autostart=True)
        self.assertIn('TryExec=/usr/bin/lookup',text)
        self.assertIn('Exec=/usr/bin/lookup --autostart',text)

    def test_installed_detection_requires_executable_and_package_desktop(self):
        with mock.patch.object(Path,'is_file',side_effect=[True,True]):self.assertTrue(lifecycle.is_installed())
        with mock.patch.object(Path,'is_file',side_effect=[True,False]):self.assertFalse(lifecycle.is_installed())

    def test_unsafe_desktop_paths_are_refused(self):
        for path in (Path('relative'),Path('/bad\npath')):
            with self.assertRaises(ValueError):lifecycle.desktop_text(python=path)

    def test_symlink_entry_is_not_taken_over(self):
        with mock.patch.object(lifecycle,'is_installed',return_value=False), \
             mock.patch.object(Path,'is_symlink',return_value=True):
            with self.assertRaises(lifecycle.LifecycleError) as raised:lifecycle.ensure_entries()
        self.assertEqual(raised.exception.reason,'unowned_file')

    def test_installed_migrates_only_owned_source_shadows(self):
        desktop=self.root/'data/applications'/lifecycle.DESKTOP
        autostart=self.root/'config/autostart'/lifecycle.DESKTOP
        for path,automatic in ((desktop,False),(autostart,True)):
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(lifecycle.desktop_text(autostart=automatic))
        with mock.patch.object(lifecycle,'is_installed',return_value=True), \
             mock.patch('lookup.platform.run',return_value=b'') as run:
            lifecycle.ensure_entries()
        self.assertFalse(desktop.exists())
        self.assertFalse(autostart.exists())
        run.assert_called_once()

    def test_installed_preflights_both_shadows_before_removing_either(self):
        desktop=self.root/'data/applications'/lifecycle.DESKTOP
        autostart=self.root/'config/autostart'/lifecycle.DESKTOP
        for path,text in ((desktop,lifecycle.desktop_text()),(autostart,'[Desktop Entry]\nName=Other\n')):
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(text)
        with mock.patch.object(lifecycle,'is_installed',return_value=True):
            with self.assertRaises(lifecycle.LifecycleError):lifecycle.ensure_entries()
        self.assertTrue(desktop.exists())
        self.assertEqual(autostart.read_text(),'[Desktop Entry]\nName=Other\n')

    def test_legacy_generated_entry_is_recognized_but_comment_alone_is_not(self):
        desktop=self.root/'data/applications'/lifecycle.DESKTOP
        desktop.parent.mkdir(parents=True)
        legacy=lifecycle.desktop_text().replace(lifecycle.MARKER+'\n','')
        desktop.write_text(legacy)
        with mock.patch.object(lifecycle,'is_installed',return_value=False),mock.patch('lookup.platform.run',return_value=b''):
            lifecycle.ensure_entries()
        self.assertIn(lifecycle.MARKER,desktop.read_text())
        desktop.write_text('[Desktop Entry]\nComment=LookUp Linux owned application trigger\nExec=/other\n')
        with self.assertRaises(lifecycle.LifecycleError):lifecycle._existing(desktop)
