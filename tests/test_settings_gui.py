"""Native settings controls and acknowledged asynchronous application."""
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from tests._support import make_tempdir, forbid_network
from lookup import config, lifecycle, dicts

try:
    from PyQt6.QtCore import Qt, QEvent
    from PyQt6.QtGui import QKeySequence,QDesktopServices
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtTest import QTest
except ImportError:
    QApplication=None


class FakeEngine:
    def __init__(self):self.reloads=[]
    def request_reload(self):
        revision=len(self.reloads)+1
        self.reloads.append(revision)
        return revision


class Registry:
    def __init__(self):
        self.keys=(lifecycle.parse_shortcut('Meta+Shift+E')[1],)
        self.changes=[]
        self.threads=[]
        self.error=None
        self.rollback_error=False
    def inspect(self):
        self.threads.append(threading.get_ident())
        return lifecycle.Binding((lifecycle.DESKTOP,'_launch','LookUp','Launch'),self.keys)
    def change(self,text):
        self.threads.append(threading.get_ident())
        if self.error:raise lifecycle.LifecycleError(self.error)
        before=self.keys
        self.keys=(lifecycle.parse_shortcut(text)[1],)
        self.changes.append(text)
        registry=self
        class Transaction:
            active=True
            def commit(self):self.active=False
            def rollback(self):
                registry.threads.append(threading.get_ident())
                if registry.rollback_error:raise lifecycle.LifecycleError('rollback_failed')
                registry.keys=before;self.active=False
        return Transaction()


