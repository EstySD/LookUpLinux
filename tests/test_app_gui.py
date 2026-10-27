"""Native Qt presentation and queued-generation rules; no desktop required."""
import os
import unittest
from dataclasses import replace

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
try:
    from PyQt6.QtCore import Qt, QEvent
    from PyQt6.QtGui import QFont, QPalette, QColor
    from PyQt6.QtWidgets import QApplication, QLabel, QTextEdit
    from PyQt6.QtTest import QTest
except ImportError:
    QApplication=None

from lookup import app, translate
from lookup.dicts import Article
from lookup.platform import Monitor


class FakeEngine:
    def __init__(self,publish,**kwargs):
        self.publish=publish
        self.generation=0
        self.pending=[]
        self.stopping=False
    def begin(self):
        self.generation+=1
        return self.generation
    def enqueue(self,identity):
        self.pending.append(identity)
    def current(self,identity):
        return identity==self.generation and not self.stopping
    def dismiss(self,identity):
        if self.current(identity):self.generation+=1
    def stop(self):self.stopping=True
    def is_alive(self):return False
    def join(self,timeout):pass


@unittest.skipIf(QApplication is None,'PyQt6 unavailable')
class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application=QApplication.instance() or QApplication([])
    def setUp(self):
        from lookup import gui
        self.Popup,self.Owner=gui.components()
        self.owner=self.Owner({},engine_factory=FakeEngine,focus=False,on_quit=lambda:None)
        owner=self.owner
        def close():
            owner.quit()
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
    def result(self):
        first=Article('First','word','wɜːd',(('noun',('значение','слово')),),'<img src="file:///private"> literal article')
        second=Article('Second','word',None,(), 'Другой словарь')
        return translate.Result('word','word',articles=(first,second),lemma='lemma',saved=True,count=3,context_pending=True)
    def texts(self):
        return '\n'.join(label.text() for label in self.owner.popup.findChildren(QLabel))+ '\n' + '\n'.join(widget.toPlainText() for widget in self.owner.popup.findChildren(QTextEdit))
    def test_actual_fields_order_plain_text_and_no_invented_metadata(self):
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
        QTest.qWait(40)
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
        self.assertTrue(all(not action.isEnabled() for action in self.owner.future_actions))
        self.assertEqual([a.text() for a in self.owner.future_actions],['Слова','Повторение','Настройки'])
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


if __name__=='__main__':
    unittest.main()
