"""Lazy native KDE owner/client and translation card. No Qt import on import."""
import os
import math
import re
import sqlite3
from pathlib import Path
import subprocess
import sys
import threading
import time
from dataclasses import replace

from . import app as core, platform, timing, config
from .store import MigrationError,SchemaTooNewError

SERVICE='org.lookup.Linux'
OBJECT='/Lookup'
TITLE='Перевод LookUp Linux'
DESKTOP='org.lookup.Linux.desktop'
_components=None

REASONS={
    'missing_gnome_extension':('Недоступно расширение LookUp Linux для GNOME','Установите и включите расширение по инструкции docs/UBUNTU.md, затем войдите в сеанс снова.'),
    'placement_failed':('Не удалось разместить окно перевода','Повторите поиск.'),
    'ocr_timeout':('Не удалось распознать текст вовремя','Наведите курсор на слово или выделите текст и повторите поиск.'),
    'ocr_failed':('Не удалось распознать текст','Наведите курсор на слово или выделите текст и повторите поиск.'),
    'no_network':('Нет сети','Проверьте подключение и повторите поиск. Офлайн-словари доступны.'),
    'blocked':('Онлайн-перевод заблокирован','Попробуйте позже.'),
    'timeout':('Перевод не ответил вовремя','Повторите поиск.'),
    'bad_response':('Не удалось получить перевод','Повторите поиск.'),
    'cursor_failed':('Не удалось получить положение курсора','Повторите поиск.'),
    'monitor_failed':('Не удалось определить экран','Повторите поиск.'),
    'capture_failed':('Не удалось получить снимок экрана','Повторите поиск.'),
    'unsupported_session':('Недоступен сеанс KDE Wayland','Запустите LookUp Linux в сеансе KDE Wayland.'),
    'not_found':('Не найдено','Наведите курсор на английское слово или выделите текст и повторите поиск.'),
    'reload_failed':('Не удалось применить настройки','Откройте настройки, повторите применение или запустите lookup --doctor.'),
}
PACKAGES={'missing_tesseract':'tesseract','missing_eng':'tesseract-data-eng',
          'missing_pyqt6':'python-pyqt6','missing_kdotool':'kdotool','missing_kscreen':'libkscreen'}
SAVE_ERROR='Не удалось сохранить поиск. Перевод доступен; повторите поиск позже.'
MEANING_SAVE_ERROR='Не удалось сохранить значение в контексте. Перевод доступен.'
CACHE_ERROR='Не удалось обновить кэш перевода.'
MEANING_REASONS={
    'disabled':'Значение в контексте недоступно: онлайн-перевод выключен.',
    'no_context':'Недостаточно надёжного контекста для определения значения.',
    'busy':'Значение в контексте пока недоступно.',
    'timeout':'Не удалось получить значение в контексте: время ожидания истекло.',
    'bad_response':'Не удалось надёжно определить значение в контексте.',
    'not_found':'Не удалось надёжно определить значение в контексте.',
}
MAX_DISPLAY_CHARS=32_000
MAX_DISPLAY_BLOCKS=128
TRUNCATED='Показана часть слишком длинного текста.'


def display_text(text,limit):
    return text if len(text)<=limit else text[:limit]+'\n'+TRUNCATED


def valid_token(value):
    try:
        return isinstance(value,str) and '\x00' not in value and len(value.encode('utf-8'))<=4096
    except UnicodeError:
        return False


def desktop_text(python=None,directory=None):
    from .lifecycle import desktop_text as build
    return build(python,directory)