@unittest.skipIf(QApplication is None,'PyQt6 unavailable')
class SettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.application=QApplication.instance() or QApplication([])
    def setUp(self):
        self.root=make_tempdir(self)
        forbid_network(self)
        from lookup.settings_gui import components
        self.Window,self.Controller=components()
        self.engine=FakeEngine()
        self.registry=Registry()
        self.controllers=[]
        self.windows=[]
        def cleanup():
            for controller in self.controllers:controller.shutdown()
            self.wait(lambda:not any(c.pending for c in self.controllers))
            for window in self.windows:window.close();window.deleteLater()
            for controller in self.controllers:controller.deleteLater()
            self.application.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        self.addCleanup(cleanup)
    def wait(self,predicate,timeout=3):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            self.application.processEvents()
            if predicate():return
            QTest.qWait(5)
        self.fail('settings operation did not complete')
    def controller(self,**kwargs):
        value=self.Controller(self.engine,registry=self.registry,discover=lambda:[dict(id='found',name='<Found>')],**kwargs)
        self.controllers.append(value)
        return value
    def window(self,controller=None):
        value=self.Window(controller or self.controller())
        self.windows.append(value)
        value.show()
        self.wait(lambda:not value.controller.pending)
        return value
    def snapshot(self,**kwargs):
        value=dict(dictionaries=[dict(id='found',enabled=True)],online=False,popup_timeout=7,
                   autostart=False,shortcut='Meta+Shift+F',shortcut_edited=False)
        value.update(kwargs)
        return value
    def ack(self,controller,error=None,revision=None):
        controller.ack(SimpleNamespace(stage='reload',reload_revision=revision or controller.reload_revision,error=error))
    def test_popup_controls_persist_reopen_and_rollback(self):
        window=self.window()
        controls=(window.popup_show_context,window.popup_show_meaning,window.popup_expand_articles)
        self.assertEqual(tuple(control.isChecked() for control in controls),(False,True,False))
        for control in controls:
            self.assertTrue(control.accessibleName())
            control.toggle()
        window.controller.apply(window.snapshot())
        self.wait(lambda:window.controller.reload_revision is not None)
        self.assertTrue(all(not control.isEnabled() for control in controls))
        self.ack(window.controller)
        reopened=self.window()
        self.assertEqual(tuple(getattr(reopened,name).isChecked() for name in
            ('popup_show_context','popup_show_meaning','popup_expand_articles')),(True,False,True))
        saved=config.load()
        controller=self.controller()
        applied=[];controller.applied.connect(applied.append)
        controller.apply(self.snapshot(popup_show_context=False,popup_show_meaning=True,popup_expand_articles=False))
        self.wait(lambda:controller.reload_revision is not None)
        revision=controller.reload_revision
        self.ack(controller,error='reload_failed')
        self.wait(lambda:controller.reload_revision!=revision)
        self.ack(controller)
        self.assertEqual(config.load(),saved)
        self.assertEqual(applied,[])
    def test_controls_keep_missing_ids_order_enabled_and_external_binding(self):
        config.save(dict(dictionaries=[dict(id='missing',enabled=False),dict(id='found',enabled=True)]))
        value=self.window()
        self.assertEqual(value.shortcut.keySequence().toString(QKeySequence.SequenceFormat.PortableText),'Meta+Shift+E')
        self.assertIn('Meta+Shift+E',value.actual_binding.text())
        self.assertEqual(value.dictionaries.item(0).data(Qt.ItemDataRole.UserRole),'missing')
        self.assertIn('недоступен',value.dictionaries.item(0).text())
        value.dictionaries.setCurrentRow(1);QTest.mouseClick(value.up_button,Qt.MouseButton.LeftButton)
        self.assertEqual(value.dictionaries.item(0).data(Qt.ItemDataRole.UserRole),'found')
        self.assertFalse(value.up_button.isEnabled())
        value.dictionaries.item(0).setCheckState(Qt.CheckState.Unchecked)
        value.online.setChecked(False)
        self.assertIn('Локальные словари отключены',value.dictionary_help.text())
        self.assertTrue(value.apply_button.isEnabled())
        self.assertEqual(config.load().online,True)
        self.assertEqual(value.snapshot()['shortcut_edited'],False)
        self.assertEqual((value.timeout.minimum(),value.timeout.maximum(),value.timeout.value()),(1,300,20))
    def test_apply_preserves_override_and_waits_latest_ack(self):
        controller=self.controller()
        states=[];applied=[]
        controller.state.connect(states.append);controller.applied.connect(applied.append)
        controller.apply(self.snapshot())
        self.wait(lambda:controller.reload_revision is not None)
        self.assertTrue(controller.pending)
        self.assertEqual(applied,[])
        self.ack(controller,revision=controller.reload_revision+1)
        self.assertTrue(controller.pending)
        self.ack(controller)
        self.assertFalse(controller.pending)
        self.assertEqual(applied[0].popup_timeout,7)
        self.assertEqual(config.load().shortcut,'Meta+Shift+D')
        self.assertEqual(self.registry.changes,[])
        self.assertEqual(states[-1]['status'],'success')
    def test_explicit_key_edit_and_config_write_run_off_gui_thread(self):
        writes=[]
        def save(changes):
            writes.append(threading.get_ident())
            return config.save(changes)
        controller=self.controller(save=save)
        controller.apply(self.snapshot(shortcut_edited=True))
        self.wait(lambda:controller.reload_revision is not None)
        self.ack(controller)
        self.assertEqual(config.load().shortcut,'Meta+Shift+F')
        self.assertEqual(self.registry.changes,['Meta+Shift+F'])
        self.assertTrue(all(value!=threading.get_ident() for value in self.registry.threads))
        self.assertTrue(writes)
        self.assertTrue(all(value!=threading.get_ident() for value in writes))
    def test_conflict_and_save_failure_restore_key_without_worker_ack(self):
        controller=self.controller()
        states=[];controller.state.connect(states.append)
        self.registry.error='shortcut_conflict'
        controller.apply(self.snapshot(shortcut_edited=True))
        self.wait(lambda:not controller.pending)
        self.assertEqual(states[-1]['status'],'shortcut_conflict')
        self.assertEqual(self.engine.reloads,[])
        self.registry.error=None
        original=self.registry.keys
        def fail(changes):raise config.ConfigError('unavailable')
        controller=self.controller(save=fail)
        controller.state.connect(states.append)
        controller.apply(self.snapshot(shortcut_edited=True))
        self.wait(lambda:not controller.pending)
        self.assertEqual(states[-1]['status'],'save_failed')
        self.assertEqual(self.registry.keys,original)
        self.assertEqual(config.load().online,True)
    def test_reload_failure_restores_saved_config_key_and_acknowledges_restoration(self):
        original=config.load()
        before=self.registry.keys
        controller=self.controller()
        applied=[];states=[]
        controller.applied.connect(applied.append);controller.state.connect(states.append)
        controller.apply(self.snapshot(shortcut_edited=True))
        self.wait(lambda:len(self.engine.reloads)==1)
        first=controller.reload_revision
        self.ack(controller,error='reload_failed')
        self.wait(lambda:len(self.engine.reloads)==2)
        self.assertEqual(config.load(),original)
        self.assertEqual(self.registry.keys,before)
        self.ack(controller,revision=first)
        self.assertTrue(controller.pending)
        self.ack(controller)
        self.assertFalse(controller.pending)
        self.assertEqual(applied,[])
        self.assertEqual(states[-1]['status'],'runtime_failed')
    def test_rollback_uncertainty_and_failed_restoration_ack_are_not_success(self):
        self.registry.rollback_error=True
        def fail(changes):raise config.ConfigError('unavailable')
        controller=self.controller(save=fail)
        states=[];controller.state.connect(states.append)
        controller.apply(self.snapshot(shortcut_edited=True))
        self.wait(lambda:not controller.pending)
        self.assertEqual(states[-1]['status'],'rollback_shortcut')
        self.registry.rollback_error=False
        controller=self.controller();controller.state.connect(states.append)
        controller.apply(self.snapshot())
        self.wait(lambda:controller.reload_revision is not None)
        self.ack(controller,error='reload_failed')
        self.wait(lambda:len(self.engine.reloads)==2)
        self.ack(controller,error='reload_failed')
        self.assertEqual(states[-1]['status'],'restore_unconfirmed')
        self.assertEqual(config.load().online,True)
    def test_timeout_rolls_back_and_shutdown_during_prepare_restores_snapshot(self):
        controller=self.controller(ack_timeout=60)
        states=[];controller.state.connect(states.append)
        controller.apply(self.snapshot())
        self.wait(lambda:len(self.engine.reloads)==2)
        self.ack(controller)
        self.assertEqual(states[-1]['status'],'runtime_failed')
        release=threading.Event();entered=threading.Event()
        self.addCleanup(release.set)
        def delayed(changes):
            entered.set();release.wait(2)
            return config.save(changes)
        controller=self.controller(save=delayed)
        controller.apply(self.snapshot(shortcut_edited=True))
        self.assertTrue(entered.wait(1))
        controller.shutdown();release.set()
        self.wait(lambda:not controller.pending)
        self.assertEqual(config.load().online,True)
        self.assertEqual(self.registry.keys,(lifecycle.parse_shortcut('Meta+Shift+E')[1],))

    def test_config_rollback_error_does_not_claim_old_saved_state(self):
        def fail(changes):raise config.ConfigError('unavailable')
        controller=self.controller(restore=fail)
        states=[];controller.state.connect(states.append)
        controller.apply(self.snapshot())
        self.wait(lambda:controller.reload_revision is not None)
        self.ack(controller,error='reload_failed')
        self.wait(lambda:not controller.pending)
        self.assertEqual(states[-1]['status'],'rollback_config')
        self.assertFalse(config.load().online)
    def test_close_reopen_pending_preserves_snapshot_then_unsaved_draft_is_discarded(self):
        entered=threading.Event();release=threading.Event()
        self.addCleanup(release.set)
        def delayed(changes):
            entered.set();release.wait(2)
            return config.save(changes)
        controller=self.controller(save=delayed)
        value=self.window(controller)
        value.online.setChecked(False)
        QTest.mouseClick(value.apply_button,Qt.MouseButton.LeftButton)
        self.assertTrue(entered.wait(1))
        self.assertFalse(value.online.isEnabled())
        QTest.keyClick(value,Qt.Key.Key_Escape)
        self.assertFalse(value.isVisible())
        value.show();self.application.processEvents()
        self.assertFalse(value.online.isChecked())
        release.set();self.wait(lambda:controller.reload_revision is not None)
        self.ack(controller)
        self.assertIn('Настройки применены',value.status.text())
        value.online.setChecked(True)
        value.close();value.show()
        self.wait(lambda:not controller.pending)
        self.assertFalse(value.online.isChecked())
    def test_invalid_shortcut_and_empty_dictionaries_have_accessible_retryable_controls(self):
        controller=self.Controller(self.engine,registry=self.registry,discover=lambda:[])
        self.controllers.append(controller)
        value=self.window(controller)
        self.assertIn('Локальные словари не найдены',value.dictionary_help.text())
        self.assertEqual(value.dictionaries.accessibleName(),'Порядок и включение словарей')
        value.shortcut.clear()
        self.assertEqual(value.status.text(),'Укажите одно сочетание клавиш')
        self.assertFalse(value.apply_button.isEnabled())
        self.assertTrue(value.close_button.isEnabled())

    def test_keyboard_controls_and_actual_key_label_after_ack(self):
        value=self.window()
        value.online.setFocus()
        QTest.keyClick(value.online,Qt.Key.Key_Space)
        self.assertFalse(value.online.isChecked())
        value.shortcut.setKeySequence(QKeySequence('Meta+Shift+F'))
        value.apply_button.setFocus()
        QTest.keyClick(value.apply_button,Qt.Key.Key_Return)
        self.wait(lambda:value.controller.reload_revision is not None)
        self.ack(value.controller)
        self.assertEqual(value.actual_binding.text(),'В KDE: Meta+Shift+F')
        value.close_button.setFocus();QTest.keyClick(value.close_button,Qt.Key.Key_Return)
        self.assertFalse(value.isVisible())

    def test_thread_start_failure_is_private_and_retryable(self):
        controller=self.controller()
        states=[];controller.state.connect(states.append)
        with patch.object(threading.Thread,'start',side_effect=RuntimeError('private detail')):
            controller.apply(self.snapshot())
        self.assertFalse(controller.pending)
        self.assertEqual(states[-1]['status'],'runtime_failed')
        controller.apply(self.snapshot())
        self.wait(lambda:controller.reload_revision is not None)
        self.ack(controller)
        self.assertEqual(states[-1]['status'],'success')

    def test_dictionary_folder_honors_first_override_and_enables_unchanged_apply(self):
        destination=self.root/'dictionary folder with spaces'
        other=self.root/'second'
        with patch.dict(os.environ,LOOKUP_DICTS=str(destination)+os.pathsep+str(other)):
            value=self.window()
            before=value.snapshot()
            self.assertEqual(value.folder_path.text(),str(destination.absolute()))
            self.assertFalse(destination.exists())
            self.assertTrue(value.folder_button.isVisible())
            self.assertTrue(value.folder_button.isEnabled())
            self.assertIn('StarDict',value.folder_help.text())
            self.assertIn('весь комплект',value.folder_help.text())
            opened=[]
            with patch.object(QDesktopServices,'openUrl',side_effect=lambda url:opened.append(url) or True):
                QTest.mouseClick(value.folder_button,Qt.MouseButton.LeftButton)
                self.wait(lambda:not value.controller.pending)
            self.assertTrue(destination.is_dir())
            self.assertEqual(Path(opened[0].toLocalFile()),destination.absolute())
            self.assertEqual(value.snapshot(),before)
            self.assertTrue(value.apply_button.isEnabled())
            value.close();value.show()
            self.wait(lambda:not value.controller.pending)
            self.assertTrue(value.apply_button.isEnabled())

    def test_dictionary_folder_empty_xdg_destination_and_private_failures_keep_path(self):
        data=self.root/'xdg data'
        with patch.dict(os.environ,XDG_DATA_HOME=str(data)):
            os.environ.pop('LOOKUP_DICTS',None)
            controller=self.Controller(self.engine,registry=self.registry,discover=lambda:[])
            self.controllers.append(controller)
            value=self.window(controller)
            destination=data/'lookup'/'dicts'
            self.assertEqual(value.folder_path.text(),str(destination.absolute()))
            self.assertFalse(destination.exists())
            self.assertTrue(value.folder_button.isEnabled())
            self.assertIn('Локальные словари не найдены',value.dictionary_help.text())
            with patch.object(Path,'mkdir',side_effect=OSError('private directory')), \
                 patch.object(QDesktopServices,'openUrl') as opened:
                QTest.mouseClick(value.folder_button,Qt.MouseButton.LeftButton)
                self.wait(lambda:not controller.pending)
            opened.assert_not_called()
            self.assertIn('Не удалось открыть папку словарей',value.status.text())
            self.assertNotIn('private',value.status.text())
            self.assertEqual(value.folder_path.text(),str(destination.absolute()))
            self.assertTrue(value.folder_path.textInteractionFlags() & Qt.TextInteractionFlag.TextSelectableByKeyboard)
            with patch.object(QDesktopServices,'openUrl',return_value=False):
                QTest.mouseClick(value.folder_button,Qt.MouseButton.LeftButton)
                self.wait(lambda:not controller.pending)
            self.assertIn('Скопируйте указанный путь',value.status.text())
            self.assertEqual(value.folder_path.text(),str(destination.absolute()))

    def test_dictionary_rescan_refreshes_rows_after_ack_and_preserves_draft_order(self):
        rows=[dict(id='found',name='Found')]
        controller=self.Controller(self.engine,registry=self.registry,discover=lambda:list(rows))
        self.controllers.append(controller)
        config.save(dict(dictionaries=[dict(id='missing',enabled=False),dict(id='found',enabled=True)]))
        value=self.window(controller)
        value.dictionaries.setCurrentRow(1);QTest.mouseClick(value.up_button,Qt.MouseButton.LeftButton)
        value.dictionaries.item(0).setCheckState(Qt.CheckState.Unchecked)
        draft=value.snapshot()['dictionaries']
        with patch.object(QDesktopServices,'openUrl',return_value=True):
            QTest.mouseClick(value.folder_button,Qt.MouseButton.LeftButton)
            self.wait(lambda:not controller.pending)
        self.assertEqual(value.snapshot()['dictionaries'],draft)
        rows.append(dict(id='copied',name='Copied dictionary'))
        QTest.mouseClick(value.apply_button,Qt.MouseButton.LeftButton)
        self.wait(lambda:controller.reload_revision is not None)
        self.assertEqual(value.dictionaries.count(),2)
        self.ack(controller)
        values=value.snapshot()['dictionaries']
        self.assertEqual(values[:2],draft)
        self.assertEqual(values[2],dict(id='copied',enabled=True))
        self.assertFalse(value.apply_button.isEnabled())

    def test_separator_only_override_keeps_other_settings_usable_without_inventing_folder(self):
        with patch.dict(os.environ,LOOKUP_DICTS=os.pathsep):
            controller=self.Controller(self.engine,registry=self.registry)
            self.controllers.append(controller)
            value=self.window(controller)
            self.assertEqual(dicts.dict_roots(),[])
            self.assertEqual(dicts.discover(),[])
            self.assertEqual(value.dictionaries.count(),0)
            self.assertEqual(value.folder_path.text(),'')
            self.assertTrue(value.folder_button.isVisible())
            self.assertFalse(value.folder_button.isEnabled())
            self.assertIn('LOOKUP_DICTS',value.folder_help.text())
            self.assertTrue(all(widget.isEnabled() for widget in (value.online,value.autostart,value.timeout)))
            value.online.setChecked(False);value.autostart.setChecked(False);value.timeout.setValue(9)
            self.assertTrue(value.apply_button.isEnabled())
            QTest.mouseClick(value.apply_button,Qt.MouseButton.LeftButton)
            self.wait(lambda:controller.reload_revision is not None)
            self.ack(controller)
            saved=config.load()
            self.assertEqual((saved.online,saved.autostart,saved.popup_timeout),(False,False,9))
            self.assertEqual(dicts.dict_roots(),[])


class LazyImportTests(unittest.TestCase):
    def test_import_is_stdlib_only(self):
        result=subprocess.run([sys.executable,'-S','-c',
            'import sys; import lookup.settings_gui; assert not any(n.startswith("PyQt6") for n in sys.modules)'],
            capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
