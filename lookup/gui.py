"""Lazy native KDE owner/client and translation card. No Qt import on import."""
import os
import math
from pathlib import Path
import subprocess
import sys
import threading
import time

from . import app as core, platform

SERVICE='org.lookup.Linux'
OBJECT='/Lookup'
TITLE='Перевод LookUp Linux'
DESKTOP='org.lookup.Linux.desktop'
_components=None

REASONS={
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
}
PACKAGES={'missing_tesseract':'tesseract','missing_eng':'tesseract-data-eng',
          'missing_pyqt6':'python-pyqt6','missing_kdotool':'kdotool','missing_kscreen':'libkscreen'}
SAVE_ERROR='Не удалось сохранить поиск. Перевод доступен; повторите поиск позже.'
CACHE_ERROR='Не удалось обновить кэш перевода.'
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
    python=Path(python or sys.executable)
    directory=Path(directory or Path(__file__).resolve().parents[1])
    def quote(path):
        value=str(path)
        if not path.is_absolute() or any(c in value for c in '\r\n\x00'):
            raise ValueError('invalid_desktop_path')
        for char in ('\\','"','`','$'):
            value=value.replace(char,'\\'+char)
        return '"'+value.replace('%','%%')+'"'
    executable=quote(python)
    quote(directory)  # Validate the separate Desktop Entry string field too.
    workdir=str(directory).replace('\\','\\\\')
    return ('[Desktop Entry]\nType=Application\nName=LookUp Linux\n'
            'Comment=LookUp Linux owned application trigger\n'
            f'Exec={executable} -m lookup --trigger\nPath={workdir}\n'
            'Icon=accessories-dictionary\nTerminal=false\nStartupNotify=true\n'
            'X-KDE-Shortcuts=Meta+Shift+D\n')


