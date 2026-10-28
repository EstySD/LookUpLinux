"""Native settings controls and acknowledged asynchronous application."""
import os
import subprocess
import sys
import threading
import time
import unittest
from types import SimpleNamespace

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from tests._support import make_tempdir, forbid_network
from lookup import config, lifecycle

try:
    from PyQt6.QtCore import Qt, QEvent
    from PyQt6.QtGui import QKeySequence
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
        controller=self.controller()
        controller.apply(self.snapshot(shortcut_edited=True))
        self.wait(lambda:controller.reload_revision is not None)
        self.ack(controller)
        self.assertEqual(config.load().shortcut,'Meta+Shift+F')
        self.assertEqual(self.registry.changes,['Meta+Shift+F'])
        self.assertTrue(all(value!=threading.get_ident() for value in self.registry.threads))
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


class LazyImportTests(unittest.TestCase):
    def test_import_is_stdlib_only(self):
        result=subprocess.run([sys.executable,'-S','-c',
            'import sys; import lookup.settings_gui; assert not any(n.startswith("PyQt6") for n in sys.modules)'],
            capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
