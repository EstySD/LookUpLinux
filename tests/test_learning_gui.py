"""Real native learning widgets with isolated persistence and controlled time."""
import contextlib
import csv
import os
import sqlite3
import subprocess
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
try:
    from PyQt6.QtCore import Qt, QEvent
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication, QFileDialog
except ImportError:
    QApplication=None

from lookup import learning, store
from tests._support import make_tempdir, forbid_network


@unittest.skipIf(QApplication is None,'PyQt6 unavailable')
class LearningGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application=QApplication.instance() or QApplication([])

    def setUp(self):
        from lookup.learning_gui import components
        self.Words,self.Review=components()
        self.root=make_tempdir(self)
        self.conn=store.open_store(self.root/'learning.db')
        self.conn.execute('PRAGMA busy_timeout=20')
        self.addCleanup(self.conn.close)
        forbid_network(self)
        self.now=1000

    def window(self,kind):
        value=kind(self.conn,clock=lambda:self.now)
        value.show();self.application.processEvents()
        def close():
            value.close();value.deleteLater()
            self.application.sendPostedEvents(None,QEvent.Type.DeferredDelete)
            self.application.processEvents()
        self.addCleanup(close)
        return value

    def card(self,word='bank',translation='банк',context='The bank.\nPublic context.'):
        return learning.add_card(self.conn,dict(word=word,translation=translation,context=context),now=self.now)

    def words(self,value):
        return [value.table.item(row,0).text() for row in range(value.table.rowCount())]

    def click(self,button):
        QTest.mouseClick(button,Qt.MouseButton.LeftButton)
        self.application.processEvents()

    def test_history_numeric_sort_search_and_empty_copy_never_recount(self):
        for word,count in (('bank',2),('river',10),('apple',2)):
            for _ in range(count):store.upsert_word(self.conn,word,'перевод',now=20)
        before=self.conn.total_changes
        value=self.window(self.Words)
        self.assertEqual(self.words(value),['river','apple','bank'])
        value.table.horizontalHeader().sectionClicked.emit(2)
        self.assertEqual(self.words(value),['apple','bank','river'])
        value.search.setText('BANK')
        self.assertEqual(self.words(value),['bank'])
        value.search.setText('absent')
        self.assertEqual(value.status.text(),'Ничего не найдено')
        self.assertFalse(value.add_button.isEnabled())
        self.assertFalse(value.delete_button.isEnabled())
        self.assertEqual(self.conn.total_changes,before)

    def test_add_duplicate_delete_preserves_card_and_next_count_starts_one(self):
        store.upsert_word(self.conn,'bank','банк','The bank.',now=1)
        value=self.window(self.Words)
        value.table.selectRow(0)
        self.click(value.add_button)
        self.assertEqual(value.status.text(),'Добавлено в карточки')
        original=learning.get_card(self.conn,'bank')
        self.click(value.add_button)
        self.assertEqual(value.status.text(),'Уже в карточках')
        self.assertEqual(learning.get_card(self.conn,'bank'),original)
        self.click(value.delete_button)
        self.assertIn('Учебная карточка сохранится',value.status.text())
        self.assertEqual(learning.get_card(self.conn,'bank'),original)
        self.assertEqual(store.upsert_word(self.conn,'bank',now=3),1)
        value.close()
        self.assertEqual(self.conn.execute('SELECT count FROM words').fetchone()[0],1)

    def test_missing_translation_and_database_errors_are_fixed_and_retryable(self):
        store.upsert_word(self.conn,'bank',now=1)
        value=self.window(self.Words)
        value.table.selectRow(0)
        value.add_selected()
        self.assertEqual(value.status.text(),'Нет перевода для карточки')
        with patch.object(learning,'list_words',side_effect=sqlite3.OperationalError('private source')):
            value.refresh()
        self.assertNotIn('private',value.status.text())
        self.assertFalse(value.add_button.isEnabled())
        store.upsert_word(self.conn,'bank','банк',now=2)
        value.refresh();value.table.selectRow(0)
        with patch.object(learning,'add_history_card',side_effect=sqlite3.OperationalError('private source')):
            self.click(value.add_button)
        self.assertEqual(value.status.text(),'Не удалось сохранить карточку. Попробуйте ещё раз')
        self.click(value.add_button)
        self.assertEqual(value.status.text(),'Добавлено в карточки')

    def test_native_export_cancel_writes_nothing_and_formats_preserve_snapshot(self):
        self.card(translation='банк, "место"',context='The bank.\n<public> context.')
        value=self.window(self.Words)
        with patch.object(QFileDialog,'getSaveFileName',return_value=('','')), \
             patch.object(learning,'export_csv') as export:
            self.click(value.csv_button)
        export.assert_not_called()
        csv_path=self.root/'cards.csv'
        with patch.object(QFileDialog,'getSaveFileName',return_value=(str(csv_path),'')):
            self.click(value.csv_button)
        with csv_path.open(encoding='utf-8',newline='') as stream:
            self.assertEqual(list(csv.reader(stream)),[['word','translation','context'],
                ['bank','банк, "место"','The bank.\n<public> context.']])
        anki_path=self.root/'cards.txt'
        with patch.object(QFileDialog,'getSaveFileName',return_value=(str(anki_path),'')):
            self.click(value.anki_button)
        exported=anki_path.read_text(encoding='utf-8')
        self.assertIn('#separator:Tab\n#html:true',exported)
        self.assertIn('&lt;public&gt;',exported)
        self.assertIn('<br>',exported)
        with patch.object(QFileDialog,'getSaveFileName',return_value=(str(csv_path),'')), \
             patch.object(learning,'export_csv',side_effect=learning.LearningError('export_failed')):
            self.click(value.csv_button)
        self.assertEqual(value.status.text(),'Не удалось экспортировать карточки. Попробуйте ещё раз')

    def test_review_front_reveal_exact_intervals_one_grade_and_restart(self):
        self.card(translation='<b>банк</b>',context='The bank.\nPublic context.')
        value=self.window(self.Review)
        self.assertEqual(value.front.text(),'bank')
        self.assertFalse(value.translation.isVisible())
        self.assertFalse(any(button.isEnabled() for button in value.rating_buttons.values()))
        expected=learning.preview(learning.get_card(self.conn,'bank'),'Good')['delay']
        self.click(value.reveal_button)
        self.assertEqual(value.translation.toPlainText(),'<b>банк</b>')
        self.assertEqual(value.context.toPlainText(),'The bank.\nPublic context.')
        self.assertIn('1 дн',value.rating_buttons['Good'].text())
        self.click(value.rating_buttons['Good'])
        self.click(value.rating_buttons['Good'])
        card=learning.get_card(self.conn,'bank')
        self.assertEqual((card['due'],card['review_version']),(self.now+expected,1))
        self.assertIn('Нет карточек для повторения',value.front.text())
        restarted=self.window(self.Review)
        self.assertIsNone(restarted.current)
        self.now=card['due'];restarted.refresh()
        self.assertEqual(restarted.front.text(),'bank')
        self.assertFalse(restarted.translation.isVisible())

    def test_stale_review_reloads_and_database_error_keeps_retryable_answer(self):
        self.card()
        value=self.window(self.Review)
        self.click(value.reveal_button)
        with patch.object(learning,'grade_card',side_effect=sqlite3.OperationalError('private data')):
            self.click(value.rating_buttons['Good'])
        self.assertEqual(value.status.text(),'Не удалось сохранить ответ. Попробуйте ещё раз')
        self.assertEqual(learning.get_card(self.conn,'bank')['review_version'],0)
        self.assertTrue(value.rating_buttons['Good'].isEnabled())
        learning.grade_card(self.conn,'bank',0,'Good',now=self.now)
        self.click(value.rating_buttons['Good'])
        self.assertIn('уже изменена',value.status.text())
        self.assertEqual(learning.get_card(self.conn,'bank')['review_version'],1)
        self.assertIsNone(value.current)


class LazyImportTests(unittest.TestCase):
    def test_import_does_not_load_qt(self):
        result=subprocess.run([sys.executable,'-c',
            'import sys; import lookup.learning_gui; assert not any(n.startswith("PyQt6") for n in sys.modules)'],
            capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':
    unittest.main()
