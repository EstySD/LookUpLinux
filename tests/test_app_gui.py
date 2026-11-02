"""Native Qt presentation and queued-generation rules; no desktop required."""
import os
import subprocess
import sqlite3
import time
import unittest
from dataclasses import replace
from unittest import mock

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
try:
    from PyQt6.QtCore import Qt, QEvent, QTimer
    from PyQt6.QtGui import QFont, QPalette, QColor,QDesktopServices
    from PyQt6.QtWidgets import QApplication, QLabel, QTextEdit, QPushButton
    from PyQt6.QtTest import QTest
except ImportError:
    QApplication=None

from lookup import app, translate
from lookup.dicts import Article
from lookup.platform import Monitor
from lookup import learning
from lookup.store import open_store, upsert_word, MigrationError
from tests._support import make_tempdir


class FakeEngine:
    def __init__(self,publish,**kwargs):
        self.publish=publish
        self.generation=0
        self.pending=[]
        self.stopping=False
        self.reloads=[]
    def begin(self):
        self.generation+=1
        return self.generation
    def enqueue(self,identity,snapshot=None):
        self.pending.append(identity)
        self.snapshot=snapshot
    def enqueue_scene(self,identity,snapshot=None):
        self.enqueue(identity,snapshot)
        return True
    def select_scene(self,identity,session_id,point):
        self.selects=getattr(self,'selects',[])+[(identity,session_id,point)]
        return True
    def close_scene(self,session_id=None):
        self.closed=getattr(self,'closed',[])+[session_id]
        self.generation+=1
        return True
    def current(self,identity):
        return identity==self.generation and not self.stopping
    def dismiss(self,identity):
        if self.current(identity):self.generation+=1
    def request_reload(self):
        if self.stopping:return None
        self.generation+=1
        revision=len(self.reloads)+1
        self.reloads.append(revision)
        return revision
    def stop(self):self.stopping=True
    def is_alive(self):return False
    def join(self,timeout):pass


class TriggerSpawnTests(unittest.TestCase):
    def test_cold_spawn_inherits_stderr_only_for_exact_timing_opt_in(self):
        from lookup import gui
        for setting,stderr in ((None,subprocess.DEVNULL),('0',subprocess.DEVNULL),
                               ('1',None),('true',subprocess.DEVNULL)):
            with self.subTest(setting=setting):
                env={'PATH':'synthetic-bin'}
                if setting is not None:env['LOOKUP_TIMING']=setting
                core=mock.Mock()
                dbus=mock.Mock()
                bus=dbus.QDBusConnection.sessionBus.return_value
                missing=mock.Mock()
                missing.type.return_value=dbus.QDBusMessage.MessageType.ErrorMessage
                ready=mock.Mock()
                ready.arguments.return_value=[1]
                bus.call.side_effect=[missing,ready]
                registered=bus.interface.return_value.isServiceRegistered.return_value
                registered.isValid.return_value=True
                registered.value.return_value=False
                command=['/usr/bin/lookup','--app']
                with mock.patch.dict(os.environ,env,clear=True), \
                     mock.patch.dict('sys.modules',{'PyQt6.QtCore':core,'PyQt6.QtDBus':dbus}), \
                     mock.patch.object(gui.platform,'session_env',return_value=env), \
                     mock.patch('lookup.lifecycle.launch_command',return_value=(command,'/safe/path')) as launch, \
                     mock.patch.object(gui.subprocess,'Popen') as spawn:
                    self.assertEqual(gui.run(trigger=True),0)
                launch.assert_called_once_with('--app')
                spawn.assert_called_once_with(command,env=env,cwd='/safe/path',
                    stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                    stderr=stderr,start_new_session=True)
                self.assertEqual(bus.call.call_count,2)