def components():
    global _components
    if _components is not None:
        return _components
    from PyQt6.QtCore import QObject,QTimer,Qt,QEvent,QPoint,QRect,pyqtSignal,pyqtSlot,pyqtClassInfo
    from PyQt6.QtGui import QFont,QIcon,QKeySequence,QShortcut,QTextOption,QPalette
    from PyQt6.QtWidgets import (QApplication,QWidget,QLabel,QVBoxLayout,QHBoxLayout,
                                 QScrollArea,QToolButton,QStyle,QFrame,QSizePolicy,
                                 QSystemTrayIcon,QMenu,QTextEdit,QPushButton,QMessageBox)

    class PlainBlock(QTextEdit):
        """Selectable plain text with anywhere wrapping and no inner scrollbar."""
        def __init__(self,text):
            super().__init__()
            self.setReadOnly(True)
            self.setAcceptRichText(False)
            self.setFrameShape(QFrame.Shape.NoFrame)
            self.setAutoFillBackground(False)
            self.viewport().setAutoFillBackground(False)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
            self.document().setDocumentMargin(0)
            self.setPlainText(text)
        def text(self):return self.toPlainText()
        def setText(self,text):
            self.setPlainText(text)
            self.fit(self.viewport().width())
            self.updateGeometry()
        def heightForWidth(self,width):
            self.document().setTextWidth(max(1,width))
            return max(1,math.ceil(self.document().size().height()))
        def fit(self,width):
            height=self.heightForWidth(width)
            if self.height()!=height:self.setFixedHeight(height)
        def resizeEvent(self,event):
            super().resizeEvent(event)
            self.fit(self.viewport().width())
        def wheelEvent(self,event):
            event.ignore()  # The one outer reading surface owns scrolling.

    class Bridge(QObject):
        event=pyqtSignal(object)
        focus_done=pyqtSignal(object)

    class Popup(QWidget):
        dismissed=pyqtSignal()
        def __init__(self):
            super().__init__()
            self.setWindowTitle(TITLE)
            self.setAccessibleName(TITLE)
            self.setWindowFlags(Qt.WindowType.Tool|Qt.WindowType.FramelessWindowHint)
            self.setAutoFillBackground(True)
            self._armed=False
            self._labels=[]
            self.preferences=config.Config()
            self._shown_preferences=self.preferences
            self._available=None
            self._article_buttons=[]
            self._duration=20000
            self.timer=QTimer(self)
            self.timer.setSingleShot(True)
            self.timer.timeout.connect(self.expire)
            self.layout_box=QVBoxLayout(self)
            self.layout_box.setContentsMargins(16,16,16,16)
            self.layout_box.setSpacing(8)
            header=QHBoxLayout()
            header.setSpacing(8)
            self.state_icon=self.label('')
            self.state_icon.hide()
            self.title=self.label('',1.5,True)
            self.title.setAccessibleName('Перевод или состояние поиска')
            self.title.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)
            self.close_button=QToolButton()
            self.close_button.setAutoRaise(True)
            self.close_button.setAccessibleName('Закрыть карточку')
            self.close_button.setToolTip('Закрыть (Esc)')
            self.close_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.close_button.setIcon(QIcon.fromTheme('window-close',self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton)))
            self.close_button.clicked.connect(self.dismiss)
            header.addWidget(self.state_icon,0,Qt.AlignmentFlag.AlignTop)
            header.addWidget(self.title,1)
            header.addWidget(self.close_button,0,Qt.AlignmentFlag.AlignTop)
            self.layout_box.addLayout(header)
            self.scroll=QScrollArea()
            self.scroll.setAccessibleName('Перевод и исходный текст')
            self.scroll.setWidgetResizable(True)
            self.scroll.setFrameShape(QFrame.Shape.NoFrame)
            self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            content=QWidget()
            content.setMinimumWidth(0)
            self.content_layout=QVBoxLayout(content)
            self.content_layout.setContentsMargins(0,0,0,0)
            self.content_layout.setSpacing(8)
            self.primary_translation=self.label('',1.3,True,block=True)
            self.primary_translation.setAccessibleName('Краткий перевод')
            self.content_layout.addWidget(self.primary_translation)
            self.primary_translation.hide()
            self.meaning_heading=self.label('Значение в контексте',bold=True)
            self.meaning_value=self.label('',block=True)
            self.meaning_value.setAccessibleName('Значение в контексте')
            for widget in (self.primary_translation,self.meaning_value):
                widget.document().setDocumentMargin(10)
                widget.viewport().setBackgroundRole(QPalette.ColorRole.AlternateBase)
                widget.viewport().setAutoFillBackground(True)
            for widget in (self.meaning_heading,self.meaning_value):
                self.content_layout.addWidget(widget)
                widget.hide()
            self.body=QVBoxLayout()
            self.body.setSpacing(8)
            self.content_layout.addLayout(self.body)
            self.content_layout.addSpacing(16)
            self.context_heading=self.label('Исходный текст',bold=True)
            self.context_source=self.label('',block=True)
            self.context_source.setAccessibleName('Исходный текст')
            self.context_fragment=self.label('Показан доступный фрагмент; границы предложения не определены.')
            self.context_value=self.label('',block=True)
            self.context_value.setAccessibleName('Перевод контекста')
            self.cache_warning=self.label('')
            for widget in (self.context_heading,self.context_source,self.context_fragment,self.context_value,self.cache_warning):
                self.content_layout.addWidget(widget)
                widget.hide()
            self.content_layout.addStretch()
            self.scroll.setWidget(content)
            self.layout_box.addWidget(self.scroll,1)
            self.footer=self.label('')
            self.footer.setAccessibleName('Сохранение поиска')
            footer_row=QHBoxLayout()
            footer_row.addWidget(self.footer,1)
            self.card_button=QPushButton('В карточки')
            self.card_button.setAccessibleName('Добавить слово в карточки')
            self.card_button.setEnabled(False)
            self.card_button.hide()
            footer_row.addWidget(self.card_button)
            self.layout_box.addLayout(footer_row)
            self.card_status=self.label('')
            self.card_status.setAccessibleName('Сохранение учебной карточки')
            self.card_status.hide()
            self.layout_box.addWidget(self.card_status)
            self.shortcut=QShortcut(QKeySequence(Qt.Key.Key_Escape),self)
            self.shortcut.activated.connect(self.dismiss)
            QApplication.instance().installEventFilter(self)
        def label(self,text,factor=1,bold=False,block=False):
            label=PlainBlock(text) if block else QLabel(text)
            if not block:
                label.setTextFormat(Qt.TextFormat.PlainText)
                label.setWordWrap(True)
            label.setMinimumWidth(0)
            label.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse|Qt.TextInteractionFlag.TextSelectableByKeyboard)
            label._role=(factor,bold)
            self._labels.append(label)
            self.font_for(label)
            return label
        def font_for(self,label):
            base=QApplication.font()
            size=base.pointSizeF()
            if size<=0:
                size=max(1,base.pixelSize())*72/96
            font=QFont(base)
            font.setPointSizeF(size*label._role[0])
            font.setWeight(QFont.Weight.DemiBold if label._role[1] else QFont.Weight.Normal)
            label.setFont(font)
            if isinstance(label,PlainBlock):label.document().setDefaultFont(font)
        def clear_body(self):
            self._remaining=MAX_DISPLAY_CHARS
            self._blocks=0
            self._truncated=False
            self._article_buttons=[]
            while self.body.count():
                widget=self.body.takeAt(0).widget()
                if widget is not None:
                    if widget in self._labels:self._labels.remove(widget)
                    widget.hide();widget.deleteLater()
            for label in (self.primary_translation,self.meaning_heading,self.meaning_value,self.context_heading,self.context_source,
                          self.context_fragment,self.context_value,self.cache_warning):
                label.hide()
            self.footer.clear()
            self.card_button.setEnabled(False)
            self.card_button.hide()
            self.card_status.clear()
            self.card_status.hide()
            self.state_icon.hide()
        def add(self,text,bold=False,factor=1):
            if text:
                if self._truncated:return
                text=str(text)
                if len(text)>self._remaining or self._blocks>=MAX_DISPLAY_BLOCKS:
                    text=display_text(text,self._remaining) if self._blocks<MAX_DISPLAY_BLOCKS else TRUNCATED
                    self._truncated=True
                self._remaining=max(0,self._remaining-len(text))
                self._blocks+=1
                label=self.label(text,factor,bold,block=True)
                self.body.addWidget(label)
                # A visible layout queues new child visibility; size this card now.
                label.show()
                return label
        def heading(self,text,state=False):
            self.title.setText(text)
            self.title._role=(1.75 if state else 1.5,True)
            self.font_for(self.title)
        def loading(self):
            self.clear_body()
            self.heading('Ищем перевод…',True)
        def error(self,reason):
            self.clear_body()
            if reason in PACKAGES:
                package=PACKAGES[reason]
                heading,body='Не установлен пакет '+package,'Установите '+package+' и повторите поиск.'
            else:
                heading,body=REASONS.get(reason,('Не удалось выполнить поиск','Повторите поиск.'))
            self.heading(heading,True)
            self.add(body)
            self.state_icon.setPixmap(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning).pixmap(20,20))
            self.state_icon.show()
        def result(self,value,context,save_error):
            self.clear_body()
            self._shown_preferences=self.preferences
            useful=bool(value.articles or value.online)
            if value.kind=='sentence':
                self.heading('Перевод выделения')
                self.add(value.key)
            elif useful:
                key=value.key or ''
                self.heading(key if len(key)<=80 else 'Перевод')
                if len(key)>80:
                    self.add(key,True,1.5)
            else:
                heading,body=REASONS.get(value.online_error,REASONS['not_found'])
                self.heading(heading,True)
                self.add(body)
            if value.lemma:
                self.add('Форма слова: '+value.lemma)
            ipa=next((a.transcription for a in value.articles if a.transcription),None)
            if not ipa and value.online:
                ipa=value.online.transcription
            self.add(ipa)
            from .translate import short_translation
            structured=tuple(article for article in value.articles if article.senses)
            # Raw article prefixes can contain metadata rather than a translation.
            summary=short_translation(structured,None if value.articles else value.online)
            self.primary_translation.setText(summary or '')
            for article in value.articles:
                if self.body.count():self.body.addSpacing(8)
                name=article.dict_name
                heading=self.add('Словарь: '+(name[:79]+'…' if len(name)>80 else name))
                if heading is not None:
                    heading.setAccessibleName('Словарь: '+name)
                    heading.setToolTip(name)
                for pos,terms in article.senses:
                    self.add((pos+': ' if pos else '')+'; '.join(terms))
                if not article.senses and article.text:
                    self.add(article.text[:239]+'…' if len(article.text)>240 else article.text)
            if value.online:
                self.add(value.online.main)
                for pos,terms in value.online.parts:
                    self.add((pos+': ' if pos else '')+'; '.join(terms))
            if not value.online_enabled:
                self.add('Онлайн-перевод выключен.')
            for article in value.articles:
                if not article.text or self._truncated:continue
                button=QPushButton()
                button.setCheckable(True)
                button.setAutoDefault(True)
                button.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)
                button._article_name=article.dict_name
                self._article_buttons.append(button)
                self.body.addWidget(button)
                text=self.add(article.text)
                if text is None:
                    self.body.removeWidget(button);button.deleteLater()
                    continue
                def toggle(expanded,button=button,text=text):
                    self.article_caption(button)
                    text.setVisible(expanded)
                    if self._available is not None:
                        self.size_for(self._available)
                        x=min(max(self.x(),self._available.left()),self._available.right()-self.width()+1)
                        y=min(max(self.y(),self._available.top()),self._available.bottom()-self.height()+1)
                        self.move(x,y)
                button.toggled.connect(toggle)
                button.setChecked(self._shown_preferences.popup_expand_articles)
                toggle(button.isChecked())
                button.show()
                if self._truncated:
                    warning=self.label(TRUNCATED)
                    self.body.addWidget(warning)
                    warning.show()
            if context and self._shown_preferences.popup_show_context:
                self.context_heading.show()
                self.context_source.setText(display_text(context,8000))
                self.context_source.show()
                self.context_fragment.setVisible(not value.context_complete)
            self.update_context(value)
            if save_error:
                self.footer.setText(SAVE_ERROR)
            elif value.meaning_save_error:
                self.footer.setText(MEANING_SAVE_ERROR)
            elif value.saved and value.count is not None:
                self.footer.setText(f'Искали {value.count} раз')
            elif value.kind=='sentence':
                self.footer.setText('Текст не добавлен в историю слов.')
        def update_context(self,value):
            contextual=bool(value.context_meaning and self._shown_preferences.popup_show_meaning)
            self.primary_translation.setVisible(bool(self.primary_translation.text()) and not contextual)
            self.meaning_value._role=(1.3,True) if contextual else (1,False)
            self.font_for(self.meaning_value)
            if value.context_meaning:
                meaning=value.context_meaning
            elif value.meaning_pending:
                meaning='Определяем значение в контексте…'
            elif value.meaning_error:
                meaning=MEANING_REASONS.get(value.meaning_error)
                if meaning is None:
                    reason=REASONS.get(value.meaning_error,('Перевод недоступен',''))[0].lower()
                    meaning='Значение в контексте недоступно: '+reason+'.'
            else:
                meaning=''
            self.meaning_value.setText(display_text(meaning,1000))
            self.meaning_heading.setVisible(bool(meaning) and self._shown_preferences.popup_show_meaning)
            self.meaning_value.setVisible(bool(meaning) and self._shown_preferences.popup_show_meaning)
            if value.context_translation:
                text='Перевод контекста\n'+value.context_translation
            elif value.context_pending:
                text='Переводим контекст…'
            elif value.context_error=='busy':
                text='Перевод контекста пока недоступен.'
            elif value.context_error:
                reason=REASONS.get(value.context_error,('Перевод недоступен',''))[0].lower()
                text='Перевод контекста недоступен: '+reason+'.'
            else:
                text=''
            self.context_value.setText(display_text(text,8000))
            self.context_value.setVisible(bool(text) and self._shown_preferences.popup_show_context)
            self.cache_warning.setText(CACHE_ERROR if value.cache_error else '')
            self.cache_warning.setVisible(bool(value.cache_error))
        def article_caption(self,button):
            prefix='Свернуть статью — ' if button.isChecked() else 'Показать полную статью — '
            caption=prefix+button._article_name
            metrics=button.fontMetrics()
            available=max(1,self.width()-56-metrics.horizontalAdvance(prefix))
            button.setText(prefix+metrics.elidedText(button._article_name,Qt.TextElideMode.ElideRight,available))
            button.setAccessibleName(caption)
            button.setToolTip(caption)
        def size_for(self,available):
            self._available=available
            from . import gnome
            if gnome.active():
                self.setMinimumHeight(0)
                self.setMaximumHeight(16777215)
            width=min(440,max(1,available.width()-32) if available.width()>64 else available.width())
            self.setFixedWidth(width)
            for button in self._article_buttons:self.article_caption(button)
            self.layout_box.activate()
            body_width=max(1,width-32)
            for label in self._labels:
                if isinstance(label,PlainBlock):label.fit(body_width)
            self.body.invalidate()
            self.content_layout.invalidate()
            content_height=self.content_layout.heightForWidth(body_width)
            if content_height<0:
                content_height=self.content_layout.sizeHint().height()
            if gnome.active():
                # Qt 6.4 can retain a stale height-for-width after replacing nested blocks.
                content_height=max(content_height,self.content_layout.minimumSize().height())
            chrome=self.title.heightForWidth(max(1,body_width-self.close_button.sizeHint().width()-8))
            chrome=max(chrome,self.close_button.sizeHint().height())+self.footer.sizeHint().height()+56
            limit=min(540,max(1,available.height()-32) if available.height()>64 else available.height())
            height=min(limit,max(140,content_height+chrome))
            # Mutter's move configure must not restore the previous card's height.
            if gnome.active():self.setFixedHeight(height)
            self.resize(width,height)
        def hide_for_capture(self):
            self._armed=False
            self.timer.stop()
            self.hide()
            self.setUpdatesEnabled(True)
        def dismiss(self):
            owner=getattr(self,'scene_owner',None)
            if self.isVisible() or (owner is not None and owner.scene_window is not None):
                self.hide_for_capture()
                self.dismissed.emit()
        def expire(self):
            owner=getattr(self,'scene_owner',None)
            if owner is not None and owner.scene_window is not None and self.isVisible() and self.underMouse():
                self.timer.start(self._duration)
                return
            self.dismiss()
        def leaveEvent(self,event):
            owner=getattr(self,'scene_owner',None)
            if owner is not None and owner.scene_window is not None and self.isVisible():
                self.timer.start(self._duration)
            super().leaveEvent(event)
        def keyPressEvent(self,event):
            if event.key()==Qt.Key.Key_Escape:
                self.dismiss();event.accept()
            else:
                super().keyPressEvent(event)
        def closeEvent(self,event):
            self.dismiss()
            event.accept()
        def event(self,event):
            if event.type()==QEvent.Type.WindowDeactivate and self._armed and self.isVisible():
                owner=getattr(self,'scene_owner',None)
                if owner is not None and owner.scene_window is not None:
                    if owner._focus:owner._scene_focus_event(QApplication.focusWindow())
                    return super().event(event)
                menu=QApplication.activePopupWidget()
                if menu is None or not self.isAncestorOf(menu):
                    self.dismiss()
            return super().event(event)
        def eventFilter(self,watched,event):
            owner=getattr(self,'scene_owner',None)
            if (self.isVisible() or (owner is not None and owner.scene_window is not None)) and isinstance(watched,QWidget):
                inside=watched==self or self.isAncestorOf(watched)
                if owner is not None and owner.scene_window is not None:
                    inside=inside or watched==owner.scene_window or owner.scene_window.isAncestorOf(watched)
                deliberate=event.type() in (QEvent.Type.MouseButtonPress,QEvent.Type.MouseButtonDblClick,QEvent.Type.KeyPress,QEvent.Type.Wheel)
                dragging=event.type()==QEvent.Type.MouseMove and event.buttons()!=Qt.MouseButton.NoButton
                if inside and (deliberate or dragging) and self.timer.isActive():
                    self.timer.start(self._duration)
                elif not inside and self._armed and event.type()==QEvent.Type.MouseButtonPress:
                    self.dismiss()
            return False
        def changeEvent(self,event):
            super().changeEvent(event)
            if event.type() in (QEvent.Type.ApplicationFontChange,QEvent.Type.FontChange):
                for label in getattr(self,'_labels',()):
                    self.font_for(label)

    @pyqtClassInfo('D-Bus Interface',SERVICE)
    class Owner(QObject):
        def __init__(self,env,*,engine_factory=None,focus=True,on_quit=None):
            super().__init__()
            self.env=env
            self._focus=focus
            self._on_quit=on_quit or QApplication.instance().quit
            self._stopping=False
            self._identity=None
            self._timing=timing.Sink()
            self._timing_request=None
            self._meaning_timed=False
            self._displayed=None
            self._known_cards=set()
            self._learning_conn=None
            self.words_window=None
            self.review_window=None
            self.settings_window=None
            self.home_window=None
            self._home_focus_thread=None
            self._home_token=''
            self.scene_window=None
            self._scene_id=None
            self._scene_pending=False
            self._scene_focus_armed=False
            self._popup_timeout=20
            self._focus_thread=None
            self._focus_pending=None
            self._waiting_ready=None
            self._waiting_context=None
            self._paint_revision=None
            self.popup_uuid=None
            self.presentations=0
            self.bridge=Bridge(self)
            self.bridge.event.connect(self.receive,Qt.ConnectionType.QueuedConnection)
            self.bridge.focus_done.connect(self.focus_done,Qt.ConnectionType.QueuedConnection)
            self.popup=Popup()
            self.popup.scene_owner=self
            self.popup.dismissed.connect(self.dismiss)
            self.popup.card_button.clicked.connect(self.add_card)
            self.engine=(engine_factory or core.Engine)(self.bridge.event.emit,source=core.Source(env))
            if self._focus:QApplication.instance().focusWindowChanged.connect(self._scene_focus_event)
            from .settings_gui import components as settings_components
            self._SettingsWindow,ApplyController=settings_components()
            self.settings_controller=ApplyController(self.engine,self)
            self.settings_controller.applied.connect(self._settings_applied)
            self.settings_controller.initialized.connect(self._settings_applied)
            self.settings_controller.invalidating.connect(self._invalidate_settings)
            self.settings_controller.initialize()
            self.tray=QSystemTrayIcon(QIcon.fromTheme('accessories-dictionary',QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView)),self)
            self.tray.setToolTip('LookUp Linux')
            self.menu=QMenu()
            self.menu.addAction('Открыть LookUp Linux',self.open_home)
            self.menu.addSeparator()
            self.future_actions=[]
            for name in ('Слова','Повторение','Настройки'):
                action=self.menu.addAction(name)
                action.setEnabled(False)
                self.future_actions.append(action)
            self.future_actions[0].setEnabled(True)
            self.future_actions[0].triggered.connect(self.open_words)
            self.future_actions[1].setEnabled(True)
            self.future_actions[1].triggered.connect(self.open_review)
            self.future_actions[2].setEnabled(True)
            self.future_actions[2].triggered.connect(self.open_settings)
            self.menu.addSeparator()
            self.menu.addAction('Выход',self.quit)
            self.tray.setContextMenu(self.menu)
            self.tray.activated.connect(self._tray_activated)
            self.tray.show()
        def _tray_activated(self,reason):
            if reason in (QSystemTrayIcon.ActivationReason.Trigger,QSystemTrayIcon.ActivationReason.DoubleClick):
                self.open_home()
        @pyqtSlot(str,result=int)
        def Open(self,token=''):
            if self._stopping or not valid_token(token):return 0
            self._home_token=token
            self.open_home()
            return 1
        def open_home(self):
            if self._stopping:return
            if self.home_window is None:
                self.home_window=QWidget()
                self.home_window.setWindowTitle('LookUp Linux')
                layout=QVBoxLayout(self.home_window)
                layout.setContentsMargins(16,16,16,16);layout.setSpacing(8)
                heading=QLabel('Перевод английских слов')
                font=heading.font();font.setBold(True);heading.setFont(font)
                layout.addWidget(heading)
                self.home_instructions=QLabel()
                self.home_instructions.setWordWrap(True)
                self.home_instructions.setTextFormat(Qt.TextFormat.PlainText)
                self.home_instructions.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                layout.addWidget(self.home_instructions)
                self.home_buttons={}
                for name,action in (('Настройки',self.open_settings),('Слова',self.open_words),('Повторение',self.open_review)):
                    button=QPushButton(name)
                    button.clicked.connect(action);layout.addWidget(button)
                    self.home_buttons[name]=button
                status=QLabel('При закрытии этого окна перевод продолжает работать в трее.\nОткрыть окно снова можно через меню приложений или щелчком по значку в трее.')
                status.setWordWrap(True);layout.addWidget(status)
                QShortcut(QKeySequence('Escape'),self.home_window,activated=self.home_window.close)
            self._home_text()
            available=QApplication.primaryScreen().availableGeometry()
            self.home_window.resize(min(440,available.width()),min(self.home_window.sizeHint().height(),available.height()))
            self.home_window.show();self.home_window.raise_();self.home_window.activateWindow()
            if self._focus:QTimer.singleShot(100,self._activate_home)
        def _activate_home(self):
            if self._stopping or self.home_window is None or not self.home_window.isVisible():return
            if self._home_focus_thread is not None and self._home_focus_thread.is_alive():return
            env=dict(self.env)
            if self._home_token:env['XDG_ACTIVATION_TOKEN']=self._home_token
            self._home_token=''
            def activate():
                try:
                    from . import gnome
                    if gnome.active(env):return
                    windows=platform.run(['kdotool','search','--all','--pid',str(os.getpid()),'--name','^LookUp Linux$'],env,limit=4096).decode().split()
                    if windows and not self._stopping:
                        platform.window_action(env,os.getpid(),windows[0],'windowactivate')
                except platform.PlatformError:pass
            self._home_focus_thread=threading.Thread(target=activate,name='lookup-home-focus',daemon=True)
            self._home_focus_thread.start()
        def _home_text(self):
            if self.home_window is not None:
                self.home_instructions.setText('Наведите курсор на английское слово или выделите текст и нажмите '+
                    self.popup.preferences.shortcut+'.\nEsc закрывает перевод и возвращает управление приложению.')
        def _learning_connection(self):
            if self._learning_conn is None:
                from .store import open_store
                conn=open_store(timeout=0.05)
                try:
                    conn.execute('PRAGMA busy_timeout=50')
                except Exception:
                    conn.close()
                    raise
                self._learning_conn=conn
            return self._learning_conn
        def _refresh_learning(self):
            source=self.sender()
            for window in (self.words_window,self.review_window):
                if window is not None and window is not source and window.isVisible():
                    window.refresh()
        def _open_learning(self,which):
            if self._stopping:return
            try:
                from .learning_gui import components as learning_components
                classes=learning_components()
                attribute='words_window' if which==0 else 'review_window'
                window=getattr(self,attribute)
                if window is None:
                    window=classes[which](self._learning_connection())
                    window.changed.connect(self._refresh_learning)
                    setattr(self,attribute,window)
                window.refresh()
                window.show()
                window.raise_()
                window.activateWindow()
            except (sqlite3.Error,OSError,ValueError,MigrationError,SchemaTooNewError):
                QMessageBox.warning(None,'LookUp Linux','Не удалось открыть сохранённые данные. Повторите попытку.')
        def open_words(self):
            self._open_learning(0)
        def open_review(self):
            self._open_learning(1)
        def _settings_applied(self,value):
            self._popup_timeout=value.popup_timeout
            self.popup.preferences=value
            self._home_text()
        def _invalidate_settings(self):
            self._end_scene()
            self.engine.dismiss(self._identity)
            self._identity=None
            self._focus_pending=None
            self._clear_displayed()
            self.popup.hide_for_capture()
        def open_settings(self):
            if self._stopping:return
            if self.settings_window is None:
                self.settings_window=self._SettingsWindow(self.settings_controller)
            self.settings_window.refresh()
            available=QApplication.primaryScreen().availableGeometry()
            self.settings_window.resize(min(self.settings_window.width(),available.width()),
                                        min(self.settings_window.height(),available.height()))
            self.settings_window.show()
            self.settings_window.raise_()
            self.settings_window.activateWindow()
        def _clear_displayed(self):
            self._displayed=None
            self._waiting_ready=self._waiting_context=None
            self.popup.card_button.setEnabled(False)
            self.popup.card_button.hide()
        def _bind_displayed(self,event):
            value=event.result
            if value.kind not in ('word','phrase') or not value.key or not (value.context_meaning or value.translation):
                self._clear_displayed()
                return
            self._displayed=(event.id,dict(word=value.key,translation=value.translation,
                meaning=value.context_meaning,provider=value.meaning_provider,
                context=event.context,span=event.span))
            known=value.key in self._known_cards
            self.popup.card_button.setText('В карточках' if known else 'В карточки')
            self.popup.card_button.setEnabled(not known)
            self.popup.card_button.show()
            if known:
                self.popup.card_status.setText('Уже в карточках.')
                self.popup.card_status.show()
        def add_card(self):
            if self._stopping or self._displayed is None or not self.popup.isVisible():return
            identity,snapshot=self._displayed
            if not self.engine.current(identity):return
            from . import learning
            try:
                outcome=learning.add_card(self._learning_connection(),dict(snapshot))
            except (sqlite3.Error,OSError,ValueError,MigrationError,SchemaTooNewError):
                self.popup.card_status.setText('Не удалось сохранить карточку. Повторите попытку.')
                self.popup.card_status.show()
                return
            self._known_cards.add(snapshot['word'])
            self.popup.card_button.setText('В карточках')
            self.popup.card_button.setEnabled(False)
            self.popup.card_status.setText('Добавлено в карточки.' if outcome=='created' else 'Уже в карточках.')
            self.popup.card_status.show()
            self._refresh_learning()
        @pyqtSlot(str,result=int)
        def Trigger(self,token):
            entered=time.monotonic_ns()
            if not valid_token(token) or self._stopping:
                return 0
            token=''
            snapshot_error=False
            try:
                snapshot=core.capture.take_hotkey(self.env)
            except core.platform.PlatformError as error:
                if error.reason=='hotkey_consumed':return os.getpid()
                snapshot=None
                snapshot_error=True
            if self.scene_window is not None:
                self._end_scene()
                return os.getpid()
            identity=self.engine.begin()
            if identity is None:
                return 0
            self._identity=identity
            self._timing_request=(identity,entered)
            self._meaning_timed=False
            self._timing.emit('trigger',identity,at_ns=entered)
            self._clear_displayed()
            was_visible=self.popup.isVisible()
            self.popup.hide_for_capture()
            if snapshot_error:
                self.receive(core.Event(identity,'error',error='capture_failed'))
                return os.getpid()
            if snapshot is not None:
                self._timing.emit('capture',identity,at_ns=snapshot.capture_ns,
                                  elapsed_ms=(snapshot.capture_ns-snapshot.input_ns)/1e6)
                self._time('queue',identity)
                self._scene_pending=True
                self.engine.enqueue_scene(identity,snapshot)
            elif was_visible:
                QTimer.singleShot(75,lambda:self._enqueue(identity))
            else:
                self._enqueue(identity)
            return os.getpid()
        def _enqueue(self,identity):
            if self.engine.current(identity):
                self._time('queue',identity)
                self._scene_pending=True
                self.engine.enqueue_scene(identity)
        def _time(self,stage,identity,**fields):
            if self._timing_request is None or self._timing_request[0]!=identity:return
            now=time.monotonic_ns()
            self._timing.emit(stage,identity,at_ns=now,
                              elapsed_ms=(now-self._timing_request[1])/1e6,**fields)
        def _time_meaning(self,event):
            if not self._meaning_timed and isinstance(event.result.context_meaning,str) and event.result.context_meaning.strip():
                self._meaning_timed=True
                self._time('meaning_ready',event.id,engine_ms=event.elapsed_ms,
                           meaning_cache=int(event.result.meaning_from_cache),**event.result.timings)
        def dismiss(self):
            if self._end_scene():return
            self.engine.dismiss(self._identity)
            self._clear_displayed()
        def _end_scene(self):
            if self.scene_window is None and not self._scene_pending:return False
            layer=self.scene_window
            session_id=self._scene_id
            self.scene_window=None;self._scene_id=None;self._scene_pending=False;self._scene_focus_armed=False
            self.popup._armed=False
            if self.popup.windowHandle() is not None:self.popup.windowHandle().setTransientParent(None)
            if layer is not None:
                layer.release();layer.deleteLater()
            self.engine.close_scene(session_id)
            self.engine.dismiss(self._identity)
            self._identity=None
            self._focus_pending=None;self._paint_revision=None
            self._clear_displayed()
            self.popup.hide_for_capture()
            return True
        def _scene_focus_event(self,window):
            if self.scene_window is None:return
            if window is not None and window in (self.scene_window.windowHandle(),self.popup.windowHandle()):
                self._scene_focus_armed=True
                return
            if self._scene_focus_armed:
                session_id=self._scene_id
                # Wayland can report no focus briefly between our two surfaces.
                QTimer.singleShot(75,lambda:self.scene_focus_changed(QApplication.focusWindow())
                    if self._scene_id==session_id and self._scene_focus_armed else None)
        def scene_focus_changed(self,window):
            if self.scene_window is None:return
            owned=(self.scene_window,self.popup)
            handles=tuple(widget.windowHandle() for widget in owned)
            menu=QApplication.activePopupWidget()
            if (window is not None and (window in owned or window in handles)) or (
                menu is not None and any(widget.isAncestorOf(menu) for widget in owned)):
                return
            self._end_scene()
        def _show_scene(self,event):
            from .selection_gui import components as selection_components
            try:
                layer=selection_components()(event.scene)
                self.scene_window=layer;self._scene_id=event.scene.session_id;self._scene_pending=False
                layer.selected.connect(self.select_scene)
                layer.dismissed.connect(self.dismiss)
                layer.present(self._focus)
                self.popup.winId()
                self.popup.windowHandle().setTransientParent(layer.windowHandle())
                self.popup._duration=self._popup_timeout*1000
                self.popup.timer.start(self.popup._duration)
            except (ValueError,RuntimeError,TypeError):
                self._scene_pending=True
                self._end_scene()
                identity=self.engine.begin()
                if identity is not None:self.receive(replace(event,id=identity,stage='error',scene=None,error='capture_failed'))
        def select_scene(self,point):
            if self.scene_window is None or self._stopping:return
            identity=self.engine.begin()
            if identity is None:
                self._end_scene();return
            self._identity=identity
            self._timing_request=(identity,time.monotonic_ns());self._meaning_timed=False
            self._focus_pending=None;self._paint_revision=None
            self._clear_displayed();self.popup.hide_for_capture()
            self.scene_window.set_status('Ищем перевод…')
            self.popup._duration=self._popup_timeout*1000
            self.popup.timer.start(self.popup._duration)
            if not self.engine.select_scene(identity,self._scene_id,point):self._end_scene()
        def receive(self,event):
            if event.stage=='reload':
                self.settings_controller.ack(event)
                return
            if self._stopping or not self.engine.current(event.id):
                return
            self._identity=event.id
            if event.stage=='scene':
                self._show_scene(event)
                return
            if self.scene_window is None and event.mode=='primary':self._scene_pending=False
            if event.stage=='context':
                if self._waiting_ready is not None:
                    self._waiting_context=event
                    return
                if self.popup.isVisible():
                    self.popup.update_context(event.result)
                    self._bind_displayed(event)
                    self._time_meaning(event)
                    if event.result.meaning_save_error:
                        self.popup.footer.setText(MEANING_SAVE_ERROR)
                return
            if event.stage=='frozen':
                self._clear_displayed()
                self.popup.loading()
            elif event.stage=='ready':
                if self._focus:
                    handle=self.popup.windowHandle()
                    if handle is None or not handle.isExposed():
                        self._waiting_ready=(event,time.monotonic()+1)
                        if not self.popup.isVisible():
                            self.popup.loading()
                            self.present(replace(event,stage='frozen',result=None))
                        self.popup.timer.stop()
                        QTimer.singleShot(10,self.ready_when_exposed)
                        return
                    # Mutter needs a committed buffer to acknowledge a Wayland resize.
                    from . import gnome
                    if not gnome.active(self.env):self.popup.setUpdatesEnabled(False)
                if timing.useful(event.result):
                    self._time('useful_ready',event.id,engine_ms=event.elapsed_ms,**event.result.timings)
                self.popup.result(event.result,event.context,event.save_error)
                self._bind_displayed(event)
                self._time_meaning(event)
                if self.scene_window is not None:
                    self.scene_window.set_selection(event.result.key or '',event.selection_box)
            else:
                self._time('error',event.id,engine_ms=event.elapsed_ms)
                if self.scene_window is not None and event.error=='not_found':
                    self._clear_displayed();self.popup.hide_for_capture()
                    self.scene_window.set_selection('')
                    self.popup.timer.start(self._popup_timeout*1000)
                    return
                if self._end_scene():
                    identity=self.engine.begin()
                    if identity is None:return
                    self._identity=identity
                    event=replace(event,id=identity)
                self._clear_displayed()
                self.popup.error(event.error)
            from . import gnome
            if event.stage=='ready' and gnome.active(self.env):
                # Qt 6.4 queues nested text/layout sizes until the next event turn.
                QTimer.singleShot(0,lambda:self.present(event) if not self._stopping and self.engine.current(event.id) else None)
            else:self.present(event)
        def ready_when_exposed(self):
            if self._waiting_ready is None:return
            event,deadline=self._waiting_ready
            if self._stopping or not self.engine.current(event.id) or not self.popup.isVisible():
                self._waiting_ready=self._waiting_context=None
                return
            if not self.popup.windowHandle().isExposed() and time.monotonic()<deadline:
                QTimer.singleShot(10,self.ready_when_exposed)
                return
            context=self._waiting_context
            self._waiting_ready=self._waiting_context=None
            if not self.popup.windowHandle().isExposed():
                self.receive(replace(event,stage='error',result=None,error='placement_failed'))
                return
            self.receive(event)
            if context is not None:self.receive(context)
        def present(self,event):
            self.presentations+=1
            if not self.popup.updatesEnabled():self._paint_revision=self.presentations
            point=event.point
            screen=QApplication.screenAt(QPoint(round(point[0]),round(point[1]))) if point else None
            screen=screen or QApplication.primaryScreen()
            available=QRect(*event.available) if event.available else screen.availableGeometry()
            if self.scene_window is not None:available=available.intersected(self.scene_window.popup_area())
            point=point or (available.center().x(),available.center().y())
            self.popup.size_for(available)
            target=platform.popup_rect(point,(self.popup.width(),self.popup.height()),
                                       (available.x(),available.y(),available.width(),available.height()))
            self.popup._armed=False
            self.popup._duration=self._popup_timeout*1000
            self.popup.setGeometry(*target)
            self.popup.show()
            if self.popup.updatesEnabled():self.popup.timer.start(self.popup._duration)
            else:self.popup.timer.stop()
            self._time('present',event.id,useful=int(timing.useful(event.result)))
            if not self._focus:
                self.popup._armed=True
                return
            self.popup.raise_()
            self.popup.activateWindow()
            self.popup.windowHandle().requestActivate()
            self._focus_pending=(event.id,self.presentations,target)
            QTimer.singleShot(75,self.start_focus)
        def start_focus(self):
            if self._stopping or self._focus_pending is None or (self._focus_thread is not None and self._focus_thread.is_alive()):
                return
            identity,revision,target=self._focus_pending
            self._focus_pending=None
            def run():
                uuid,error=None,None
                try:
                    if self.engine.current(identity):
                        from . import gnome
                        if gnome.active(self.env):
                            gnome.place(os.getpid(),TITLE,*target[:2])
                        else:
                            values=platform.run(['kdotool','search','--all','--pid',str(os.getpid()),'--name','^'+re.escape(TITLE)+'$'],self.env,limit=4096).decode().split()
                            uuid=values[0]
                            for action,args in (('windowmove',target[:2]),('windowraise',()),('windowactivate',())):
                                if not self.engine.current(identity):break
                                platform.window_action(self.env,os.getpid(),uuid,action,*args)
                except Exception:
                    error='focus_failed'
                self.bridge.focus_done.emit((identity,revision,uuid,error))
            self._focus_thread=threading.Thread(target=run,name='lookup-focus',daemon=True)
            self._focus_thread.start()
        def focus_done(self,result):
            identity,revision,uuid,error=result
            if not self._stopping and revision==self.presentations and self.engine.current(identity) and self.popup.isVisible():
                self.popup_uuid=uuid
                self.focus_error=error
                if error and (self.scene_window is not None or self._scene_pending):
                    point=(self.popup.x(),self.popup.y())
                    self._end_scene()
                    identity=self.engine.begin()
                    if identity is not None:
                        self.receive(core.Event(identity,'error',point=point,error='placement_failed'))
                    return
                if self._paint_revision==revision:
                    if error:
                        self.popup.error('placement_failed')
                        self._clear_displayed()
                    self._paint_revision=None
                    self.popup.setUpdatesEnabled(True)
                    self.popup.timer.start(self.popup._duration)
                QTimer.singleShot(300,lambda:self.arm(identity,revision))
            if self._focus_pending is not None:
                QTimer.singleShot(25,self.start_focus)
        def arm(self,identity,revision):
            if revision==self.presentations and self.engine.current(identity) and self.popup.isVisible():
                self.popup._armed=True
        def quit(self):
            if self._stopping:return
            self._end_scene()
            self._stopping=True
            self.settings_controller.shutdown()
            if self.settings_window is not None:
                self.settings_window.close()
                self.settings_window.deleteLater()
                self.settings_window=None
            if self.home_window is not None:
                self.home_window.close()
                self.home_window.deleteLater()
                self.home_window=None
            self._clear_displayed()
            self.engine.stop()
            self._focus_pending=None
            self.popup.hide_for_capture()
            self.tray.hide()
            for window in (self.words_window,self.review_window):
                if window is not None:
                    window.close()
                    window.deleteLater()
            self.words_window=self.review_window=None
            if self._learning_conn is not None:
                self._learning_conn.close()
                self._learning_conn=None
            self.poll_quit()
        def poll_quit(self):
            focus_alive=self._focus_thread is not None and self._focus_thread.is_alive()
            focus_alive=focus_alive or (self._home_focus_thread is not None and self._home_focus_thread.is_alive())
            if self.engine.is_alive() or focus_alive or self.settings_controller.is_alive():
                QTimer.singleShot(25,self.poll_quit)
            else:
                self._on_quit()

    _components=(Popup,Owner)
    return _components