def components():
    global _components
    if _components is not None:
        return _components
    from PyQt6.QtCore import QObject,QTimer,Qt,QEvent,QPoint,QRect,pyqtSignal,pyqtSlot,pyqtClassInfo
    from PyQt6.QtGui import QFont,QIcon,QKeySequence,QShortcut,QTextOption
    from PyQt6.QtWidgets import (QApplication,QWidget,QLabel,QVBoxLayout,QHBoxLayout,
                                 QScrollArea,QToolButton,QStyle,QFrame,QSizePolicy,
                                 QSystemTrayIcon,QMenu,QTextEdit)

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
            self._duration=20000
            self.timer=QTimer(self)
            self.timer.setSingleShot(True)
            self.timer.timeout.connect(self.dismiss)
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
            self.body=QVBoxLayout()
            self.body.setSpacing(8)
            self.content_layout.addLayout(self.body)
            self.content_layout.addSpacing(16)
            self.context_heading=self.label('Исходный текст',bold=True)
            self.context_source=self.label('',block=True)
            self.context_source.setAccessibleName('Исходный текст')
            self.context_value=self.label('',block=True)
            self.context_value.setAccessibleName('Перевод контекста')
            self.cache_warning=self.label('')
            for widget in (self.context_heading,self.context_source,self.context_value,self.cache_warning):
                self.content_layout.addWidget(widget)
                widget.hide()
            self.content_layout.addStretch()
            self.scroll.setWidget(content)
            self.layout_box.addWidget(self.scroll,1)
            self.footer=self.label('')
            self.footer.setAccessibleName('Сохранение поиска')
            self.layout_box.addWidget(self.footer)
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
            while self.body.count():
                widget=self.body.takeAt(0).widget()
                if widget is not None:
                    self._labels.remove(widget)
                    widget.hide();widget.deleteLater()
            for label in (self.context_heading,self.context_source,self.context_value,self.cache_warning):
                label.hide()
            self.footer.clear()
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
            for article in value.articles:
                if self.body.count():self.body.addSpacing(8)
                self.add('Словарь: '+article.dict_name,True)
                for pos,terms in article.senses:
                    self.add((pos+': ' if pos else '')+'; '.join(terms),True)
                self.add(article.text)
            if value.online:
                self.add(value.online.main)
                for pos,terms in value.online.parts:
                    self.add((pos+': ' if pos else '')+'; '.join(terms))
            if not value.online_enabled:
                self.add('Онлайн-перевод выключен.')
            if context:
                self.context_heading.show()
                self.context_source.setText(display_text(context,8000))
                self.context_source.show()
            self.update_context(value)
            if save_error:
                self.footer.setText(SAVE_ERROR)
            elif value.saved and value.count is not None:
                self.footer.setText(f'Искали {value.count} раз')
            elif value.kind=='sentence':
                self.footer.setText('Текст не добавлен в историю слов.')
        def update_context(self,value):
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
            self.context_value.setVisible(bool(text))
            self.cache_warning.setText(CACHE_ERROR if value.cache_error else '')
            self.cache_warning.setVisible(bool(value.cache_error))
        def size_for(self,available):
            width=min(440,max(1,available.width()-32) if available.width()>64 else available.width())
            self.setFixedWidth(width)
            self.layout_box.activate()
            body_width=max(1,width-32)
            for label in self._labels:
                if isinstance(label,PlainBlock):label.fit(body_width)
            self.body.invalidate()
            self.content_layout.invalidate()
            content_height=self.content_layout.heightForWidth(body_width)
            if content_height<0:
                content_height=self.content_layout.sizeHint().height()
            chrome=self.title.heightForWidth(max(1,body_width-self.close_button.sizeHint().width()-8))
            chrome=max(chrome,self.close_button.sizeHint().height())+self.footer.sizeHint().height()+56
            limit=min(540,max(1,available.height()-32) if available.height()>64 else available.height())
            self.resize(width,min(limit,max(140,content_height+chrome)))
        def hide_for_capture(self):
            self._armed=False
            self.timer.stop()
            self.hide()
        def dismiss(self):
            if self.isVisible():
                self.hide_for_capture()
                self.dismissed.emit()
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
                menu=QApplication.activePopupWidget()
                if menu is None or not self.isAncestorOf(menu):
                    self.dismiss()
            return super().event(event)
        def eventFilter(self,watched,event):
            if self.isVisible() and isinstance(watched,QWidget):
                inside=watched==self or self.isAncestorOf(watched)
                deliberate=event.type() in (QEvent.Type.MouseButtonPress,QEvent.Type.MouseButtonDblClick,QEvent.Type.KeyPress,QEvent.Type.Wheel)
                dragging=event.type()==QEvent.Type.MouseMove and event.buttons()!=Qt.MouseButton.NoButton
                if inside and (deliberate or dragging):
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
            self._focus_thread=None
            self._focus_pending=None
            self.popup_uuid=None
            self.presentations=0
            self.bridge=Bridge(self)
            self.bridge.event.connect(self.receive,Qt.ConnectionType.QueuedConnection)
            self.bridge.focus_done.connect(self.focus_done,Qt.ConnectionType.QueuedConnection)
            self.popup=Popup()
            self.popup.dismissed.connect(self.dismiss)
            self.engine=(engine_factory or core.Engine)(self.bridge.event.emit,source=core.Source(env))
            self.tray=QSystemTrayIcon(QIcon.fromTheme('accessories-dictionary',QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView)),self)
            self.tray.setToolTip('LookUp Linux')
            self.menu=QMenu()
            self.future_actions=[]
            for name in ('Слова','Повторение','Настройки'):
                action=self.menu.addAction(name)
                action.setEnabled(False)
                self.future_actions.append(action)
            self.menu.addSeparator()
            self.menu.addAction('Выход',self.quit)
            self.tray.setContextMenu(self.menu)
            self.tray.show()
        @pyqtSlot(str,result=int)
        def Trigger(self,token):
            if not valid_token(token) or self._stopping:
                return 0
            token=''
            identity=self.engine.begin()
            if identity is None:
                return 0
            self._identity=identity
            self.popup.hide_for_capture()
            QTimer.singleShot(75,lambda:self.engine.enqueue(identity) if self.engine.current(identity) else None)
            return os.getpid()
        def dismiss(self):
            self.engine.dismiss(self._identity)
        def receive(self,event):
            if self._stopping or not self.engine.current(event.id):
                return
            self._identity=event.id
            if event.stage=='context':
                if self.popup.isVisible():
                    self.popup.update_context(event.result)
                return
            if event.stage=='frozen':
                self.popup.loading()
            elif event.stage=='ready':
                self.popup.result(event.result,event.context,event.save_error)
            else:
                self.popup.error(event.error)
            self.present(event)
        def present(self,event):
            self.presentations+=1
            point=event.point
            screen=QApplication.screenAt(QPoint(round(point[0]),round(point[1]))) if point else None
            screen=screen or QApplication.primaryScreen()
            available=QRect(*event.available) if event.available else screen.availableGeometry()
            point=point or (available.center().x(),available.center().y())
            self.popup.size_for(available)
            target=platform.popup_rect(point,(self.popup.width(),self.popup.height()),
                                       (available.x(),available.y(),available.width(),available.height()))
            self.popup._armed=False
            self.popup.setGeometry(*target)
            self.popup.show()
            self.popup.timer.start(self.popup._duration)
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
                        values=platform.run(['kdotool','search','--pid',str(os.getpid()),'--name',TITLE],self.env,limit=4096).decode().split()
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
                QTimer.singleShot(300,lambda:self.arm(identity,revision))
            if self._focus_pending is not None:
                QTimer.singleShot(25,self.start_focus)
        def arm(self,identity,revision):
            if revision==self.presentations and self.engine.current(identity) and self.popup.isVisible():
                self.popup._armed=True
        def quit(self):
            if self._stopping:return
            self._stopping=True
            self.engine.stop()
            self._focus_pending=None
            self.popup.hide_for_capture()
            self.tray.hide()
            self.poll_quit()
        def poll_quit(self):
            focus_alive=self._focus_thread is not None and self._focus_thread.is_alive()
            if self.engine.is_alive() or focus_alive:
                QTimer.singleShot(25,self.poll_quit)
            else:
                self._on_quit()

    _components=(Popup,Owner)
    return _components


def run(trigger=False):
    token=os.environ.pop('XDG_ACTIVATION_TOKEN','')
    os.environ.pop('DESKTOP_STARTUP_ID',None)
    if not valid_token(token):token=''
    env=platform.session_env()
    os.environ.update(env)
    from PyQt6.QtCore import QCoreApplication
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
    def forward():
        message=QDBusMessage.createMethodCall(SERVICE,OBJECT,SERVICE,'Trigger')
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
            subprocess.Popen([sys.executable,'-m','lookup','--app'],env=env,
                             cwd=Path(__file__).resolve().parents[1],stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            if forward() is not None:
                return 0
            time.sleep(.05)
        return 1
    if not bus.registerService(SERVICE):
        return 0
    token=''
    _,Owner=components()
    owner=Owner(env)
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
