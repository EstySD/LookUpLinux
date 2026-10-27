"""Native learning windows. Qt is imported only when components are requested."""
import sqlite3
import time

from . import learning
from .store import get_word_context

_components=None
_ERRORS=(sqlite3.Error,learning.LearningError,OSError)


def _duration(seconds):
    if seconds<3600:
        return f'{seconds//60} мин'
    if seconds<86400:
        return f'{seconds//3600} ч'
    return f'{seconds//86400} дн'


def components():
    global _components
    if _components is not None:
        return _components
    from PyQt6.QtCore import Qt,QDateTime,pyqtSignal
    from PyQt6.QtWidgets import (QWidget,QLabel,QVBoxLayout,QHBoxLayout,QLineEdit,
                                QPushButton,QTableWidget,QTableWidgetItem,QAbstractItemView,
                                QHeaderView,QFileDialog,QTextEdit)

    def label(text='',name=None):
        value=QLabel(text)
        value.setTextFormat(Qt.TextFormat.PlainText)
        value.setWordWrap(True)
        value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        if name:value.setAccessibleName(name)
        return value

    class WordsWindow(QWidget):
        changed=pyqtSignal()

        def __init__(self,conn,*,clock=None):
            super().__init__()
            self.conn=conn
            self.clock=clock or time.time
            self._sort='count'
            self._descending=True
            self.setWindowTitle('Слова')
            self.resize(680,480)
            layout=QVBoxLayout(self)
            self.search=QLineEdit()
            self.search.setPlaceholderText('Поиск слов')
            self.search.setAccessibleName('Поиск слов')
            self.search.setMaxLength(500)
            layout.addWidget(self.search)
            self.table=QTableWidget(0,4)
            self.table.setAccessibleName('История поиска слов')
            self.table.setHorizontalHeaderLabels(('Слово','Перевод','Искали','Последний поиск'))
            self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.table.verticalHeader().hide()
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.table.horizontalHeader().setSortIndicatorShown(True)
            self.table.horizontalHeader().sectionClicked.connect(self._sort_column)
            layout.addWidget(self.table,1)
            actions=QHBoxLayout()
            self.add_button=QPushButton('В карточки')
            self.delete_button=QPushButton('Удалить из истории')
            self.refresh_button=QPushButton('Обновить')
            for button in (self.add_button,self.delete_button,self.refresh_button):actions.addWidget(button)
            layout.addLayout(actions)
            layout.addWidget(label('При удалении из истории учебная карточка сохранится.'))
            layout.addWidget(label('Экспорт всех учебных карточек:'))
            exports=QHBoxLayout()
            self.csv_button=QPushButton('Экспорт CSV…')
            self.anki_button=QPushButton('Экспорт для Anki…')
            exports.addWidget(self.csv_button);exports.addWidget(self.anki_button)
            layout.addLayout(exports)
            self.status=label(name='Состояние списка слов')
            layout.addWidget(self.status)
            self.search.textChanged.connect(self.refresh)
            self.table.itemSelectionChanged.connect(self._selection_changed)
            self.add_button.clicked.connect(self.add_selected)
            self.delete_button.clicked.connect(self.delete_selected)
            self.refresh_button.clicked.connect(self.refresh)
            self.csv_button.clicked.connect(lambda:self.export(False))
            self.anki_button.clicked.connect(lambda:self.export(True))
            self.refresh()

        def selected_word(self):
            selected=self.table.selectionModel().selectedRows()
            return self.table.item(selected[0].row(),0).text() if selected else None

        def _selection_changed(self):
            word=self.selected_word()
            self.delete_button.setEnabled(word is not None)
            eligible=False
            if word is not None:
                try:
                    value=get_word_context(self.conn,word)
                    eligible=bool(value and (value['meaning'] or value['translation'] or '').strip())
                    if not eligible:self.status.setText('Нет перевода для карточки')
                except _ERRORS:
                    self.status.setText('Не удалось загрузить слова. Попробуйте ещё раз')
            self.add_button.setEnabled(eligible)

        def _sort_column(self,column):
            sort=('word','translation','count','last_seen')[column]
            self._descending=not self._descending if sort==self._sort else False
            self._sort=sort
            self.refresh()

        def refresh(self):
            selected=self.selected_word()
            try:
                rows=learning.list_words(self.conn,self.search.text(),self._sort,self._descending)
            except _ERRORS:
                self.table.setRowCount(0)
                self.add_button.setEnabled(False);self.delete_button.setEnabled(False)
                self.status.setText('Не удалось загрузить слова. Попробуйте ещё раз')
                return
            self.table.setRowCount(0)
            self.table.setRowCount(len(rows))
            for row,value in enumerate(rows):
                date=QDateTime.fromSecsSinceEpoch(value['last_seen']).toLocalTime().toString('dd.MM.yyyy HH:mm')
                for column,text in enumerate((value['word'],value['translation'] or '',str(value['count']),date)):
                    self.table.setItem(row,column,QTableWidgetItem(text))
            column=('word','translation','count','last_seen').index(self._sort)
            self.table.horizontalHeader().setSortIndicator(column,Qt.SortOrder.DescendingOrder
                                                           if self._descending else Qt.SortOrder.AscendingOrder)
            self.status.setText('' if rows else 'Ничего не найдено' if self.search.text() else 'История пока пуста')
            if rows:
                self.table.selectRow(next((i for i,value in enumerate(rows) if value['word']==selected),0))
            self._selection_changed()

        def add_selected(self):
            word=self.selected_word()
            if word is None:return
            try:
                result=learning.add_history_card(self.conn,word,now=self.clock())
            except learning.LearningError as error:
                self.status.setText('Нет перевода для карточки' if error.reason=='missing_translation'
                                    else 'Не удалось сохранить карточку. Попробуйте ещё раз')
                return
            except _ERRORS:
                self.status.setText('Не удалось сохранить карточку. Попробуйте ещё раз')
                return
            self.changed.emit()
            self.status.setText('Добавлено в карточки' if result=='created' else 'Уже в карточках')

        def delete_selected(self):
            word=self.selected_word()
            if word is None:return
            try:
                deleted=learning.delete_word(self.conn,word)
            except _ERRORS:
                self.status.setText('Не удалось удалить слово. Попробуйте ещё раз')
                return
            self.refresh()
            self.changed.emit()
            self.status.setText('Удалено из истории. Учебная карточка сохранится.' if deleted
                                else 'Слово уже удалено. Список обновлён.')

        def export(self,anki):
            path,_=QFileDialog.getSaveFileName(self,'Экспорт всех учебных карточек',
                'lookup-cards.txt' if anki else 'lookup-cards.csv',
                'Текст для Anki (*.txt)' if anki else 'CSV (*.csv)')
            if not path:return
            try:
                (learning.export_anki if anki else learning.export_csv)(self.conn,path)
            except _ERRORS:
                self.status.setText('Не удалось экспортировать карточки. Попробуйте ещё раз')
                return
            self.status.setText('Все учебные карточки экспортированы.')

    class ReviewWindow(QWidget):
        changed=pyqtSignal()

        def __init__(self,conn,*,clock=None):
            super().__init__()
            self.conn=conn
            self.clock=clock or time.time
            self.current=None
            self._revealed=False
            self._grading=False
            self.setWindowTitle('Повторение')
            self.resize(560,480)
            layout=QVBoxLayout(self)
            self.front=label(name='Слово для повторения')
            font=self.front.font();font.setPointSizeF(font.pointSizeF()*1.4);font.setBold(True)
            self.front.setFont(font)
            layout.addWidget(self.front)
            self.translation=QTextEdit()
            self.context=QTextEdit()
            for block,name in ((self.translation,'Перевод карточки'),(self.context,'Контекст карточки')):
                block.setReadOnly(True);block.setAcceptRichText(False);block.setAccessibleName(name)
                layout.addWidget(block,1)
            self.reveal_button=QPushButton('Показать ответ')
            layout.addWidget(self.reveal_button)
            ratings=QHBoxLayout()
            self.rating_buttons={}
            for rating in ('Again','Hard','Good','Easy'):
                button=QPushButton(rating)
                button.clicked.connect(lambda checked=False,rating=rating:self.grade(rating))
                self.rating_buttons[rating]=button
                ratings.addWidget(button)
            layout.addLayout(ratings)
            self.refresh_button=QPushButton('Обновить')
            layout.addWidget(self.refresh_button)
            self.status=label(name='Состояние повторения')
            layout.addWidget(self.status)
            self.reveal_button.clicked.connect(self.reveal)
            self.refresh_button.clicked.connect(self.refresh)
            self.refresh()

        def refresh(self):
            if self._grading:return
            self.current=None
            self._revealed=False
            self.translation.clear();self.context.clear()
            self.translation.hide();self.context.hide()
            self.reveal_button.setEnabled(False)
            for rating,button in self.rating_buttons.items():
                button.setText(rating);button.setEnabled(False)
            try:
                cards=learning.due_cards(self.conn,now=self.clock())
                self.current=cards[0] if cards else None
                if self.current is not None:
                    for rating,button in self.rating_buttons.items():
                        duration=_duration(learning.preview(self.current,rating)['delay'])
                        button.setText(rating+'\n'+duration)
                        button.setAccessibleName(rating+', '+duration)
            except _ERRORS:
                self.current=None
                self.front.setText('Не удалось загрузить карточки.')
                self.status.setText('Попробуйте обновить список ещё раз.')
                return
            self.front.setText(self.current['word'] if self.current else 'Нет карточек для повторения. Можно вернуться позже.')
            self.reveal_button.setEnabled(self.current is not None)
            self.status.setText('')

        def reveal(self):
            if self.current is None or self._grading:return
            self._revealed=True
            self.translation.setPlainText(self.current['translation']);self.translation.show()
            self.context.setPlainText(self.current['context'] or '')
            self.context.setVisible(bool(self.current['context']))
            self.reveal_button.setEnabled(False)
            for button in self.rating_buttons.values():button.setEnabled(True)

        def grade(self,rating):
            if self.current is None or not self._revealed or self._grading:return
            self._grading=True
            for button in self.rating_buttons.values():button.setEnabled(False)
            try:
                result=learning.grade_card(self.conn,self.current['word'],self.current['review_version'],
                                           rating,now=self.clock())
            except _ERRORS:
                self.status.setText('Не удалось сохранить ответ. Попробуйте ещё раз')
                for button in self.rating_buttons.values():button.setEnabled(True)
                return
            finally:
                self._grading=False
            if result=='applied':self.changed.emit()
            self.refresh()
            self.status.setText('Ответ сохранён.' if result=='applied' else 'Карточка уже изменена. Список обновлён.')

    _components=(WordsWindow,ReviewWindow)
    return _components