def run(trigger=False,background=False):
    token=os.environ.pop('XDG_ACTIVATION_TOKEN','')
    os.environ.pop('DESKTOP_STARTUP_ID',None)
    if not valid_token(token):token=''
    env=platform.session_env()
    if not trigger and not background and token:env['XDG_ACTIVATION_TOKEN']=token
    os.environ.update(env)
    from PyQt6.QtCore import QCoreApplication,QTimer
    from PyQt6.QtDBus import QDBusConnection,QDBusMessage,QDBus
    if trigger:
        application=QCoreApplication(['lookup-trigger'])
    else:
        from PyQt6.QtWidgets import QApplication
        application=QApplication(['lookup'])
        application.setApplicationName('LookUp Linux')
        application.setDesktopFileName(DESKTOP.removesuffix('.desktop'))
        application.setQuitOnLastWindowClosed(False)
    bus=QDBusConnection.sessionBus()
    def forward(method='Trigger'):
        message=QDBusMessage.createMethodCall(SERVICE,OBJECT,SERVICE,method)
        message.setArguments([token])
        reply=bus.call(message,QDBus.CallMode.Block,1000)
        if reply.type()==QDBusMessage.MessageType.ErrorMessage:
            return None
        values=reply.arguments()
        return values[0] if values and type(values[0]) is int and values[0]>0 else None
    if trigger:
        if forward() is not None:
            return 0
        present=bus.interface().isServiceRegistered(SERVICE)
        if not present.isValid():
            return 1
        if not present.value():
            from .lifecycle import launch_command
            command,directory=launch_command('--background')
            subprocess.Popen(command,env=env,
                             cwd=directory,stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL,
                             stderr=None if env.get('LOOKUP_TIMING')=='1' else subprocess.DEVNULL,
                             start_new_session=True)
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            if forward() is not None:
                return 0
            time.sleep(.05)
        return 1
    if not bus.registerService(SERVICE):
        return 0 if background or forward('Open') is not None else 1
    from .lifecycle import ensure_entries,ensure_shortcut,LifecycleError
    core.capture.enable_hotkey_bridge(env)
    registration_error=None
    try:
        ensure_entries()
        ensure_shortcut()
    except LifecycleError as error:registration_error=error.reason
    token=''
    _,Owner=components()
    owner=Owner(env)
    owner.lifecycle_error=registration_error
    if registration_error is not None:
        QTimer.singleShot(0,owner.open_settings)
    if not background:
        QTimer.singleShot(0,owner.open_home)
    if not bus.registerObject(OBJECT,owner,QDBusConnection.RegisterOption.ExportAllSlots):
        owner.quit()
        owner.engine.join(12)
        return 1
    application.aboutToQuit.connect(owner.quit)
    try:
        return application.exec()
    finally:
        owner.quit()
        owner.engine.join(12)
        if owner._focus_thread is not None:
            owner._focus_thread.join(3)
        bus.unregisterObject(OBJECT)
        bus.unregisterService(SERVICE)