@unittest.skipIf(QApplication is None,'PyQt6 unavailable')
class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application=QApplication.instance() or QApplication([])
    def setUp(self):
        self.root=make_tempdir(self)
        from lookup import gui
        self.Popup,self.Owner=gui.components()
        self.owner=self.Owner({},engine_factory=FakeEngine,focus=False,on_quit=lambda:None)
        owner=self.owner
        def close():
            owner.quit()
            deadline=time.monotonic()+2
            while owner.settings_controller.is_alive() and time.monotonic()<deadline:
                self.application.processEvents();QTest.qWait(5)
            owner.popup.deleteLater()
            owner.menu.deleteLater()
            owner.deleteLater()
            self.application.sendPostedEvents(None,QEvent.Type.DeferredDelete)
            self.application.processEvents()
        self.addCleanup(close)
        self.owner.Trigger('')
        self.identity=self.owner.engine.generation
        self.monitor=Monitor('public',0,0,1000,800,1)
    def event(self,stage='ready',result=None,**kwargs):
        return app.Event(self.identity,stage,result=result,point=(100,100),monitor=self.monitor,mode='primary',**kwargs)
    def enter_scene(self):
        from PyQt6.QtCore import QBuffer,QIODevice
        from PyQt6.QtGui import QImage,QColor
        from lookup.capture import Capture
        image=QImage(1000,800,QImage.Format.Format_RGB32);image.fill(QColor('white'))
        output=QBuffer();output.open(QIODevice.OpenModeFlag.WriteOnly);image.save(output,'PNG')
        scene=app.Scene(self.identity,app.Frozen('ocr',(100,100),self.monitor,
            image=Capture(bytes(output.data()),1000,800,'public',0)))
        self.owner.receive(replace(self.event('scene'),mode='ocr',scene=scene))
        return self.owner.scene_window

    def test_retained_scene_reselects_without_reopening_or_stale_result(self):
        layer=self.enter_scene()
        image=layer._image
        self.assertTrue(layer.isVisible())
        self.owner.receive(self.event('frozen'))
        self.owner.receive(self.event(result=self.result(),selection_box=(80,80,50,20)))
        self.assertFalse(layer.selection_rect().isEmpty())
        layer.selected.emit((350,250))
        identity=self.owner.engine.generation
        self.assertEqual(self.owner.engine.selects,[(identity,self.identity,(350,250))])
        self.assertIs(layer._image,image)
        self.owner.receive(self.event(result=self.result()))
        self.assertIsNone(self.owner._displayed)
        self.owner.receive(replace(self.event(result=replace(self.result(),translation='слово'),context='new context'),id=identity))
        self.assertEqual(self.owner._displayed[0],identity)
        self.assertEqual(self.owner._displayed[1]['context'],'new context')
        self.assertIs(self.owner.scene_window,layer)

    def test_scene_all_session_exit_routes_release_image_and_cancel(self):
        for action in ('escape','popup_close','layer_close','timeout','repeat','settings','external','error'):
            with self.subTest(action=action):
                if not self.owner.engine.current(self.identity):
                    self.owner.Trigger('');self.identity=self.owner.engine.generation
                layer=self.enter_scene()
                self.owner.receive(self.event('frozen'))
                if action=='escape':QTest.keyClick(self.owner.popup,Qt.Key.Key_Escape)
                elif action=='popup_close':self.owner.popup.close()
                elif action=='layer_close':layer.close_button.click()
                elif action=='timeout':self.owner.popup.timer.timeout.emit()
                elif action=='repeat':self.owner.Trigger('')
                elif action=='settings':self.owner._invalidate_settings()
                elif action=='external':self.owner.scene_focus_changed(None)
                elif action=='error':self.owner.receive(self.event('error',error='ocr_failed'))
                self.assertIsNone(self.owner.scene_window)
                self.assertIsNone(layer._image)
                self.assertFalse(layer.isVisible())
                if action!='error':self.assertFalse(self.owner.popup.isVisible())
                else:self.assertIn('Не удалось распознать',self.owner.popup.title.text())
                self.assertIn(self.identity,self.owner.engine.closed)

    def test_scene_internal_focus_no_hit_primary_and_shutdown(self):
        self.assertIsNone(self.owner.scene_window)
        self.owner.receive(self.event(result=self.result()))
        self.assertIsNone(self.owner.scene_window)
        layer=self.enter_scene()
        self.owner.scene_focus_changed(layer.windowHandle())
        self.owner.scene_focus_changed(self.owner.popup.windowHandle())
        self.assertIs(self.owner.scene_window,layer)
        self.owner.receive(self.event('error',error='not_found'))
        self.assertIs(self.owner.scene_window,layer)
        self.assertTrue(layer.isVisible())
        self.assertIn('Нажмите на другое слово',layer.status.accessibleName())
        self.owner.quit()
        self.assertIsNone(layer._image)
        self.assertIsNone(self.owner.scene_window)

    def test_scene_focus_commit_delay_duplicate_activation_and_hidden_timeout(self):
        layer=self.enter_scene()
        generation=self.owner.engine.generation
        with mock.patch.object(app.capture,'take_hotkey',side_effect=app.platform.PlatformError('hotkey_consumed')):
            self.owner.Trigger('')
        self.assertEqual(self.owner.engine.generation,generation)
        self.assertIs(self.owner.scene_window,layer)
        self.owner._scene_focus_event(None)
        QTest.qWait(90)
        self.assertIs(self.owner.scene_window,layer)
        self.owner._scene_focus_event(layer.windowHandle())
        with mock.patch.object(QApplication,'focusWindow',return_value=layer.windowHandle()):
            self.owner._scene_focus_event(None);QTest.qWait(90)
        self.assertIs(self.owner.scene_window,layer)
        self.owner.receive(self.event('error',error='not_found'))
        self.owner.popup.timer.start(1000)
        QTest.keyClick(layer,Qt.Key.Key_A)
        self.assertGreater(self.owner.popup.timer.remainingTime(),19000)
        with mock.patch.object(QApplication,'focusWindow',return_value=None):
            self.owner._scene_focus_event(None);QTest.qWait(90)
        self.assertIsNone(self.owner.scene_window)
        self.assertIsNone(layer._image)

    def test_bad_scene_and_pending_capture_cannot_leave_owned_surfaces(self):
        from lookup.capture import Capture
        bad=app.Scene(self.identity,app.Frozen('ocr',(100,100),self.monitor,
            image=Capture(b'bad',1000,800,'public',0)))
        self.owner.receive(replace(self.event('scene'),mode='ocr',scene=bad))
        self.assertIsNone(self.owner.scene_window)
        self.assertIn('Не удалось получить снимок',self.owner.popup.title.text())
        self.owner.Trigger('');self.identity=self.owner.engine.generation
        self.owner._enqueue(self.identity)
        self.owner._invalidate_settings()
        self.enter_scene()
        self.assertIsNone(self.owner.scene_window)

    def test_scene_placement_failure_releases_layer_before_ordinary_error(self):
        for waiting_paint in (True,False):
            with self.subTest(waiting_paint=waiting_paint):
                self.owner.Trigger('');self.identity=self.owner.engine.generation
                layer=self.enter_scene()
                ready=self.event(result=replace(self.result(),translation='слово'))
                self.owner.receive(ready)
                revision=self.owner.presentations
                self.owner._paint_revision=revision if waiting_paint else None
                self.owner._focus_pending=(self.identity,revision,(1,1,10,10))
                self.owner._waiting_ready=(ready,time.monotonic()+1)
                self.owner._waiting_context=self.event('context',result=self.result())
                self.owner.focus_done((self.identity,revision,None,'focus_failed'))
                self.assertIsNone(self.owner.scene_window)
                self.assertIsNone(layer._image)
                self.assertFalse(layer.isVisible())
                self.assertIsNone(self.owner._waiting_ready)
                self.assertIsNone(self.owner._waiting_context)
                self.assertIsNone(self.owner._displayed)
                self.assertIsNone(self.owner._paint_revision)
                self.assertTrue(self.owner.popup.updatesEnabled())
                self.assertIn('Не удалось разместить',self.owner.popup.title.text())
                self.assertFalse(self.owner.engine.current(self.identity))
                self.owner.receive(ready)
                self.assertIn('Не удалось разместить',self.owner.popup.title.text())
    def test_hidden_popup_enqueues_without_a_hide_delay(self):
        self.owner.popup.hide_for_capture()
        self.owner.engine.pending.clear()
        with mock.patch.object(QTimer,'singleShot') as timer:
            self.owner.Trigger('')
        self.assertEqual(self.owner.engine.pending,[self.owner.engine.generation])
        timer.assert_not_called()
    def test_hotkey_snapshot_bypasses_hide_delay_and_is_queued_with_request(self):
        self.owner.popup.show()
        self.owner.engine.pending.clear()
        snapshot=mock.Mock(input_ns=1,capture_ns=2)
        with mock.patch.object(app.capture,'take_hotkey',return_value=snapshot), \
             mock.patch.object(QTimer,'singleShot') as timer:
            self.owner.Trigger('')
        timer.assert_not_called()
        self.assertFalse(self.owner.popup.isVisible())
        self.assertEqual(self.owner.engine.pending,[self.owner.engine.generation])
        self.assertIs(self.owner.engine.snapshot,snapshot)
    def test_duplicate_activation_does_not_cancel_the_request_that_consumed_latest_frame(self):
        generation=self.owner.engine.generation
        pending=list(self.owner.engine.pending)
        with mock.patch.object(app.capture,'take_hotkey',side_effect=app.platform.PlatformError('hotkey_consumed')):
            self.owner.Trigger('')
        self.assertEqual(self.owner.engine.generation,generation)
        self.assertEqual(self.owner.engine.pending,pending)
    def test_visible_popup_retains_hide_delay_and_discards_superseded_capture(self):
        self.owner.popup.show()
        self.owner.engine.pending.clear()
        with mock.patch.object(QTimer,'singleShot') as timer:
            self.owner.Trigger('')
        self.assertFalse(self.owner.popup.isVisible())
        self.assertEqual(self.owner.engine.pending,[])
        self.assertEqual(timer.call_args.args[0],75)
        self.owner.Trigger('')
        latest=self.owner.engine.generation
        timer.call_args.args[1]()
        self.assertEqual(self.owner.engine.pending,[latest])
    def wait_for_dismissal(self):
        deadline=time.monotonic()+1
        while (self.owner.popup.isVisible() or self.owner.engine.current(self.identity)) and time.monotonic()<deadline:
            self.application.processEvents()
            QTest.qWait(1)
    def result(self):
        first=Article('First','word','wɜːd',(('noun',('значение','слово')),),'<img src="file:///private"> literal article')
        second=Article('Second','word',None,(), 'Другой словарь')
        return translate.Result('word','word',articles=(first,second),lemma='lemma',saved=True,count=3,context_pending=True)
    def texts(self):
        return '\n'.join(label.text() for label in self.owner.popup.findChildren(QLabel))+ '\n' + '\n'.join(widget.toPlainText() for widget in self.owner.popup.findChildren(QTextEdit))
    def preferences(self,**changes):
        from lookup.config import Config
        deadline=time.monotonic()+2
        while self.owner.settings_controller.pending and time.monotonic()<deadline:
            self.application.processEvents();QTest.qWait(5)
        self.owner._settings_applied(replace(Config(),**changes))

    def test_compact_offline_summaries_precede_expandable_articles(self):
        self.preferences()
        first=Article('Long','word',None,(('noun',('первое значение',)),),'long detail '*1500)
        second=Article('Useful','word',None,(('noun',('нужный перевод',)),),'second detail')
        raw=Article('Raw','word',None,(),'plain preview '*100)
        value=replace(self.result(),articles=(first,second,raw),online_enabled=False)
        self.owner.receive(self.event(result=value,context='source context'))
        popup=self.owner.popup
        self.assertEqual(popup.title.text(),'word')
        widgets=[popup.body.itemAt(i).widget() for i in range(popup.body.count())]
        summaries=[widget for widget in widgets if isinstance(widget,QTextEdit) and not widget.isHidden()]
        self.assertIn('нужный перевод','\n'.join(widget.toPlainText() for widget in summaries))
        preview=next(widget for widget in summaries if widget.toPlainText().startswith('plain preview'))
        self.assertLessEqual(len(preview.toPlainText()),240)
        self.assertTrue(preview.toPlainText().endswith('…'))
        details=next(widget for widget in widgets if isinstance(widget,QTextEdit) and widget.toPlainText().startswith('long detail'))
        self.assertTrue(details.isHidden())
        self.assertLess(widgets.index(preview),widgets.index(details))
        buttons=[widget for widget in widgets if isinstance(widget,QPushButton)]
        self.assertEqual(len(buttons),3)
        self.assertTrue(all(button.isCheckable() and button.accessibleName() for button in buttons))
        identity=self.owner.engine.generation
        QTest.keyClick(buttons[0],Qt.Key.Key_Space)
        self.assertFalse(details.isHidden())
        self.assertTrue(buttons[0].isChecked())
        self.assertLessEqual(popup.height(),540)
        QTest.keyClick(buttons[0],Qt.Key.Key_Space)
        self.assertTrue(details.isHidden())
        self.assertEqual(self.owner.engine.generation,identity)
        self.owner.receive(self.event(result=value))
        self.assertTrue(all(not button.isChecked() for button in popup.findChildren(QPushButton) if button.isCheckable() and not button.isHidden()))

    def test_hidden_blocks_stay_hidden_after_late_updates_and_cards_keep_context(self):
        self.preferences(popup_show_meaning=False)
        value=replace(self.result(),translation='слово',context_meaning='значение',context_translation='перевод',
                      meaning_provider='google-gtx-marked-v1',context_complete=True)
        self.owner.receive(self.event(result=value,context='The word has meaning.',span=(4,8)))
        popup=self.owner.popup
        for widget in (popup.meaning_heading,popup.meaning_value,popup.context_heading,popup.context_source,popup.context_fragment,popup.context_value):
            self.assertTrue(widget.isHidden())
        self.owner.receive(self.event('context',result=replace(value,context_meaning='поздно',context_translation='поздний перевод'),
                                      context='The word has meaning.',span=(4,8)))
        self.assertTrue(popup.meaning_value.isHidden())

        self.assertTrue(popup.context_value.isHidden())
        popup.card_button.click()
        conn=open_store();self.addCleanup(conn.close)
        card=learning.get_card(conn,'word')
        self.assertEqual((card['translation'],card['context'],card['span']),('поздно','The word has meaning.',(4,8)))
        self.preferences(popup_show_context=True,popup_show_meaning=False)
        self.owner.receive(self.event(result=value,context='Visible source'))
        self.assertFalse(popup.context_source.isHidden())
        self.assertFalse(popup.context_value.isHidden())
        self.assertTrue(popup.meaning_value.isHidden())

    def test_article_disclosure_elides_long_name_preserving_action(self):
        self.preferences()
        name='Very long dictionary name '*50
        article=replace(self.result().articles[0],dict_name=name)
        self.owner.receive(self.event(result=replace(self.result(),articles=(article,))))
        heading=next(widget for widget in self.owner.popup.findChildren(QTextEdit) if widget.toPlainText().startswith('Словарь:'))
        self.assertLessEqual(len(heading.toPlainText()),89)
        self.assertEqual(heading.toolTip(),name)
        button=self.owner.popup._article_buttons[0]
        self.assertTrue(button.text().startswith('Показать полную статью — '))
        self.assertLess(len(button.text()),len(name))
        self.assertEqual(button.accessibleName(),'Показать полную статью — '+name)
        self.assertEqual(button.toolTip(),button.accessibleName())
        self.assertLessEqual(button.fontMetrics().horizontalAdvance(button.text()),self.owner.popup.width()-56)
        QTest.keyClick(button,Qt.Key.Key_Return)
        self.assertTrue(button.isChecked())
        self.assertTrue(button.text().startswith('Свернуть статью — '))

    def test_owner_initialization_loads_saved_popup_preferences(self):
        from lookup import config
        config.save(dict(popup_show_context=True,popup_show_meaning=False,popup_expand_articles=True))
        owner=self.Owner({},engine_factory=FakeEngine,focus=False,on_quit=lambda:None)
        try:
            deadline=time.monotonic()+2
            while owner.settings_controller.pending and time.monotonic()<deadline:
                self.application.processEvents();QTest.qWait(5)
            owner.Trigger('')
            owner.receive(app.Event(owner.engine.generation,'ready',result=replace(self.result(),context_meaning='hidden'),
                context='Persisted source',point=(100,100),monitor=self.monitor,mode='primary'))
            self.assertFalse(owner.popup.context_source.isHidden())
            self.assertTrue(owner.popup.meaning_value.isHidden())
            self.assertTrue(all(button.isChecked() for button in owner.popup.findChildren(QPushButton) if button.isCheckable()))
        finally:
            owner.quit();owner.popup.deleteLater();owner.menu.deleteLater();owner.deleteLater()

    def test_actual_fields_order_plain_text_and_no_invented_metadata(self):
        self.preferences(popup_show_context=True)
        self.owner.receive(self.event(result=self.result(),context='Public source'))
        text=self.texts()
        for expected in ('word','wɜːd','lemma','значение','Public source','Искали 3 раз','file:///private'):
            self.assertIn(expected,text)
        self.assertLess(text.index('First'),text.index('Second'))
        self.assertTrue(all(label.textFormat()==Qt.TextFormat.PlainText for label in self.owner.popup.findChildren(QLabel)))
        self.assertTrue(all(not widget.acceptRichText() for widget in self.owner.popup.findChildren(QTextEdit)))
        self.assertEqual(self.owner.popup.close_button.accessibleName(),'Закрыть карточку')

    def test_stale_queued_signal_and_late_context_cannot_reopen_dismissed_card(self):
        self.owner.receive(self.event('frozen'))
        self.owner.popup.dismiss()
        self.owner.receive(self.event(result=self.result()))
        self.owner.receive(self.event('context',result=self.result()))
        self.assertFalse(self.owner.popup.isVisible())
        self.assertFalse(self.owner.engine.current(self.identity))

    def test_context_update_preserves_count_focus_and_inactivity_deadline(self):
        value=self.result()
        self.owner.receive(self.event(result=value,context='Public source'))
        self.application.processEvents()
        remaining=self.owner.popup.timer.remainingTime()
        positions=self.owner.presentations
        self.owner.receive(self.event('context',result=replace(value,context_pending=False,context_translation='Контекст'),context='Public source'))
        self.assertLessEqual(self.owner.popup.timer.remainingTime(),remaining)
        self.assertEqual(self.owner.presentations,positions)
        self.assertIn('Контекст',self.texts())
        self.assertIn('Искали 3 раз',self.texts())

    def test_meaning_and_sentence_update_independently_without_resetting_article(self):
        value=replace(self.result(),meaning_pending=True,context_complete=True)
        self.owner.receive(self.event(result=value,context='The bank holds money.'))
        popup=self.owner.popup
        self.assertTrue(popup.context_fragment.isHidden())
        article=popup.body.itemAt(popup.body.count()-1).widget()
        remaining=popup.timer.remainingTime()
        presentations=self.owner.presentations
        self.assertIn('Определяем значение в контексте',self.texts())
        final=replace(value,meaning_pending=False,context_meaning='банк',meaning_provider='google-gtx-marked-v1',
                      context_pending=False,context_translation='Банк хранит деньги.')
        self.owner.receive(self.event('context',result=final))
        self.assertEqual(popup.meaning_value.text(),'банк')
        self.assertEqual(popup.meaning_value.accessibleName(),'Значение в контексте')
        self.assertIn('Банк хранит деньги.',popup.context_value.text())
        self.assertIs(popup.body.itemAt(popup.body.count()-1).widget(),article)
        self.assertEqual(self.owner.presentations,presentations)
        self.assertLessEqual(popup.timer.remainingTime(),remaining)
        self.assertIn('Искали 3 раз',self.texts())

    def test_meaning_failures_fragment_and_plain_text_remain_readable(self):
        self.preferences(popup_show_context=True)
        value=replace(self.result(),context_pending=False,meaning_error='no_context')
        self.owner.receive(self.event(result=value,context='available source'))
        self.assertFalse(self.owner.popup.context_fragment.isHidden())
        self.assertIn('Показан доступный фрагмент',self.texts())
        self.assertIn('Недостаточно надёжного контекста',self.texts())
        self.assertIn('Другой словарь',self.texts())
        for reason,copy in (('disabled','выключен'),('busy','пока недоступно'),
                            ('timeout','время ожидания'),('no_network','нет сети'),
                            ('bad_response','надёжно определить')):
            self.owner.receive(self.event('context',result=replace(value,meaning_error=reason)))
            self.assertIn(copy,self.owner.popup.meaning_value.text())
        self.owner.receive(self.event('context',result=replace(value,meaning_error=None,
                              context_meaning='<b>банк</b>')))
        self.assertEqual(self.owner.popup.meaning_value.toPlainText(),'<b>банк</b>')
        self.assertFalse(self.owner.popup.meaning_value.acceptRichText())

    def test_late_meaning_save_warning_keeps_article_and_valid_lookup_count(self):
        value=replace(self.result(),meaning_pending=True,context_complete=True)
        self.owner.receive(self.event(result=value,context='The bank holds money.'))
        self.owner.receive(self.event('context',result=replace(value,meaning_pending=False,
                           context_meaning='банк',meaning_save_error=True)))
        self.assertIn('Не удалось сохранить значение в контексте',self.owner.popup.footer.text())
        self.assertIn('Другой словарь',self.texts())
        self.assertEqual(self.owner.popup.meaning_value.text(),'банк')

    def test_popup_add_freezes_displayed_pair_without_reading_newer_history(self):
        value=replace(self.result(),translation='слово',context_meaning='значение',
                      meaning_provider='google-gtx-marked-v1',context_complete=True)
        self.owner.receive(self.event(result=value,context='The word has meaning.',span=(4,8)))
        conn=open_store()
        self.addCleanup(conn.close)
        upsert_word(conn,'word','более новый перевод','Different word context.')
        self.owner.popup.card_button.click()
        card=learning.get_card(conn,'word')
        self.assertEqual((card['translation'],card['context'],card['span']),
                         ('значение','The word has meaning.',(4,8)))
        self.assertIn('Добавлено',self.owner.popup.card_status.text())
        self.assertIn('Искали 3',self.owner.popup.footer.text())
        self.owner.receive(self.event('context',result=replace(value,context_meaning='другое значение'),
                                      context='The word has meaning.',span=(4,8)))
        self.assertEqual(learning.get_card(conn,'word'),card)
        self.assertFalse(self.owner.popup.card_button.isEnabled())
        self.owner._known_cards.clear()  # A restarted owner discovers the existing immutable card.
        self.owner.receive(self.event(result=value,context='The word has meaning.',span=(4,8)))
        self.owner.popup.card_button.click()
        self.assertIn('Уже в карточках',self.owner.popup.card_status.text())
        self.assertEqual(learning.get_card(conn,'word'),card)

    def test_popup_fallback_card_does_not_follow_late_meaning(self):
        value=replace(self.result(),translation='слово',meaning_pending=True,context_complete=True)
        self.owner.receive(self.event(result=value,context='The word has meaning.',span=(4,8)))
        self.owner.popup.card_button.click()
        conn=open_store()
        self.addCleanup(conn.close)
        self.assertEqual(learning.get_card(conn,'word')['translation'],'слово')
        final=replace(value,meaning_pending=False,context_meaning='значение',meaning_provider='google-gtx-marked-v1')
        self.owner.receive(self.event('context',result=final,context='The word has meaning.',span=(4,8)))
        self.assertEqual(learning.get_card(conn,'word')['translation'],'слово')
        self.assertEqual(conn.execute('SELECT count(*) FROM words').fetchone()[0],0)

    def test_closed_loading_sentence_and_missing_translation_cannot_add(self):
        value=replace(self.result(),translation='слово')
        self.owner.receive(self.event(result=value))
        self.owner.popup.dismiss()
        self.owner.add_card()
        self.assertIsNone(self.owner._learning_conn)
        self.owner.Trigger('')
        self.identity=self.owner.engine.generation
        for event in (self.event('frozen'),self.event(result=translate.Result('sentence','A whole sentence.')),
                      self.event(result=self.result())):
            self.owner.receive(event)
            self.assertFalse(self.owner.popup.card_button.isEnabled())
            self.owner.add_card()
        self.assertIsNone(self.owner._learning_conn)

    def test_tray_windows_reuse_one_gui_connection_and_close_it_on_quit(self):
        self.owner.open_words()
        words=self.owner.words_window
        self.assertIsNotNone(words)
        self.assertTrue(words.isVisible())
        self.owner.open_words()
        self.assertIs(self.owner.words_window,words)
        self.owner.open_review()
        review=self.owner.review_window
        self.assertTrue(review.isVisible())
        self.owner.open_review()
        self.assertIs(self.owner.review_window,review)
        conn=self.owner._learning_conn
        self.assertEqual(conn.execute('PRAGMA busy_timeout').fetchone()[0],50)
        self.owner.quit()
        with self.assertRaises(sqlite3.ProgrammingError):conn.execute('SELECT 1')

    def test_gui_open_and_card_errors_are_private_and_retryable(self):
        value=replace(self.result(),translation='слово')
        self.owner.receive(self.event(result=value))
        with mock.patch('lookup.store.open_store',side_effect=MigrationError('private sentinel')), \
             mock.patch('PyQt6.QtWidgets.QMessageBox.warning') as warning:
            self.owner.add_card()
            self.assertIn('Не удалось сохранить карточку',self.owner.popup.card_status.text())
            self.assertNotIn('private sentinel',self.texts())
            self.owner.open_words()
            warning.assert_called_once()
            self.assertNotIn('private sentinel',str(warning.call_args))
        self.owner.add_card()
        self.assertIn('Добавлено',self.owner.popup.card_status.text())

    def test_loading_to_result_sizes_new_children_before_next_event_turn(self):
        self.owner.receive(self.event('frozen'))
        self.application.processEvents()
        loading_height=self.owner.popup.height()
        self.owner.receive(self.event(result=self.result(),context='Public source'))
        self.assertGreater(self.owner.popup.height(),loading_height+80)

    def test_escape_timeout_and_programmatic_hide_have_distinct_effect(self):
        self.owner.receive(self.event('frozen'))
        self.owner.popup.hide_for_capture()
        self.assertTrue(self.owner.engine.current(self.identity))
        self.owner.receive(self.event(result=self.result()))
        QTest.keyClick(self.owner.popup,Qt.Key.Key_Escape)
        self.assertFalse(self.owner.engine.current(self.identity))
        self.owner.Trigger('')
        self.identity=self.owner.engine.generation
        self.owner.receive(self.event('frozen'))
        self.owner.popup.timer.start(20)
        self.wait_for_dismissal()
        self.assertFalse(self.owner.popup.isVisible())
        self.assertFalse(self.owner.engine.current(self.identity))

    def test_timeout_dispatch_after_queued_gui_work(self):
        self.owner.receive(self.event('frozen'))
        QTimer.singleShot(0,lambda:time.sleep(.08))
        self.owner.popup.timer.start(20)
        self.wait_for_dismissal()
        self.assertFalse(self.owner.popup.isVisible())
        self.assertFalse(self.owner.engine.current(self.identity))

    def test_errors_and_save_failure_are_readable_without_false_count(self):
        self.owner.receive(self.event('error',error='missing_tesseract'))
        self.assertIn('Не установлен пакет tesseract',self.texts())
        value=replace(self.result(),saved=False,count=None)
        self.owner.receive(self.event(result=value,save_error='unavailable'))
        self.assertIn('Не удалось сохранить поиск',self.texts())
        self.assertNotIn('Искали 3',self.texts())
        self.assertIn('значение',self.texts())
        self.owner.receive(self.event('error',error='ocr_timeout'))
        self.assertIn('Не удалось распознать текст вовремя',self.texts())

    def test_native_palette_font_long_text_and_disabled_future_actions(self):
        self.preferences(popup_expand_articles=True)
        value=self.result()
        value.articles=(replace(value.articles[0],text='unbroken'*1000),)
        self.owner.receive(self.event(result=value))
        self.application.processEvents()
        self.assertLessEqual(self.owner.popup.width(),440)
        self.assertLessEqual(self.owner.popup.height(),540)
        self.assertGreater(self.owner.popup.height(),400)
        self.assertEqual(self.owner.popup.scroll.horizontalScrollBarPolicy(),Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        article=next(widget for widget in self.owner.popup.findChildren(QTextEdit) if widget.toPlainText().startswith('unbroken'))
        self.assertGreater(article.height(),article.fontMetrics().lineSpacing()*10)
        self.assertEqual(article.verticalScrollBarPolicy(),Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.assertEqual([action.isEnabled() for action in self.owner.future_actions],[True,True,True])
        self.assertEqual([a.text() for a in self.owner.future_actions],['Слова','Повторение','Настройки'])

    def test_settings_reuses_window_ack_is_not_lookup_identity_and_timeout_is_next_popup(self):
        from tests.test_settings_gui import Registry
        from lookup import config
        controller=self.owner.settings_controller
        controller.registry=Registry()
        states=[]
        controller.state.connect(states.append)
        self.owner.open_settings()
        window=self.owner.settings_window
        def wait(predicate):
            deadline=time.monotonic()+3
            while time.monotonic()<deadline:
                self.application.processEvents()
                if predicate():return
                QTest.qWait(5)
            self.fail('settings acknowledgement did not arrive')
        wait(lambda:not controller.pending)
        self.assertIsNotNone(window._baseline,[(value.get('kind'),value.get('status')) for value in states])
        self.owner.receive(self.event(result=self.result(),context='Public source'))
        self.assertTrue(self.owner.popup.isVisible())
        old_identity=self.identity
        window.timeout.setValue(7)
        window.popup_show_context.setChecked(True)
        window.popup_show_meaning.setChecked(False)
        window.popup_expand_articles.setChecked(True)
        self.assertTrue(window.apply_button.isEnabled(),repr(window.snapshot()))
        QTest.mouseClick(window.apply_button,Qt.MouseButton.LeftButton)
        wait(lambda:controller.reload_revision is not None)
        revision=controller.reload_revision
        self.assertFalse(self.owner.popup.isVisible())
        self.assertIsNone(self.owner._displayed)
        self.assertEqual(self.owner._popup_timeout,20)
        self.owner.receive(app.Event(old_identity,'ready',result=self.result(),context='stale'))
        self.assertFalse(self.owner.popup.isVisible())
        self.owner.receive(app.Event(old_identity,'reload',reload_revision=revision+1))
        self.assertTrue(controller.pending)
        self.owner.receive(app.Event(-100,'reload',reload_revision=revision))
        self.assertFalse(controller.pending)
        self.assertEqual(self.owner._popup_timeout,7)
        self.identity=self.owner.engine.begin()
        self.owner.receive(self.event(result=self.result(),context='Public source'))
        self.assertEqual(self.owner.popup._duration,7000)
        self.assertEqual(self.owner.popup.timer.interval(),7000)
        self.assertFalse(self.owner.popup.context_source.isHidden())
        self.assertTrue(self.owner.popup.meaning_value.isHidden())
        self.assertTrue(all(button.isChecked() for button in self.owner.popup.findChildren(QPushButton) if button.isCheckable() and not button.isHidden()))
        window.close();self.owner.open_settings()
        wait(lambda:not controller.pending)
        self.assertIs(self.owner.settings_window,window)
        self.assertEqual(config.load().popup_timeout,7)

    def test_quit_rolls_back_pending_settings_before_owner_shutdown_finishes(self):
        from lookup import config
        from tests.test_settings_gui import Registry
        controller=self.owner.settings_controller
        deadline=time.monotonic()+2
        while controller.pending and time.monotonic()<deadline:
            self.application.processEvents();QTest.qWait(5)
        controller.registry=Registry()
        before=config.load()
        done=[]
        self.owner._on_quit=lambda:done.append(True)
        controller.apply(dict(dictionaries=[],online=False,popup_timeout=4,autostart=False,
                              shortcut='Meta+Shift+F',shortcut_edited=True))
        deadline=time.monotonic()+2
        while controller.reload_revision is None and time.monotonic()<deadline:
            self.application.processEvents();QTest.qWait(5)
        self.assertIsNotNone(controller.reload_revision)
        self.owner.quit()
        deadline=time.monotonic()+2
        while not done and time.monotonic()<deadline:
            self.application.processEvents();QTest.qWait(5)
        self.assertTrue(done)
        self.assertFalse(controller.pending)
        self.assertEqual(config.load(),before)

    def test_quit_and_qt_events_remain_responsive_while_second_ocr_child_finishes(self):
        import contextlib,threading
        from lookup import gui,config,ocr
        from tests.test_app import fallback_source
        from tests.test_ocr import tsv
        entered,release=threading.Event(),threading.Event();closed=[]
        self.addCleanup(release.set)
        @contextlib.contextmanager
        def resources():yield app.Resources(config.Config(online=False))
        def child(argv,**kwargs):
            output=tsv()
            if argv[6]=='11':
                entered.set();release.wait(3)
                output=tsv((5,1,1,1,1,1,48,48,60,20,95,'word'))
            return subprocess.CompletedProcess(argv,0,output,b'')
        _,Owner=gui.components()
        owner=Owner({},engine_factory=lambda publish,**kwargs:app.Engine(publish,source=fallback_source(),resources=resources),
                    focus=False,on_quit=lambda:closed.append(True))
        def wait(predicate):
            deadline=time.monotonic()+3
            while time.monotonic()<deadline:
                self.application.processEvents()
                if predicate():return
                QTest.qWait(5)
            self.fail('held OCR owner did not reach expected state')
        def cleanup():
            release.set();owner.quit()
            wait(lambda:not owner.engine.is_alive() and not owner.settings_controller.is_alive())
            owner.popup.deleteLater();owner.menu.deleteLater();owner.deleteLater()
            self.application.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        self.addCleanup(cleanup)
        with mock.patch.object(ocr.subprocess,'run',side_effect=child):
            wait(lambda:not owner.settings_controller.pending)
            owner.Trigger('');wait(entered.is_set)
            alive=[]
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0,lambda:alive.append(True));QTest.qWait(30)
            self.assertTrue(alive)
            owner.quit();QTest.qWait(30)
            self.assertEqual(closed,[]);self.assertTrue(owner.engine.is_alive())
            release.set();wait(lambda:bool(closed))
        self.assertFalse(owner.popup.isVisible());self.assertIsNone(owner._displayed)

    def test_copy_dictionary_then_unchanged_apply_serves_next_lookup_without_restart(self):
        from lookup import config
        from tests.test_app import FixedSource
        from tests.test_settings_gui import Registry
        from tests._stardict_writer import write_stardict
        from lookup import gui
        config.save(dict(online=False))
        _,Owner=gui.components()
        owner=Owner({},engine_factory=lambda publish,**kwargs:app.Engine(publish,source=FixedSource('bank')),
                    focus=False,on_quit=lambda:None)
        def wait(predicate):
            deadline=time.monotonic()+3
            while time.monotonic()<deadline:
                self.application.processEvents()
                if predicate():return
                QTest.qWait(5)
            self.fail('dictionary rescan did not become observable')
        def close():
            owner.quit()
            wait(lambda:not owner.engine.is_alive() and not owner.settings_controller.is_alive())
            owner.popup.deleteLater();owner.menu.deleteLater();owner.deleteLater()
            self.application.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        self.addCleanup(close)
        controller=owner.settings_controller
        controller.registry=Registry()
        owner.open_settings()
        window=owner.settings_window
        wait(lambda:not controller.pending)
        self.assertEqual(window.dictionaries.count(),0)
        before=window.snapshot()
        with mock.patch.object(QDesktopServices,'openUrl',return_value=True):
            QTest.mouseClick(window.folder_button,Qt.MouseButton.LeftButton)
            wait(lambda:not controller.pending)
        destination=self.root/'dicts'
        self.assertEqual(window.folder_path.text(),str(destination.absolute()))
        write_stardict(destination,'copied',[('bank','проверенный перевод')])
        self.assertEqual(window.snapshot(),before)
        self.assertTrue(window.apply_button.isEnabled())
        engine=owner.engine
        QTest.mouseClick(window.apply_button,Qt.MouseButton.LeftButton)
        wait(lambda:not controller.pending)
        self.assertIn('Настройки применены',window.status.text())
        self.assertEqual(window.dictionaries.count(),1)
        self.assertIs(owner.engine,engine)
        owner.Trigger('')
        wait(lambda:owner._displayed is not None)
        self.assertEqual(owner._displayed[1]['translation'],'проверенный перевод')
        previous=QFont(self.application.font())
        try:
            changed=QFont(previous);changed.setPointSizeF(previous.pointSizeF()+2)
            self.application.setFont(changed);self.application.processEvents()
            self.assertAlmostEqual(self.owner.popup.title.font().pointSizeF(),changed.pointSizeF()*1.5,delta=.1)
        finally:
            self.application.setFont(previous)

    def test_close_window_and_focus_loss_invalidate_current_request(self):
        self.owner.receive(self.event('frozen'))
        self.owner.popup.close()
        self.assertFalse(self.owner.engine.current(self.identity))
        self.owner.Trigger('');self.identity=self.owner.engine.generation
        self.owner.receive(self.event('frozen'))
        self.application.sendEvent(self.owner.popup,QEvent(QEvent.Type.WindowDeactivate))
        self.assertFalse(self.owner.engine.current(self.identity))
        self.assertFalse(self.owner.popup.isVisible())

    def test_passive_pointer_does_not_extend_inactivity_but_key_input_does(self):
        self.owner.receive(self.event('frozen'))
        self.owner.popup.timer.start(1000)
        remaining=self.owner.popup.timer.remainingTime()
        QTest.mouseMove(self.owner.popup)
        self.assertLessEqual(self.owner.popup.timer.remainingTime(),remaining)
        QTest.keyClick(self.owner.popup,Qt.Key.Key_Tab)
        self.assertGreater(self.owner.popup.timer.remainingTime(),19000)

    def test_oversized_source_text_has_visible_render_limit(self):
        from lookup import gui
        value=self.result()
        value.articles=(replace(value.articles[0],text='x'*(gui.MAX_DISPLAY_CHARS+100)),)
        self.owner.receive(self.event(result=value))
        self.assertIn(gui.TRUNCATED,self.texts())
        self.assertLess(sum(len(widget.toPlainText()) for widget in self.owner.popup.findChildren(QTextEdit)),gui.MAX_DISPLAY_CHARS+1000)

    def test_late_multiline_context_grows_outer_scroll_without_focus_or_timer_reset(self):
        self.preferences(popup_show_context=True)
        value=self.result()
        self.owner.receive(self.event(result=value,context='Public source'))
        self.application.processEvents()
        widget=self.owner.popup.context_value
        before_height=widget.height()
        before_scroll=self.owner.popup.scroll.verticalScrollBar().maximum()
        remaining=self.owner.popup.timer.remainingTime()
        presentations=self.owner.presentations
        self.owner.receive(self.event('context',result=replace(value,context_pending=False,
            context_translation='long public translated context '*200),context='Public source'))
        QTest.qWait(30)  # Nested layout and scroll-area requests need event turns.
        self.assertGreater(widget.height(),before_height+100)
        self.assertGreater(self.owner.popup.scroll.verticalScrollBar().maximum(),before_scroll)
        self.assertLessEqual(self.owner.popup.timer.remainingTime(),remaining)
        self.assertEqual(self.owner.presentations,presentations)

    def test_compositor_work_area_clamps_entire_card_above_panel(self):
        value=self.result()
        value.articles=(replace(value.articles[0],text='long article '*1000),)
        event=replace(self.event(result=value),point=(950,750),available=(0,0,1000,640))
        self.owner.receive(event)
        rect=self.owner.popup.geometry()
        self.assertGreaterEqual(rect.left(),0)
        self.assertGreaterEqual(rect.top(),0)
        self.assertLessEqual(rect.x()+rect.width(),1000)
        self.assertLessEqual(rect.y()+rect.height(),640)

    def test_ready_paint_waits_for_matching_compositor_move(self):
        self.preferences(popup_expand_articles=True)
        self.owner.receive(self.event('frozen'))
        QTest.qWait(20)
        self.owner._focus=True
        value=self.result()
        value.articles=(replace(value.articles[0],text='long article '*1000),)
        event=replace(self.event(result=value),point=(684,376),available=(0,0,1280,738))
        with mock.patch.object(self.owner,'start_focus'):
            self.owner.receive(event)
            revision=self.owner.presentations
            self.assertFalse(self.owner.popup.updatesEnabled())
            self.assertEqual(self.owner._focus_pending[2][:2],(696,0))
            self.owner.focus_done((self.identity,revision-1,'old',None))
            self.assertFalse(self.owner.popup.updatesEnabled())
            self.owner.focus_done((self.identity,revision,'owned',None))
            self.assertTrue(self.owner.popup.updatesEnabled())
            self.assertIn('word',self.texts())

    def test_delayed_placement_starts_full_timeout_at_reveal_and_cancel_stays_closed(self):
        self.owner._popup_timeout=1
        self.owner.receive(self.event('frozen'))
        QTest.qWait(20)
        self.owner._focus=True
        with mock.patch.object(self.owner,'start_focus'):
            for error in (None,'focus_failed'):
                with self.subTest(error=error):
                    self.owner.receive(self.event(result=self.result()))
                    revision=self.owner.presentations
                    QTest.keyClick(self.owner.popup,Qt.Key.Key_A)
                    QTest.qWait(1200)
                    self.assertTrue(self.owner.popup.isVisible())
                    self.assertTrue(self.owner.engine.current(self.identity))
                    self.assertFalse(self.owner.popup.timer.isActive())
                    self.owner.focus_done((self.identity,revision-1,'old',None))
                    self.assertFalse(self.owner.popup.timer.isActive())
                    self.owner.focus_done((self.identity,revision,'owned',error))
                    self.assertTrue(self.owner.popup.updatesEnabled())
                    self.assertGreater(self.owner.popup.timer.remainingTime(),850)
            self.owner.receive(self.event(result=self.result()))
            revision=self.owner.presentations
            self.owner.popup.dismiss()
            self.owner.focus_done((self.identity,revision,'old',None))
            self.assertFalse(self.owner.popup.isVisible())
            self.assertFalse(self.owner.popup.timer.isActive())

    def test_failed_move_reveals_error_and_new_trigger_restores_paint(self):
        self.owner.receive(self.event('frozen'))
        QTest.qWait(20)
        self.owner._focus=True
        with mock.patch.object(self.owner,'start_focus'):
            self.owner.receive(self.event(result=self.result()))
            self.owner.focus_done((self.identity,self.owner.presentations,None,'focus_failed'))
            self.assertTrue(self.owner.popup.updatesEnabled())
            self.assertIn('Не удалось разместить',self.texts())
            self.assertIsNone(self.owner._displayed)
            self.owner.receive(self.event(result=self.result()))
            self.assertFalse(self.owner.popup.updatesEnabled())
            self.owner.Trigger('')
            self.assertTrue(self.owner.popup.updatesEnabled())
            self.assertFalse(self.owner.popup.isVisible())

    def test_unexposed_loading_defers_ready_and_keeps_latest_context(self):
        self.owner.receive(self.event('frozen'))
        self.owner._focus=True
        handle=self.owner.popup.windowHandle()
        with mock.patch.object(self.owner,'start_focus'), \
             mock.patch.object(type(handle),'isExposed',return_value=False):
            self.owner.receive(self.event(result=self.result()))
            self.assertIsNotNone(self.owner._waiting_ready)
            context=self.event('context',result=replace(self.result(),context_meaning='public meaning'))
            self.owner.receive(context)
            self.assertIs(self.owner._waiting_context,context)
        QTest.qWait(20)
        self.owner.ready_when_exposed()
        self.assertIsNone(self.owner._waiting_ready)
        self.assertEqual(self.owner.popup.meaning_value.text(),'public meaning')
        self.owner.popup.dismiss()
        self.owner.focus_done((self.identity,self.owner.presentations,'old',None))
        self.assertFalse(self.owner.popup.isVisible())
        self.assertTrue(self.owner.popup.updatesEnabled())

    def test_unexposed_timeout_is_bounded_and_cancelled_ready_cannot_reopen(self):
        self.owner.receive(self.event('frozen'))
        self.owner._focus=True
        event=self.event(result=self.result())
        handle=self.owner.popup.windowHandle()
        with mock.patch.object(self.owner,'start_focus'), \
             mock.patch.object(type(handle),'isExposed',return_value=False):
            self.owner.receive(event)
            self.owner._waiting_ready=(event,0)
            self.owner.ready_when_exposed()
            self.assertIsNone(self.owner._waiting_ready)
            self.assertIn('Не удалось разместить',self.texts())
            self.assertTrue(self.owner.popup.updatesEnabled())
            self.owner.receive(event)
            self.owner.popup.dismiss()
            self.owner.ready_when_exposed()
            self.assertIsNone(self.owner._waiting_ready)
            self.assertFalse(self.owner.popup.isVisible())


if __name__=='__main__':
    unittest.main()
